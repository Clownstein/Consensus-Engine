#!/usr/bin/env python3
"""
Helper script to find GitHub App installation ID and validate setup
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env file
load_dotenv()

def check_env_setup():
    """Verify all required environment variables are configured."""
    required_vars = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY", 
        "GEMINI_API_KEY",
        "GITHUB_APP_ID",
        "GITHUB_PRIVATE_KEY_PATH",
        "GITHUB_WEBHOOK_SECRET",
    ]
    
    optional_vars = [
        "GITHUB_INSTALLATION_ID",
    ]
    
    print("Checking environment setup...\n")
    
    missing = []
    for var in required_vars:
        if var in os.environ:
            print(f"[OK] {var} is set")
        else:
            print(f"[X]  {var} is NOT set")
            missing.append(var)
    
    print("\nOptional:")
    for var in optional_vars:
        if var in os.environ:
            print(f"[OK] {var} is set")
        else:
            print(f"    {var} is not set (can be passed as --installation-id)")
    
    if missing:
        print(f"\n[ERROR] Missing required environment variables: {', '.join(missing)}")
        print("\nTo fix:")
        print("1. Copy .env.example to .env")
        print("2. Fill in the required API keys and GitHub App credentials")
        print("3. Ensure private-key.pem exists in the project root")
        return False
    
    # Check private key file
    pk_path = os.environ.get("GITHUB_PRIVATE_KEY_PATH", "private-key.pem")
    if Path(pk_path).exists():
        print(f"\n[OK] Private key file exists: {pk_path}")
    else:
        print(f"\n[X]  Private key file NOT found: {pk_path}")
        return False
    
    print("\n[SUCCESS] Environment setup looks good!")
    return True


def main():
    print("Multi-Agent PR Reviewer - Setup Verification\n")
    print("=" * 60)
    
    if not check_env_setup():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("\nTo start batch reviewing PRs:\n")
    print("1. Find your GitHub App installation ID:")
    print("   - Go to: https://github.com/settings/apps")
    print("   - Click on your 'Multi-Agent PR Reviewer' app")
    print("   - Go to 'Installations' tab")
    print("   - The ID is in the URL after /installations/")
    print("   - Or set GITHUB_INSTALLATION_ID environment variable\n")
    
    print("2. Run the batch reviewer:")
    print("   python batch_review_prs.py <owner> <repo> --installation-id <id>\n")
    
    print("3. For a dry run (don't post to GitHub):")
    print("   python batch_review_prs.py <owner> <repo> --installation-id <id> --no-post\n")
    
    print("4. To limit to first N PRs:")
    print("   python batch_review_prs.py <owner> <repo> --installation-id <id> --max-prs 3\n")
    
    print("See BATCH_REVIEW.md for complete documentation.")


if __name__ == "__main__":
    main()
