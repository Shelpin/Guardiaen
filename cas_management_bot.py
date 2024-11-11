import logging
from telethon import TelegramClient, events, errors
import csv
import os

# Enable logging for detailed output
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.info("Starting the bot script...")

# ===============================
# IMPORTANT: Replace these placeholders
# ===============================
api_id = YOUR_API_ID  # Replace with your actual API ID
api_hash = 'YOUR_API_HASH'  # Replace with your actual API hash
bot_token = 'YOUR_BOT_TOKEN'  # Replace with your actual bot token
group_id = -100YOUR_GROUP_ID  # Replace with your target group ID, include the dash if given

logger.info("Initializing the Telegram client...")
# Initialize the Telethon client using the API credentials
client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

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
total_cas_users = len(cas_users)  # Track the size of the CAS list

# Function to verify if the bot is in the group with the necessary permissions
async def has_group_access():
    try:
        # Explicitly check if the bot is a member of the group with admin privileges
        participants = await client.get_participants(group_id, limit=5)
        if participants:
            logger.info("Bot has access to group participants.")
            return True
    except errors.ChatAdminRequiredError:
        logger.error("Bot is in the group but needs to be an admin to retrieve participant details.")
    except errors.ChatWriteForbiddenError:
        logger.error("Bot cannot access the group or lacks membership.")
    except Exception as e:
        logger.error(f"Unexpected error checking group access: {e}")
    return False

# Function to scan group members, match with CAS list, and save matches in `matched_users.csv`
async def scan_and_list_users():
    matched_users = []  # List to hold matched users
    scanned_count = 0   # Counter for scanned members
    logger.info("Starting scan of group members...")

    # Check if the bot has access to the group before scanning
    if not await has_group_access():
        logger.error("Bot cannot access the group. Make sure the bot is added to the group and has admin permissions.")
        return -1, 0  # Indicate an access error

    # Perform the scan if access is confirmed
    try:
        async for user in client.iter_participants(group_id):
            scanned_count += 1
            user_id_str = str(user.id)
            if user_id_str in cas_users:  # Check if the user ID is in the banned list
                logger.info(f"Match found: User ID {user_id_str} matches CAS list.")
                matched_users.append({
                    'id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                })
    except Exception as e:
        logger.error(f"Error accessing group members: {e}")
        return -1, scanned_count

    # Write `matched_users.csv` even if there are no matches
    try:
        with open('matched_users.csv', 'w', newline='') as csvfile:
            fieldnames = ['id', 'username', 'first_name', 'last_name']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(matched_users)
        logger.info(f"'matched_users.csv' created. Total matches: {len(matched_users)}")
        logger.info(f"Total users scanned: {scanned_count} out of {total_cas_users} CAS users.")
    except Exception as e:
        logger.error(f"Error writing matched users to file: {e}")
        
    # Return both the count of matches and the count of scanned users
    return len(matched_users), scanned_count

# Command to trigger the scan and list process
@client.on(events.NewMessage(pattern='/scan_for_spammers'))
async def handle_scan_for_spammers(event):
    logger.info("Received /scan_for_spammers command.")
    await event.reply("Scanning group members for spammers. This may take a few moments...")
    count, scanned_count = await scan_and_list_users()
    
    if count == -1:
        await event.reply("Error: Unable to access group members. Ensure the bot is in the group and has admin permissions.")
    elif count == 0:
        await event.reply(f"Scan completed. No potential spammers detected. Scanned {scanned_count} group users against {total_cas_users} CAS users. An empty 'matched_users.csv' file has been created.")
    else:
        await event.reply(f"Scan completed. {count} potential spammers detected out of {scanned_count} group users scanned against {total_cas_users} CAS users. Check 'matched_users.csv' to review the list.")

# Function to kick users listed in `matched_users.csv`
async def kick_listed_users():
    kicked_count = 0
    logger.info("Starting to kick users from matched_users.csv...")
    
    try:
        with open('matched_users.csv', 'r') as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                try:
                    user_id = int(row['id'])
                    await client.kick_participant(group_id, user_id)
                    kicked_count += 1
                    logger.info(f"Kicked and banned user ID: {user_id}")
                except Exception as e:
                    logger.error(f"Error kicking user ID {user_id}: {e}")
    except FileNotFoundError:
        logger.error("matched_users.csv file not found. Please run /scan_for_spammers first.")
    except Exception as e:
        logger.error(f"Unexpected error while kicking users: {e}")
        
    return kicked_count

# Command to kick users from `matched_users.csv`
@client.on(events.NewMessage(pattern='/kick_listed_spammers'))
async def handle_kick_listed_spammers(event):
    logger.info("Received /kick_listed_spammers command.")
    await event.reply("Starting to kick users listed in 'matched_users.csv'...")
    kicked_count = await kick_listed_users()
    await event.reply(f"Kicked and banned {kicked_count} users listed in 'matched_users.csv'.")

# Command to display help information
@client.on(events.NewMessage(pattern='/help'))
async def handle_help(event):
    logger.info("Received /help command.")
    help_text = """
    **Bot Commands:**

    1. **/scan_for_spammers** - Scans all group members and cross-references them with the CAS CSV file (`cas_users.csv`). Matches are saved in `matched_users.csv` for review.

    2. **/kick_listed_spammers** - Kicks and bans users listed in `matched_users.csv`. Use this command after reviewing the matched users.

    3. **/help** - Shows this help message with a list of available commands.

    **Note:** The bot must be an admin in the group to be able to scan and kick users.
    """
    await event.reply(help_text)

logger.info("Starting the bot...")

# Start the bot and keep it running
with client:
    client.loop.run_until_complete(client.connect())
    client.run_until_disconnected()
