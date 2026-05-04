#!/usr/bin/env python3
"""
Enhanced Batch PR Reviewer with API Capture and Confidence Tracking

Extends the base batch reviewer to:
- Capture all API requests/responses for fine-tuning
- Track confidence scores
- Generate fine-tuning datasets
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import List
from dataclasses import dataclass

from api_capture import init_api_capture

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceScore:
    """Tracks confidence metrics for a review."""
    agent_name: str
    verdict: str
    confidence: float
    correct: bool
    secure: bool
    working: bool


class ConfidenceTracker:
    """Tracks confidence scores across all reviews."""
    
    def __init__(self):
        self.scores: List[ConfidenceScore] = []
    
    def add_score(self, agent_name: str, verdict: str, confidence: float, 
                  correct: bool, secure: bool, working: bool):
        """Add a confidence score."""
        score = ConfidenceScore(
            agent_name=agent_name,
            verdict=verdict,
            confidence=confidence,
            correct=correct,
            secure=secure,
            working=working
        )
        self.scores.append(score)
    
    def get_summary(self) -> dict:
        """Get summary statistics."""
        if not self.scores:
            return {}
        
        total_confidence = sum(s.confidence for s in self.scores)
        avg_confidence = total_confidence / len(self.scores)
        
        approvals = sum(1 for s in self.scores if s.verdict == "approve")
        approval_rate = approvals / len(self.scores) * 100
        
        correctness = sum(1 for s in self.scores if s.correct) / len(self.scores) * 100
        security = sum(1 for s in self.scores if s.secure) / len(self.scores) * 100
        working = sum(1 for s in self.scores if s.working) / len(self.scores) * 100
        
        return {
            "total_reviews": len(self.scores),
            "average_confidence": round(avg_confidence, 2),
            "approval_rate": round(approval_rate, 2),
            "correctness_rate": round(correctness, 2),
            "security_rate": round(security, 2),
            "working_rate": round(working, 2),
            "by_agent": self._agent_breakdown(),
        }
    
    def _agent_breakdown(self) -> dict:
        """Get breakdown by agent."""
        breakdown = {}
        
        for score in self.scores:
            if score.agent_name not in breakdown:
                breakdown[score.agent_name] = []
            breakdown[score.agent_name].append(score)
        
        result = {}
        for agent, scores in breakdown.items():
            avg_conf = sum(s.confidence for s in scores) / len(scores)
            approvals = sum(1 for s in scores if s.verdict == "approve")
            result[agent] = {
                "count": len(scores),
                "average_confidence": round(avg_conf, 2),
                "approval_count": approvals,
                "approval_rate": round(approvals / len(scores) * 100, 2),
            }
        
        return result


def format_confidence_summary(tracker: ConfidenceTracker) -> str:
    """Format confidence summary for display."""
    summary = tracker.get_summary()
    
    if not summary:
        return "No confidence data available"
    
    lines = []
    lines.append("\n" + "="*70)
    lines.append("CONFIDENCE & QUALITY METRICS")
    lines.append("="*70)
    lines.append(f"\nOverall Metrics:")
    lines.append(f"  Total Reviews: {summary['total_reviews']}")
    lines.append(f"  Average Confidence: {summary['average_confidence']}%")
    lines.append(f"  Approval Rate: {summary['approval_rate']}%")
    lines.append(f"\nCode Quality:")
    lines.append(f"  Correctness: {summary['correctness_rate']}%")
    lines.append(f"  Security: {summary['security_rate']}%")
    lines.append(f"  Working/Tested: {summary['working_rate']}%")
    
    if summary['by_agent']:
        lines.append(f"\nBy Agent:")
        for agent, metrics in summary['by_agent'].items():
            lines.append(f"  {agent}:")
            lines.append(f"    Avg Confidence: {metrics['average_confidence']}%")
            lines.append(f"    Approved: {metrics['approval_count']}/{metrics['count']}")
            lines.append(f"    Approval Rate: {metrics['approval_rate']}%")
    
    lines.append("="*70 + "\n")
    return "\n".join(lines)


def extract_confidence_from_review(review: dict) -> tuple:
    """Extract confidence metrics from a review."""
    return (
        review.get("agent_name", "Unknown"),
        review.get("verdict", "unknown"),
        review.get("confidence", 0.0),
        review.get("correct", False),
        review.get("secure", False),
        review.get("working", False),
    )


def enhance_results_with_confidence(results: List[dict], tracker: ConfidenceTracker) -> dict:
    """Enhance batch results with confidence summary."""
    return {
        "batch_results": results,
        "confidence_summary": tracker.get_summary(),
        "formatted_summary": format_confidence_summary(tracker),
    }


def save_enhanced_results(results: dict, output_file: str = "batch_review_results_enhanced.json"):
    """Save enhanced results with confidence metrics."""
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved enhanced results to {output_file}")


if __name__ == "__main__":
    # Example usage
    tracker = ConfidenceTracker()
    
    # Simulate adding scores
    tracker.add_score("OpenAI Architect", "approve", 0.95, True, True, True)
    tracker.add_score("Anthropic Security", "approve", 0.92, True, True, True)
    tracker.add_score("Gemini Runtime", "needs_changes", 0.85, True, False, False)
    
    print(format_confidence_summary(tracker))
