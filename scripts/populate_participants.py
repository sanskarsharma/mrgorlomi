'''
This script populates the participants table in given sqlite db file, with the data from the provided CSV file.
'''

import os
import sqlite3
import csv
import logging
import sys

logging.basicConfig()
logging.getLogger().setLevel(os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


if __name__ == "__main__":

    sqlite_db_filepath = sys.argv[1]
    participants_csv_filepath = sys.argv[2]

    if os.path.getsize(sqlite_db_filepath) == 0 or  os.path.getsize(participants_csv_filepath) == 0:
        logger.error("Filepaths provided are either empty or does not exist.")
        sys.exit(1)

    with open(participants_csv_filepath, 'r', newline='', encoding='utf-8') as csvfile :
        csvreader = csv.DictReader(csvfile)
        to_insert = []
        
        # loop and prepare data
        for i, row in enumerate(csvreader):
            to_insert.append((row['username'], row['full_name'], row['bio']))
        
        # insert if not already present
        conn = sqlite3.connect(sqlite_db_filepath)
        conn.executemany("""
            INSERT OR IGNORE INTO participants (username, full_name, bio) VALUES (?, ?, ?)
            """, to_insert)
        conn.commit()
    
    logger.info(f"Done. Participants data has been written to {sqlite_db_filepath}")

'''
USAGE
    python scripts/populate_participants.py data/hackathon.db data/participants.csv
'''