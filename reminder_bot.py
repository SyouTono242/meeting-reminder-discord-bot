import json
import argparse
import datetime

import discord
import gspread
import pytz
from oauth2client.service_account import ServiceAccountCredentials
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# === CONFIGURATION ===
parser = argparse.ArgumentParser(description="Lab Event Reminder Bot")
parser.add_argument('--config', type=str, default="config.json", help="Path to config JSON file")
parser.add_argument('--test', action='store_true', help="Run in test mode and exit")
args = parser.parse_args()

with open(args.config, 'r') as f:
    config = json.load(f)

DISCORD_TOKEN = config["discord_token"]
TIMEZONE = config["timezone"]
SERVICE_ACCOUNT_FILE = config["service_account_file"]
DATE_FORMAT = config["date_format"]
TEST_CHANNEL_ID = config["test_channel_id"]
EVENT_RESOURCES = config["event_resources"]

# === Google Sheets Setup ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
gs_client = gspread.authorize(credentials)

# === Discord Setup ===
intents = discord.Intents.default()
client_bot = discord.Client(intents=intents)
scheduler = AsyncIOScheduler(timezone=TIMEZONE)


def get_next_meeting(sheet_name: str, 
                     range_: str, 
                     date_format: str):
    """Gets the most recent upcoming meeting from a google sheet

    Args:
        sheet_name (str): Name of google sheet to look for meeting info
        range_ (str): Range in google sheet to look for meeting info
        date_format (str): Format of date from the google sheet

    Returns:
        (list, list): List of column headers, list of meeting info sorted by date
    """
    
    sheet = gs_client.open(sheet_name).worksheet(range_.split("!")[0])
    all_values = sheet.get(range_.split("!")[1])
    
    headers = all_values[0]
    rows = all_values[1:]
    
    now = datetime.datetime.now(pytz.timezone(TIMEZONE)).date()
    upcoming = []
    
    for row in rows:
        try:
            # Assuming the first column to be date
            date_str = row[0].strip()
            meeting_date = datetime.datetime.strptime(date_str, DATE_FORMAT).date()
            if meeting_date > now:
                upcoming.append((meeting_date, row))
        except Exception:
            continue

    if not upcoming:
        return None

    upcoming.sort()
    return headers, upcoming[0][1]


async def send_reminder(event_config: dict, 
                        test_mode: bool = False):
    """Gets meeting info from google sheets and sends reminder to discord

    Args:
        event_config (dict): Dictionary with event info, including event name, google sheet name, link, range; discord channel ID, role ID for mentioning; days before the event to send reminder
        test_mode (bool, optional): Whether the reminder should be sent to the test channel. Defaults to False.
    """
    
    now_datetime = datetime.datetime.now(pytz.timezone(TIMEZONE))
    print(f"[{event_config['name']}] reminder triggered on {now_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    channel_id = TEST_CHANNEL_ID if test_mode else event_config["channel_id"]
    mention_role = None if test_mode else event_config.get("mention_role", None)
    days_before = event_config.get("days_before", 1)
    
    channel = client_bot.get_channel(channel_id)
    if not channel:
        print(f"[{event_config['name']}] Channel {channel_id} not found.")
        return

    result = get_next_meeting(
        event_config["google_sheet_name"],
        event_config["spreadsheet_range"],
        DATE_FORMAT
    )
    
    if not result:
        await channel.send(f"No upcoming meetings found in the Google Sheet {event_config['google_sheet_name']}.")
        return

    headers, row = result
    meeting_date = datetime.datetime.strptime(row[0].strip(), DATE_FORMAT).date()
    
    if (meeting_date - now_datetime.date()).days != days_before:
        print(f"[{event_config['name']}] No event in {days_before} days (next is {meeting_date})")
        return
    
    print(f"Sending reminder for meeting [{event_config['name']}] on {meeting_date} to channel {channel.name}...")
    
    fields = [
        f"**{header.strip()}:** {value.strip()}"
        for header, value in zip(headers, row) if value.strip()
    ]
            
    prefix = (
        f"{mention_role} Hi all. "
        if mention_role else "Tester tester. "
    )
    
    message = (
        prefix +
        f"Reminder that we have a **{event_config['name']}** event in {days_before} day(s).\n\n" +
        "\n".join(fields) +
        f"\n\nMeeting calendar: {event_config['google_sheet_viewer_link']}"
    )
    
    await channel.send(message)


@client_bot.event
async def on_ready():
    print(f"Bot logged in as {client_bot.user}")
    
    if args.test:
        print("Running in test mode...")
        for event in EVENT_RESOURCES:
            await send_reminder(event, test_mode=True)
        await client_bot.close()
    else:
        for event in EVENT_RESOURCES:
            scheduler.add_job(
                send_reminder,
                trigger=CronTrigger(hour=9, minute=0),
                args=[event],
                kwargs={"test_mode": False},
                name=f"Reminder: {event['name']}"
            )
        scheduler.start()

client_bot.run(DISCORD_TOKEN)
