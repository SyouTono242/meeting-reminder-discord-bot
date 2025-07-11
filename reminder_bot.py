import json
import argparse
import os
import datetime

import discord
import gspread
import pytz
import asyncio
from oauth2client.service_account import ServiceAccountCredentials
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# === CONFIGURATION ===
parser = argparse.ArgumentParser(description="Lab Meeting Reminder Bot")
parser.add_argument('--config', type=str, default="config.json", help="Path to config JSON file")
args = parser.parse_args()

with open(args.config, 'r') as f:
    config = json.load(f)

DISCORD_TOKEN = config["discord_token"]
CHANNEL_ID = config["channel_id"]
MENTION_ROLE_ID = config["mention_role_id"]
SHEET_NAME = config["google_sheet_name"]
SPREADSHEET_RANGE = config["spreadsheet_range"]
TIMEZONE = config["timezone"]
SERVICE_ACCOUNT_FILE = config["service_account_file"]
DATE_FORMAT = config["date_format"]



# === Google Sheets Setup ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
client = gspread.authorize(credentials)
sheet = client.open(SHEET_NAME).sheet1

# === Discord Setup ===
intents = discord.Intents.default()
client_bot = discord.Client(intents=intents)
scheduler = AsyncIOScheduler(timezone=TIMEZONE)


def get_next_meeting():
    # Returns: 
    #   headers: list of column headers 
    #   row: list of metainfo of the closest meeting in the future
    
    all_values = sheet.get_all_values()
    headers = all_values[0]
    rows = all_values[1:]
    
    now = datetime.datetime.now(pytz.timezone(TIMEZONE)).date()

    upcoming = []
    for row in rows:
        try:
            date_str = row[0].strip()
            meeting_date = datetime.datetime.strptime(date_str, DATE_FORMAT).date()
            if meeting_date > now:
                upcoming.append((meeting_date, row))
        except Exception:
            continue

    if not upcoming:
        return None

    upcoming.sort()
    row = upcoming[0][1]
    
    return headers, row

async def send_reminder():
    channel = client_bot.get_channel(CHANNEL_ID)
    if not channel:
        print("Channel not found.")
        return

    result = get_next_meeting()
    if not result:
        await channel.send("No upcoming meetings found in the Google Sheet. Update it or ask Yiran to kill the bot plz")
        return

    headers, row = result
    
    try:
        meeting_date = datetime.datetime.strptime(row[0].strip(), DATE_FORMAT).date()
    except ValueError:
        print(f"Invalid date format in sheet: {row[0]}")
        return
    
    # Check and send reminders only 1 day before the meeting happens
    now = datetime.datetime.now(pytz.timezone(TIMEZONE)).date()
    if (meeting_date - now).days != 1:
        print(f"No meeting tomorrow. Next meeting is on {meeting_date}")
        return
    
    print(f"Sending reminder for meeting on {meeting_date} to channel {CHANNEL_ID}...")
    
    fields = []
    for header, value in zip(headers, row):
        if value.strip():
            fields.append(f"**{header.strip()}:** {value.strip()}")
            
    message = f"<@&{str(MENTION_ROLE_ID)}> Hi all. Reminder that we have a {SHEET_NAME} event tomorrow.\n\n" + "\n".join(fields)

    await channel.send(message)

@client_bot.event
async def on_ready():
    print(f"Bot logged in as {client_bot.user}")
    
    scheduler.add_job(send_reminder, CronTrigger(hour=9, minute=0))
    scheduler.start()

client_bot.run(DISCORD_TOKEN)
