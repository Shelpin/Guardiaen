import logging
from logging.handlers import RotatingFileHandler
from telethon import TelegramClient, events, errors
import csv
import os

# Set up rotating file handler for detailed bot activity log
file_handler = RotatingFileHandler("bot_activity.log", maxBytes=5*1024*1024, backupCount=5)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)

# Console handler for minimal logging (only important info and above)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(file_formatter)

# Set up the main logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info("Starting the bot script...")

# ===============================
# YOUR SPECIFIC VARIABLES
# ===============================
api_id = YOUR_API_ID  # Replace with your Telegram API ID
api_hash = 'YOUR_API_HASH'  # Replace with your Telegram API Hash
bot_token = 'YOUR_BOT_TOKEN'  # Replace with your bot token
group_id = YOUR_GROUP_ID  # Replace with your target group ID
allowed_users = {USER_ID_1, USER_ID_2, USER_ID_3}  # Replace with allowed user IDs

logger.info("Initializing the Telegram client...")
# Initialize the Telethon client
client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# Function to check if the user is allowed
def is_allowed_user(user_id):
    return user_id in allowed_users

# Decorator to restrict command usage to allowed users
def restricted_command(func):
    async def wrapper(event):
        if not is_allowed_user(event.sender_id):
            await event.reply("🚫 You don’t have permission to use this command.")
            logger.warning(f"Unauthorized user {event.sender_id} tried to use command {event.raw_text}.")
            return
        logger.info(f"Authorized user {event.sender_id} issued command: {event.raw_text}")
        return await func(event)
    return wrapper

# Function to load CAS-banned users from `cas_users.csv`
def load_cas_users(filename='cas_users.csv'):
    logger.info("Loading CAS users from CSV file...")
    cas_users = set()
    try:
        with open(filename, 'r') as csvfile:
            csvreader = csv.reader(csvfile)
            for row in csvreader:
                user_id = row[0].strip()
                if user_id.isdigit():  # Ensure IDs are numeric
                    cas_users.add(user_id)
        logger.info(f"Loaded {len(cas_users)} CAS user IDs from {filename}")
    except Exception as e:
        logger.error(f"Error loading CAS users from file: {e}")
    return cas_users

# Load CAS users from the CSV file
cas_users = load_cas_users()
total_cas_users = len(cas_users)

# Function to verify if the bot has access to the group
async def has_group_access():
    try:
        participants = await client.get_participants(group_id, limit=5)
        if participants:
            logger.info("Bot has access to group participants.")
            return True
    except errors.ChatAdminRequiredError:
        logger.error("Bot needs to be an admin to retrieve participant details.")
    except errors.ChatWriteForbiddenError:
        logger.error("Bot cannot access the group or lacks membership.")
    except Exception as e:
        logger.error(f"Unexpected error checking group access: {e}")
    return False

