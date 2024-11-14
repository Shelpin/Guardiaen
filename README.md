# Guardiæn
![guardiaen logo with text](https://github.com/user-attachments/assets/0d82fcd9-ee5f-4a02-aa17-ae0c834193fd)


# Telegram Group spammer kicker bot 

## Objective
None of the major telegram moderation bots allow to identify spammers that are already present in a group.

Guardiæn is designed to help administrators of large Telegram groups manage and mute or remove users who have been flagged as spammers in the Combot Anti-Spam (CAS) system. 
The bot performs an initial scan for spammers by cross-referencing group members with a local CAS-banned users list, and then userrs that are allowed to use the bot, can mute / unmute or kick and ban them out. 

## Features

- **Initial Group Member Scan**: Cross-checks group members against a local `cas_users.csv` CAS-banned list and generates a `matched_users.csv` file with any matches.
- **Mute, Unmute, and Kick** : Automate management by muting, unmuting, or kicking/banning flagged members.
- **Access Control**: Only specified Telegram users can control the bot.
- **Detailed Logging**: Logs events to both console and a file with a rotating handler.
- **Admin Verification**: Ensures the bot has access to necessary permissions.

## Setup Guide

### Prerequisites

1. **Python 3.6+**: Make sure Python is installed. Check your version with:
   ```bash
   python3 --version

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
```pip3 install telethon requests```

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

```python3 cas_management_bot.py```

### Commands
The bot provides the following commands for managing group members:

- /scan_for_spammers:

Scans all group members against the local CAS-banned list (cas_users.csv) and saves any matches to matched_users.csv.
Use this command first to perform a one-time check and review the results before taking action.

- /mute_listed_spammers:

Mutes users found in matched_users.csv.

- /unmute_listed_spammers: 

Unmutes users in matched_users.csv.

- /kick_listed_spammers:

Kicks and bans all users listed in matched_users.csv. Run this command after reviewing the list of matches.

- /ping:

Responds with "Pong!" to confirm bot functionality.

- /help:

Displays a help message with an overview of available commands.

![telegram-cloud-photo-size-4-5886748451994190595-y](https://github.com/user-attachments/assets/40a62e5e-7169-4d1a-a011-d56c84ab120a)


### Logging and Monitoring

The bot utilizes both console and file logging with rotating files for bot_activity.log, capturing all events, and interactions.

![telegram-cloud-photo-size-4-5886748451994190597-y](https://github.com/user-attachments/assets/9e1da1bf-80e8-4e78-94e2-3ff7d6449555)

You can also check the actions taken in the "recent actions" admin section of your telegram group.

![telegram-cloud-photo-size-4-5886748451994190594-y](https://github.com/user-attachments/assets/d287c2fb-7f6e-48b9-ad25-5957c2065279)





### Running as a System Service

With this setup you should keep the session of the bot host machine connected for the bot to work. If you want to keep the bot running continuously:

#### Create the Service File
Create a file /etc/systemd/system/telegram_bot.service:

```
[Unit]
Description=Telegram Bot Service
After=network.target

[Service]
User=root
ExecStart=/usr/bin/python3 /path/to/cas_management_bot.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```
#### Start and Enable the Service

```sudo systemctl daemon-reload
sudo systemctl start telegram_bot
sudo systemctl enable telegram_bot
```

#### Check Bot Status

```sudo systemctl status telegram_bot```

#### Restart the bot

```sudo systemctl restart telegram_bot```

#### Stop the bot

```sudo systemctl stop telegram_bot```

#### Check real time logs 

```sudo journalctl -u telegram_bot -f```



