import asyncio
import os
import argparse
from dotenv import load_dotenv
from app.github_client import GitHubAppClient
from app.diff_builder import build_review_context
from app.graph.workflow import run_review_graph

async def main(installation_id: int, owner: str, repo: str, pr_number: int):
    load_dotenv()
    gh = GitHubAppClient.for_installation(installation_id)
    try:
        print("Building review context...")
        ctx = build_review_context(gh, owner, repo, pr_number)
        print("Running review graph...")
        res = await run_review_graph(ctx)
        print(res)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run review graph against one PR.")
    parser.add_argument("owner", help="Repository owner")
    parser.add_argument("repo", help="Repository name")
    parser.add_argument("pr_number", type=int, help="Pull request number")
    parser.add_argument(
        "--installation-id",
        type=int,
        default=int(os.environ.get("GITHUB_INSTALLATION_ID", "0")),
        help="GitHub App installation ID (or set GITHUB_INSTALLATION_ID)",
    )
    args = parser.parse_args()

    if args.installation_id <= 0:
        raise SystemExit("Missing installation ID. Pass --installation-id or set GITHUB_INSTALLATION_ID.")

    asyncio.run(main(args.installation_id, args.owner, args.repo, args.pr_number))
