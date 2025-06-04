#!/usr/bin/env python3
"""
Custom Issue Closer - GitHub Action

This script processes commit messages to find and close issues based on
custom regex patterns.
"""

import os
import re
import json
import logging
from github import Github
from github.GithubException import GithubException

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('custom-issue-closer')

def get_github_event():
    """Read the GitHub event data from the event path."""
    event_path = os.environ.get('GITHUB_EVENT_PATH')
    if not event_path:
        raise ValueError("GITHUB_EVENT_PATH environment variable not set")
    
    with open(event_path, 'r') as f:
        return json.load(f)

def get_commit_messages(event, github_client):
    """Extract commit messages from the event."""
    repo_name = os.environ.get('GITHUB_REPOSITORY')
    if not repo_name:
        raise ValueError("GITHUB_REPOSITORY environment variable not set")
    
    repo = github_client.get_repo(repo_name)
    event_name = os.environ.get('GITHUB_EVENT_NAME')
    
    if event_name == 'push':
        # For push events, get messages from the payload
        return [commit['message'] for commit in event.get('commits', [])]
    
    elif event_name == 'pull_request' and event.get('pull_request', {}).get('merged'):
        # For merged PRs, get the PR commits
        pr_number = event['pull_request']['number']
        pr = repo.get_pull(pr_number)
        return [commit.commit.message for commit in pr.get_commits()]
    
    return []

def find_issue_numbers(commit_messages, pattern=r'[d]?(?:\s*:)?\s*#(\d+)$'):
    """Find issue numbers in commit messages using regex pattern."""
    regex = re.compile(pattern, re.IGNORECASE)
    issue_numbers = set()
    
    for message in commit_messages:
        logger.info(f"Processing commit message: {message}")
        if message.lower().startswith("reverts") or message.lower().startswith("revert")):
            logger.info(f"Skipping revert commit: {message}")
            continue
        matches = regex.finditer(message)
        for match in matches:
            issue_number = int(match.group(1))
            issue_numbers.add(issue_number)
    
    return issue_numbers

def close_issues(issue_numbers, github_client):
    """Close the specified issues."""
    if not issue_numbers:
        logger.info("No issues to close")
        return
    
    repo_name = os.environ.get('GITHUB_REPOSITORY')
    repo = github_client.get_repo(repo_name)
    
    for issue_number in issue_numbers:
        try:
            logger.info(f"Closing issue #{issue_number}")
            issue = repo.get_issue(number=issue_number)
            
            # Add a comment to the issue
            issue.create_comment(
                "This issue was automatically closed by the custom-issue-closer action."
            )
            
            # Close the issue
            issue.edit(state='closed')
            
            logger.info(f"Successfully closed issue #{issue_number}")
        except GithubException as e:
            logger.error(f"Error closing issue #{issue_number}: {e}")

def main():
    """Main function to process commits and close issues."""
    try:
        # Get GitHub token
        github_token = os.environ.get('INPUT_GITHUB_TOKEN') or os.environ.get('GITHUB_TOKEN')
        if not github_token:
            raise ValueError("No GitHub token provided")
        
        # Initialize GitHub client
        github_client = Github(github_token)
        
        # Get the custom regex pattern (if provided)
        custom_pattern = os.environ.get('INPUT_PATTERN')
        
        # Get the event data
        event = get_github_event()
        
        # Get commit messages
        commit_messages = get_commit_messages(event, github_client)
        logger.info(f"Found {len(commit_messages)} commit messages to process")
        
        # Find issue numbers to close
        pattern = custom_pattern or r'auto[-\s]?close[d]?(?:\s*:)?\s*#(\d+)'
        issue_numbers = find_issue_numbers(commit_messages, pattern)
        logger.info(f"Found {len(issue_numbers)} issues to close: {issue_numbers}")
        
        # Close the issues
        close_issues(issue_numbers, github_client)
        
        logger.info("Process completed successfully")
    
    except Exception as e:
        logger.error(f"Error in custom issue closer action: {e}")
        raise

if __name__ == "__main__":
    main()
