    
import logging
import sys

import click

from pd2slack.util import allPDUsersOnCall, allSlackUsers, createUserGroup, getSlackUserGroups, updateUserGroup


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

log = logging.getLogger(__name__)

@click.command()
@click.option('-slackApiKey', 'slackApiKey', help='Slack API key to use', envvar='SLACK_API_KEY')
@click.option('-pdApiKey', 'pdApiKey', help='Pager Duty API key to use', envvar='PD_API_KEY')
def main(slackApiKey: str, pdApiKey: str):
    """
    Main entrypoint to sync PD on call for ALL services with slack user groups
    """
    # Ensure we have all our needed options
    if not slackApiKey or not pdApiKey:
        raise Exception('Missing slackApiKey or pdApiKey param! Please ensure they are set!')

    # First get a list of slack email address
    slackUsers = allSlackUsers(slackApiKey)

    # Create a mapping of slackEmail <-> slackUserId
    slackUserEmailMapping = {}
    for slackUser in slackUsers:
        if 'profile' in slackUser and 'email' in slackUser['profile']:
            slackUserEmailMapping[slackUser['profile']['email']] = slackUser['id']


    # Now get a map of ScheduleName <-> onCall user email
    pdUsersOnCall = allPDUsersOnCall(pdApiKey)

    # Get all user groups
    userGroups = getSlackUserGroups(slackApiKey)
    userGroupsFlattened = [userGroup['name'] for userGroup in userGroups]

    # Loop over all the pdUsersOnCall
    for serviceName, email in pdUsersOnCall.items():
        # Check if the user group exist 
        onCallUserGroupName = f'{serviceName}-oncall'
        if onCallUserGroupName not in userGroupsFlattened:
            # We need to create a new user group
            newUserGroup = createUserGroup(onCallUserGroupName, serviceName, slackApiKey)
            userGroups.append(newUserGroup)
        
        # Get the userGroupId
        userGroupId = [userGroup['id'] for userGroup in userGroups if userGroup['name'] == onCallUserGroupName]
        if not userGroupId:
            log.error(f'Unable to find userGroupId for service: {onCallUserGroupName}')
            continue
        userGroupId = userGroupId[0]

        # Update the userGroups on slack
        log.info(f'Updating oncall group for PD service: {serviceName} to email: {email}')
        updateUserGroup(userGroupId, slackUserEmailMapping[email], slackApiKey)

