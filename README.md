# Mr Gorlomi
This is a gen-ai bot to help organise a hackathon. Primarily helps with team registration, evolving to have more features by day.

Tech/Tools used : Python, Streamlit, Slack SDKs, Langchain, OpenAI LLM, SQLite

## Setup
Assuming you're running this on a VM or on your local

1. Install required libs
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in root directory with below contents
```bash
# all values are dummy data here
OPENAI_API_KEY='sk-1234abcd'
SLACK_BOT_TOKEN='xoxb-sample-value'
SLACK_APP_TOKEN='xapp-sample-value'
SLACK_BOT_USER_ID='U1234ABCD'
LOG_LEVEL='INFO'
SQLITE_DB_FILEPATH='data/hackathon_data.db'
```

## Running on Streamlit (local / testing)
```bash
streamlit run streamlit_app.py --server.port=80 --server.address=0.0.0.0
```

## Running on Slack
Assuming a slack app is created, with right permissions and socket mode enabled (This is a little involved, wiki on this soon), you can run this bot via the slack app as below.

```bash
python slackbot.py
```

### Maintenance & Data
All of the data gathered by bot will be stored in a sqlite DB file present at `SQLITE_DB_FILEPATH` - value for which you need to provide before starting the bot.

To make the bot operational for slack, we need to pre-fill data for participants table.

**How to get data of users from a slack workspace ?**
Checkout [scripts/import_slack_users.py](scripts/import_slack_users.py)

**How to pre-fill slack users CSV data in the participants table ?**
Checkout [scripts/populate_participants.py](scripts/populate_participants.py)

Both are simple self-explanatory scripts.
