import os
import time
import github
import datetime
import requests
#from discord import Webhook, RequestsWebhookAdapter


##########################
#### GITHUB API CALLS ####
##########################

def get_changed_lines(repo_name):
    """Get the list of files changed in the last day."""

    # Set the personal access token for the GitHub API
    access_token = os.getenv('GH_ACCESS_TOKEN')
    if not access_token:
        print("GITHUB_ACCESS_TOKEN wasn't configured in the secrets!")
        return []
    
    # Create a GitHub API client using the personal access token
    client = github.Github(access_token)

    # Get the repository object
    repo = client.get_repo(repo_name)

    # Store files changed in the last day
    files = []

    # Set the number of lines changed threshold
    lines_changed_threshold = 15

    # Set the time range for commits to check (one day in seconds)
    time_range = 24 * 60 * 60

    # Set the current time
    current_time = int(time.time())

    # Set the starting time for commits to check
    start_time = datetime.datetime.fromtimestamp(current_time - time_range)

    # Get the list of commits within the specified time range
    commits = repo.get_commits(since=start_time)

    # Loop through the list of commits
    for commit in commits:
        # Get the commit SHA
        commit_sha = commit.sha

        # Get the commit object
        commit_obj = repo.get_commit(commit_sha)

        # Get the list of modified files for the commit
        modified_files = commit_obj.files

        # Loop through the list of modified files
        for file in modified_files:
            # Get the file name and number of lines changed
            file_name = file.filename
            lines_changed = file.changes

            # Check if the number of lines changed is greater than the threshold
            if lines_changed > lines_changed_threshold:
                files.append(file_name)
    
    return files

def get_modified_urls(repo_url):
    """Get the URLs of the modified files in a repository."""

    repo_name, url  = repo_url
    
    files = get_changed_lines(repo_name)
    files = [f.replace("/README.md", "") for f in files]

    urls = [url + f for f in files]

    return urls


def get_changed_urls():
    """Get the URLs of the modified files in all repositories."""

    repos_urls = [
        ("carlospolop/hacktricks", "https://book.hacktricks.xyz/"),
        ("carlospolop/hacktricks-cloud", "https://cloud.hacktricks.xyz/")
    ]

    urls = []

    for repo_url in repos_urls:
        urls += get_modified_urls(repo_url)
    
    return urls




##########################
###### SOCIAL MSGS #######
##########################


def send_telegram_message(message: str):
    ''' Send a message to the telegram group '''

    telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not telegram_bot_token:
        print("TELEGRAM_BOT_TOKEN wasn't configured in the secrets!")
        return
    
    if not telegram_chat_id:
        print("TELEGRAM_CHAT_ID wasn't configured in the secrets!")
        return

    message = message.replace(".", "\.").replace("-", "\-").replace("(", "\(").replace(")", "\)").replace("_", "").replace("[","\[").replace("]","\]").replace("{","\{").replace("}","\}").replace("=","\=")
    r = requests.get(f'https://api.telegram.org/bot{telegram_bot_token}/sendMessage?parse_mode=MarkdownV2&text={message}&chat_id={telegram_chat_id}')

    resp = r.json()
    if not resp['ok']:
        r = requests.get(f'https://api.telegram.org/bot{telegram_bot_token}/sendMessage?parse_mode=MarkdownV2&text=Error with' + message.split("\n")[0] + f'{resp["description"]}&chat_id={telegram_chat_id}')
        resp = r.json()
        if not resp['ok']:
            print("ERROR SENDING TO TELEGRAM: "+ message.split("\n")[0] + resp["description"])


"""def send_discord_message(message: str):
    ''' Send a message to the discord channel webhook '''

    discord_webhok_url = os.getenv('DISCORD_WEBHOOK_URL')

    if not discord_webhok_url:
        print("DISCORD_WEBHOOK_URL wasn't configured in the secrets!")
        return

    message = message.replace("(", "\(").replace(")", "\)").replace("_", "").replace("[","\[").replace("]","\]").replace("{","\{").replace("}","\}").replace("=","\=")
    webhook = Webhook.from_url(discord_webhok_url, adapter=RequestsWebhookAdapter())
    
    webhook.send(message)"""


##########################
######### MAIN ###########
##########################

def main():
    urls = get_changed_urls()
    
    if urls:
        print(urls)
        
        message = "📓 New content has been added to the following pages 📓\n\n"
        for url in urls:
            url_name = url.split("/")[-1]
            message += f"- [{url_name}]({url})\n"
        
        send_telegram_message(message)
        #send_discord_message(message)
    
    else:
        print("No new content added")



if __name__ == "__main__":
    main()