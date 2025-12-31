import requests
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta

class Contest(BaseModel):
    name: str
    start_time: str
    duration: int
    link: str

class PlatformResponse(BaseModel):
    success: bool
    contests: list[Contest] = []
    error: str | None = None

# Helper function to convert timestamp to IST
def _convert_to_ist(ts: str) -> str:
    # ts is in seconds since epoch (UTC)
    utc_dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
    
    # IST = UTC + 5:30
    ist_dt = utc_dt + timedelta(hours=5, minutes=30)

    return ist_dt.strftime("%d %b %Y %H:%M:%S")


def fetch_contest_data() -> dict[str, PlatformResponse]:
    all_data = {}
    
    # Fetch LeetCode contests
    try:
        lc = requests.get('https://alfa-leetcode-api.onrender.com/contests/upcoming', timeout=10)
        lc.raise_for_status()
        lc_contests = lc.json().get('contests', [])
        
        contests = [
            Contest(
                name=contest['title'],
                start_time=_convert_to_ist(contest['startTime']),
                duration=contest['duration'],
                link=f"https://leetcode.com/contest/{contest['title'].lower().replace(' ', '-')}/"
            )
            for contest in lc_contests
        ]
        all_data["leetcode"] = PlatformResponse(success=True, contests=contests)
    except requests.RequestException as e:
        all_data["leetcode"] = PlatformResponse(success=False, error=f"Network error: {str(e)}")
    except (KeyError, ValueError) as e:
        all_data["leetcode"] = PlatformResponse(success=False, error=f"Data parsing error: {str(e)}")

    # Fetch Codeforces contests
    try:
        cf = requests.get('https://codeforces.com/api/contest.list', timeout=10)
        cf.raise_for_status()
        cf_contests = cf.json().get('result', [])
        
        contests = [
            Contest(
                name=contest['name'],
                start_time=_convert_to_ist(contest['startTimeSeconds']),
                duration=contest['durationSeconds'],
                link=f"https://codeforces.com/contests/{contest['id']}"
            )
            for contest in cf_contests if contest.get('phase') == 'BEFORE'
        ]
        all_data["codeforces"] = PlatformResponse(success=True, contests=contests)
    except requests.RequestException as e:
        all_data["codeforces"] = PlatformResponse(success=False, error=f"Network error: {str(e)}")
    except (KeyError, ValueError) as e:
        all_data["codeforces"] = PlatformResponse(success=False, error=f"Data parsing error: {str(e)}")

    # Fetch CodeChef contests
    try:
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        cc = requests.get('https://www.codechef.com/api/list/contests/all?sort_by=START&sorting_order=asc&offset=0&mode=all', headers=header, timeout=10)
        cc.raise_for_status()
        cc_contests = cc.json().get('future_contests', [])
        
        contests = [
            Contest(
                name=contest['contest_name'],
                start_time=str(contest['contest_start_date']),
                duration=contest['contest_duration'],
                link=f"https://www.codechef.com/{contest['contest_code']}"
            )
            for contest in cc_contests
        ]
        all_data["codechef"] = PlatformResponse(success=True, contests=contests)
    except requests.RequestException as e:
        all_data["codechef"] = PlatformResponse(success=False, error=f"Network error: {str(e)}")
    except (KeyError, ValueError) as e:
        all_data["codechef"] = PlatformResponse(success=False, error=f"Data parsing error: {str(e)}")

    return all_data
