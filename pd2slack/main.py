    
import logging

import click

from pd2slack.util import allPDUsersOnCall, allSlackUsers, createUserGroup, getSlackUserGroups


log = logging.getLogger(__name__)




@click.command()
@click.option('-slackApiKey', 'slackApiKey', help='Slack API key to use')
@click.option('-pdApiKey', 'pdApiKey', help='Pager Duty API key to use')
def main(slackApiKey: str, pdApiKey: str):
    """
    Main entrypoint to sync PD on call for ALL services with slack user groups
    """
    # First get a list of slack email address
    slackUsers = allSlackUsers(slackApiKey)
    slackUserEmailMapping = {}
    # for slackUser in slackUsers:
        # if 'profile' in slackUser and 'email' in slackUser['profile']:
            # slackUserEmailMapping[slackUser['profile']['email']] = 
    slackUserEmails = [slackUser['profile']['email'] for slackUser in slackUsers if 'profile' in slackUser and 'email' in slackUser['profile']]

    # Now get a map of ScheduleName <-> onCall user email
    pdUsersOnCall = allPDUsersOnCall(pdApiKey)

    # Create a mapping PD on call <-> Slack Username

    print(slackUserEmails)
    print(pdUsersOnCall)

    # Get all user groups
    userGroups = getSlackUserGroups(slackApiKey)

    # Loop over all the pdUsersOnCall
    for serviceName, email in pdUsersOnCall.items():
        # Check if the user group exist 
        if serviceName not in userGroups:
            # We need to create a new user group
            createUserGroup(serviceName, slackApiKey)
        
        # Update the userGroups on slack