# Function to scan group members, match with CAS list, and save matches in `matched_users.csv`
async def scan_and_list_users(event=None):
    matched_users = []
    scanned_count = 0
    deleted_count = 0

    logger.info("Starting scan of group members...")

    if not await has_group_access():
        logger.error("Bot cannot access the group.")
        if event:
            await event.reply("Error: Unable to access group members.")
        return -1, 0

    try:
        async for user in client.iter_participants(group_id, limit=None):
            scanned_count += 1
            user_id_str = str(user.id)

            if user.deleted or (not user.username and not user.first_name and not user.last_name):
                deleted_count += 1
                logger.info(f"Deleted account detected. Total deleted so far: {deleted_count}")
                continue

            if user_id_str in cas_users:
                logger.info(f"Match found: User ID {user_id_str} matches CAS list.")
                matched_users.append({
                    'id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                })

            if scanned_count % 50 == 0:
                logger.info(f"Scanned {scanned_count} members so far, including {deleted_count} deleted accounts.")

    except Exception as e:
        logger.error(f"Error accessing group members: {e}")
        return -1, scanned_count

    try:
        with open('matched_users.csv', 'w', newline='') as csvfile:
            fieldnames = ['id', 'username', 'first_name', 'last_name']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(matched_users)
        logger.info(f"'matched_users.csv' created. Total matches: {len(matched_users)}")
        logger.info(f"Total users scanned: {scanned_count} (including {deleted_count} deleted accounts).")
    except Exception as e:
        logger.error(f"Error writing matched users to file: {e}")
        
    return len(matched_users), scanned_count, deleted_count

# Mute matched users in `matched_users.csv`
async def mute_listed_users():
    muted_count = 0
    logger.info("Starting mute operation for users listed in 'matched_users.csv'...")

    try:
        with open('matched_users.csv', 'r') as csvfile:
            csvreader = csv.DictReader(csvfile)
            if not csvreader.fieldnames or 'id' not in csvreader.fieldnames:
                logger.error("The 'matched_users.csv' file is missing the required 'id' field.")
                return muted_count

            for row in csvreader:
                try:
                    user_id = int(row['id'])
                    logger.info(f"Attempting to mute user ID: {user_id}")
                    await client.edit_permissions(group_id, user_id, send_messages=False)
                    muted_count += 1
                    logger.info(f"Muted user ID: {user_id}")
                except errors.ChatAdminRequiredError:
                    logger.error(f"Bot lacks admin permission to mute user ID: {user_id}")
                    return muted_count
                except Exception as e:
                    logger.error(f"Error muting user ID {user_id}: {e}")
    except FileNotFoundError:
        logger.error("matched_users.csv file not found. Please run /scan_for_spammers first.")
    except Exception as e:
        logger.error(f"Error reading matched users file: {e}")
    
    logger.info(f"Completed muting operation. Total users muted: {muted_count}")
    return muted_count

# Unmute matched users in `matched_users.csv`
async def unmute_listed_users():
    unmuted_count = 0
    logger.info("Starting unmute operation for users listed in 'matched_users.csv'...")

    try:
        with open('matched_users.csv', 'r') as csvfile:
            csvreader = csv.DictReader(csvfile)
            if not csvreader.fieldnames or 'id' not in csvreader.fieldnames:
                logger.error("The 'matched_users.csv' file is missing the required 'id' field.")
                return unmuted_count

            for row in csvreader:
                try:
                    user_id = int(row['id'])
                    logger.info(f"Attempting to unmute user ID: {user_id}")
                    await client.edit_permissions(group_id, user_id, send_messages=True)
                    unmuted_count += 1
                    logger.info(f"Unmuted user ID: {user_id}")
                except errors.ChatAdminRequiredError:
                    logger.error(f"Bot lacks admin permission to unmute user ID: {user_id}")
                    return unmuted_count
                except Exception as e:
                    logger.error(f"Error unmuting user ID {user_id}: {e}")
    except FileNotFoundError:
        logger.error("matched_users.csv file not found. Please run /scan_for_spammers first.")
    except Exception as e:
        logger.error(f"Error reading matched users file: {e}")
    
    logger.info(f"Completed unmuting operation. Total users unmuted: {unmuted_count}")
    return unmuted_count

# Kick and ban matched users in `matched_users.csv`
async def kick_and_ban_listed_users():
    kicked_count = 0
    logger.info("Starting kick and ban operation for users listed in 'matched_users.csv'...")

    try:
        with open('matched_users.csv', 'r') as csvfile:
            csvreader = csv.DictReader(csvfile)
            if not csvreader.fieldnames or 'id' not in csvreader.fieldnames:
                logger.error("The 'matched_users.csv' file is missing the required 'id' field.")
                return kicked_count

            for row in csvreader:
                try:
                    user_id = int(row['id'])
                    logger.info(f"Attempting to kick and ban user ID: {user_id}")
                    await client.kick_participant(group_id, user_id)
                    await client.edit_permissions(group_id, user_id, until_date=0)  # Permanent ban
                    kicked_count += 1
                    logger.info(f"Kicked and banned user ID: {user_id}")
                except errors.ChatAdminRequiredError:
                    logger.error(f"Bot lacks admin permission to kick and ban user ID: {user_id}")
                    return kicked_count
                except Exception as e:
                    logger.error(f"Error kicking and banning user ID {user_id}: {e}")
    except FileNotFoundError:
        logger.error("matched_users.csv file not found. Please run /scan_for_spammers first.")
    except Exception as e:
        logger.error(f"Error reading matched users file: {e}")
    
    logger.info(f"Completed kicking and banning operation. Total users kicked and banned: {kicked_count}")
    return kicked_count

@client.on(events.NewMessage(pattern='/help'))
@restricted_command
async def handle_help(event):
    logger.info("Received /help command.")
    help_text = """
    **Bot Commands:**
    - **/scan_for_spammers**: Scans group members and checks against the CAS list.
    - **/mute_listed_spammers**: Mutes users in `matched_users.csv`.
    - **/unmute_listed_spammers**: Unmutes users in `matched_users.csv`.
    - **/kick_listed_spammers**: Kicks and bans users in `matched_users.csv`.
    - **/ping**: Checks bot status.
    - **/help**: Shows this help message.
    """
    await event.reply(help_text)
    logger.info(f"User {event.sender_id} requested help.")

@client.on(events.NewMessage(pattern='/ping'))
@restricted_command
async def handle_ping(event):
    await event.reply("Pong!")
    logger.info(f"Replied to /ping command issued by user {event.sender_id}.")

@client.on(events.NewMessage(pattern='/scan_for_spammers'))
@restricted_command
async def handle_scan_for_spammers(event):
    await event.reply("Scanning for spammers. This may take a few moments...")
    count, scanned_count, deleted_count = await scan_and_list_users()
    
    if count == -1:
        await event.reply("Error: Bot lacks access to group members.")
    elif count == 0:
        await event.reply(f"No spammers detected. Scanned {scanned_count} members ({deleted_count} deleted accounts).")
    else:
        await event.reply(f"{count} spammers detected out of {scanned_count} members ({deleted_count} deleted accounts). See 'matched_users.csv'.")

@client.on(events.NewMessage(pattern='/mute_listed_spammers'))
@restricted_command
async def handle_mute_listed_spammers(event):
    logger.info("Received /mute_listed_spammers command.")
    muted_count = await mute_listed_users()
    await event.reply(f"Muted {muted_count} users listed in 'matched_users.csv'.")
    logger.info(f"Reply sent for /mute_listed_spammers: Muted {muted_count} users.")

@client.on(events.NewMessage(pattern='/unmute_listed_spammers'))
@restricted_command
async def handle_unmute_listed_spammers(event):
    logger.info("Received /unmute_listed_spammers command.")
    unmuted_count = await unmute_listed_users()
    await event.reply(f"Unmuted {unmuted_count} users listed in 'matched_users.csv'.")
    logger.info(f"Reply sent for /unmute_listed_spammers: Unmuted {unmuted_count} users.")

@client.on(events.NewMessage(pattern='/kick_listed_spammers'))
@restricted_command
async def handle_kick_listed_spammers(event):
    logger.info("Received /kick_listed_spammers command.")
    kicked_count = await kick_and_ban_listed_users()
    await event.reply(f"Kicked and banned {kicked_count} users listed in 'matched_users.csv'.")
    logger.info(f"Reply sent for /kick_listed_spammers: Kicked and banned {kicked_count} users.")

logger.info("Starting the bot...")

with client:
    client.loop.run_until_complete(client.connect())
    client.run_until_disconnected()
