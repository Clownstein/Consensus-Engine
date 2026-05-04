#!/usr/bin/env python3
"""
Extract installation ID from GitHub webhook payload JSON
"""

import argparse
import json


def extract_id_from_payload(owner: str, repo: str):
    """
    Prompts user to paste a GitHub webhook payload and extracts the installation ID
    """
    print("\n" + "="*70)
    print("Extract Installation ID from Webhook Payload")
    print("="*70 + "\n")
    
    print("Steps to get the webhook payload:")
    print(f"1. Go to: https://github.com/{owner}/{repo}/settings/hooks")
    print("2. Find your GitHub App webhook (should say 'GitHub App')")
    print("3. Click 'Recent Deliveries' tab")
    print("4. Click on any delivery (green check mark)")
    print("5. Click 'Request' tab")
    print("6. Copy the entire JSON payload")
    print("7. Paste it below and press Enter twice when done\n")
    
    print("Paste the JSON payload here (Press Enter twice when done):")
    print("-" * 70)
    
    lines = []
    empty_count = 0
    
    try:
        while True:
            line = input()
            if line == "":
                empty_count += 1
                if empty_count >= 2:
                    break
            else:
                empty_count = 0
                lines.append(line)
    except EOFError:
        pass
    
    if not lines:
        print("\n[ERROR] No payload provided")
        return None
    
    payload_str = "\n".join(lines)
    
    try:
        payload = json.loads(payload_str)
        installation_id = payload.get("installation", {}).get("id")
        
        if installation_id:
            print("\n" + "="*70)
            print("SUCCESS!")
            print("="*70)
            print(f"\nInstallation ID: {installation_id}\n")
            print("Use this command:")
            print(f"  python batch_review_prs.py {owner} {repo} --installation-id {installation_id}\n")
            print("Or set as environment variable:")
            print(f"  export GITHUB_INSTALLATION_ID={installation_id}\n")
            return installation_id
        else:
            print("\n[ERROR] Could not find 'installation.id' in payload")
            print("Make sure you copied the correct payload")
            return None
    
    except json.JSONDecodeError as e:
        print(f"\n[ERROR] Invalid JSON: {e}")
        print("Make sure you copied the complete JSON payload")
        return None


def show_quick_guide(owner: str, repo: str):
    """
    Show the quickest way to find the ID
    """
    print("\n" + "="*70)
    print("FASTEST WAY TO FIND INSTALLATION ID")
    print("="*70 + "\n")
    
    print("Option 1: Direct from App Settings (Easiest)")
    print("-" * 70)
    print(f"1. Go to: https://github.com/{owner}/{repo}/settings/apps")
    print("2. Find 'Alberts Code Reviewer'")
    print("3. Look at the URL or page - you should see the ID")
    print("   (URL format: https://github.com/apps/your-app/installations/ID)")
    print()
    
    print("Option 2: From Webhook History (Most Reliable)")
    print("-" * 70)
    print(f"1. Go to: https://github.com/{owner}/{repo}/settings/hooks")
    print("2. Find your app's webhook")
    print("3. Click 'Recent Deliveries'")
    print("4. Click a delivery to see the payload")
    print("5. Look for: \"installation\": { \"id\": YOUR_ID }")
    print()
    
    print("Option 3: Use Interactive Parser Below")
    print("-" * 70)
    print("If you're comfortable with the above, paste the webhook JSON")
    print("and this script will extract the ID for you.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract GitHub App installation ID from webhook payload JSON."
    )
    parser.add_argument("owner", nargs="?", help="Repository owner")
    parser.add_argument("repo", nargs="?", help="Repository name")
    args = parser.parse_args()

    owner = args.owner or "<owner>"
    repo = args.repo or "<repo>"

    show_quick_guide(owner, repo)
    
    response = input("Do you want to paste a webhook payload? (y/n): ").strip().lower()
    
    if response == 'y':
        extract_id_from_payload(owner, repo)
    else:
        print("\nGo find your installation ID using one of the methods above.")
        print(f"Then run: python batch_review_prs.py {owner} {repo} --installation-id <ID>")
