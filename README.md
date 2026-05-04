# Multi-Agent PR Reviewer

Automated GitHub Pull Request reviewer built with FastAPI + LangGraph, powered by three specialized LLM agents:
- OpenAI Architect (correctness and maintainability)
- Anthropic Security Auditor (security and threat modeling)
- Gemini Runtime Tester (tests, performance, and deployability)

The system runs consensus-based review rounds and posts an approval or requested changes back to GitHub as a GitHub App.

## What It Does

- Receives GitHub webhook events for pull requests
- Builds PR review context from changed files and diffs
- Runs multi-agent review and debate workflow
- Enforces fail-closed approval logic (all agents must approve)
- Posts review output to PRs and updates check runs
- Supports batch review of open PRs
- Optionally captures API interactions and generates a fine-tuning JSONL dataset

## Requirements

- Python 3.11+
- GitHub App credentials
- API keys for:
  - OpenAI
  - Anthropic
  - Gemini

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

## Configuration

Create `.env` from `.env.example` and set required values:

```bash
cp .env.example .env
```

Required environment variables:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`
- `GITHUB_APP_ID`
- `GITHUB_PRIVATE_KEY_PATH` (default: `./private-key.pem`)
- `GITHUB_WEBHOOK_SECRET`

Optional:
- `GITHUB_INSTALLATION_ID` (if you do not pass `--installation-id`)
- `MAX_DEBATE_ROUNDS`
- `MIN_CONFIDENCE_TO_APPROVE`
- `OPENAI_MODEL`
- `ANTHROPIC_MODEL`
- `GEMINI_MODEL`

Verify setup:

```bash
python verify_setup.py
```

## Run Webhook Service

Start the FastAPI app:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Health check:

```bash
GET /health
```

GitHub webhook endpoint:

```bash
POST /webhooks/github
```

Supported pull request actions:
- `opened`
- `synchronize`
- `reopened`
- `ready_for_review`

## Batch Review Commands

### Basic Batch Review

```bash
python batch_review_prs.py <owner> <repo> --installation-id <id>
```

Options:
- `--no-post` (dry run)
- `--max-prs <n>`

### Enhanced Batch Review (confidence + capture)

```bash
python batch_review_enhanced.py <owner> <repo> --installation-id <id>
```

Additional option:
- `--no-capture` (skip API capture and fine-tuning dataset generation)

## Output Files

Depending on mode:
- `batch_review_results.json`
- `batch_review_results_enhanced.json`
- `api_interactions_*.jsonl`
- `api_capture_*.log`
- `fine_tuning_dataset.jsonl`

## Project Structure

```text
app/
  main.py                    # FastAPI webhook service
  github_client.py           # GitHub App API operations
  diff_builder.py            # PR context builder
  schemas.py                 # Review schema
  prompts.py                 # Agent prompts
  graph/
    workflow.py              # LangGraph orchestration
    consensus.py             # Approval logic
  providers/
    openai_agent.py
    anthropic_agent.py
    gemini_agent.py
  rendering/
    github_markdown.py       # PR comment rendering

batch_review_prs.py          # Batch reviewer
batch_review_enhanced.py     # Enhanced batch reviewer
api_capture.py               # API capture + fine-tuning export
confidence_tracker.py        # Confidence metrics
verify_setup.py              # Environment validation
find_installation_id.py      # Installation lookup helper
cleanup.py                   # Cleanup utility
```

## Additional Docs

- `SETUP.md` for setup and usage walkthrough
- `FEATURES.md` for architecture and feature reference

