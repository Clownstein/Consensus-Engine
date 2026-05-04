#!/usr/bin/env python3
"""
Enhanced Batch PR Reviewer with API Capture & Confidence Tracking

Extends batch_review_prs.py with:
- API request/response capture for fine-tuning datasets
- Confidence score tracking and reporting
- Fine-tuning dataset generation (JSONL format)
"""

import asyncio
import json
import logging
import sys
import argparse
from pathlib import Path
from datetime import datetime

from app.diff_builder import build_review_context
from app.github_client import GitHubAppClient
from app.graph.workflow import run_review_graph
from app.rendering.github_markdown import render_review_body

from api_capture import init_api_capture
from confidence_tracker import ConfidenceTracker, extract_confidence_from_review, format_confidence_summary

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedBatchReviewer:
    """Enhanced batch reviewer with capture and tracking."""
    
    def __init__(self, post_to_github: bool = True, capture_api: bool = True):
        self.post_to_github = post_to_github
        self.capture_api = capture_api
        self.confidence_tracker = ConfidenceTracker()
        
        if capture_api:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.api_capture = init_api_capture(f"api_interactions_{timestamp}.jsonl")
            
            # Set the capture instance on all agents
            from app.providers.openai_agent import set_api_capture as set_openai_capture
            from app.providers.anthropic_agent import set_api_capture as set_anthropic_capture
            from app.providers.gemini_agent import set_api_capture as set_gemini_capture
            
            set_openai_capture(self.api_capture)
            set_anthropic_capture(self.api_capture)
            set_gemini_capture(self.api_capture)
        else:
            self.api_capture = None
    
    def track_review_confidence(self, review_result: dict):
        """Track confidence scores from a review result."""
        reviews = review_result.get("reviews", [])
        
        for review in reviews:
            agent_name, verdict, confidence, correct, secure, working = extract_confidence_from_review(review)
            self.confidence_tracker.add_score(
                agent_name, verdict, confidence, correct, secure, working
            )
    
    async def review_single_pr(
        self,
        gh: GitHubAppClient,
        owner: str,
        repo: str,
        pr_number: int,
        pr_data: dict,
    ) -> dict:
        """Review a single PR with enhanced tracking."""
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Reviewing PR #{pr_number}: {pr_data['title']}")
        logger.info(f"{'='*60}")
        
        try:
            logger.info("Building review context...")
            review_context = build_review_context(gh, owner, repo, pr_number)
            
            logger.info("Running multi-agent review workflow...")
            result = await run_review_graph(review_context)
            
            # Track confidence scores
            self.track_review_confidence(result)
            
            body = render_review_body(result)
            
            status = "APPROVED" if result["approved"] else "CHANGES_REQUESTED"
            logger.info(f"Review complete: {status}")
            logger.info(f"Final summary: {result.get('final_summary', 'N/A')}")
            
            # Extract confidence for logging
            avg_confidence = sum(r.get("confidence", 0) for r in result.get("reviews", [])) / len(result.get("reviews", [])) if result.get("reviews") else 0
            logger.info(f"Average Confidence: {avg_confidence:.1%}")
            
            if self.post_to_github:
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
                "confidence": avg_confidence,
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
                "confidence": 0,
                "error": f"{type(e).__name__}: internal_error",
                "error_type": type(e).__name__,
            }
    
    async def batch_review_prs(
        self,
        owner: str,
        repo: str,
        installation_id: int,
        max_prs: int | None = None
    ) -> list[dict]:
        """Review all open PRs with enhanced features."""
        
        logger.info(f"\nStarting enhanced batch PR review for {owner}/{repo}")
        logger.info(f"Installation ID: {installation_id}")
        logger.info(f"Post to GitHub: {self.post_to_github}")
        logger.info(f"Capturing API interactions: {self.capture_api}")
        
        gh = GitHubAppClient.for_installation(installation_id)
        
        # Fetch all open PRs
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
            
            result = await self.review_single_pr(
                gh, owner, repo, pr['number'], pr
            )
            results.append(result)
            
            if i < len(prs):
                delay = 2
                logger.info(f"Waiting {delay}s before next PR...")
                await asyncio.sleep(delay)
        
        return results
    
    def print_summary(self, results: list[dict]):
        """Print comprehensive summary with confidence metrics."""
        
        logger.info(f"\n{'='*60}")
        logger.info("BATCH REVIEW SUMMARY")
        logger.info(f"{'='*60}")
        
        approved_count = sum(1 for r in results if r["approved"])
        error_count = sum(1 for r in results if r["status"] == "ERROR")
        
        logger.info(f"Total PRs reviewed: {len(results)}")
        logger.info(f"  Approved: {approved_count}")
        logger.info(f"  Changes requested: {len(results) - approved_count - error_count}")
        logger.info(f"  Errors: {error_count}")
        
        # Confidence metrics
        valid_results = [r for r in results if r.get("confidence", 0) > 0]
        if valid_results:
            avg_confidence = sum(r["confidence"] for r in valid_results) / len(valid_results)
            logger.info(f"\nConfidence Metrics:")
            logger.info(f"  Average Confidence: {avg_confidence:.1%}")
            logger.info(f"  Min Confidence: {min(r['confidence'] for r in valid_results):.1%}")
            logger.info(f"  Max Confidence: {max(r['confidence'] for r in valid_results):.1%}")
        
        if error_count > 0:
            logger.info("\nErrors encountered:")
            for r in results:
                if r["status"] == "ERROR":
                    logger.info(f"  PR #{r['pr_number']}: {r['error']}")
        
        # Print confidence summary
        logger.info(format_confidence_summary(self.confidence_tracker))
        
        # Save results
        results_file = Path("batch_review_results_enhanced.json")
        enhanced_data = {
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "confidence_summary": self.confidence_tracker.get_summary(),
        }
        
        with open(results_file, "w") as f:
            json.dump(enhanced_data, f, indent=2)
        logger.info(f"Detailed results saved to {results_file}")
        
        # Save API capture data if enabled
        if self.api_capture:
            self.api_capture.save_interactions()
            fine_tuning_file = self.api_capture.generate_fine_tuning_dataset("fine_tuning_dataset.jsonl")
            logger.info(f"Fine-tuning dataset saved to {fine_tuning_file}")


async def main():
    parser = argparse.ArgumentParser(
        description="Enhanced batch review all open PRs in a GitHub repository"
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
    parser.add_argument(
        "--no-capture",
        action="store_true",
        help="Don't capture API interactions for fine-tuning"
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
    
    # Run enhanced batch review
    reviewer = EnhancedBatchReviewer(
        post_to_github=not args.no_post,
        capture_api=not args.no_capture
    )
    
    results = await reviewer.batch_review_prs(
        args.owner,
        args.repo,
        installation_id,
        max_prs=args.max_prs
    )
    
    # Print summary
    reviewer.print_summary(results)


if __name__ == "__main__":
    asyncio.run(main())
