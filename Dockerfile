FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /mrgorlomi
WORKDIR /mrgorlomi
RUN mkdir -p /mrgorlomi/data

COPY requirements.txt /mrgorlomi
RUN pip install --no-cache-dir -r requirements.txt

COPY ./core /mrgorlomi/core
COPY ./llm /mrgorlomi/llm
COPY ./scripts /mrgorlomi/scripts
COPY ./slackbot.py /mrgorlomi/slackbot.py

CMD ["python", "slackbot.py"]