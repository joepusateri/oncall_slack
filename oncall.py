#!/usr/bin/env python

import argparse
import datetime

import pdpyras
import requests

DEBUG = False
BASE_URL = 'https://slack.com/api/'
global slack_token


def get_oncalls(session, range):
    me = 'get_oncalls'
    pd_user_map = {}

    # expecting 'd' or 'w'
    if range == 'd':
        until_date = (datetime.datetime.utcnow() + datetime.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        until_date = (datetime.datetime.utcnow() + datetime.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

    if DEBUG: print(f'   {me}: Getting on-calls range:{range} -> {until_date}')

    for oncall in session.iter_all('oncalls', params={'until': until_date}):
        try:
            if DEBUG: print(f'{oncall["escalation_level"]} {oncall["user"]["summary"]}')
            if not (oncall["user"]["id"] in pd_user_map):
                user = session.rget(f'/users/{oncall["user"]["id"]}')
                if DEBUG: print(f'user:{user}')
                pd_user_map[user['id']] = user['email']

            if DEBUG: print(f'pd_user_map:{pd_user_map}')
        except:
            print(f'User not found {oncall["user"]["id"]}')
    return pd_user_map


def create_or_find_conversation(conversation_name):
    me = 'create_or_find_conversation'

    if DEBUG: print(f'   {me}: Searching for conversation name={conversation_name}')

    url = f'{BASE_URL}conversations.list'

    payload = dict(limit=100, exclude_archived='false')
    slack_headers = {
        'Authorization': f'Bearer {slack_token}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    more_records: bool = True  #pagination control
    while more_records:
        if DEBUG: print(f'   {me}: Search for Conversation with payload={payload}')
        search_conversation_response = requests.request("POST", url=url, headers=slack_headers, data=payload)
        if DEBUG: print(f'   {me}: Search for Conversation response={search_conversation_response.text}')

        channel_id = ""
        for channel in search_conversation_response.json()['channels']:
            if DEBUG: print(f'   {me}: Matching {conversation_name} to {channel["name"]}')
            if conversation_name == channel['name']:
                channel_id = channel['id']
                print(f'   {me}: Conversation {channel["name"]} found')
                break

        if DEBUG: print(f'   {me}: Searched for Conversation id={channel_id}')
        if len(channel_id) > 0: #found the channel in this batch
            more_records = False
            if DEBUG: print(f'   {me}: Found Conversation id={channel_id}')

        else: # Did not find the channel in this batch
            json_response = search_conversation_response.json()
            if len(json_response['response_metadata']['next_cursor']) > 0: # more channels to retrieve
                payload['cursor'] = json_response['response_metadata']['next_cursor']
            else: # no more channels to retrieve - give up looking
                more_records = False

    # conversation_name was not found, so attempt to create it instead
    if len(channel_id) == 0:
        if DEBUG: print(f'   {me}: Creating conversation name={conversation_name}')

        url = f'{BASE_URL}conversations.create'
        payload = f'name={conversation_name}'
        slack_headers = {
            'Authorization': f'Bearer {slack_token}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        if DEBUG: print(f'   {me}: Create Conversation with payload={payload}')
        create_conversation_response = requests.request("POST", url=url, headers=slack_headers, data=payload)

        if create_conversation_response.json()["ok"]:
            if DEBUG: print(f'   {me}: Conversation created Successfully')
            channel_id = create_conversation_response.json()["channel"]["id"]
            print(f'   {me}: Conversation {create_conversation_response.json()["channel"]["name"]} created')
        else:
            print(f'   {me}: Create Conversation failed:{create_conversation_response.text}')

        if DEBUG: print(f'   {me}: Created Conversation id={channel_id}')
    if DEBUG: print(f'   {me}: Returning Conversation id={channel_id}')
    return channel_id


def post_message(conversation_id, message):
    me = 'post_message'
    if DEBUG: print(f'   {me}: Posting a Message in {conversation_id} message={message}')

    url = f'{BASE_URL}chat.postMessage'
    payload = dict(channel=conversation_id, text=message)
    slack_headers = {
        'Authorization': f'Bearer {slack_token}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    if DEBUG: print(f'   {me}: Posting a Message with payload={payload}')
    post_message_response = requests.request("POST", url=url, headers=slack_headers, params=payload)
    if DEBUG: print(f'   {me}: Posting a Message response={post_message_response.text}')
    json_resp = post_message_response.json()
    if json_resp["ok"]:
        if DEBUG: print(f'   {me}: Message Posted Successfully')
    else:
        print(f'   {me}: Posting a Message failed:{post_message_response.text}')


def get_slack_ids(pd_users):
    me = 'get_slack_ids'

    slack_headers = {
        'Authorization': f'Bearer {slack_token}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    slack_user_ids = []
    if DEBUG: print(f'   {me}: Getting Slack Ids for pd_users={pd_users}')
    for pd_id, email_address in pd_users.items():
        if DEBUG: print(f'   {me}: email_address={email_address}')

        url = f'{BASE_URL}users.lookupByEmail'
        payload = {'email': email_address}

        if DEBUG: print(f'   {me}: get Slack user with payload={payload}')
        get_user_response = requests.get(url, headers=slack_headers, params=payload)
        if DEBUG: print(f'   {me}: Get User response={get_user_response.text}')
        json_resp = get_user_response.json()
        if json_resp["ok"]:
            get_user_response_id = json_resp['user']['id']
            if DEBUG: print(f'   {me}: Get User id={get_user_response_id}')
            slack_user_ids.append(get_user_response_id)
        else:
            print(f'   {me}: {email_address} not found:{get_user_response.text}')

    if DEBUG: print(f'   {me}: Slack ids={slack_user_ids}')

    return slack_user_ids


def invite_users(channel_id, slack_user_ids):
    me = 'invite_users'

    cd_slack_user_ids = ",".join(slack_user_ids)
    if DEBUG: print(f'   {me}: Inviting Users to conversation id={channel_id}')

    url = f'{BASE_URL}conversations.invite'
    payload = dict(channel=channel_id, users=cd_slack_user_ids)
    slack_headers = {
        'Authorization': f'Bearer {slack_token}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    if DEBUG: print(f'   {me}: Inviting Users with payload={payload}')
    invite_users_response = requests.request("POST", url=url, headers=slack_headers, params=payload)
    json_resp = invite_users_response.json()
    if json_resp["ok"]:
        if DEBUG: print(f'   {me}: Invited Successfully')
    else:
        print(f'   {me}: Invite Users failed:{invite_users_response.text}')

    return


if __name__ == '__main__':
    # print(date.today())
    ap = argparse.ArgumentParser(description="Retrieves PagerDuty users who will be on-call in the next day or week, "
                                             "creates a Slack Conversation and invites them to it, then sends a "
                                             "message to that Conversation")
    ap.add_argument('-k', "--api-key", required=True, help="(Required) REST API key")
    ap.add_argument('-t', "--slack-token", required=True, help="(Required) Slack BOT token")
    ap.add_argument('-m', "--message", required=True, help="(Required) Message to Send to Slack Conversation")
    ap.add_argument('-r', "--range", required=False, help="(Optional) Time range to check for on-calls. Allowed Values 'd' (day) "
                                                          "or 'w' (week). Defaults to 'd'.")
    ap.add_argument('-c', "--chat-name", required=False, help="(Optional) Name of Conversation/Chat to create")
    ap.add_argument('-d', "--debug", required=False, help="(Optional) Debug flag", action="store_true")
    args = ap.parse_args()
    session = pdpyras.APISession(args.api_key)
    slack_token = args.slack_token
    DEBUG = args.debug
    range = "d" if args.range is None else args.range
    if DEBUG: print(f'Range is {range}')

    pd_users = get_oncalls(session, range)
    print(f'{len(pd_users.items())} PagerDuty users found on-call')
    slack_ids = get_slack_ids(pd_users)
    print(f'{len(slack_ids)} matching Slack users found')
    if len(slack_ids) > 0:
        if len(slack_ids) > 1000:
            print("Warning: only the first 1000 users will be invited")
        conv_id = create_or_find_conversation(args.chat_name if args.chat_name is not None and len(args.chat_name) > 0 else f'oncalls_{datetime.date.today()}')
        if  len(conv_id) > 0:
            print('Conversation found or created')
            invite_users(conv_id, slack_ids)
            print('All users invited')
            post_message(conv_id, args.message)
            print('Message posted')
        else:
            print('Failed to find or create conversation ... Process failed.')
