# Guardiaen
A simple telegram bot for detecting and kicking out existing spammers in a telegram public group, and keep it free from any account that has been CAS banned. Made using Combot's CAS spammer user ID database and its real time feed.  

# Telegram Group Moderation Bot with CAS Integration

## Objective
This bot is designed to help administrators of large Telegram groups manage and remove users who have been flagged as spammers in the Combot Anti-Spam (CAS) system. The bot performs an initial cleanup by cross-referencing group members with a local CAS-banned users list and then periodically syncs with the CAS feed to keep the group free of banned users.

## Features

- **Initial Group Member Scan**: Cross-checks group members against a local `cas_users.csv` CAS-banned list and generates a `matched_users.csv` file with any matches.
- **One-Time Mass Kick**: Allows the admin to kick and ban all users listed in `matched_users.csv` after reviewing the list.
- **Continuous Real-Time Sync with CAS Feed**: Periodically fetches the latest CAS feed from `https://cas.chat/feed` and automatically kicks any newly detected banned users.

## Setup Guide

### Prerequisites

1. **Python 3.6+**: Make sure Python is installed. Check your version with:
   ```bash
   python --version

2. **Telegram API ID and API Hash:**
- Go to my.telegram.org and log in.
- Navigate to "API Development Tools" and create a new application.
- Telegram will provide an API ID and API Hash for you to use.

3. **Bot Token:**

- In Telegram, start a chat with @BotFather.
- Use /newbot to create a bot and follow the instructions.
- BotFather will provide a bot token for you to use.

4. **Group ID:**

- Add your bot to the target group as an admin with permission to ban users.
- You can find the group ID by inviting your bot and using commands to retrieve the group ID or by checking your group’s settings.

### Required Libraries

Install the necessary Python packages by running:
```pip install telethon request```

### Preparing the CAS CSV Files 
- Download the CAS-banned list using the CAS API (https://api.cas.chat/export.csv) and save it as cas_users.csv in the same directory as the bot script.
- matched_users.csv will be generated by the bot after the initial scan to display detected spammers.
  
### Configuration and Running the Bot
- Clone this repository or download the cas_management_bot.py file.
- Open cas_management_bot.py in a text editor.
- Replace the following placeholders with your actual credentials:
- api_id = YOUR_API_ID (your API ID from my.telegram.org)
- api_hash = 'YOUR_API_HASH' (your API Hash from my.telegram.org)
- bot_token = 'YOUR_BOT_TOKEN' (your bot token from BotFather)
- group_id = 'YOUR_GROUP_ID' (the target group ID where the bot will operate)
- Save the file and run the bot:

```python cas_management_bot.py```

### Commands
The bot provides the following commands for managing group members:

- /scan_for_spammers:

Scans all group members against the local CAS-banned list (cas_users.csv) and saves any matches to matched_users.csv.
Use this command first to perform a one-time check and review the results before taking action.

- /kick_listed_spammers:

Kicks and bans all users listed in matched_users.csv. Run this command after reviewing the list of matches.

- /help:

Displays a help message with an overview of available commands.

### Features in Detail

- Initial Scan: Use /scan_for_spammers to generate matched_users.csv, which lists group members who match the CAS-banned user IDs.
- One-Time Mass Kick: After reviewing matched_users.csv, use /kick_listed_spammers to remove all flagged users.
- Real-Time Sync: The bot will also continuously sync with the CAS feed, running in the background to kick any newly CAS-banned users automatically.
