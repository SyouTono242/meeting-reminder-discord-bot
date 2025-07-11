# Custom Discord Bot Mostly for Sending Lab Meeting Reminders

Yeah I was looking for a bot that reads event (and its related info) from a Google Sheet and posts weekly reminders but couldn't find any... so here it is.

Initially designed for the Wang Group at UofT because we're too cool (i.e., too broke) to use Slack. Posting the bot here for record. Modify it as you wish. 

## Running the bot locally
On your local machine, run the bot with
```bash
python reminder_bot.py --config config.json
```
with `config.json` file defined like this:
```json
{
	"discord_token": <discord_token>,
	"channel_id": <discord_channel_id>,
	"google_sheet_name": <preauthorized_google_sheet_name>,
	"spreadsheet_range": "Sheet1!A1:Z",
	"timezone": "America/Toronto",
	"service_account_file": <google_service_account_credential_file_name>,
	"date_format": "%Y-%m-%d"
}
```

The Google Sheet this bot reads from should be formatted like this:
```csv
Date, Time, Location, Presenter, Notes
2025-07-16, 13:30, Donnelly 11th floor, Lucky lab member A, A will present the space
```

