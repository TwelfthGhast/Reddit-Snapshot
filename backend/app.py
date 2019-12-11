from flask import Flask, jsonify, request
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
            temp["time"] = timesort

        answer.append(temp)
    return jsonify(answer)

# Potentially dangerous - Check SQL sanitisation
@app.route("/api/V1/getposts", methods=["GET"])
def list_posts():
    # Assume only one table can have the same timestamp
    # probably not the most effective but prevents sql injections
    table = request.args.get("utctimestamp")
    start = request.args.get("start")
    end = request.args.get("end")

    try:
        start = int(start)
        try:
            end = int(end)
        except:
            end = start + 50
    except:
        start = 0
        end = 50

    if table is None:
        return jsonify()

    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")
    tables = cur.fetchall()
    for table_name in tables:
        if table in table_name[0]:
            try:
                cur.execute(f"SELECT title, author, text, url, score, createdutc FROM {table_name[0]} OFFSET %s LIMIT %s", (start, end - start))
                table_data = cur.fetchall()
                answer = []
                for row in table_data:
                    title, author, text, url, score, createdutc = row
                    answer.append({
                        "title" : title,
                        "author" : author,
                        "text" : text,
                        "url" : url,
                        "score" : score,
                        "created_utc" : createdutc
                    })
                return jsonify(answer)
            except Exception as e:
                print(e)
                return jsonify()
    return jsonify()
