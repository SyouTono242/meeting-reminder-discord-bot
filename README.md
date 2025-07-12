# Discord Bot Mostly for Sending Lab Meeting Reminders

Yeah I was looking for a bot that reads event (and its related info) from a Google Sheet and posts weekly reminders but couldn't find any... so here it is.

Initially designed for the Wang Group at UofT because we're too cool (i.e., too broke) to use Slack. Posting the bot here for record. Modify it as you wish. 


## Demo
Input:
```bash
python reminder_bot.py --config config.json --test
```
<img width="653" height="316" alt="demo" src="https://github.com/SyouTono242/meeting-reminder-discord-bot/blob/58d6bef54ed949f435b4668588ef0e9faaf74959/demo.png" />

Output log:
```bash
2025-07-12 19:00:48 INFO     discord.client logging in using static token
2025-07-12 19:00:49 INFO     discord.gateway Shard ID None has connected to Gateway (Session ID: ###).
Bot logged in as ###
Running in test mode...
Scheduler triggered on 2025-07-12 19:00:51
Sending reminder for meeting on 2025-07-13 to channel tester-channel...
```

## Prereqs for setting up your own bot
- Set Up the Google Sheet
	- The Google Sheet this bot reads from should be formatted like this:
```csv
Date, Time, Location, Presenter, Notes
2025-07-11, 23:59, Tester dungeon, Tester guy, Tester guy wont present anything bc he is badass and he is free
...
```
  
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


## Running the bot
On your local machine, run the bot with
```bash
python reminder_bot.py --config config.json
```
with `config.json` file defined like this:
```json
{
	"discord_token": <discord_token>,
	"channel_id": <discord_channel_id>,
	"mention_role_id": <discord_role_id_to_mention>,
	"google_sheet_name": <preauthorized_google_sheet_name>,
	"google_sheet_viewer_link": <google_sheet_link_with_viewer_access>,
	"timezone": "America/Toronto",
	"service_account_file": <google_service_account_credential_file_name>,
	"date_format": "%Y-%m-%d",
	"test_channel_id": <discord_channel_to_run_tests_on>
}
```
