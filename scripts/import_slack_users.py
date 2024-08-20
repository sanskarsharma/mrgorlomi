from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
import logging
import os
import csv
import ssl
import certifi
import logging
from slack_sdk import WebClient

logging.basicConfig()
logging.getLogger().setLevel(os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


def fetch_all_active_slack_users_to_csv(client, filename="slack_users.csv"):
    try:
        all_users = []
        cursor = None
        
        while True:
            # Fetch users with pagination
            result = client.users_list(limit=1000, cursor=cursor)
            users = result["members"]
            
            for user in users:
                if (not user.get('is_bot', False) and 
                    not user.get('deleted', False) and 
                    user['id'] != 'USLACKBOT' and
                    user.get('is_active', True)):  # Check if user is active
                    all_users.append(user)
            
            # Check if there are more users to fetch
            cursor = result.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        # Write users to CSV
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=["user_id", "full_name", "bio"])
            writer.writeheader()

            for user in all_users:
                writer.writerow({
                    "user_id": user.get("id"),
                    "full_name": user.get("real_name"),
                    "bio": user.get("profile", {}).get("title")
                })

        print(f"All active user information has been written to {filename}")
        print(f"Total active users fetched: {len(all_users)}")
        return True
    except SlackApiError as e:
        print(f"Error fetching users from Slack: {e}")
        return False


if __name__ == "__main__":
    
    load_dotenv()

    client = WebClient(
        token=os.environ.get("SLACK_BOT_TOKEN"),
        ssl=ssl.create_default_context(cafile=certifi.where()))

    # if os.path.isfile(users_csv_filepath) and os.path.getsize(users_csv_filepath) == 0:
    #     pass
    # else:
    #     logger.info("Slack users already in CSV, not calling slack API")

    users_csv_filepath = "slack_users.csv"
    success = fetch_all_active_slack_users_to_csv(client, filename=users_csv_filepath)
    if success:
        logger.info("Slack users written to CSV")
    else:
        logger.error("Failed to write slack users CSV file")



'''
USAGE
    export SLACK_BOT_TOKEN=<value>
    python import_slack_users.py
'''