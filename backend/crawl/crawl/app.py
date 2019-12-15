import praw
import psycopg2
import os
import sys
from datetime import datetime
from image import save_image

# REDDIT SETTINGS
CLIENT_ID = os.environ['RS_CLIENT_ID']
CLIENT_SECRET = os.environ['RS_CLIENT_SECRET']
try:
    DB_LOC = os.environ['RS_DB_LOC']
except:
    DB_LOC = "localhost"
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
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PWD, host=DB_LOC)
    cur = conn.cursor()
except Exception as e:
    print("Could not connect to local PostgreSQL database.")
    print(e)
    exit(1)

DATETIME_CONST = int(datetime.utcnow().timestamp())
TABLE_NAME = f"{POST_FILTER}_{DATETIME_CONST}_{SUBREDDIT}_{POST_LIMIT}"
COMMENT_TABLE_NAME = f"comments_{DATETIME_CONST}"

if POST_FILTER in ["top", "controversial"]:
    TABLE_NAME += f"_{TIME_FILTER}"

# Create a new table for each run of script - each table represents a different snapshot
cur.execute(
    f"CREATE TABLE {TABLE_NAME}(id varchar (10), title varchar (300), author varchar (20), \
    text varchar (50000), url varchar (1000), score int, created_utc varchar (15));",
)

# Create a table to store each comment snapshot
cur.execute(
    f"CREATE TABLE {COMMENT_TABLE_NAME}(id varchar(15), created_utc varchar (15), author varchar(20), \
    edited varchar(15), text varchar(50000), score int, submission_id varchar (10), parent_id varchar (15))"
)

# Insert crawled data into database
for submission in submission_data:
    # Save post
    cur.execute(
        f"INSERT INTO {TABLE_NAME}(id, title, author, text, url, score, created_utc) VALUES (\
        %s,%s,%s,%s,%s,%s,%s);",
        [submission.id, submission.title, submission.author.name, submission.selftext,
        submission.url, submission.score, submission.created_utc]
    )
    save_image(submission.url, submission.id)
    # Save comments
    submission.comments.replace_more(limit=None)
    for comment in submission.comments.list():
        # Some Redditor classes evaluate as None due to deleted/banned accounts?
        try:
            author = comment.author.name
        except:
            author = "[deleted]"
        cur.execute(
            f"INSERT INTO {COMMENT_TABLE_NAME}(id, author, text, edited, score, created_utc, submission_id, parent_id) VALUES (\
            %s,%s,%s,%s,%s,%s,%s,%s);",
            [comment.id, author, comment.body, comment.edited,
            comment.score, comment.created_utc, comment.link_id, comment.parent_id]
        )

conn.commit()
