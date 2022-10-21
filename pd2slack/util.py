import json
import logging

import requests

log = logging.getLogger(__name__)


def allSlackUsers(slackApiKey: str):
    """
    Gets all slack users
    """
    url = f'https://slack.com/api/users.list'
    response = makeGETRequest(url, headers={'Authorization': f'Bearer {slackApiKey}'})
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
    response = makeGETRequest(url, headers={'Authorization': f'Bearer {slackApiKey}'})
    responseJson = response.json()

    if (responseJson['ok'] != True):
        raise Exception(f'Invalid status code when getting all userGroups: {responseJson["error"]}')

    log.info('Found %d total Slack userGroup', len(responseJson['usergroups']))
    return responseJson['usergroups']

def createUserGroup(userGroupName: str, serviceName: str, slackApiKey: str):
    """
    Creates a user group
    """
    url = 'https://slack.com/api/usergroups.create'
    response = makePOSTRequest(url, headers={'Authorization': f'Bearer {slackApiKey}'}, 
        data={'name': userGroupName, 'handle': userGroupName.lower(), 'description': f'Autocreated usergroup for PagerDuty service: {serviceName}'})
    responseJson = response.json()

    if (responseJson['ok'] != True):
        raise Exception(f'Error creating user group: {userGroupName}. {responseJson["error"]}')
    
    return responseJson

def updateUserGroup(userGroupId: str, userId: str, slackApiKey: str):
    """
    Updates a given userGroup to a slack email
    """
    url = 'https://slack.com/api/usergroups.users.update'
    response = makePOSTRequest(url, headers={'Authorization': f'Bearer {slackApiKey}'}, data={'usergroup': userGroupId, 'users': [userId]})
    responseJson = response.json()

    if (responseJson['ok'] != True):
        raise Exception(f'Error updating user group: {userGroupId} for user: ${userId}. {responseJson["error"]}')


def allPDUsersOnCall(pdApiKey: str):
    """
    Get all pager duty users on call
    """
    headers = {'Authorization': f'Token token={pdApiKey}'}

    # First query for all schedules
    schedulesUrl = 'https://api.pagerduty.com/schedules'
    scheduleInfo = makeGETRequest(schedulesUrl, headers=headers)
    scheduleInfoParsed = scheduleInfo.json()
    onCallMap = {}

    # Loop over each schedule to create a map of scheduleName <-> email
    for schedule in scheduleInfoParsed['schedules']:
        scheduleId = schedule['id']


        # Get the user on call
        params = {
            'schedule_ids[]': [scheduleId],
            'include[]': ['users']
        }
        userOnCallUrl = 'https://api.pagerduty.com/oncalls'
        userOnCallInfo = makeGETRequest(userOnCallUrl, headers=headers, params=params)
        userOnCallInfoParsed = userOnCallInfo.json()

        # Parse out the users email
        onCallUserEmail = userOnCallInfoParsed['oncalls'][0]['user']['email']

        onCallMap[schedule['summary']] = onCallUserEmail

    return onCallMap


def makeGETRequest(url, params={}, headers={}):
    log.info('Making GET request to %s', url)

    req = requests.get(url, params=params, headers=headers)

    return req

def makePOSTRequest(url, data={}, headers={}):
    log.info('Making POST request to %s', url)

    req = requests.post(url, json=data, headers=headers)

    return req