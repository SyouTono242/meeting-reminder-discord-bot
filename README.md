# Discord Bot for Sending Lab Meeting and Other Reminders

Yeah I was looking for a bot that reads event (and its related info) from a Google Sheet and posts weekly reminders but couldn't find any... so here it is.

Initially designed for the Wang Group at UofT because we're too cool (i.e., too broke) to use Slack. Posting the bot here for record. Modify it as you wish. 

## What this bot does

Input:

```bash
python reminder_bot.py --config config.json --test
```

<img width="653" height="316" alt="demo" src="https://github.com/SyouTono242/meeting-reminder-discord-bot/blob/58d6bef54ed949f435b4668588ef0e9faaf74959/demo.png" />

Output log:

```
2025-07-31 01:35:26 INFO     discord.client logging in using static token
2025-07-31 01:35:26 INFO     discord.gateway Shard ID None has connected to Gateway (Session ID: ###).
Bot logged in as ###
Running in test mode: True, force mode: False
[Event 1] reminder triggered on 2025-07-31 01:35:29
[Event 1] No event in 1 days (next is 2025-08-06)
[Event 2] reminder triggered on 2025-07-31 01:35:30
Sending reminder for meeting [Event 2] on 2025-08-04 to channel tester-channel...
```

## Options the bot takes

- **--config**: Path to the config JSON file, default to "./config.json"
- **--test**: Run in test mode, i.e., messages will be sent to the test channel as specified in the config file, and it will not mention anyone
- **--force**: Force to send reminders to the most recent upcoming events from all sheets listed in the config file. Ignores "days_before"

## Running the bot

### Prereqs

Before you start, make sure you have your Google API set up (for accessing the Google Sheet) and its credentials stored in the file "credentials.json", and bot config settings stored in the file "config.json" (for telling the bot where and when to send messages, who to mention, etc.), under the same directory as the bot itself. 

If you're running the bot for the Wang Group, you can request for these files here:

- credentials.json: https://drive.google.com/file/d/15vG_W8DEJ-xPwm8-DJiRHfdK-qgsNFau/view?usp=drive_link
- config.json: https://drive.google.com/file/d/17amno0Bm0CaetNx_zI_JOlWvpDmTuqjY/view?usp=drive_link

Otherwise if you have to make your own config files:

- credentials.json: Following the [steps for set up](#setting-up-your-own-bot) it will be provided to your with your Google Service Account as JSON key

- config.json:

  - ```json
    {
      "discord_token": "your_token",
      "timezone": "America/Toronto",
      "service_account_file": "credentials.json",
      "test_channel_id": 123456789012345678,
      "event_sources": [
        {
          "name": "Event 1",
          "google_sheet_name": "Event 1 Sheet",
          "google_sheet_viewer_link": "https://docs.google.com/sheet1",
          "spreadsheet_range": "Sheet1!A2:Z",
          "date_format": "%Y-%m-%d",
          "channel_id": 987654321012345678,
          "mention_role": "<@&112233445566778899>",
          "days_before": 1
        },
        {
          "name": "Event 2",
          "google_sheet_name": "Event 1 Sheet",
          "google_sheet_viewer_link": "https://docs.google.com/sheet2",
          "spreadsheet_range": "Schedule!A2:Z",
          "date_format": "%Y-%m-%d",
          "channel_id": 888888888888888888,
          "mention_role": "@everyone",
          "days_before": 2
        }
      ]
    }
    ```

### Running the bot

```bash
python reminder_bot.py --config config.json
```
## Setting up your own bot

- Set Up the Google Sheet
	- We assume that the Google Sheet has a header row
	- Currently we assume that the first column in the Google Sheet to be Date, in format defined by "date_format" in config.json
- Create a Discord Bot
  	- Go to [Discord Developer Portal](https://discord.com/developers/applications) to create the bot
  	- Add bot and enable `MESSAGE CONTENT INTENT`
  	- Go to OAuth2 and give it the permission to `Send Messages` and `Mention Everyone`
  	- Copy the generated URL and use it to invite the bot to your server
- Setup Google Sheets and Google Drive API
	- Create a Google Cloud Project: https://console.cloud.google.com/
 	- Enable the Google Sheets API and Google Drive API
  	- Create a Service Account
  	- Create a JSON Key, save it, and later supply its path as your `<google_service_account_credential_file_name>` in the `config.json` file below
      	- Save the service account email (e.g., `discord-bot-reader@your-project.iam.gserviceaccount.com`)
- Share Your Google Sheet with the Service Account Email
	- Add your service account email with Viewer access to the Google Sheet
