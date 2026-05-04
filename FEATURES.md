# Multi-Agent PR Reviewer - Features & Reference

## Core Features

### 1. Multi-Agent Debate System

Three specialized AI agents collaborate to review code:

**OpenAI Architect (GPT-5.4-mini)**
- Correctness and logical soundness
- Design patterns and maintainability
- Code clarity and readability
- Backward compatibility concerns
- API design best practices

**Anthropic Security Auditor (Claude Sonnet)**
- Vulnerability detection
- Threat modeling
- Authentication/authorization issues
- Input validation and sanitization
- Data protection compliance

**Gemini Runtime Tester (Gemini 3.1 Flash)**
- Test coverage analysis
- Performance implications
- Database migration safety
- Deployment readiness
- Environment-specific issues

### 2. Consensus Mechanism

**Voting Rules:**
- All 3 agents must approve to merge
- No critical/high severity issues allowed
- Configurable confidence threshold (default: 80%)
- Up to 3 rebuttal rounds if agents disagree

**Decision Matrix:**
```
All Approve        → ✅ APPROVED (merge ready)
Any Disapprove     → ❌ REQUEST_CHANGES (rework needed)
Debate Continues   → Agents provide rebuttals (up to 3 rounds)
```

### 3. Confidence Scoring

Each agent provides confidence metrics (0-100%):

- **Correctness** (OpenAI) - Design soundness
- **Security** (Anthropic) - Vulnerability-free
- **Tests** (Gemini) - Coverage and performance

Aggregate metrics:
- **Average**: Mean of all agent confidence scores
- **Per-category**: Clarity on specific concerns

**Example Output:**
```json
{
  "confidence_scores": {
    "average": 92.3,
    "by_agent": {
      "openai_architect": 95.0,
      "anthropic_security": 88.0,
      "gemini_runtime": 92.0
    }
  }
}
```

### 4. API Request & Response Capture

**What Gets Captured:**
- All LLM API calls (requests and responses)
- Model, tokens, latency
- Complete prompt and completion
- Tool calls and reasoning steps

**Files Generated:**
- `api_interactions_*.jsonl` - Raw request/response pairs
- `api_capture_*.log` - Human-readable API log

**Example Interaction:**
```json
{
  "request_id": "req_001",
  "timestamp": "2024-05-03T23:50:00Z",
  "provider": "openai",
  "model": "gpt-5.4-mini",
  "system_prompt": "You are a code review architect...",
  "user_message": "Review this PR...",
  "temperature": 0.7,
  "max_tokens": 2000,
  "response": "The code looks correct...",
  "tokens_used": {"prompt": 1250, "completion": 850},
  "latency_ms": 3421
}
```

### 5. Fine-Tuning Dataset Generation

**What Gets Generated:**
- `fine_tuning_dataset.jsonl` - Training data in OpenAI format
- Paired request/response samples
- All agent perspectives (architect, security, tester)

**Format (OpenAI Fine-tuning):**
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a code review architect..."
    },
    {
      "role": "user",
      "content": "Review this PR:\n<diff>"
    },
    {
      "role": "assistant",
      "content": "The code looks correct..."
    }
  ]
}
```

**Use Cases:**
- Fine-tune open-source models (Llama, Mistral, etc.)
- Train domain-specific code reviewers
- Improve review consistency
- Reduce API costs with smaller fine-tuned models

### 6. GitHub Integration

**Webhook Events Handled:**
- `pull_request.opened` - New PR submitted
- `pull_request.synchronize` - Commits pushed
- `pull_request.reopened` - PR reopened

**Check Run Status:**
- Creates GitHub Check with detailed output
- Real-time status updates
- Links to full review results

**PR Review Comments:**
- Posts formatted markdown review
- Includes verdict and confidence
- Lists specific issues per agent
- Structured rebuttals if agents disagree

### 7. Batch Review Mode

Review multiple PRs programmatically with confidence tracking and dataset generation.

**Command:**
```bash
python batch_review_enhanced.py owner/repo \
  --installation-id ID \
  [--no-post] [--max-prs N] [--no-capture]
