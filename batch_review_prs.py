#!/usr/bin/env python3
"""
Batch PR Reviewer Script

Fetches all open PRs from a GitHub repository and runs the multi-agent review
workflow on each one, posting reviews directly to the PRs.

Usage:
    python batch_review_prs.py <owner> <repo> [--app-id <id>] [--no-post]
    
    --no-post: Run reviews but don't post to GitHub (dry run mode)
"""

import asyncio
import json
import logging
import sys
import argparse
from pathlib import Path
import time

from app.diff_builder import build_review_context
from app.github_client import GitHubAppClient
from app.graph.workflow import run_review_graph
from app.rendering.github_markdown import render_review_body

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_all_open_prs(gh: GitHubAppClient, owner: str, repo: str) -> list[dict]:
    """Fetch all open PRs from the repository."""
    logger.info(f"Fetching open PRs from {owner}/{repo}...")
    prs = []
    page = 1
    
    while True:
        try:
            r = gh.client.get(
                f"/repos/{owner}/{repo}/pulls",
                params={
                    "state": "open",
                    "per_page": 100,
                    "page": page,
                    "sort": "created",
                    "direction": "desc"
                }
            )
            r.raise_for_status()
            chunk = r.json()
            
            if not chunk:
                break
                
            prs.extend(chunk)
            logger.info(f"  Fetched {len(chunk)} PRs (page {page})")
            
            if len(chunk) < 100:
                break
                
            page += 1
            
        except Exception as e:
            logger.error(f"Error fetching PRs page {page}: {e}")
            break
    
    logger.info(f"Total open PRs found: {len(prs)}")
    return prs


async def review_single_pr(
    gh: GitHubAppClient,
    owner: str,
    repo: str,
    pr_number: int,
    pr_data: dict,
    post_to_github: bool = True
) -> dict:
    """Review a single PR and optionally post the review to GitHub."""
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Reviewing PR #{pr_number}: {pr_data['title']}")
    logger.info(f"{'='*60}")
    
    try:
        # Build review context
        logger.info("Building review context...")
        review_context = build_review_context(gh, owner, repo, pr_number)
        
        # Run the review graph
        logger.info("Running multi-agent review workflow...")
        result = await run_review_graph(review_context)
        
        # Render the review
        body = render_review_body(result)
        
        # Log the result
        status = "APPROVED" if result["approved"] else "CHANGES_REQUESTED"
        logger.info(f"Review complete: {status}")
        logger.info(f"Final summary: {result.get('final_summary', 'N/A')}")
        
        # Post to GitHub if requested
        if post_to_github:
            logger.info("Posting review to GitHub...")
            event = "APPROVE" if result["approved"] else "REQUEST_CHANGES"
            gh.create_pull_request_review(
                owner, repo, pr_number, event=event, body=body
            )
            logger.info("Review posted successfully")
        else:
            logger.info("(Dry run mode: not posting to GitHub)")
        
        return {
            "pr_number": pr_number,
            "title": pr_data['title'],
            "approved": result["approved"],
            "status": status,
            "error": None,
            "review_body_preview": body[:500] + ("..." if len(body) > 500 else "")
        }
        
    except Exception as e:
        logger.error(f"Error reviewing PR #{pr_number}: {type(e).__name__}", exc_info=True)
        return {
            "pr_number": pr_number,
            "title": pr_data['title'],
            "approved": False,
            "status": "ERROR",
            "error": f"{type(e).__name__}: internal_error",
            "error_type": type(e).__name__,
        }


async def batch_review_prs(
    owner: str,
    repo: str,
    installation_id: int,
    post_to_github: bool = True,
    max_prs: int | None = None
) -> list[dict]:
    """Review all open PRs in the repository."""
    
    logger.info(f"\nStarting batch PR review for {owner}/{repo}")
    logger.info(f"Installation ID: {installation_id}")
    logger.info(f"Post to GitHub: {post_to_github}")
    
    # Authenticate with GitHub
    gh = GitHubAppClient.for_installation(installation_id)
    
    # Fetch all open PRs
    prs = get_all_open_prs(gh, owner, repo)
    
    if max_prs:
        prs = prs[:max_prs]
        logger.info(f"Limited to first {max_prs} PRs")
    
    if not prs:
        logger.info("No open PRs found")
        return []
    
    # Review each PR
    results = []
    for i, pr in enumerate(prs, 1):
        logger.info(f"\n[{i}/{len(prs)}] Processing PR #{pr['number']}")
        
        result = await review_single_pr(
            gh, owner, repo, pr['number'], pr, post_to_github
        )
        results.append(result)
        
        # Add delay between reviews to avoid rate limiting
        if i < len(prs):
            delay = 2
            logger.info(f"Waiting {delay}s before next PR...")
            await asyncio.sleep(delay)
    
    return results


def print_summary(results: list[dict]) -> None:
    """Print a summary of all reviews."""
    
    logger.info(f"\n{'='*60}")
    logger.info("BATCH REVIEW SUMMARY")
    logger.info(f"{'='*60}")
    
    approved_count = sum(1 for r in results if r["approved"])
    error_count = sum(1 for r in results if r["status"] == "ERROR")
    
    logger.info(f"Total PRs reviewed: {len(results)}")
    logger.info(f"  Approved: {approved_count}")
    logger.info(f"  Changes requested: {len(results) - approved_count - error_count}")
    logger.info(f"  Errors: {error_count}")
    
    if error_count > 0:
        logger.info("\nErrors encountered:")
        for r in results:
            if r["status"] == "ERROR":
                logger.info(f"  PR #{r['pr_number']}: {r['error']}")
    
    # Save detailed results to file
    results_file = Path("batch_review_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"\nDetailed results saved to {results_file}")


async def main():
    parser = argparse.ArgumentParser(
        description="Batch review all open PRs in a GitHub repository"
    )
    parser.add_argument("owner", help="Repository owner")
    parser.add_argument("repo", help="Repository name")
    parser.add_argument(
        "--installation-id",
        type=int,
        help="GitHub App installation ID (defaults to env var GITHUB_INSTALLATION_ID)"
    )
    parser.add_argument(
        "--no-post",
        action="store_true",
        help="Run reviews but don't post to GitHub (dry run mode)"
    )
    parser.add_argument(
        "--max-prs",
        type=int,
        help="Limit to N PRs for testing"
    )
    
    args = parser.parse_args()
    
    # Get installation ID
    import os
    installation_id = args.installation_id
    if not installation_id:
        installation_id = os.environ.get("GITHUB_INSTALLATION_ID")
        if not installation_id:
            logger.error(
                "Installation ID not provided and GITHUB_INSTALLATION_ID env var not set"
            )
            sys.exit(1)
        installation_id = int(installation_id)
    
    # Run batch review
    results = await batch_review_prs(
        args.owner,
        args.repo,
        installation_id,
        post_to_github=not args.no_post,
        max_prs=args.max_prs
    )
    
    # Print summary
    print_summary(results)


if __name__ == "__main__":
    asyncio.run(main())
