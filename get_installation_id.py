#!/usr/bin/env python3
"""
Quick workaround to find installation ID from GitHub repository settings
"""

import sys
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()


def extract_installation_id_from_webhook(owner: str, repo: str):
    """
    Try to get installation ID by checking the app installations page
    """
    
    # Since we can't authenticate properly to list installations,
    # we'll guide the user to find it manually from webhook history
    
    print("\n" + "="*70)
    print("GitHub App Installation ID Lookup")
    print("="*70 + "\n")
    
    print("The automatic lookup isn't working, but here's how to find it manually:\n")
    
    print("[Method 1] Via Repository Webhooks (Fastest)")
    print("-" * 70)
    print(f"1. Go to: https://github.com/{owner}/{repo}/settings/apps")
    print("2. Find your 'Multi-Agent PR Reviewer' (or similar) app")
    print("3. Click 'Configure'")
    print("4. Look at the URL or in the page - find the installation ID number")
    print("   URL format: https://github.com/apps/your-app-name/installations/ID")
    print()
    
    print("[Method 2] Via App Settings")
    print("-" * 70)
    print("1. Go to: https://github.com/settings/apps")
    print("2. Click your app name")
    print("3. Go to 'Installations' tab")
    print(f"4. Find {owner}/{repo} in the list")
    print("5. The ID is displayed or check the URL when you click 'Configure'")
    print()
    
    print("[Method 3] Via Webhook Delivery History")
    print("-" * 70)
    print("If the app has been triggered before:")
    print(f"1. Go to: https://github.com/{owner}/{repo}/settings/hooks")
    print("2. Find your GitHub App webhook")
    print("3. Click 'Recent Deliveries'")
    print("4. Open any delivery")
    print("5. In the payload JSON, find: \"installation\": { \"id\": YOUR_ID }")
    print()
    
    print("[Method 4] Check Your .env File")
    print("-" * 70)
    print("If you set GITHUB_INSTALLATION_ID in your .env file:")
    env_id = os.environ.get("GITHUB_INSTALLATION_ID")
    if env_id:
        print(f"Installation ID: {env_id}")
    else:
        print("GITHUB_INSTALLATION_ID is not set in .env")
        print("You can set it with: export GITHUB_INSTALLATION_ID=<id>")
    print()
    
    print("="*70)
    print("Once you have the installation ID, run:")
    print(f"  python batch_review_prs.py {owner} {repo} --installation-id <ID>")
    print("="*70 + "\n")


if __name__ == "__main__":
    owner = "<owner>"
    repo = "<repo>"
    
    if len(sys.argv) > 2:
        owner = sys.argv[1]
        repo = sys.argv[2]
    
    extract_installation_id_from_webhook(owner, repo)
