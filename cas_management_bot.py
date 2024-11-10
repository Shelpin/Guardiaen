# Import necessary libraries
from telethon import TelegramClient, events  # Telethon to interact with Telegram API
import requests  # Requests to fetch CAS data from the web
import csv  # CSV module to parse CAS data
import time  # Time to create delays in our script

# ===============================
# IMPORTANT: Replace these values
# ===============================
api_id = YOUR_API_ID  # Integer; your Telegram API ID from my.telegram.org
api_hash = 'YOUR_API_HASH'  # String; your Telegram API Hash from my.telegram.org
bot_token = 'YOUR_BOT_TOKEN'  # String; your bot token from BotFather
group_id = 'YOUR_GROUP_ID'  # Integer or String; your group ID (make sure bot is an admin)

# CAS feed URL and sync interval settings
CAS_FEED_URL = "https://cas.chat/feed"
SYNC_INTERVAL = 3600  # Interval (in seconds) to sync with CAS feed, here set to 1 hour

# Initialize the Telethon client using the API credentials
client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# ===============================
# FUNCTION DEFINITIONS
# ===============================

# Function to load CAS-banned users from a local CSV file (cas_users.csv)
def load_cas_users(filename):
    cas_users = set()
    with open(filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            cas_users.add(row[0].strip())
    return cas_users

# Function to fetch CAS feed from the CAS website
def fetch_cas_feed():
    try:
        response = requests.get(CAS_FEED_URL)
        response.raise_for_status()
        
        cas_users = set()
        reader = csv.reader(response.text.splitlines())
        for row in reader:
            cas_users.add(row[0].strip())
        return cas_users
    except requests.exceptions.RequestException as e:
        print(f"Error fetching CAS feed: {e}")
        return set()

# Function to scan group members, compare with CAS list, and save matches in CSV
async def scan_and_list_users():
    cas_users = load_cas_users('cas_users.csv')  # Load CAS-banned user list
    matched_users = []  # List to hold matched users

    async for user in client.iter_participants(group_id):
        if str(user.id) in cas_users:
            matched_users.append({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name
            })

    with open('matched_users.csv', 'w', newline='') as csvfile:
        fieldnames = ['id', 'username', 'first_name', 'last_name']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(matched_users)

    return len(matched_users)

# Function to kick and ban users listed in 'matched_users.csv'
async def kick_listed_users():
    kicked_count = 0
    with open('matched_users.csv', 'r') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            try:
                user_id = int(row['id'])
                await client.kick_participant(group_id, user_id)
                kicked_count += 1
                print(f"Kicked and banned user ID: {user_id}")
            except Exception as e:
                print(f"Error kicking user ID {user_id}: {e}")
    return kicked_count

# Function to sync and kick new CAS-banned users from the CAS feed
async def sync_and_kick_cas_banned_users(cas_users):
    async for user in client.iter_participants(group_id):
        if str(user.id) in cas_users:
            try:
                await client.kick_participant(group_id, user.id)
                print(f"Kicked and banned CAS user ID: {user.id}")
            except Exception as e:
                print(f"Error kicking CAS user ID {user.id}: {e}")

# Background task to sync CAS feed and kick flagged users periodically
async def cas_sync_daemon():
    while True:
        print("Fetching CAS feed...")
        cas_users = fetch_cas_feed()
        
        if cas_users:
            print("Syncing CAS-banned users with group...")
            await sync_and_kick_cas_banned_users(cas_users)
        else:
            print("Failed to fetch CAS feed.")
        
        print(f"Waiting {SYNC_INTERVAL} seconds until the next sync...")
        time.sleep(SYNC_INTERVAL)

# ===============================
# BOT COMMANDS
# ===============================

@client.on(events.NewMessage(pattern='/scan_for_spammers'))
async def scan_for_spammers(event):
    count = await scan_and_list_users()
    await event.reply(f"Scan completed. {count} potential spammers detected. Check 'matched_users.csv' to review the list.")

@client.on(events.NewMessage(pattern='/kick_listed_spammers'))
async def kick_listed_spammers(event):
    kicked_count = await kick_listed_users()
    await event.reply(f"Kicked and banned {kicked_count} users listed in 'matched_users.csv'.")

@client.on(events.NewMessage(pattern='/help'))
async def help_command(event):
    help_text = """
    **Bot Commands:**
    
    1. **/scan_for_spammers** - Scans all group members and cross-references them with the local CAS CSV file (cas_users.csv). Matches are saved in matched_users.csv for review.

    2. **/kick_listed_spammers** - Kicks and bans users listed in matched_users.csv. Use this command after reviewing matched users.

    3. **/help** - Shows this help message with a list of available commands.
    
    **Note:** The bot also runs a background process that automatically syncs with the CAS feed every hour and kicks any new CAS-banned users.
    """
    await event.reply(help_text)

# Start the bot and CAS sync daemon in the background
with client:
    client.loop.create_task(cas_sync_daemon())
    client.run_until_disconnected()
