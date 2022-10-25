    
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
@click.option('-slackEmailDomain', 'slackEmailDomain', help='With SSO, sometimes slack will create two users, and this can cause issues syncing, specify the slack email domain to use', default=None)
@click.option('-dryRun', 'dryRun', help='Don\'t make any changes, just log what we\'ll do', default=False)
def main(slackApiKey: str, pdApiKey: str, configPath: str, ignoreEmailDomain: bool, slackEmailDomain: str, dryRun: bool):
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
        raise Exception('Config must be passed in')

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
            if slackEmailDomain:
                # If we set up to only look for a specific domain, just filter based on that and skip it if it doesn't include it
                if slackEmailDomain not in slackEmail:
                    continue
            
            if ignoreEmailDomain:
                slackEmail = slackEmail.split('@')[0]  # test@gmail.com -> test
            slackUserEmailMapping[slackEmail] = slackUser['id']
    

    # Now get a map of ScheduleName <-> onCall user email
    log.info('Getting all pd users on call')
    pdUsersOnCall = allPDUsersOnCall(pdApiKey)

    # Get all user groups
    userGroups = getSlackUserGroups(slackApiKey)
    userGroupsFlattened = [userGroup['handle'] for userGroup in userGroups]

    # Loop over all the pdUsersOnCall
    for serviceName, email in pdUsersOnCall.items():
        # Save the pd service name
        pdServiceName = serviceName

        if email:
            if email and ignoreEmailDomain:
                email = email.split('@')[0] # test@gmail.com -> test
            
            # Check if we have a custom email mapping in our config
            if config.get('customEmailMapping', None):
                if email in config['customEmailMapping']:
                    email = config['customEmailMapping'][email]

            if email not in slackUserEmailMapping:
                # If the email of PD does not match anyone we know in slack :sad_cowboy:
                log.error(f'Unable to sync email {email} as there is no corresponding slack email!')
                continue
        else: 
            # Email is None, this means there is no one on call
            log.info(f'No user on call for {serviceName}')

        # If we have passed a config, use that as the serviceName instead
        if serviceName in config['serviceMapping']:
            onCallUserGroupName = config['serviceMapping'][serviceName]['alias']
        else: 
            # We only want to sync whats in the config
            log.warn(f'Skipping serviceName: {serviceName} since its not in config!')
            continue

        log.info(f'Syncing serviceName: {serviceName} with slack userGroup {onCallUserGroupName}')
        
        # Check if the user group exist 
        if onCallUserGroupName not in userGroupsFlattened:
            # We need to create a new user group
            if (not dryRun):
                newUserGroup = createUserGroup(onCallUserGroupName, serviceName, pdServiceName, slackApiKey)
            else: 
                log.info(f'DryRun set to: {dryRun}. Would create userGroup: {onCallUserGroupName}')
                newUserGroup = {'usergroup': {'name': onCallUserGroupName, 'id': 'fake', 'handle': onCallUserGroupName}}

            if 'usergroup' not in newUserGroup:
                raise Exception('Something went wrong with the request')

            # Add that to the list of the userGroups we already queried above, so we don't need to re-query
            userGroups.append(newUserGroup['usergroup'])
        
        # Get the userGroupId
        userGroupId = [userGroup['id'] for userGroup in userGroups if 'name' in userGroup and userGroup['handle'] == onCallUserGroupName]
        if not userGroupId:
            log.error(f'Unable to find userGroupId from service: {serviceName} with alias: {onCallUserGroupName}')
            continue
        userGroupId = userGroupId[0]

        # Build a list of userIds, if the config specified to add extra users, add them as well
        userIds = []
        if email:
            userIds.append(slackUserEmailMapping[email])
        if 'usersToAdd' in config['serviceMapping'][serviceName]:
            for userToAdd in config['serviceMapping'][serviceName]['usersToAdd']:
                # Lookup the slack userId from the email 
                if ignoreEmailDomain:
                    userToAdd = userToAdd.split('@')[0] # test@gmail.com -> test
                slackId = slackUserEmailMapping[userToAdd]
                userIds.append(slackId)

        # Update the userGroups on slack
        if not dryRun:
            log.info(f'Updating oncall group for PD service: {serviceName} to slackUserIds: {userIds}')
            updateUserGroup(userGroupId, userIds, slackApiKey)
        else: 
            log.info(f'DryRun set to: {dryRun}. Would update onCall group from service: {serviceName} with alias: {onCallUserGroupName} to slackUserIds: {userIds}')

