import logging
import time
import pandas as pd
import requests


import re
import clickhouse_connect
import json
from datetime import datetime
from settings.worker import worker_settings as settings
from common.utils import setup_worker
from camunda.external_task.external_task import ExternalTask


# Topic for Camunda
TOPIC = "social_sentiment_core"

# Logger setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- CONFIG ---
AGENT_NAME = "mindshare_agent"
RAW_MESSAGES_TABLE = 'x_raw_messages'
TOKENS_SENTIMENT_TABLE = 'x_tokens_sentiment'
TWEETS_PER_AUTHOR = 10
AUTHORS_TO_FETCH = 10
RAPIDAPI_HOST = "twitter241.p.rapidapi.com"

def get_base_url():
    return f"https://{RAPIDAPI_HOST}"

def create_raw_messages_table(client):
    CLICKHOUSE_DATABASE = settings.CLICKHOUSE_DATABASE
    RAW_MESSAGES_TABLE = 'x_raw_messages'
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {CLICKHOUSE_DATABASE}.{RAW_MESSAGES_TABLE} (
        author_username String,
        user_id String,
        tweet_id String,
        created_at DateTime,
        content String,
        metrics String,
        url String,
        insert_ts DateTime DEFAULT now(),
        processed UInt8 DEFAULT 0
    ) ENGINE = MergeTree
    ORDER BY (user_id, created_at)
    SETTINGS index_granularity = 8192;
    """
    client.command(create_sql)

def create_x_tokens_sentiment_table(client):
    CLICKHOUSE_DATABASE = settings.CLICKHOUSE_DATABASE
    TOKENS_SENTIMENT_TABLE = 'x_tokens_sentiment'
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {CLICKHOUSE_DATABASE}.{TOKENS_SENTIMENT_TABLE}
    (
        author_username String,
        user_id String,
        tweet_id String,
        created_at DateTime,
        content String,
        metrics String,
        url String,
        token String,
        mention_type String,
        matched_text String,
        summary String,
        author_name String,
        tokens_sentiment String,
        sentiment Float64,
        insert_ts DateTime DEFAULT now()
    )
    ENGINE = MergeTree
    ORDER BY (user_id, created_at)
    SETTINGS index_granularity = 8192;
    """
    client.command(create_sql)

