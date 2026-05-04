import os
import httpx
import hmac
import hashlib
import json
import argparse
from dotenv import load_dotenv

load_dotenv()

parser = argparse.ArgumentParser(description="Send a test PR webhook payload to local server.")
parser.add_argument("owner", help="Repository owner")
parser.add_argument("repo", help="Repository name")
parser.add_argument("pr_number", type=int, help="Pull request number")
parser.add_argument("--head-sha", default="dummy", help="Head commit SHA for payload")
parser.add_argument(
    "--installation-id",
    type=int,
    default=int(os.environ.get("GITHUB_INSTALLATION_ID", "0")),
    help="GitHub App installation ID (or set GITHUB_INSTALLATION_ID)",
)
args = parser.parse_args()

if args.installation_id <= 0:
    raise SystemExit("Missing installation ID. Pass --installation-id or set GITHUB_INSTALLATION_ID.")

secret = os.environ["GITHUB_WEBHOOK_SECRET"]
payload = {
    "action": "synchronize",
    "pull_request": {"number": args.pr_number, "head": {"sha": args.head_sha}, "draft": False},
    "repository": {"name": args.repo, "owner": {"login": args.owner}},
    "installation": {"id": args.installation_id},
}
payload_bytes = json.dumps(payload).encode("utf-8")
sig = "sha256=" + hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()

resp = httpx.post(
    "http://127.0.0.1:8000/webhooks/github",
    content=payload_bytes,
    headers={"x-github-event": "pull_request", "x-hub-signature-256": sig, "content-type": "application/json"},
)
print(resp.status_code)
print(resp.text)
