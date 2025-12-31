from typing import Literal

from fastapi import FastAPI
from get_data import fetch_contest_data, PlatformResponse

app = FastAPI()

contest_data: dict[str, PlatformResponse] = fetch_contest_data()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/contests")
def all_contests():
    return contest_data

@app.get("/contests/{type}")
def contests(type: Literal["leetcode", "codeforces", "codechef"]):
    return contest_data[type]