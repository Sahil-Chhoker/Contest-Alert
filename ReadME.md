# Contest-Alert

I kept missing Leetcode and Codeforces rounds because I’d forget to check the schedule. This is a simple Python setup that scrapes upcoming contest dates and shoots you an email so you don't have to keep 20 tabs open.

### What it does

It basically aggregates the schedule for **Leetcode, Codechef, and Codeforces** into one place.

1. **`get_data.py`** hits the APIs (or scrapes the pages) to find what's coming up.
2. **`email_sender.py`** cleans that data up and sends it to your inbox.
3. **`main.py`** is the "go" button that ties it all together.

### Setup

First, grab the code and get your environment ready:

```bash
git clone https://github.com/Sahil-Chhoker/Contest-Alert.git
cd Contest-Alert

# Set up a virtual env so you don't mess up your global python
python3 -m venv venv
source venv/bin/activate

# Get the dependencies
pip install -r requirements.txt

```

### Configuring the Email

Since this uses Gmail/SMTP, you can't just use your regular password (Google will block it).

* You’ll need to go to your Google Account settings and generate an **"App Password"**.
* Pop your email and that App Password into the config section of `email_sender.py` (or set them as environment variables).

### Running it

Just run the main script using FastAPI:

```bash
fastapi dev main.py

```
