import praw
#import psycopg2

CLIENT_ID = input("Enter Client ID:").strip()
CLIENT_SECRET = input("Enter Client Secret:").strip()
SUBREDDIT = input("Enter target subreddit:").strip()
USER_AGENT = "Snapshot Tool v0.0.1 Built: 11 Dec 2019"
# time_filter – Can be one of: all, day, hour, month, week, year (default: all).
TIME_FILTER = "day"


reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT
)

subreddit = reddit.subreddit(SUBREDDIT)



# PRAW api limits to top 1000
for submission in subreddit.top(time_filter=TIME_FILTER, limit=1):
    print(vars(submission))
    #print(f"{submission.title}\t{submission.url}")