import praw
import psycopg2
import os
import sys
from datetime import datetime

# REDDIT SETTINGS
CLIENT_ID = input("Enter Client ID:").strip()
CLIENT_SECRET = input("Enter Client Secret:").strip()
USER_AGENT = "Snapshot Tool v0.0.4 Built: 11 Dec 2019"

if len(sys.argv) >= 2:
    SUBREDDIT = sys.argv[1]
else:
    SUBREDDIT = "all"

if len(sys.argv) >= 3:
    try:
        POST_LIMIT = int(sys.argv[2])
    except:
        POST_LIMIT = 100
else:
    POST_LIMIT = 100

# top/hot/controversial/gilded/new
if len(sys.argv) >= 4:
    POST_FILTER = sys.argv[3]
else:
    POST_FILTER = "top"
# time_filter – Can be one of: all, day, hour, month, week, year (default: all).
# Only applies to top and controversial
if len(sys.argv) >= 5:
    TIME_FILTER = sys.argv[4]
else:
    TIME_FILTER = "day"

if TIME_FILTER not in ["all", "day", "hour", "month", "week", "year"]:
    TIME_FILTER = "day"



# POSTGRESQL SETTINGS
try:
    DB_NAME = os.environ['RS_DB_NAME']
    DB_USER = os.environ['RS_DB_USER']
    DB_PWD = os.environ['RS_DB_PWD']
except KeyError:
    print("Please set environment variables RS_DB_NAME, RS_DB_USER and RS_DB_PWD")
    exit(1)

# Initialise our reddit instance and variables
reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT
)

subreddit = reddit.subreddit(SUBREDDIT)

if POST_FILTER == "hot":
    submission_data = subreddit.hot(limit=POST_LIMIT)
elif POST_FILTER == "controversial":
    submission_data = subreddit.controversial(time_filter=TIME_FILTER, limit=POST_LIMIT)
elif POST_FILTER == "gilded":
    submission_data = subreddit.gilded(limit=POST_LIMIT)
elif POST_FILTER == "new":
    submission_data = subreddit.new(limit=POST_LIMIT)
else:
    POST_FILTER = "top"
    submission_data = subreddit.top(time_filter=TIME_FILTER, limit=POST_LIMIT)

# Initialise our postgreSQL connection and variables
try:
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PWD, host='localhost')
    cur = conn.cursor()
except Exception as e:
    print("Could not connect to local PostgreSQL database.")
    print(e)
    exit(1)

TABLE_NAME = f"{POST_FILTER}_{int(datetime.utcnow().timestamp())}_{SUBREDDIT}_{POST_LIMIT}"

if POST_FILTER in ["top", "controversial"]:
    TABLE_NAME += f"_{TIME_FILTER}"

# Create a new table for each run of script - each table represents a different snapshot
cur.execute(
    f"CREATE TABLE {TABLE_NAME}(title varchar (300), author varchar (20), \
    text varchar (40000), url varchar (1000), score int, createdutc varchar (15));",
)

# Insert crawled data into database
for submission in submission_data:
    cur.execute(
        f"INSERT INTO {TABLE_NAME}(title, author, text, url, score, createdutc) VALUES (\
        %s,%s,%s,%s,%s,%s);",
        [submission.title, submission.author.name, submission.selftext,
        submission.url, submission.score, submission.created_utc]
    )

conn.commit()
