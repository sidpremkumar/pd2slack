    
import logging
import json

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
@click.option('-configPath', 'configPath', help='Optional config path to use', envvar='PD2SLACK_CINFIG')
@click.option('-ignoreEmailDomain', 'ignoreEmailDomain', help='Ignore the email domain, and just use the alias', default=False)
@click.option('-dryRun', 'dryRun', help='Don\'t make any changes, just log what we\'ll do', default=True)
def main(slackApiKey: str, pdApiKey: str, configPath: str, ignoreEmailDomain: bool, dryRun: bool):
    """
    Main entrypoint to sync PD on call for ALL services with slack user groups
    """
    if (configPath):
        # Open up the config
        configRaw = open(configPath)
        config = json.load(configRaw)
        
        if 'serviceMapping' not in config:
            raise Exception('Missing key "serviceMapping" in config!')
        
        log.info(f'Using passed in config: {configPath}')
    else:
        config = None

    # Ensure we have all our needed options
    if not slackApiKey or not pdApiKey:
        raise Exception('Missing slackApiKey or pdApiKey param! Please ensure they are set!')

    # First get a list of slack email address
    slackUsers = allSlackUsers(slackApiKey)
    log.info(f'Found total: {len(slackUsers)} slack users!')

    # Create a mapping of slackEmail <-> slackUserId
    slackUserEmailMapping = {}
    for slackUser in slackUsers:
        if 'profile' in slackUser and 'email' in slackUser['profile']:
            slackEmail = slackUser['profile']['email']
            if ignoreEmailDomain:
                slackEmail = slackEmail.split('@')[0]  # test@gmail.com -> test
            slackUserEmailMapping[slackEmail] = slackUser['id']
    

    # Now get a map of ScheduleName <-> onCall user email
    log.info('Getting all pd users on call')
    pdUsersOnCall = allPDUsersOnCall(pdApiKey)

    # Get all user groups
    userGroups = getSlackUserGroups(slackApiKey)
    userGroupsFlattened = [userGroup['name'] for userGroup in userGroups]

    # Loop over all the pdUsersOnCall
    for serviceName, email in pdUsersOnCall.items():
        if ignoreEmailDomain:
            email = email.split('@')[0] # test@gmail.com -> test
        
        if email not in slackUserEmailMapping:
            # If the email of PD does not match anyone we know in slack :sad_cowboy:
            log.error(f'Unable to sync email {email} as there is no corresponding slack email!')
            print(slackUserEmailMapping)
            continue

        # If we have passed a config, use that as the serviceName instead
        if not config is None:
            if serviceName in config['serviceMapping']:
                serviceName = config['serviceMapping'][serviceName]
            else: 
                # We only want to sync whats in the config
                log.warn(f'Skipping serviceName: {serviceName} since its not in config!')
                continue
        onCallUserGroupName = f'{serviceName}-oncall'

        log.info(f'Syncing serviceName: {serviceName} with slack userGroup {onCallUserGroupName}')
        
        # Check if the user group exist 
        if onCallUserGroupName not in userGroupsFlattened:
            # We need to create a new user group
            if (not dryRun):
                newUserGroup = createUserGroup(onCallUserGroupName, serviceName, slackApiKey)
            else: 
                log.info(f'DryRun set to: {dryRun}. Would create userGroup: {onCallUserGroupName}')
                newUserGroup = {'usergroup': {'name': onCallUserGroupName, 'id': 'fake'}}

            if 'usergroup' not in newUserGroup:
                raise Exception('Something went wrong with the request')

            # Add that to the list of the userGroups we already queried above, so we don't need to re-query
            userGroups.append(newUserGroup['usergroup'])
        
        # Get the userGroupId
        userGroupId = [userGroup['id'] for userGroup in userGroups if 'name' in userGroup and userGroup['name'] == onCallUserGroupName]
        if not userGroupId:
            log.error(f'Unable to find userGroupId from service: {serviceName} with alias: {onCallUserGroupName}')
            continue
        userGroupId = userGroupId[0]

        # Update the userGroups on slack
        if not dryRun:
            log.info(f'Updating oncall group for PD service: {serviceName} to email: {email}')
            updateUserGroup(userGroupId, slackUserEmailMapping[email], slackApiKey)
        else: 
            log.info(f'DryRun set to: {dryRun}. Would update onCall group from service: {serviceName} with alias: {onCallUserGroupName} to email: {email} with slackUserId: {slackUserEmailMapping[email]}')

