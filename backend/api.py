import os
import psycopg2

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
