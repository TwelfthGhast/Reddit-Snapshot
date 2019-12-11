import praw

CLIENT_ID = input("Enter Client ID:").strip()
CLIENT_SECRET = input("Enter Client Secret:").strip()
SUBREDDIT = input("Enter target subreddit:").strip()
USER_AGENT = "Snapshot Tool v0.0.1 Built: 11 Dec 2019"

reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT
)

subreddit = reddit.subreddit(SUBREDDIT)

print(subreddit.display_name)
print(subreddit.title)
print(subreddit.description)