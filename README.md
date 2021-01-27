# oncall_slack

This is a script to retrieve the upcoming On-call users for the next day OR week and notify them in a Slack channel that they will soon be on-call.

## Files
* oncall.py - main script
* requirements.txt - the Python required libraries.  

## Setup

### Using the requirements.txt file
The following command will install the packages according to the configuration file requirements.txt.

```
$ pip3 install -r requirements.txt
```

### Setting the Permissions for your bot
This script assumes you have created a Slack bot with the proper permissions and obtained the Bot User OAuth Access Token.

Here are the necessary permissions:
* channels:manage
* channels:read
* chat:write
* groups:read
* im:read
* mpim:read
* users.profile:read
* users:read
* users:read.email

## Running

Parameters:
```
* k = PagerDuty API Key (required) - This is an API token (global or user)
* t = Slack bot Token (required) - A bot in Slack needs to be first created and the necessary permissions granted.
* m = Message to send (required) - This message will be sent to all users who are oncall
* r = Range to include oncall users. (optional) - Can be either a 'd' for 1 day or a 'w' for 1 week ahead. Defaults to 'd'
* c = Conversation name (optional) - The conversation name to invite users and send the message to. Defaults to "oncall_YYYY-MM-DD" using the current date.
* d (optional) - include this to print debug messages
```
Example:
```
./oncall -k 0123456789001234567890 -t xoxb-xxxxxx-xxxxx -m "You will be going oncall in the next day"
```
This creates a conversation named "oncalls_2021-01-27" (for 1/27/2021) for all people who will be going oncall in the next day.

```
./oncall -k 0123456789001234567890 -t xoxb-xxxxxx-xxxxx -m "You will be going oncall in the next week" -r w -c all_teams -d
```
This creates a conversation named "all_teams" and invites all people who will be oncall in the next week. It also prints the debug messages to the console.
