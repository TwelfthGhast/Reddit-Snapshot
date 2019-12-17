from datetime import datetime
from image import save_image
import praw
import psycopg2
import os
import sys
import multiprocessing
import concurrent.futures
import threading
import requests
import youtube_dl
import re
import time

class YTDL_Logger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)
        return [False, msg]


def YTDL_hook(d):
    if d["status"] == "finished":
        pass

def preserve_content(url, post_id, location=""):

    video_re = [
        "youtu\.be",
        "\.youtube\.com",
        "v\.redd\.it"
    ]

    for match_string in video_re:
        if re.search(match_string, url):
            try:
                ydl_opts = {
                    'format': 'bestvideo+bestaudio',
                    'logger': YTDL_Logger(),
                    'progress_hooks': [YTDL_hook],
                }
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    if ydl.download([url]) != 0:
                        # Unusual output
                        return [False, f"{url}: Unusual exit code for YTDL"]
                    return [True, "Success"]
            except Exception as e:
                return [False, f"YDL error for {url}: {e}"]

    # Load the url
    try:
        url_data = requests.get(url, stream=True)
    except Exception as e:
        return [False, f"Could not load URL: {e}"]

    # check that the request is valid
    if url_data.status_code != 200 or url_data == False:
        return [False, "Invalid URL request"]

    # Try to validate file is an image by checking magic bytes
    # https://en.wikipedia.org/wiki/List_of_file_signatures

    image_bytes = [
        # jpeg
        b'\xff\xd8\xff\xe0',
        b'\xff\xd8\xff\xdb',
        b'\xff\xd8\xff\xee',
        b'\xff\xd8\xff\xe1',
        # png
        b'\x89\x50\x4E\x47'
    ]

    for header in image_bytes:
        if url_data.content[:4] == header:
            return save_image(url_data, post_id, location=location)
    
    return [False, f"Could not save file - bytes: {url_data.content[:4]}"]


def save_comments(submission):
    cur = con_db()
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
    cur.close()


def con_db():
    # Initialise our postgreSQL connection and variables
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PWD, host=DB_LOC)
        conn.set_session(autocommit=True)
        cur = conn.cursor()
        return cur
    except Exception as e:
        print("Could not connect to PostgreSQL database.")
        print(e)
        exit(1)


if __name__ == "__main__":
    # REDDIT SETTINGS
    CLIENT_ID = os.environ['RS_CLIENT_ID']
    CLIENT_SECRET = os.environ['RS_CLIENT_SECRET']

    try:
        DB_LOC = os.environ['RS_DB_LOC']
    except:
        DB_LOC = "localhost"
    
    USER_AGENT = "Snapshot Tool v0.0.6 Built: 15 Dec 2019 /u/12ghast"

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

    cur = con_db()

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

    posts = []
    # max workers defaults to min(32, os.cpu_count() + 4) according to documentation
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        count = 0
        print(f"Estimated: 0/{POST_LIMIT}\t0%", end="")
        for submission in submission_data:
            # Save post
            cur.execute(
                f"INSERT INTO {TABLE_NAME}(id, title, author, text, url, score, created_utc) VALUES (\
                %s,%s,%s,%s,%s,%s,%s);",
                [submission.id, submission.title, submission.author.name, submission.selftext,
                submission.url, submission.score, submission.created_utc]
            )
            # Save post media content
            future = executor.submit(preserve_content, submission.url, submission.id)
            posts.append(
                {
                    "future" : future,
                    "url" : submission.url
                }
            )
            futures.append(future)
            # Save comments
            # This contributes to postgreSQL cursor count, so don't set max workers too high...
            futures.append(executor.submit(save_comments, submission))
            # QOL Progress Tracker
            count += 1
            sys.stdout.write(f"\rEstimated: {count}/{POST_LIMIT}\t{int(count * 100/POST_LIMIT)}%")
            sys.stdout.flush()
        print("\n")
        print(f"{count} posts queued.")
        print("Waiting for threads to finish downloading media...")
        print(f"{threading.active_count()} threads still working...")
    print(f"Crawling complete!")
    for post in posts:
        result = post["future"].result()
        if not result[0]:
            print(f"Error: {post['url']} with \"{result[1]}\"")
