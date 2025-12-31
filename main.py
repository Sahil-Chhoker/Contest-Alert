from typing import Literal
from fastapi import FastAPI
from contextlib import asynccontextmanager
from get_data import fetch_contest_data, PlatformResponse
from email_sender import router as email_router, configure_email_sending_time, scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the email scheduler
    configure_email_sending_time()
    print("Email scheduler started")
    yield
    # Shutdown: Stop the scheduler
    scheduler.shutdown()
    print("Email scheduler stopped")


app = FastAPI(lifespan=lifespan)

# Include the email router
app.include_router(email_router, prefix="/email", tags=["Email"])

contest_data: dict[str, PlatformResponse] = fetch_contest_data()


@app.get("/")
def read_root():
    return {
        "message": "Contest API",
        "endpoints": {
            "/contests": "Get all contests",
            "/contests/{type}": "Get contests by platform (leetcode, codeforces, codechef)",
            "/email/send-test-email": "Send test email manually",
            "/email/schedule-info": "Get scheduler information",
        },
    }


@app.get("/contests")
def all_contests():
    global contest_data
    contest_data = fetch_contest_data()
    return contest_data


@app.get("/contests/{type}")
def contests(type: Literal["leetcode", "codeforces", "codechef"]):
    global contest_data
    contest_data = fetch_contest_data()
    return contest_data[type]


@app.post("/contests/refresh")
def refresh_contests():
    global contest_data
    contest_data = fetch_contest_data()
    return {"message": "Contest data refreshed", "data": contest_data}
