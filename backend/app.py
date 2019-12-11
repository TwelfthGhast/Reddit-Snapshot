from flask import Flask, jsonify
import os
import psycopg2

app = Flask(__name__)

# POSTGRESQL SETTINGS
try:
    DB_NAME = os.environ['RS_DB_NAME']
    DB_USER = os.environ['RS_DB_USER']
    DB_PWD = os.environ['RS_DB_PWD']
except KeyError:
    print("Please set environment variables RS_DB_NAME, RS_DB_USER and RS_DB_PWD")
    exit(1)

try:
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PWD, host='localhost')
    cur = conn.cursor()
except Exception as e:
    print("Could not connect to local PostgreSQL database.")
    print(e)
    exit(1)


@app.route("/api/V1/snapshot", methods=["GET"])
def list_snapshots():
    answer = []
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")
    tables = cur.fetchall()
    for table_name in tables:
        tbl_list = table_name[0].split("_")
        if len(tbl_list) == 4:
            type, timestamp, subreddit, limit = tbl_list
            timesort = False
        else:
            type, timestamp, subreddit, limit, timesort = tbl_list

        temp = {
            "sort" : type,
            "utctimestamp" : timestamp,
            "subreddit" : subreddit
        }
        if timesort:
            temp["timesort"] = timesort

        answer.append(temp)
    return jsonify(answer)