def get_user_tweets(user_id, count, author_username):
    BASE_URL = get_base_url()
    RAPIDAPI_KEY = settings.RAPIDAPI_KEY
    RAPIDAPI_HOST = "twitter241.p.rapidapi.com"
    url = f"{BASE_URL}/user-tweets"
    headers = {
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    params = {"user": user_id, "count": count}
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()
    def find_tweets(obj):
        tweets = []
        if isinstance(obj, dict):
            if obj.get("__typename") == "TimelineTweet" or "tweet_results" in obj:
                tweets.append(obj)
            for v in obj.values():
                tweets.extend(find_tweets(v))
        elif isinstance(obj, list):
            for item in obj:
                tweets.extend(find_tweets(item))
        return tweets
    tweets = find_tweets(data)
    tweet_objs = []
    for tweet in tweets:
        try:
            tweet_result = tweet.get("tweet_results", {}).get("result", {})
            legacy = tweet_result.get("legacy", {})
            tweet_id = tweet_result.get("rest_id", None)
            created_at = legacy.get("created_at", None)
            content = legacy.get("full_text", "")
            metrics = {
                "likes": legacy.get("favorite_count", 0),
                "retweets": legacy.get("retweet_count", 0),
                "replies": legacy.get("reply_count", 0),
                "quotes": legacy.get("quote_count", 0)
            }
            url = f"https://x.com/{author_username}/status/{tweet_id}" if tweet_id else ""
            if created_at:
                created_at_dt = pd.to_datetime(created_at)
            else:
                created_at_dt = datetime.now()
            tweet_objs.append({
                "tweet_id": tweet_id,
                "created_at": created_at_dt,
                "content": content,
                "metrics": json.dumps(metrics),
                "url": url
            })
        except Exception:
            continue
    return tweet_objs

def clean_user_id(user_id):
    user_id = str(user_id)
    if "e+" in user_id or "." in user_id:
        try:
            user_id = str(int(float(user_id)))
        except Exception:
            pass
    return user_id

def fetch_and_store_raw_messages():
    client = clickhouse_connect.get_client(
        host=settings.CLICKHOUSE_HOST,
        port=int(settings.CLICKHOUSE_PORT),
        username=settings.CLICKHOUSE_USER,
        password=settings.CLICKHOUSE_PASSWORD,
        database=settings.CLICKHOUSE_DATABASE
    )
    create_raw_messages_table(client)
    authors = pd.read_csv("ai/social_sentiment_worker_kol_list.csv").head(AUTHORS_TO_FETCH)
    inserted = 0
    for _, row in authors.iterrows():
        author_username = row["author_username"]
        user_id = clean_user_id(row["user_id"])
        if pd.isna(user_id) or user_id == "nan":
            logger.info(f"Skipping {author_username}: no user_id")
            continue
        logger.info(f"Fetching tweets for {author_username} ({user_id})...")
        try:
            tweets = get_user_tweets(user_id, TWEETS_PER_AUTHOR, author_username)
        except Exception as e:
            logger.info(f"Error fetching tweets for {author_username}: {e}")
            continue
        new_tweets = []
        for tweet in tweets:
            if not tweet.get("tweet_id") or not str(tweet["tweet_id"]).isdigit():
                continue
            if not tweet.get("content") or not isinstance(tweet["content"], str):
                continue
            # Check if tweet already exists
            query = f"""SELECT count() FROM {settings.CLICKHOUSE_DATABASE}.{RAW_MESSAGES_TABLE} WHERE tweet_id = %(tweet_id)s"""
            result = client.query(query, parameters={"tweet_id": tweet["tweet_id"]})
            if result.result_rows[0][0] > 0:
                continue
            new_tweets.append([
                str(author_username),
                str(user_id),
                str(tweet["tweet_id"]),
                tweet["created_at"],
                tweet["content"],
                tweet["metrics"],
                tweet["url"]
            ])
        if new_tweets:
            logger.info(f"Bulk inserting {len(new_tweets)} tweets for {author_username}")
            try:
                client.insert(
                    f"{settings.CLICKHOUSE_DATABASE}.{RAW_MESSAGES_TABLE}",
                    new_tweets,
                    column_names=[
                        "author_username",
                        "user_id",
                        "tweet_id",
                        "created_at",
                        "content",
                        "metrics",
                        "url"
                    ]
                )
                inserted += len(new_tweets)
            except Exception as e:
                logger.error(f"Bulk insert error: {e}\nData: {new_tweets}")
        else:
            logger.info(f"No new tweets to insert for {author_username}")
        time.sleep(1)
    return inserted

def query_mindsdb_agent(question, agent_name):
    url = f"{settings.MINDS_DB_HOST}/api/projects/mindsdb/agents/{agent_name}/completions"
    payload = {"messages": [{"question": question, "answer": ""}]}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data.get("message", {}).get("content", "")

def extract_sentiment_and_summary(token, text, max_retries=3):
    prompt = (
        "You are an analytics and summarization agent for tweets. "
        "For the following tweet, provide:\n"
        "1. A sentiment score from -10 (very negative) to 10 (very positive).\n"
        "2. A one-sentence summary of the tweet, strictly no more than 240 characters.\n"
        "Return your answer as JSON: {'sentiment': <float>, 'summary': <string>}\n\n"
        f"Tweet: {text}"
    )
    for attempt in range(max_retries):
        result = query_mindsdb_agent(prompt, AGENT_NAME)
        try:
            result_stripped = result.strip()
            if result_stripped.startswith("```"):
                lines = result_stripped.splitlines()
                if lines[0].strip().startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                result_stripped = "\n".join(lines).strip()
            parsed = json.loads(result_stripped)
            return parsed.get("sentiment"), parsed.get("summary")
        except Exception as e:
            logger.info(f"Error parsing agent response (attempt {attempt+1}): {result}")
            if attempt < max_retries - 1:
                logger.info("Retrying...")
    return None, None

def find_token_mentions(text, tokens):
    found = []
    for token, mention_type in tokens:
        if mention_type in ['token', 'symbol']:
            # Only match UPPERCASE tokens or $TOKEN (case-sensitive)
            if token.isupper():
                # Match either $TOKEN or TOKEN as a whole word
                pattern = rf'(\${token})|\b{token}\b'
                matches = re.finditer(pattern, text)
                for match in matches:
                    found.append((token, mention_type, match.group(0)))
            else:
                continue  # skip non-uppercase tokens for these types
        else:
            pattern = re.escape(token)
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                found.append((token, mention_type, match.group(0)))
    return found

def process_sentiment():
    client = clickhouse_connect.get_client(
        host=settings.CLICKHOUSE_HOST,
        port=int(settings.CLICKHOUSE_PORT),
        username=settings.CLICKHOUSE_USER,
        password=settings.CLICKHOUSE_PASSWORD,
        database=settings.CLICKHOUSE_DATABASE
    )
    create_x_tokens_sentiment_table(client)
    tokens_df = pd.read_csv('ai/social_sentiment_worker_tokens_list.csv')
    tokens = []
    for _, row in tokens_df.iterrows():
        for key in ['token', 'fullname', 'symbol']:
            if pd.notna(row.get(key)):
                tokens.append((str(row[key]), key))
    query = f"SELECT author_username, user_id, tweet_id, created_at, content, metrics, url FROM {RAW_MESSAGES_TABLE} WHERE processed = 0"
    rows = client.query(query).result_rows
    processed = 0
    for row in rows:
        author_username, user_id, tweet_id, created_at, content, metrics, url = row
        url = f"https://x.com/{author_username}/status/{tweet_id}" if tweet_id and author_username else url
        mentions = find_token_mentions(content, tokens)
        for token, mention_type, matched_text in mentions:
            sentiment, summary = extract_sentiment_and_summary(token, content)
            if sentiment is not None:
                tokens_sentiment = json.dumps({token: float(sentiment)})
                client.insert(
                    f"{settings.CLICKHOUSE_DATABASE}.{TOKENS_SENTIMENT_TABLE}",
                    [[
                        author_username,
                        user_id,
                        tweet_id,
                        created_at,
                        content,
                        metrics,
                        url,
                        token,
                        mention_type,
                        matched_text,
                        summary if summary is not None else "",
                        "",  # author_name (if available, fill here)
                        tokens_sentiment,
                        float(sentiment)
                    ]],
                    column_names=[
                        "author_username", "user_id", "tweet_id", "created_at", "content",
                        "metrics", "url", "token", "mention_type", "matched_text",
                        "summary", "author_name", "tokens_sentiment", "sentiment"
                    ]
                )
                processed += 1
        # Mark as processed after all mentions are handled
        client.command(f"ALTER TABLE {RAW_MESSAGES_TABLE} UPDATE processed = 1 WHERE tweet_id = '{tweet_id}'")
    return processed

def handle_task(task: ExternalTask):
    logger.info(f"Handling task {task.get_task_id()}")
    command = task.get_variable("command")
    try:
        if command == "fetch_raw_messages":
            inserted = fetch_and_store_raw_messages()
            logger.info(f"Inserted {inserted} new tweets.")
            return task.complete({"status": "success", "inserted_tweets": inserted})
        elif command == "process_sentiment":
            processed = process_sentiment()
            logger.info(f"Processed {processed} mentions for sentiment.")
            return task.complete({"status": "success", "processed_mentions": processed})
        else:
            logger.error(f"Unknown command: {command}")
            return task.bpmn_error("SOCIAL_SENTIMENT_CORE_ERROR", f"Unknown command: {command}")
    except Exception as e:
        logger.error(f"Error in social_sentiment_core worker: {e}")
        return task.bpmn_error("SOCIAL_SENTIMENT_CORE_ERROR", f"Exception: {e}")

def initialize_worker():
    try:
        client = clickhouse_connect.get_client(
            host=settings.CLICKHOUSE_HOST,
            port=int(settings.CLICKHOUSE_PORT),
            username=settings.CLICKHOUSE_USER,
            password=settings.CLICKHOUSE_PASSWORD,
            database=settings.CLICKHOUSE_DATABASE
        )
        create_raw_messages_table(client)
        create_x_tokens_sentiment_table(client)
    except Exception as e:
        logger.critical(f"Worker initialization failed: {e}")
        exit(1)

if __name__ == "__main__":
    logger.info(f"Starting the worker for topic: {TOPIC}")
    initialize_worker()
    try:
        setup_worker(TOPIC, handle_task)
        logger.info("Camunda worker setup completed successfully.")
    except Exception as e:
        logger.critical(f"Failed to setup Camunda worker: {e}")
        exit(1)
