import requests
from pydantic import BaseModel

class Contest(BaseModel):
    name: str
    start_time: int
    duration: int
    link: str

def fetch_contest_data() -> dict[str, list[Contest]]:
    # Using a third-party API for LeetCode contests
    lc = requests.get('https://alfa-leetcode-api.onrender.com/contests/upcoming')
    all_lc_contests = lc.json()['contests']

    # Fetching all Codeforces contests and filtering upcoming ones
    codeforces = requests.get('https://codeforces.com/api/contest.list')
    all_cf_contests = codeforces.json()['result']
    upcoming_cf_contests = [contest for contest in all_cf_contests if contest['phase'] == 'BEFORE']

    # TODO: Add CodeChef contests fetching logic

    all_data = {
        "leetcode": [
            Contest(
                name=contest['title'],
                start_time=contest['startTime'],
                duration=contest['duration'],
                link=f"https://leetcode.com/contest/{contest['title'].lower().replace(' ', '-')}/"
            )
            for contest in all_lc_contests
        ],
        "codeforces": [
            Contest(
                name=contest['name'],
                start_time=contest['startTimeSeconds'],
                duration=contest['durationSeconds'],
                link=f"https://codeforces.com/contests/{contest['id']}"
            )
            for contest in upcoming_cf_contests
        ],
        "codechef": []
    }

    return all_data
