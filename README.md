# Mr Gorlomi
This is a natural language bot to help organise a hackathon. Primarily helps with team registration, evolving to have more features by day.

Tech/Tools used : Python, Slack SDKs, Langchain, OpenAI LLM, SQLite & Streamlit


## Setup for local (dev and testing)
There's a [streamlit app entrypoint](streamlit_app.py) added for running this application on local. To run on local simply do :
```bash

# create a virtual env with python 3.10 (required) and install dependencies
virtualenv venv --python=/usr/bin/python3.10
pip install -r requirements.txt

# create a .env file or put OPENAI_API_KEY in environment var as below
export OPENAI_API_KEY='sk-1234abcd'

# run streamlit
streamlit run streamlit_app.py --server.port=80 --server.address=0.0.0.0
```

## Setup for Slack bot (Supposed prod)
Assuming a slack app is created, with right permissions and socket mode enabled (This is a little involved, wiki on this soon), you can connect this application to the slack app by deploying it on a VM (or your local machine). Details below.

1. Create a `.env` file in root directory with below contents
```bash
# all values are dummy data here
OPENAI_API_KEY='sk-1234abcd'
SLACK_BOT_TOKEN='xoxb-sample-value'
SLACK_APP_TOKEN='xapp-sample-value'
SLACK_BOT_USER_ID='U1234ABCD'
LOG_LEVEL='INFO'
```

2. Create a `participants.csv` file in /data directory. Checkout [data/sample_participants.csv](data/sample_participants.csv) for required columns/headers.

> Note : Both `.env` and `participants.csv` files are critical to run the slackbot

#### Run using `Docker compose`
```bash
# To start app
docker compose up --build

# To stop app and delete data
docker compose down

# To stop app and delete data
docker compose down --volumes --remove-orphans
```

#### Run using `Python and virtualenv`
```bash
virtualenv venv --python=/usr/bin/python3.10  # requires python3.10
pip install -r requirements.txt
python slackbot.py
```


### Maintenance & Data
This application writes data to a sqlite file so it needs a filesystem. All of the data gathered by bot will be stored in a sqlite DB file in data directory, i.e "data/hackathon_data.db".

To make the bot operational for slack, we need to pre-fill/update data for participants table. This is also done at the slack bot startup. Some helpful, self-explanatory scripts :

**How to get data of users from a slack workspace ?**

Checkout [scripts/import_slack_users.py](scripts/import_slack_users.py)

**How to pre-fill slack users CSV data in the participants table ?**

Checkout [scripts/populate_participants.py](scripts/populate_participants.py)
