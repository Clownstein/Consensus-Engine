#!/usr/bin/env python3
"""
Utility to help find GitHub App Installation ID

This script uses the GitHub API to find the installation ID for your
Multi-Agent PR Reviewer app on a specific repository.
"""

import os
import sys
import argparse
from pathlib import Path

import httpx
import jwt
import time

from dotenv import load_dotenv

# Load .env file
load_dotenv()


def get_app_jwt() -> str:
    """Generate a JWT for GitHub App API access."""
    app_id = os.environ.get("GITHUB_APP_ID")
    pk_path = os.environ.get("GITHUB_PRIVATE_KEY_PATH", "private-key.pem")
    
    if not app_id:
        raise ValueError("GITHUB_APP_ID environment variable not set")
    
    if not Path(pk_path).exists():
        raise ValueError(f"Private key not found: {pk_path}")
    
    with open(pk_path, "rb") as f:
        private_key = f.read()
    
    now = int(time.time())
    jwt_token = jwt.encode(
        {"iat": now - 60, "exp": now + 9 * 60, "iss": app_id},
        private_key,
        algorithm="RS256",
    )
    
    return jwt_token


def find_installation_id(owner: str, repo: str, verbose: bool = False) -> int | None:
    """Find the installation ID for a repository."""
    
    jwt_token = get_app_jwt()
    
    # Get all installations for this app
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    
    # Normalize search terms
    search_owner = owner.lower()
    search_repo = repo.lower()
    
    page = 1
    total_found = 0
    
    while True:
        response = httpx.get(
            "https://api.github.com/app/installations",
            headers=headers,
            params={"per_page": 100, "page": page},
            timeout=30,
        )
        response.raise_for_status()
        
        installations = response.json()
        
        if not installations:
            break
        
        for install in installations:
            repo_info = install.get("repository")
            if repo_info:
                inst_owner = repo_info.get("owner", {}).get("login", "").lower()
                inst_repo = repo_info.get("name", "").lower()
                
                if verbose:
                    print(f"  Found: {inst_owner}/{inst_repo} (ID: {install['id']})")
                
                total_found += 1
                
                # Case-insensitive comparison
                if inst_owner == search_owner and inst_repo == search_repo:
                    if verbose:
                        print(f"  ^ MATCH!")
                    return install["id"]
        
        if len(installations) < 100:
            break
        
        page += 1
    
    if verbose:
        print(f"\n  Total installations found: {total_found}")
        if total_found == 0:
            print("  No installations found for this app")
        else:
            print(f"  But none matched {search_owner}/{search_repo}")
    
    return None


def list_all_installations() -> list[dict]:
    """List all installations of this GitHub App."""
    
    jwt_token = get_app_jwt()
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    
    installations = []
    page = 1
    
    while True:
        response = httpx.get(
            "https://api.github.com/app/installations",
            headers=headers,
            params={"per_page": 100, "page": page},
            timeout=30,
        )
        response.raise_for_status()
        
        chunk = response.json()
        
        if not chunk:
            break
        
        for install in chunk:
            repo_info = install.get("repository", {})
            if repo_info:
                installations.append({
                    "id": install["id"],
                    "owner": repo_info.get("owner", {}).get("login"),
                    "repo": repo_info.get("name"),
                    "url": repo_info.get("html_url"),
                })
        
        if len(chunk) < 100:
            break
        
        page += 1
    
    return installations


def main():
    parser = argparse.ArgumentParser(
        description="Find GitHub App installation ID for batch PR reviews"
    )
    parser.add_argument(
        "owner",
        nargs="?",
        help="Repository owner"
    )
    parser.add_argument(
        "repo",
        nargs="?",
        help="Repository name"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all installations of this GitHub App"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show detailed debug information"
    )
    
    args = parser.parse_args()
    
    # Check environment
    if not os.environ.get("GITHUB_APP_ID"):
        print("[ERROR] GITHUB_APP_ID environment variable not set")
        print("\nPlease configure your .env file first:")
        print("  1. Copy .env.example to .env")
        print("  2. Fill in your GitHub App credentials")
        sys.exit(1)
    
    pk_path = os.environ.get("GITHUB_PRIVATE_KEY_PATH", "private-key.pem")
    if not Path(pk_path).exists():
        print(f"[ERROR] Private key not found: {pk_path}")
        print("\nPlease download your GitHub App private key and save it as:")
        print(f"  {pk_path}")
        sys.exit(1)
    
    try:
        if args.list:
            print("\n" + "="*60)
            print("Installations of your GitHub App")
            print("="*60 + "\n")
            
            installations = list_all_installations()
            
            if not installations:
                print("No installations found.")
                print("\nTo install your app on a repository:")
                print("  1. Go to https://github.com/apps/your-app-name/installations")
                print("  2. Select repositories where you want to install the app")
                sys.exit(0)
            
            for install in installations:
                print(f"ID:   {install['id']}")
                print(f"Repo: {install['owner']}/{install['repo']}")
                print(f"URL:  {install['url']}")
                print()
        
        elif args.owner and args.repo:
            print(f"\nSearching for installation ID for {args.owner}/{args.repo}...\n")
            
            installation_id = find_installation_id(args.owner, args.repo, verbose=args.debug)
            
            if installation_id:
                print("="*60)
                print("[SUCCESS] Found Installation ID")
                print("="*60)
                print(f"\nInstallation ID: {installation_id}")
                print(f"Repository:     {args.owner}/{args.repo}")
                print("\nUsage:")
                print(f"\n  python batch_review_prs.py {args.owner} {args.repo} \\")
                print(f"    --installation-id {installation_id}")
                print(f"\nOr set as environment variable:")
                print(f"\n  export GITHUB_INSTALLATION_ID={installation_id}")
                print(f"  python batch_review_prs.py {args.owner} {args.repo}")
                print()
            else:
                print("[ERROR] Installation not found")
                print(f"\nThe GitHub App is not installed on {args.owner}/{args.repo}")
                print("\nTo install:")
                print("  1. Go to https://github.com/apps/your-app-name/installations")
                print("  2. Select this repository")
                print("  3. Run this script again")
                sys.exit(1)
        
        else:
            parser.print_help()
            print("\nExamples:")
            print("\n  # Find installation ID for a specific repo")
            print("  python find_installation_id.py owner repo_name")
            print("\n  # List all installations")
            print("  python find_installation_id.py --list")
    
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
