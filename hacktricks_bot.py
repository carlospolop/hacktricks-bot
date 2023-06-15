import os
import time
import github
import datetime
import requests
import tweepy
import pyshorteners


from discord import Webhook, RequestsWebhookAdapter



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

    # Set the time range for commits to check (15 days in seconds)
    time_range = 15 * 24 * 60 * 60

    # Set the current time
    current_time = int(time.time())

    # Set the starting time for commits to check
    start_time = datetime.datetime.fromtimestamp(current_time - time_range)

    # Get the list of commits within the specified time range
    commits = repo.get_commits(since=start_time)

    file_changes = {}
    # Loop through the list of commits
    for commit in commits:
        for file in commit.files:
            # Store the number of lines each file changed
            if file.changes > lines_changed_threshold:
                file_changes[file.filename] = file_changes.get(file.filename, 0) + file.changes

    # Sort the files by the number of lines changed
    sorted_files = sorted(file_changes.items(), key=lambda x: x[1], reverse=True)

    # Get the fine names of the files changed
    files = [file_name for file_name, _ in sorted_files]
    
    return files

def get_modified_urls(repo_url):
    """Get the URLs of the modified files in a repository."""

    repo_name, url  = repo_url
    
    files = get_changed_lines(repo_name)
    files = [f.replace("/README.md", "") for f in files]
    files = [f[:-3] for f in files if f.endswith(".md")]

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
        else:
            print("Sent to telegram")


def send_discord_message(message: str):
    ''' Send a message to the discord channel webhook '''

    discord_webhok_url = os.getenv('DISCORD_WEBHOOK_URL')

    if not discord_webhok_url:
        print("DISCORD_WEBHOOK_URL wasn't configured in the secrets!")
        return

    message = message.replace("(", "\(").replace(")", "\)").replace("_", "").replace("[","\[").replace("]","\]").replace("{","\{").replace("}","\}").replace("=","\=")
    webhook = Webhook.from_url(discord_webhok_url, adapter=RequestsWebhookAdapter())
    
    webhook.send(message)
    print("Sent to discord")


def send_twitter_message(message: str):
    """ Send a message to the twitter account """

    twitter_api_key = os.getenv('TWITTER_API_KEY')
    twitter_api_secret_key = os.getenv('TWITTER_API_SECRET_KEY')
    twitter_access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    twitter_access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

    if not twitter_api_key:
        print("TWITTER_API_KEY wasn't configured in the secrets!")
        return
    
    if not twitter_api_secret_key:
        print("TWITTER_API_SECRET_KEY wasn't configured in the secrets!")
        return

    if not twitter_access_token:
        print("TWITTER_ACCESS_TOKEN wasn't configured in the secrets!")
        return
    
    if not twitter_access_token_secret:
        print("TWITTER_ACCESS_TOKEN_SECRET wasn't configured in the secrets!")
        return

    client = tweepy.Client(
        consumer_key=twitter_api_key,
        consumer_secret=twitter_api_secret_key,
        access_token=twitter_access_token,
        access_token_secret=twitter_access_token_secret
    )

    client.create_tweet(text=message)

    print("Sent to twitter")
        

##########################
######### MAIN ###########
##########################

def main():
    urls = list(set(get_changed_urls()))
    
    if urls:
        print(urls)
        
        s = pyshorteners.Shortener()

        # To use a "!", telegram needs it escaped...
        message = "📓 Top 5 modified HackTricks pages in 2 weeks 📓\n\n"
        
        for url in urls[:5]:
            s_url  = s.tinyurl.short(url)
            message += f"- {s_url}\n"

        message += "\n#hacktricks #hacking"

        print(f"Message: {message}")
        
        send_telegram_message(message.replace("#", "\\#"))
        #send_discord_message(message)
        #send_twitter_message(message)
    
    else:
        print("No new content added")



if __name__ == "__main__":
    main()