```

**Options:**
- `--installation-id` - GitHub App installation ID
- `--no-post` - Dry run (no GitHub updates)
- `--max-prs N` - Limit to N PRs (for testing)
- `--no-capture` - Skip API capture (faster)

**Output:**
```
Batch Review Results:
├── Reviewed: 40/40 PRs
├── Approved: 32 (80%)
├── Requested Changes: 8 (20%)
├── Average Confidence: 87.3%
└── Total Time: 28 minutes

Generated Files:
├── batch_review_results_enhanced.json
├── api_interactions_*.jsonl
├── api_capture_*.log
└── fine_tuning_dataset.jsonl
```

---

## Configuration Reference

### Environment Variables

```env
# LLM API Keys
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIzaSy...

# Models
OPENAI_MODEL=gpt-4o                           # Default: gpt-4o
ANTHROPIC_MODEL=claude-sonnet-4-6             # Default: claude-sonnet-4-6
GEMINI_MODEL=gemini-3.1-flash-lite-preview   # Default: gemini-3.1-flash-lite-preview

# GitHub App
GITHUB_APP_ID=3592372
GITHUB_PRIVATE_KEY_PATH=./private-key.pem
GITHUB_WEBHOOK_SECRET=your-secret-here
GITHUB_INSTALLATION_ID=<installation_id>      # Optional, can pass as CLI arg

# Review Configuration
MAX_DEBATE_ROUNDS=3                           # Max rebuttal rounds (default: 3)
MIN_CONFIDENCE_TO_APPROVE=0.80                # Minimum confidence threshold (default: 0.80)

# Optional
LOG_LEVEL=INFO
DEBUG=false
```

### Review Schema

Each agent returns JSON with this structure:

```json
{
  "verdict": "APPROVED or REQUEST_CHANGES",
  "confidence": 92.5,
  "issues": [
    {
      "severity": "HIGH or MEDIUM or LOW",
      "category": "security or correctness or performance or tests",
      "title": "Issue title",
      "description": "Detailed explanation",
      "location": "filename:line_number",
      "suggestion": "How to fix"
    }
  ],
  "summary": "Brief summary of review",
  "positives": ["What went well"],
  "rebuttal": "Response to other agents (if applicable)"
}
```

---

## API Architecture

### Request Flow

```
GitHub PR Event
    ↓
FastAPI Webhook Handler
    ↓
GitHub Context Builder (fetch PR metadata, diffs)
    ↓
LangGraph Workflow
    ├─→ OpenAI Architect Agent
    ├─→ Anthropic Security Agent
    └─→ Gemini Runtime Agent
    ↓
Consensus Evaluator
    ├─→ All approved? → Return APPROVED
    └─→ Disagreement? → Start debate rounds (max 3)
    ↓
API Capture & Logging
    ├─→ Save interactions to JSONL
    └─→ Generate confidence metrics
    ↓
GitHub Feedback
    ├─→ Create/update Check Run
    ├─→ Post PR Review
    └─→ Set approval status
```

### LangGraph Workflow

**Nodes:**
- `initial_review` - All agents review in parallel
- `evaluate_consensus` - Check if consensus reached
- `start_debate` - Begin rebuttal rounds
- `debate_round` - Each agent provides rebuttal
- `finalize_review` - Compile final verdict

**Edges:**
```
initial_review
    ↓
evaluate_consensus
    ├─→ consensus_reached → finalize_review ✅
    └─→ not_reached (< 3 rounds) → start_debate → debate_round → evaluate_consensus
    └─→ max_rounds_reached → finalize_review (all agents must approve; otherwise request changes)
