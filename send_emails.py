import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time
from fastapi import APIRouter, HTTPException
from apscheduler.schedulers.background import BackgroundScheduler
from db.models.user import User
from db.session import SessionLocal
from core.config import settings
from db.repository.questions import get_a_random_question
from schemas.questions import Question
from apscheduler.triggers.cron import CronTrigger
import pytz

class EmailSender:
    def __init__(self):
        self.email_sender = settings.SENDER_EMAIL
        self.email_password = settings.EMAIL_PASSWORD
        self.smtp_server = 'smtp.gmail.com'
        self.port = 465

        if not self.email_password:
            raise ValueError("Email password not found in environment variables.")

    def send_email(self, receiver: str, subject: str, body: str):
        try:
            em = MIMEMultipart("alternative")
            em['From'] = self.email_sender
            em['To'] = receiver
            em['Subject'] = subject
            em.attach(MIMEText(body, "html"))

            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_server, self.port, context=context) as smtp:
                smtp.login(self.email_sender, self.email_password)
                smtp.sendmail(self.email_sender, receiver, em.as_string())
        except Exception as e:
            if isinstance(e, OSError) and e.errno == 10060:
                time.sleep(5)
                self.send_email(receiver, subject, body)
            else:
                raise HTTPException(status_code=500, detail="Failed to send email.")

router = APIRouter()
email_sender = EmailSender()

def send_email_to_subscribers():
    db = SessionLocal()
    
    question = get_a_random_question(db)
    if not question:
        raise HTTPException(status_code=500, detail="Failed to fetch question.")
    question_data = Question.from_orm(question)

    subject = "Today's Question"
    body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: system-ui, -apple-system, sans-serif; display: flex; justify-content: center; background-color: #f0f2f5; padding: 20px;">
        <div style="background: white; border-radius: 8px; width: 100%; max-width: 800px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <!-- Header -->
            <div style="background: #1a56db; color: white; padding: 16px 24px; display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 20px;">🏆</span>
                <span style="font-size: 20px; font-weight: 600;">Daily Coding Challenge</span>
            </div>
            <span style="background: #fbbf24; color: #000; padding: 4px 12px; border-radius: 16px; font-size: 14px; font-weight: 500;">{question_data.difficulty_name}</span>
            </div>

            <!-- Content -->
            <div style="padding: 24px;">
            <h2 style="margin: 0 0 16px 0; font-size: 24px; color: #111827;">{question_data.name}</h2>
            
            <p style="margin: 0 0 24px 0; color: #4b5563; line-height: 1.5;">
                {question_data.preview}
            </p>

            <!-- Stats Grid -->
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 24px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                <span style="color: #fbbf24; font-size: 20px;">⭐</span>
                <span style="color: #4b5563;">Score: {question_data.max_score}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                <span style="color: #60a5fa; font-size: 20px;">👥</span>
                <span style="color: #4b5563;">Success: {round(question_data.success_ratio, 2)}</span>
                </div>
            </div>

            <!-- Tags -->
            <div style="display: flex; gap: 8px; margin-bottom: 24px;">
                {question_data.skill if question_data.skill else ""}
            </div>

            <!-- Button -->
            <a href="{question_data.link}" style="width: 100%; background: #10b981; color: white; border: none; padding: 12px; border-radius: 6px; font-size: 16px; font-weight: 500; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; text-decoration: none;">
                Solve Challenge →
            </a>

            <!-- Footer -->
            <p style="text-align: center; margin: 24px 0 0 0; color: #6b7280;">
                Happy coding! - The Problem Piper Team
            </p>
            </div>
        </div>
        </body>
        </html>
        """

    try:
        subscribers = db.query(User).filter(User.is_subscribed == True).all()
        for subscriber in subscribers:
            email_sender.send_email(subscriber.email, subject, body)
    finally:
        db.close()

scheduler = BackgroundScheduler()
default_hour = 9
default_minute = 30

def configure_email_sending_time():
    ist = pytz.timezone('Asia/Kolkata')
    scheduler.add_job(
        send_email_to_subscribers, 
        CronTrigger(hour=default_hour, minute=default_minute, timezone=ist))
    