#!/usr/bin/env python3
"""
Alternative method to find GitHub App installation ID using repository access
"""

import os
import sys

def find_installation_id_via_repo_api(owner: str, repo: str) -> int | None:
    """
    Find installation ID using a personal access token or by querying the app directly.
    This is an alternative method when the JWT approach doesn't work.
    """
    
    app_id = os.environ.get("GITHUB_APP_ID")
    
    if not app_id:
        print("[ERROR] GITHUB_APP_ID not found in environment")
        return None
    
    print(f"Searching for app installations (App ID: {app_id})...")
    print()
    print("Note: To find the installation ID, you can also:")
    print(f"1. Visit: https://github.com/{owner}/{repo}/settings/installations")
    print("2. Find your app in the list")
    print("3. Click 'Configure'")
    print("4. The installation ID will be in the URL: ...installations/XXXXX")
    print()
    print("Or from your app's settings:")
    print("1. Go to: https://github.com/settings/apps")
    print("2. Click your app")
    print("3. Click 'Installations' tab")
    print("4. Find the repository and note the ID")
    
    return None


def get_installation_id_from_webhook_history(owner: str, repo: str):
    """
    Guide user to find installation ID from webhook history
    """
    print("\n" + "="*60)
    print("How to Find Your Installation ID")
    print("="*60 + "\n")
    
    print("Method 1: From Recent PR Webhook (Easiest)")
    print("-" * 40)
    print(f"1. Open a Pull Request in {owner}/{repo}")
    print("2. Go to Settings > Webhooks")
    print("3. Find your Multi-Agent PR Reviewer app")
    print("4. Click 'Recent Deliveries' tab")
    print("5. Open any delivery and check the JSON payload")
    print("6. Look for: installation.id in the payload")
    print()
    
    print("Method 2: From App Settings")
    print("-" * 40)
    print("1. Go to: https://github.com/settings/apps")
    print("2. Click your Multi-Agent PR Reviewer app")
    print("3. Click 'Installations' tab")
    print(f"4. Find {owner}/{repo} in the list")
    print("5. The installation ID is shown or in the URL")
    print()
    
    print("Method 3: Direct URL")
    print("-" * 40)
    print(f"If the app is already installed on {owner}/{repo}:")
    print(f"1. Go to: https://github.com/{owner}/{repo}/settings/apps")
    print("2. Click your app's 'Configure' button")
    print("3. The URL will show the installation ID")
    print()


if __name__ == "__main__":
    owner = "<owner>"
    repo = "<repo>"
    if len(sys.argv) > 2:
        owner = sys.argv[1]
        repo = sys.argv[2]

    get_installation_id_from_webhook_history(owner, repo)
    
    print("Once you have the installation ID, use:")
    print(f"  python batch_review_prs.py {owner} {repo} --installation-id <id>")