```

---

## Performance Characteristics

### Time Complexity

Per PR review:
- **API calls**: 3 initial + up to 6 rebuttals = 3-9 calls
- **Time per call**: 5-15 seconds
- **Total time**: 30-60 seconds per PR

Factors affecting speed:
- PR size (larger = slower)
- Code complexity
- API provider latency
- Debate rounds (increases time)

### Cost Characteristics

Typical tokens per review:
- Prompt tokens: 1,500-3,000 (depends on diff size)
- Completion tokens: 300-800 per agent
- Total: ~5,000-10,000 tokens

Cost per PR:
- OpenAI GPT-4o: $0.02-0.10 (input/output rates)
- Anthropic Claude: $0.03-0.08
- Google Gemini: $0.01-0.05
- **Average: $0.10-0.30 per PR**

For 40 PRs: approximately **$5-15** total

### Scalability

**Batch Review Performance:**
```
10 PRs  →  5-10 minutes    →  $1-3
20 PRs  →  10-20 minutes   →  $3-6
40 PRs  →  20-40 minutes   →  $5-15
100 PRs →  50-100 minutes  →  $15-30
```

**Optimization Tips:**
- Use `--no-capture` to skip logging (2x faster)
- Review in batches (avoid hitting rate limits)
- Schedule during off-peak hours
- Use smaller models for initial screening

---

## Data Formats

### Batch Review Results JSON

```json
{
  "summary": {
    "total_prs": 40,
    "approved": 32,
    "requested_changes": 8,
    "average_confidence": 87.3,
    "total_time_seconds": 1680
  },
  "reviews": [
    {
      "pr_number": 123,
      "title": "Add user authentication",
      "verdict": "APPROVED",
      "confidence_scores": {
        "average": 92.3,
        "by_agent": {
          "openai_architect": 95.0,
          "anthropic_security": 88.0,
          "gemini_runtime": 92.0
        }
      },
      "agent_reviews": {
        "openai_architect": {...},
        "anthropic_security": {...},
        "gemini_runtime": {...}
      }
    }
  ]
}
```

### API Interactions JSONL

```jsonl
{"request_id":"req_001","timestamp":"...","provider":"openai","model":"gpt-4o","system_prompt":"...","user_message":"...","temperature":0.7,"max_tokens":2000}
{"request_id":"req_001","timestamp":"...","provider":"openai","status":200,"response":"...","tokens_used":{"prompt":1250,"completion":850},"latency_ms":3421}
```

### Fine-Tuning Dataset JSONL

```jsonl
{"messages":[{"role":"system","content":"You are a code review architect..."},{"role":"user","content":"Review this PR:\n..."},{"role":"assistant","content":"..."}]}
{"messages":[{"role":"system","content":"You are a security auditor..."},{"role":"user","content":"Review this PR:\n..."},{"role":"assistant","content":"..."}]}
```

---

## Advanced Usage

### Custom Models

Edit `.env` to use different models:

```env
# Use latest models
OPENAI_MODEL=gpt-5.5-medium
ANTHROPIC_MODEL=claude-opus-4-7-thinking-xhigh
GEMINI_MODEL=gemini-pro

