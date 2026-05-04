import os
import time
import json
import argparse
import hmac
import hashlib
import jwt
import httpx
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.environ["GITHUB_APP_ID"]
KEY_PATH = os.environ["GITHUB_PRIVATE_KEY_PATH"]
WEBHOOK_SECRET = os.environ["GITHUB_WEBHOOK_SECRET"]


def main(owner: str, repo: str):
    print(f"Authenticating as GitHub App ID {APP_ID}...")
    with open(KEY_PATH, "rb") as f:
        private_key = f.read()

    now = int(time.time())
    app_jwt = jwt.encode(
        {"iat": now - 60, "exp": now + 9 * 60, "iss": APP_ID},
        private_key,
        algorithm="RS256",
    )

    client = httpx.Client(headers={
        "Authorization": f"Bearer {app_jwt}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })

    # 1. Get Installation ID
    print(f"Finding installation for {owner}/{repo}...")
    r = client.get(f"https://api.github.com/repos/{owner}/{repo}/installation")
    if r.status_code == 404:
        print(f"ERROR: GitHub App is not installed on {owner}/{repo}.")
        print("Please install it first from your GitHub App settings.")
        return
    r.raise_for_status()
    install_id = r.json()["id"]
    print(f"Found installation ID: {install_id}")

    # 2. Get Installation Access Token
    r = client.post(f"https://api.github.com/app/installations/{install_id}/access_tokens")
    r.raise_for_status()
    token = r.json()["token"]

    # 3. Fetch open PRs
    print("Fetching open pull requests...")
    inst_client = httpx.Client(headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    r = inst_client.get(f"https://api.github.com/repos/{owner}/{repo}/pulls?state=open")
    r.raise_for_status()
    prs = r.json()
    print(f"Found {len(prs)} open PR(s).")

    # 4. Trigger Webhook for each
    local_client = httpx.Client(base_url="http://127.0.0.1:8000")
    for pr in prs:
        if pr.get("draft"):
            print(f"Skipping draft PR #{pr['number']}")
            continue

        print(f"\nTriggering review for PR #{pr['number']} - {pr['title']}...")
        
        payload = {
            "action": "synchronize",  # Tricks the webhook into thinking the PR was just updated
            "pull_request": {
                "number": pr["number"],
                "head": {"sha": pr["head"]["sha"]},
                "draft": pr.get("draft", False)
            },
            "repository": {
                "name": repo,
                "owner": {"login": owner}
            },
            "installation": {"id": install_id}
        }
        
        payload_bytes = json.dumps(payload).encode("utf-8")
        signature = "sha256=" + hmac.new(WEBHOOK_SECRET.encode(), payload_bytes, hashlib.sha256).hexdigest()
        
        try:
            # Sending directly to the local server
            resp = local_client.post(
                "/webhooks/github",
                content=payload_bytes,
                headers={
                    "x-github-event": "pull_request",
                    "x-hub-signature-256": signature,
                    "content-type": "application/json"
                },
                timeout=300.0  # Reviews take a long time, don't timeout quickly
            )
            print(f"Result for PR #{pr['number']}: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"Failed to trigger PR #{pr['number']}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trigger local webhook reviews for open PRs.")
    parser.add_argument("owner", help="Repository owner")
    parser.add_argument("repo", help="Repository name")
    args = parser.parse_args()
    main(args.owner, args.repo)
