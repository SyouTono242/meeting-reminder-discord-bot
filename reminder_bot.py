import json
import argparse
import datetime

import discord
import gspread
import pytz
from oauth2client.service_account import ServiceAccountCredentials
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger


# === CONFIGURATION ===
parser = argparse.ArgumentParser(description="Lab Event Reminder Bot")
parser.add_argument('--config', type=str, default="config.json", help="Path to config JSON file")
parser.add_argument('--test', action='store_true', help="Run in test mode and exit")
parser.add_argument('--force', action='store_true', help="Force send reminders of all most recent upcoming events now")
args = parser.parse_args()

with open(args.config, 'r') as f:
    config = json.load(f)

DISCORD_TOKEN = config["discord_token"]
TIMEZONE = config["timezone"]
SERVICE_ACCOUNT_FILE = config["service_account_file"]
TEST_CHANNEL_ID = config["test_channel_id"]
EVENT_RESOURCES = config["event_resources"]

# === Global flags ===
_scheduled = False      # Makes sure only scheduling work dont get duplicated on reconnect

# === Google Sheets Setup ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
gs_client = gspread.authorize(credentials)

# === Discord Setup ===
intents = discord.Intents.default()
client_bot = discord.Client(intents=intents)
scheduler = AsyncIOScheduler(timezone=TIMEZONE,
    job_defaults={
        "coalesce": True,
        "max_instances": 1
    })

def add_year_if_necessary(date_str: str,
                    date_format: str):
    """Check if year is specified in the date_format, and if not,
    modify the year of dates in formats with only month and date to the most recent upcoming date

    Args:
        date_str (str): Input date to modify
        date_format (str): Format of the input date

    Returns:
        (datetime): Input date in the most recent upcoming year
    """
    input_date = datetime.datetime.strptime(date_str, date_format).date()

    if "%Y" in date_format or "%y" in date_format:
        return input_date

    today = datetime.datetime.now(pytz.timezone(TIMEZONE)).date()

    parsed_date = input_date.replace(year=today.year)

    if parsed_date < today:
        parsed_date = parsed_date.replace(year = today.year + 1)

    return parsed_date


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
            # Pass empty rows
            if len(row) > 1:
                # Assuming the first column to be date
                date_str = row[0].strip()
                meeting_date = add_year_if_necessary(date_str, date_format)

                if meeting_date > now:
                    upcoming.append((meeting_date, row))
        except Exception as e:
            print(f"Error occurred iteratng events from {sheet_name}:", e)

    if not upcoming:
        return None

    upcoming.sort()
    return headers, upcoming[0][1]


async def send_reminder(event_config: dict, 
                        test_mode: bool = False,
                        force_send: bool = False):
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
        event_config["date_format"]
    )
    
    if not result:
        # await channel.send(f"No upcoming meetings found in the Google Sheet {event_config['google_sheet_name']}.")
        print(f"No upcoming meetings found in the Google Sheet {event_config['google_sheet_name']}.")
        return

    headers, row = result
    meeting_date = meeting_date = add_year_if_necessary(row[0].strip(), event_config["date_format"])

    actual_days_before = (meeting_date - now_datetime.date()).days
    
    if not force_send and actual_days_before != days_before:
        print(f"[{event_config['name']}] No event in {days_before} days (next is {meeting_date})")
        return
    
    print(f"Sending reminder for event [{event_config['name']}] on {meeting_date} to channel {channel.name}...")
    
    fields = [
        f"**{header.strip()}:** {value.strip()}"
        for header, value in zip(headers, row) if value.strip()
    ]
            
    prefix = (
        f"{mention_role} Hi all. "
        if mention_role else "Hi there. "
    )

    if force_send:
        prefix += "Force-sending all upcoming events now...\n\n"
    
    message = (
        prefix +
        f"Reminder that we have a **{event_config['name']}** event in {actual_days_before} day(s).\n\n" +
        "\n".join(fields) +
        f"\n\nMeeting calendar: {event_config['google_sheet_viewer_link']}"
    )
    
    await channel.send(message)


@client_bot.event
async def on_ready():
    print(f"Bot logged in as {client_bot.user}")
    
    global _scheduled
    if _scheduled:
        return
    _scheduled = True
    
    # Test mode: Send now, to test channels
    # Force mode: Send now, to regular channels, with special prefix
    # If both are supplied: Send now, to test channels, with special prefix
    if args.test or args.force:
        print(f"Running in test mode: {args.test}, force mode: {args.force}")
        for event in EVENT_RESOURCES:
            await send_reminder(event, test_mode=args.test, force_send=args.force)
        await client_bot.close()

    # Regular mode: Triggered at 9am daily, to regular channels
    else:
        for event in EVENT_RESOURCES:
            job_id = f"reminder_{event['name']}"
            scheduler.add_job(
                id=job_id,
                func=send_reminder,
                trigger=CronTrigger(hour=9, minute=0),
                misfire_grace_time=60,
                args=[event],
                kwargs={"test_mode": False, "force_send": False},
                replace_existing=True,
                name=f"Reminder: {event['name']}"
            )
        if not scheduler.running:
            scheduler.start()

client_bot.run(DISCORD_TOKEN)
