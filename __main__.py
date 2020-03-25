#!/usr/bin/env python
##
## Simple python to create a release branch from master and tag it appropriately
##
from github import Github, InputGitAuthor, UnknownObjectException
import yaml
import os, datetime

# Some default settings
create_needed_label = 'release-branch-needed'
release_label_prefix = 'release/'
release_version_prefix = 'release-'

# Default content for release branch commit and tag
source_branch = 'master'
release_file = 'release-version.txt'
release_commit_message = 'create new release branch for {}'
release_content = ''
tag_message = 'New release branch for {}'



# Quick and dirty way of putting all return actions in one place
def bot_status(issue, state):
    # We always want to tell github all is well with the webhook, but post an appropriate comment on issue
    if state == 'no_action_needed':
        return dict(headers={"Content-Type": "application/json", "x-gitbot-state": state, "x-gitbot-action": "noop"}, body={"state": state}, statusCode=200)
    
    if state == 'multiple_releases':
        m = issue.create_comment('It seems like this issue is labelled with multiple release versions. Please use a single release label per issue')
        return dict(headers={"Content-Type": "application/json"}, body={"state": state, "messageid": m.id}, statusCode=200)
    
    if state == 'no_releases':
        m = issue.create_comment('There was a problem with your request. Please add the release version label before adding the {} label'.format(create_needed_label))
        return dict(headers={"Content-Type": "application/json"}, body={"state": state, "messageid": m.id}, statusCode=200)
    if state == 'no_owners':
        m = issue.create_comment('I can not seem to find an OWNERS file in the repository. Please make sure an owners file is present and relabel this issue with {} when complete '.format(create_needed_label))
        return dict(headers={"Content-Type": "application/json"}, body={"state": state, "messageid": m.id}, statusCode=200)
    if state == 'error_owners':
        m = issue.create_comment('I had some issues reading the OWNERS file for this repo. Please make sure the OWNERS file exists and contact CICD team for assistance')
        return dict(headers={"Content-Type": "application/json"}, body={"state": state, "messageid": m.id}, statusCode=200)     
    if state == 'owners_yaml_error':
        m = issue.create_comment('I had some issues reading the OWNERS file for this repo. Please make sure the OWNERS file is a valid YAML format with prescribed content')
        return dict(headers={"Content-Type": "application/json"}, body={"state": state, "messageid": m.id}, statusCode=200)     
    if state == 'release_successful':
        m = issue.create_comment('I have created the release branches and tagged it as requested.')
        return dict(headers={"Content-Type": "application/json"}, body={"state": state, "messageid": m.id}, statusCode=200)     
    if state == 'only_owner_can_open':
        m = issue.create_comment('Only the main owner of the repo as specified as the firest entry in the OWNERS file can open a release request.')
        return dict(headers={"Content-Type": "application/json"}, body={"state": state, "messageid": m.id}, statusCode=200)     
         
    # If we arrive here, we have a problem and should log this to the CICD team
    return dict(headers={"Content-Type": "application/json"}, body={"state": state}, statusCode=500)     
    
def main(params):
    
    # TODO: First thing, validate the secret
    # Check X-Hub-Signature: sha1=e9c597bdb2ec51b1ec8c77d81a5dfa5dcfdc0457
    # in params['__ow_headers']['X-Hub-Signature']
    
    # We get a number of events when an issue is opened. We will just act on the label event
    if not (params['issue']['state'] == 'open' and 
            params['action'] == 'labeled' and
            params['label']['name'] == create_needed_label ):
        return bot_status(None, 'no_action_needed')
    
    # Get the necessary details from the issue
    repo=params['repository']['full_name']
    baseurl=params['repository']['url'].split('/repos/')[0]
    
    # Create a connection object to github upstream repo and issue
    g = Github(base_url=baseurl, login_or_token=params['ghtoken'])
    ur = g.get_repo(repo)
    issue = ur.get_issue(params['issue']['number'])
    
    # Figure out what release version we're cutting
    r = [ o['name'] for o in params['issue']['labels'] if o['name'].startswith(release_label_prefix)]
    if len(r) > 1:
        return bot_status(issue, 'multiple_releases')
    elif len(r) < 1:
        return bot_status(issue, 'no_releases')
    rb=r[0].replace(release_label_prefix,"")
    
    ### Check that the creator of the issue is the owner
    try:
        o = ur.get_contents('OWNERS')
    except github.UnknownObjectException:
        return bot_status(issue, 'no_owners')
    except:
        return bot_status(issue, 'error_owners')
    
    try:
        owners = yaml.safe_load(o.decoded_content)
    except:
        return bot_status(issue, 'owners_yaml_error')

    if not 'owners' in owners or len(owners['owners']) < 1:
        return bot_status(issue, 'owners_yaml_error')
    
    if not params['sender']['login'] == owners['owners'][0]:
        return bot_status(issue, 'only_owner_can_open')
    
    ### Create a new branch from master
    # From https://stackoverflow.com/questions/46120240/how-to-checkout-to-a-new-branch-with-pygithub
    # TODO: Add branch protection
    sb = ur.get_branch(source_branch)
    ur.create_git_ref(ref='refs/heads/' + rb, sha=sb.commit.sha)
     
    ## Add a file so we get a unique commit hash in branch to tag 
    # From https://pygithub.readthedocs.io/en/latest/examples/Repository.html#create-a-new-file-in-the-repository
    # TODO: Add check to see if file already exists
    rc = ur.create_file(release_file, release_commit_message.format(rb), release_content.format(rb), branch=rb)

    # Tag the release branch commit
    # TODO: Add checks to validate of the branch and tag already exists
    tag = rb.replace(release_version_prefix,"")
    rt = ur.create_git_tag(tag, tag_message.format(rb), rc['commit'].sha, 'commit', tagger=InputGitAuthor(name=params['tag_author'],email=params['tag_author_email'],date=datetime.datetime.utcnow().isoformat("T","seconds")+'-00:00'))
    gt = ur.create_git_ref(ref='refs/tags/' + tag, sha=rc.['commit'].sha)

    # TODO validate that tag was created successfully before blowing the trumpet
    return bot_status(issue, 'release_successful')