# Or use specific versions
OPENAI_MODEL=gpt-5.4-mini
ANTHROPIC_MODEL=claude-3-opus-20240229
```

### Fine-Tuning Workflow

1. Generate dataset:
   ```bash
   python batch_review_enhanced.py owner repo --installation-id ID
   ```

2. Fine-tune model (example with OpenAI):
   ```bash
   openai api fine_tunes.create \
     -t fine_tuning_dataset.jsonl \
     -m gpt-5.4-mini
   ```

3. Use fine-tuned model:
   ```env
   OPENAI_MODEL=ft-ABCxyz123
   ```

### Webhook Setup (Production)

For continuous webhook reviews:

1. Deploy FastAPI app (Heroku, Railway, AWS Lambda)
2. Set webhook URL in GitHub App settings
3. App automatically reviews all new/updated PRs
4. No batch script needed for ongoing reviews

---

## Files Overview

### Core Application
- `app/main.py` - FastAPI webhook server
- `app/graph/workflow.py` - LangGraph workflow
- `app/github_client.py` - GitHub API client
- `app/diff_builder.py` - PR context builder
- `app/schemas.py` - JSON schema definitions

### Providers (AI Agents)
- `app/providers/openai_agent.py` - GPT-4o architect
- `app/providers/anthropic_agent.py` - Claude security auditor
- `app/providers/gemini_agent.py` - Gemini runtime tester

### Batch Review
- `batch_review_enhanced.py` - Main batch review script
- `batch_review_prs.py` - Faster batch review variant
- `api_capture.py` - API request/response logging
- `confidence_tracker.py` - Confidence metrics

### Utilities
- `verify_setup.py` - Verify environment configuration
- `find_installation_id.py` - Locate GitHub App installation ID
- `cleanup.py` - Remove temporary files and caches

### Configuration
- `.env.example` - Environment template
- `.gitignore` - Git ignore patterns
- `pyproject.toml` - Python project config

### Documentation
- `SETUP.md` - Initial setup & usage guide
- `FEATURES.md` - Features & technical reference

---

## Support & Debugging

### Verbose Output

To see detailed logs during batch review:

```bash
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
python batch_review_enhanced.py owner repo --installation-id ID
```

### Check API Capture

Review raw API interactions:

```bash
# See formatted log
cat api_capture_*.log | head -50

# Count interactions
wc -l api_interactions_*.jsonl

# View first interaction
head -1 api_interactions_*.jsonl | python -m json.tool
```

### Validate Fine-Tuning Dataset

```bash
# Check format
python -c "import json; [json.loads(line) for line in open('fine_tuning_dataset.jsonl')]"

# Count examples
wc -l fine_tuning_dataset.jsonl

# Sample entry
head -1 fine_tuning_dataset.jsonl | python -m json.tool
```

---

## Common Questions

**Q: How long does batch review take?**
A: ~30-60 seconds per PR. 40 PRs = 20-40 minutes.

**Q: How much does it cost?**
A: ~$0.10-0.30 per PR. 40 PRs = ~$5-15.

**Q: Can I use my own models?**
A: Yes, edit the model names in `.env` or use fine-tuned models after training.

**Q: Does it work offline?**
A: No, requires LLM API access (OpenAI, Anthropic, Gemini).

**Q: Can I use for production?**
A: Yes, deploy the FastAPI app to a server and configure GitHub App webhook.

**Q: How do I reduce costs?**
A: Use cheaper models (Gemini instead of GPT-4), use `--no-capture` flag, or fine-tune smaller models.

**Q: What if agents disagree?**
A: They debate for up to 3 rounds. If they still disagree, the review remains fail-closed and requests changes unless all agents approve.

**Q: Can I customize the review criteria?**
A: Yes, modify agent system prompts in `app/providers/*_agent.py`.

---

## Troubleshooting Guide

### Issue: "Installation not found"
- Run: `python find_installation_id.py owner repo`
- Or manually check: https://github.com/settings/apps > Installations

### Issue: Reviews not posting to GitHub
- Test with `--no-post --max-prs 1` first
- Verify app permissions: Pull requests Read & write
- Check app is installed on repository

### Issue: API rate limits exceeded
- GitHub API: wait 1 hour before retrying
- LLM providers: check dashboard for limits
- Run batch reviews during off-peak hours

### Issue: Fine-tuning dataset is empty
- Ensure `--no-capture` is NOT used
- Check `api_interactions_*.jsonl` has data
- Run: `python cleanup.py` then retry

### Issue: Takes too long
- Use `--max-prs 5` to test speed
- Larger PRs take longer (normal)
- Use cheaper models if cost is concern
- Use `--no-capture` if speed critical

---

This completes the comprehensive features and reference documentation.
