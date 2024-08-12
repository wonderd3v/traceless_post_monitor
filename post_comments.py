import os
import asyncio
import json
from instagrapi import Client
from dotenv import load_dotenv 
import signal

# Load environment variables from .env file
load_dotenv()

# Path to the file where responded users will be stored
RESPONDED_USERS_FILE = "responded_users.json"
SESSION_FILE = "session.json"

def load_responded_users():
    if os.path.exists(RESPONDED_USERS_FILE):
        with open(RESPONDED_USERS_FILE, "r") as f:
            data = json.load(f)
            return {post_id: set(user_ids) for post_id, user_ids in data.items()}
    return {}

def save_responded_users(responded_users):
    with open(RESPONDED_USERS_FILE, "w") as f:
        json.dump({post_id: list(user_ids) for post_id, user_ids in responded_users.items()}, f)

def save_session(cl):
    session_data = cl.get_settings()
    with open(SESSION_FILE, "w") as f:
        json.dump(session_data, f)

def load_session(cl):
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            session_data = json.load(f)
            cl.set_settings(session_data)
            print("Session loaded successfully")

# Load the dictionary of posts and their responded users
responded_users = load_responded_users()

async def monitor_comments(cl, post_url, trigger_word, response_message, message_delay_seconds):
    media_id = cl.media_pk_from_url(post_url)
    post_id = str(media_id)

    if post_id not in responded_users:
        responded_users[post_id] = set()

    while True:
        comments = cl.media_comments(media_id)
        
        for comment in comments:
            user_id = str(comment.user.pk)
            if trigger_word.lower() in comment.text.lower() and user_id not in responded_users[post_id]:
                print(f"Sending message to {comment.user.username} (ID: {user_id}) for post {post_id}")
                cl.direct_send(response_message, user_ids=[user_id])
                responded_users[post_id].add(user_id)
                save_responded_users(responded_users)
                print(f"Responded to comment: {comment.text}")
                
                await asyncio.sleep(message_delay_seconds)
        
        print("Checked comments, sleeping now...")
        await asyncio.sleep(60)  # Check every minute

async def main():
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")
    post_url = os.getenv("POST_URL")
    trigger_word = os.getenv("TRIGGER_WORD")
    response_message = os.getenv("RESPONSE_MESSAGE")
    message_delay_seconds = int(os.getenv("MESSAGE_DELAY_SECONDS", "10"))

    cl = Client()

    # Set up proxy
    proxy_url = os.getenv("PROXY_URL")
    if proxy_url:
        cl.set_proxy(proxy_url)

    load_session(cl)

    if not cl.user_id:
        cl.login(username, password)
        save_session(cl)

    await monitor_comments(cl, post_url, trigger_word, response_message, message_delay_seconds)

def handle_shutdown():
    print("Shutting down...")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_shutdown)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass