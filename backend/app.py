import praw
import psycopg2
from datetime import datetime

# REDDIT SETTINGS
CLIENT_ID = input("Enter Client ID:").strip()
CLIENT_SECRET = input("Enter Client Secret:").strip()
SUBREDDIT = input("Enter target subreddit:").strip()
USER_AGENT = "Snapshot Tool v0.0.1 Built: 11 Dec 2019"
# time_filter – Can be one of: all, day, hour, month, week, year (default: all).
TIME_FILTER = "day"

# Anecdotal limit for comment length
# https://www.reddit.com/r/help/comments/8thdeu/character_limit_for_comments/
MAX_COMMENT_CHARS = 10000

# POSTGRESQL SETTINGS
DB_NAME = "snapshot"
DB_USER = "redditsnapshot"
DB_PWD = "password"

reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT
)

subreddit = reddit.subreddit(SUBREDDIT)

try:
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PWD, host='localhost')
    cur = conn.cursor()
except Exception as e:
    print("Could not connect to local PostgreSQL database.")
    print(e)
    exit(1)

TABLE_NAME = f"{TIME_FILTER}_{int(datetime.now().timestamp())}"

# Create a new table for each run of script - each table represents a different snapshot
cur.execute(
    f"CREATE TABLE {TABLE_NAME}(title varchar (300), author varchar (20), \
    text varchar (40000), url varchar (1000), score int, createdutc varchar (15));",
)

# PRAW api limits to top 1000
for submission in subreddit.top(time_filter=TIME_FILTER, limit=100):
    cur.execute(
        f"INSERT INTO {TABLE_NAME}(title, author, text, url, score, createdutc) VALUES (\
        %s,%s,%s,%s,%s,%s);",
        [submission.title, submission.author.name, submission.selftext,
        submission.url, submission.score, submission.created_utc]
    )

conn.commit()
