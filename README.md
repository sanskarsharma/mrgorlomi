# Mr Gorlomi
This is a gen-ai bot to help organise a hackathon. Primarily helps with team registration, evolving to have more features by day.

Tech/Tools used : Python, Slack SDKs, Langchain, OpenAI LLM, SQLite & Streamlit

## Setup
To run this on a VM or on your local


1. Create a `.env` file in root directory with below contents
```bash
# all values are dummy data here
OPENAI_API_KEY='sk-1234abcd'
SLACK_BOT_TOKEN='xoxb-sample-value'
SLACK_APP_TOKEN='xapp-sample-value'
SLACK_BOT_USER_ID='U1234ABCD'
LOG_LEVEL='INFO'
```

2. Create a /data directory and put `participants.csv` file in it with below strcutre (sample data below)
```csv
username,full_name,bio
U1234ABCD,Sanskar Sharma,Abcd
U5678EFGH,Shreyansh Sahare,Efgh
```

Both `.env` and `participants.csv` files are critical to run the slackbot


## Running for Slack
Assuming a slack app is created, with right permissions and socket mode enabled (This is a little involved, wiki on this soon), you can run this bot via the slack app as below.

#### Via : Docker compose
```bash
docker-compose up --build
```

#### Via : Python and virtualenv
```bash
virtualenv venv --python=/usr/bin/python3.10  # requires python3.10
pip install -r requirements.txt
python slackbot.py
```

### Maintenance & Data
All of the data gathered by bot will be stored in a sqlite DB file in data directory, i.e "data/hackathon_data.db".

To make the bot operational for slack, we need to pre-fill/update data for participants table. This is also done at the startup 

**How to get data of users from a slack workspace ?**
Checkout [scripts/import_slack_users.py](scripts/import_slack_users.py)

**How to pre-fill slack users CSV data in the participants table ?**
Checkout [scripts/populate_participants.py](scripts/populate_participants.py)

Both are simple self-explanatory scripts.

## Running on Streamlit (local / testing)
```bash
streamlit run streamlit_app.py --server.port=80 --server.address=0.0.0.0
```
