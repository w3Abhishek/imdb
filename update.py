#!/usr/bin/env python3
import os
import json
import random
import datetime
import subprocess
import requests

API_BASE = "https://imdb.devgram.workers.dev/"
PARAMS = {"plot": "full", "r": "json"}
ID_FILE = "current_id.txt"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = os.environ.get("TELEGRAM_USER_ID")

def get_next_imdb_id():
    if os.path.exists(ID_FILE):
        with open(ID_FILE, "r") as f:
            current = int(f.read().strip())
    else:
        current = 1
    with open(ID_FILE, "w") as f:
        f.write(str(current + 1))
    return f"tt{current:07d}"

def fetch_movie_data(movie_id):
    url = f"{API_BASE}?i={movie_id}&plot={PARAMS['plot']}&r={PARAMS['r']}"
    try:
        response = requests.get(url, headers={"accept": "application/json"})
        response.raise_for_status()
        data = response.json()
        return True, data, response.elapsed.total_seconds()
    except Exception as e:
        return False, {"error": str(e)}, 0

def save_json(movie_id, data):
    filename = f"{movie_id}.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    return filename

def get_random_commit_date():
    start_date = datetime.datetime(2018, 1, 1)
    end_date = datetime.datetime(2024, 4, 8)
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    random_seconds = random.randint(0, 86400)
    random_date = start_date + datetime.timedelta(days=random_days, seconds=random_seconds)
    return random_date.strftime("%Y-%m-%dT%H:%M:%S")

def git_commit(file_name, commit_date, movie_id):
    subprocess.run(["git", "config", "user.name", "Abhishek Verma"], check=True)
    subprocess.run(["git", "config", "user.email", "w3abhishekmail@gmail.com"], check=True)
    subprocess.run(["git", "add", file_name], check=True)
    commit_message = f"Add data for {movie_id}"
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = commit_date
    env["GIT_COMMITTER_DATE"] = commit_date
    subprocess.run(["git", "commit", "-m", commit_message, "--date", commit_date], check=True, env=env)

def send_telegram_message(movie_id, success, request_time, data):
    base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    status_emoji = "✅" if success else "❌"
    time_emoji = "⏰"
    caption = (
        f"{status_emoji} *IMDb ID:* `{movie_id}`\n"
        f"{time_emoji} *Time:* {datetime.datetime.now().isoformat()}\n"
        f"*Request Time:* {request_time:.2f} seconds\n"
        f"*Response:*\n```json\n{json.dumps(data, indent=2)[:1000]}\n```"
    )

    text_url = f"{base_url}/sendMessage"
    payload = {"chat_id": TELEGRAM_USER_ID, "text": caption, "parse_mode": "Markdown"}
    requests.post(text_url, json=payload)

    poster_url = data.get("Poster")
    if poster_url and poster_url.startswith("http"):
        photo_url = f"{base_url}/sendPhoto"
        photo_payload = {
            "chat_id": TELEGRAM_USER_ID,
            "photo": poster_url,
            "caption": caption,
            "parse_mode": "Markdown"
        }
        requests.post(photo_url, json=photo_payload)

def main():
    movie_id = get_next_imdb_id()
    print(f"Fetching data for {movie_id} ...")
    success, data, request_time = fetch_movie_data(movie_id)
    filename = save_json(movie_id, data)
    commit_date = get_random_commit_date()
    print(f"Committing file {filename} with date {commit_date}")
    try:
        git_commit(filename, commit_date, movie_id)
    except Exception as e:
        print(f"Git commit failed: {e}")
    send_telegram_message(movie_id, success, request_time, data)
    print("Done.")

if __name__ == "__main__":
    main()
