import json
import logging

import requests

log = logging.getLogger(__name__)


def allSlackUsers(slackApiKey: str):
    """
    Gets all slack users
    """
    url = f'https://slack.com/api/users.list'
    response = _make_request(url, headers={'Authorization': f'Bearer {slackApiKey}'})
    responseJson = response.json()

    if (responseJson['ok'] != True):
        raise Exception(f'Invalid status code when getting all users: {responseJson["error"]}')

    log.info('Found %d total Slack users', len(responseJson['members']))
    return responseJson['members']

def getSlackUserGroups(slackApiKey: str):
    """
    Gets all slack user groups that exist
    """
    url = 'https://slack.com/api/usergroups.list'
    response = _make_request(url, headers={'Authorization': f'Bearer {slackApiKey}'})
    responseJson = response.json()

    if (responseJson['ok'] != True):
        raise Exception(f'Invalid status code when getting all userGroups: {responseJson["error"]}')

    print(responseJson)

    log.info('Found %d total Slack userGroup', len(responseJson['usergroups']))
    return responseJson['usergroups']

def createUserGroup(userGroupName: str, slackApiKey: str):
    """
    Creates a user group
    """
    url = 'https://slack.com/api/usergroups.create'
    response = _make_request(url, headers={'Authorization': f'Bearer {slackApiKey}'}, params={'name': userGroupName})
    responseJson = response.json()

    if (responseJson['ok'] != True):
        raise Exception(f'Error creating user group: {userGroupName}. {responseJson["error"]}')

def allPDUsersOnCall(pdApiKey: str):
    """
    Get all pager duty users on call
    """
    headers = {'Authorization': f'Token token={pdApiKey}'}

    # First query for all schedules
    schedulesUrl = 'https://api.pagerduty.com/schedules'
    scheduleInfo = _make_request(schedulesUrl, headers=headers)
    scheduleInfoParsed = scheduleInfo.json()
    onCallMap = {}

    # Loop over each schedule to create a map of scheduleName <-> email
    for schedule in scheduleInfoParsed['schedules']:
        # Get the user on call
        userOnCallUrl = f'https://api.pagerduty.com/schedules/{schedule["id"]}/users'
        userOnCallInfo = _make_request(userOnCallUrl, headers=headers)
        userOnCallInfoParsed = userOnCallInfo.json()

        # Assume only one user
        # TODO: Support multiple users
        userInfo = userOnCallInfoParsed['users'][0]

        # TODO: remove
        if userInfo['email'] == '7rdyrbrjj2@privaterelay.appleid.com':
            userInfo['email'] = 'sid.premkumar@gmail.com'

        onCallMap[schedule['summary']] = userInfo['email']

    return onCallMap


def _make_request(url, params={}, headers={}):
    log.info('Making request to %s', url)

    req = requests.get(url, params=params, headers=headers)

    return req