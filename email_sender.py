import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time
from fastapi import APIRouter, HTTPException
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()


class EmailSender:
    def __init__(self):
        self.email_sender = os.getenv("SENDER_EMAIL")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.smtp_server = "smtp.gmail.com"
        self.port = 465

        if not self.email_password:
            raise ValueError("Email password not found in environment variables.")

    def send_email(self, receiver: str, subject: str, body: str):
        try:
            em = MIMEMultipart("alternative")
            em["From"] = self.email_sender
            em["To"] = receiver
            em["Subject"] = subject
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
                raise HTTPException(
                    status_code=500, detail=f"Failed to send email: {str(e)}"
                )


router = APIRouter()
email_sender = EmailSender()


def format_duration(minutes):
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}h {mins}m" if mins > 0 else f"{hours}h"
    return f"{mins}m"


def get_platform_color(platform):
    colors = {
        "leetcode": {"bg": "#FFA116", "text": "#ffffff"},
        "codeforces": {"bg": "#1F8ACB", "text": "#ffffff"},
        "codechef": {"bg": "#5B4638", "text": "#ffffff"},
    }
    return colors.get(platform, {"bg": "#4F46E5", "text": "#ffffff"})


def parse_time_difference(start_time_str):
    try:
        contest_time = datetime.strptime(start_time_str.strip(), "%d %b %Y %H:%M:%S")
        now = datetime.now()
        diff = contest_time - now

        if diff.total_seconds() < 0:
            return "Started"

        days = diff.days
        hours = diff.seconds // 3600

        if days > 0:
            return f"in {days}d {hours}h"
        elif hours > 0:
            return f"in {hours}h"
        else:
            mins = (diff.seconds % 3600) // 60
            return f"in {mins}m"
    except:
        return ""


def generate_contest_cards(contest_data):
    cards_html = ""

    for platform, data in contest_data.items():
        if not data.success or not data.contests:
            continue

        p_color = get_platform_color(platform)
        platform_name = platform.capitalize()

        for contest in data.contests:
            time_until = parse_time_difference(contest.start_time)

            cards_html += f"""
            <div style="background: #ffffff; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid #E5E7EB; box-shadow: 0 1px 3px rgba(0,0,0,0.05); font-family: sans-serif;">
                
                <div style="margin-bottom: 16px;">
                    <div style="display: inline-block; background: {
                p_color["bg"]
            }; color: {
                p_color["text"]
            }; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px;">
                        {platform_name}
                    </div>

                    <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px;">
                        <h3 style="margin: 0; font-size: 18px; color: #111827; font-weight: 700; line-height: 1.3;">
                            {contest.name}
                        </h3>

                        {
                f'''
                        <span style="
                            background: #EEF2FF;
                            color: #4F46E5;
                            font-size: 12px;
                            font-weight: 700;
                            padding: 4px 8px;
                            border-radius: 6px;
                            white-space: nowrap;
                        ">
                            {time_until}
                        </span>
                        '''
                if time_until
                else ""
            }
                    </div>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                        <tr>
                            <td style="padding-bottom: 8px; font-size: 14px; color: #6B7280;">
                                <span style="margin-right: 4px;">📅</span> <b>Start:</b> {
                contest.start_time
            }
                            </td>
                        </tr>
                        <tr>
                            <td style="font-size: 14px; color: #6B7280;">
                                <span style="margin-right: 4px;">⏱️</span> <b>Duration:</b> {
                format_duration(contest.duration)
            }
                            </td>
                        </tr>
                    </table>
                </div>
                
                <a href="{
                contest.link
            }" style="display: block; background: #111827; color: #ffffff; text-decoration: none; padding: 12px; border-radius: 8px; font-weight: 600; font-size: 14px; text-align: center;">
                    View Contest →
                </a>
            </div>
            """
    return cards_html


def send_email_to_me():
    from main import all_contests

    contest_data = all_contests()

    total_contests = sum(
        len(data.contests) for data in contest_data.values() if data.success
    )

    if total_contests == 0:
        print("No contests to send")
        return

    contest_cards = generate_contest_cards(contest_data)
    current_date = datetime.now().strftime("%b %d, %Y")

    subject = f"🏆 Contest Update: {total_contests} events on {current_date}"
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Inter', -apple-system, system-ui, sans-serif; background-color: #F9FAFB; -webkit-font-smoothing: antialiased;">
        <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
            
            <div style="background: #4F46E5; background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); border-radius: 16px; padding: 40px 24px; text-align: center; margin-bottom: 32px;">
                <div style="font-size: 40px; margin-bottom: 16px;">🚀</div>
                <h1 style="margin: 0; color: #ffffff; font-size: 26px; font-weight: 800; letter-spacing: -0.02em;">
                    Upcoming Contests
                </h1>
                <p style="margin: 8px 0 20px 0; color: #E0E7FF; font-size: 16px; opacity: 0.9;">
                    {current_date}
                </p>
                <div style="display: inline-block; background: rgba(255, 255, 255, 0.2); border: 1px solid rgba(255, 255, 255, 0.3); padding: 6px 16px; border-radius: 100px;">
                    <span style="color: #ffffff; font-weight: 600; font-size: 13px;">
                        {total_contests} events tracked today
                    </span>
                </div>
            </div>
            
            {contest_cards}
            
            <div style="text-align: center; padding-top: 24px;">
                <p style="margin: 0; color: #6B7280; font-size: 14px; line-height: 1.5;">
                    Stay sharp and keep coding. 💪<br>
                    <span style="font-size: 12px; color: #9CA3AF;">Automated notification via Contest Tracker API</span>
                </p>
            </div>
            
        </div>
    </body>
    </html>
    """

    if receiver_email := os.getenv("MY_EMAIL"):
        try:
            email_sender.send_email(receiver_email, subject, body)
            print(f"Email sent successfully to {receiver_email}")
        except Exception as e:
            print(f"Failed to send email: {e}")
            raise
    else:
        raise ValueError("MY_EMAIL not found in environment variables")


scheduler = BackgroundScheduler()
default_hour = 9
default_minute = 30


def configure_email_sending_time():
    ist = pytz.timezone("Asia/Kolkata")
    scheduler.add_job(
        send_email_to_me,
        CronTrigger(hour=default_hour, minute=default_minute, timezone=ist),
    )
    scheduler.start()
    print(f"Email scheduler configured for {default_hour}:{default_minute:02d} IST")


@router.get("/send-test-email")
def send_test_email():
    try:
        send_email_to_me()
        return {"success": True, "message": "Email sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule-info")
def get_schedule_info():
    ist = pytz.timezone("Asia/Kolkata")
    next_run = None

    jobs = scheduler.get_jobs()
    if jobs:
        next_run_utc = jobs[0].next_run_time
        if next_run_utc:
            next_run = next_run_utc.astimezone(ist).strftime("%d %b %Y %H:%M:%S IST")

    return {
        "scheduled_time": f"{default_hour:02d}:{default_minute:02d} IST",
        "timezone": "Asia/Kolkata",
        "next_run": next_run,
        "scheduler_running": scheduler.running,
        "email_recipient": os.getenv("MY_EMAIL", "Not configured"),
    }
