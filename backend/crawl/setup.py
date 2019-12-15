from setuptools import setup

setup(
    name = 'Reddit Snapshot Spider',
    version = "0.1",
    packages = ['crawl'],
    include_package_data = True,
    install_requires = [
        "praw",
        "psycopg2"
    ],
)
