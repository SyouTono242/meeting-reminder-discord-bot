# Discord Bot for Sending Lab Meeting and Other Reminders

Yeah I was looking for a bot that reads event (and its related info) from a Google Sheet and posts weekly reminders but couldn't find any... so here it is.

Initially designed for the Wang Group at UofT because we're too cool (i.e., too broke) to use Slack. Posting the bot here for record. Modify it as you wish. 


## Testing the bot
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
Running in test mode...
[Event 1] reminder triggered on 2025-07-31 01:35:29
[Event 1] No event in 1 days (next is 2025-08-06)
[Event 2] reminder triggered on 2025-07-31 01:35:30
Sending reminder for meeting [Event 2] on 2025-08-04 to channel tester-channel...
```

## Running the bot
On your local machine, run the bot with
```bash
python reminder_bot.py --config config.json
```
with `config.json` file defined like this:
```json
{
  "discord_token": "your_token",
  "timezone": "America/Toronto",
  "service_account_file": "credentials.json",
  "date_format": "%Y-%m-%d",
  "test_channel_id": 123456789012345678,
  "event_sources": [
    {
      "name": "Event 1",
      "google_sheet_name": "Event 1 Sheet",
      "google_sheet_viewer_link": "https://docs.google.com/sheet1",
      "spreadsheet_range": "Sheet1!A2:Z",
      "channel_id": 987654321012345678,
      "mention_role": "<@&112233445566778899>",
      "days_before": 1
    },
    {
      "name": "Event 2",
      "google_sheet_name": "Event 1 Sheet",
      "google_sheet_viewer_link": "https://docs.google.com/sheet2",
      "spreadsheet_range": "Schedule!A2:Z",
      "channel_id": 888888888888888888,
      "mention_role": "@everyone",
      "days_before": 2
    }
  ]
}

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
