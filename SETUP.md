# Multi-Agent PR Reviewer - Setup & Usage Guide

A GitHub App that automatically reviews Pull Requests using a multi-agent LLM workflow. Three specialized AI agents (Architect, Security, Runtime) debate and reach consensus before approving PRs.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Initial Setup](#initial-setup)
3. [GitHub App Configuration](#github-app-configuration)
4. [Batch Review Usage](#batch-review-usage)
5. [Commands Reference](#commands-reference)
6. [Troubleshooting](#troubleshooting)
7. [Cleanup & Maintenance](#cleanup--maintenance)

---

## Quick Start

### Prerequisites

- Python 3.11+
- OpenAI, Anthropic, and Gemini API keys
- GitHub account with repo access

### 30-Second Setup

```bash
# 1. Install dependencies
python -m venv .venv
.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On macOS/Linux
pip install -e .

# 2. Configure environment
cp .env.example .env
# Edit .env and fill in your API keys

# 3. Download GitHub App private key
# Place it as: private-key.pem

# 4. Verify setup
python verify_setup.py
```

### First Review (1 PR Test)

```bash
# Find your GitHub App installation ID
python find_installation_id.py <owner> <repo>

# Test with first PR (dry run)
python batch_review_enhanced.py <owner> <repo> \
  --installation-id <installation_id> \
  --no-post --max-prs 1

# If successful, review all PRs
python batch_review_enhanced.py <owner> <repo> \
  --installation-id <installation_id>
```

---

## Initial Setup

### 1. Create Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 2. Install Package

```bash
pip install -e .
```

This installs the project and all dependencies (FastAPI, LangGraph, OpenAI, Anthropic, etc.)

### 3. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-api03-...
GEMINI_API_KEY=AIzaSy...

GITHUB_APP_ID=3592372
GITHUB_PRIVATE_KEY_PATH=./private-key.pem
GITHUB_WEBHOOK_SECRET=your-secret-here

OPENAI_MODEL=gpt-4o
ANTHROPIC_MODEL=claude-sonnet-4-6
GEMINI_MODEL=gemini-3.1-flash-lite-preview

MAX_DEBATE_ROUNDS=3
MIN_CONFIDENCE_TO_APPROVE=0.80
```

### 4. Download GitHub App Private Key

From GitHub App settings:
1. Go to https://github.com/settings/apps
2. Select your app
3. Download the private key (`.pem` file)
4. Save as `private-key.pem` in project root

### 5. Verify Setup

```bash
python verify_setup.py
```

Should show all `[OK]` checks.

---

## GitHub App Configuration

### Create GitHub App

1. Go to: https://github.com/settings/apps/new
2. Fill in the form:
   - **App name**: Multi-Agent PR Reviewer (or your name)
   - **Webhook URL**: `https://your-domain/webhooks/github` (use ngrok for local dev)
   - **Webhook secret**: Generate a secure random string

### Permissions Required

- **Pull requests**: Read & write
- **Checks**: Read & write
- **Contents**: Read-only

### Events to Subscribe

- **Pull request**: checked

### Install App

1. Go to: https://github.com/settings/apps
2. Click your app
3. Click "Installations" tab
4. Click "Install" on target repository

---

## Batch Review Usage

### Basic Commands

**Dry run (test, first PR only):**
```bash
python batch_review_enhanced.py <owner> <repo> \
  --installation-id <installation_id> \
  --no-post \
  --max-prs 1
```

**Review all PRs:**
```bash
python batch_review_enhanced.py <owner> <repo> \
  --installation-id <installation_id>
```

**Using environment variable (easier):**
```bash
export GITHUB_INSTALLATION_ID=<installation_id>
python batch_review_enhanced.py <owner> <repo>
```

### Features

- ✅ Multi-agent consensus review
- ✅ Confidence score tracking (0-100%)
- ✅ API request/response capture
- ✅ Fine-tuning dataset generation (JSONL format)
- ✅ Quality metrics (correctness, security, tests)
- ✅ Per-agent breakdown
- ✅ Rate limiting (2s between PRs)

### Outputs Generated

| File | Contains |
|------|----------|
| `batch_review_results_enhanced.json` | PR reviews + confidence metrics |
| `api_interactions_*.jsonl` | All LLM API calls (requests/responses) |
| `api_capture_*.log` | Human-readable API log |
| `fine_tuning_dataset.jsonl` | Training data for model fine-tuning |

---

## Commands Reference

### Setup & Verification

```bash
# Verify environment is configured
python verify_setup.py

# Find GitHub App installation ID
python find_installation_id.py owner repo

# List all app installations
python find_installation_id.py --list
```

### Batch Review Scripts

```bash
# Enhanced batch review (with confidence, API capture)
python batch_review_enhanced.py owner repo --installation-id ID

# Basic batch review (fast, no capture)
python batch_review_prs.py owner repo --installation-id ID

# Test options
--no-post              # Dry run, don't post to GitHub
--max-prs N            # Limit to N PRs
--no-capture           # Skip API capture (faster)
```

### Maintenance

```bash
# Remove temp files, caches, results
python cleanup.py

# View what would be cleaned
ls api_interactions_*.jsonl
ls batch_review_results*.json
```

---

## Troubleshooting

### Setup Issues

**"Module not found" or import errors:**
```bash
pip install -e .
```

**"Missing API keys":**
```bash
# Verify .env file exists without printing secrets
ls .env

# Re-run setup verification
python verify_setup.py
```

**"Private key not found":**
- Download from GitHub App settings
- Save as `private-key.pem` in project root
- Update `GITHUB_PRIVATE_KEY_PATH` in `.env` if needed

### Batch Review Issues

**"Installation ID not found":**
```bash
python find_installation_id.py owner repo
# Or check: https://github.com/settings/apps > Installations
```

**"Reviews not posting to GitHub":**
```bash
# Test with dry run first
python batch_review_enhanced.py owner repo --installation-id ID --no-post --max-prs 1

# Check permissions: Pull requests Read & write
# Verify app is installed on repository
```

**"API rate limits exceeded":**
- GitHub API has ~5,000 requests/hour
- Script adds 2s delay between PRs
- Retry after a few minutes
- Run during off-peak hours

**"Takes too long":**
- Each review: 30-60 seconds per PR
- 40 PRs = 20-40 minutes total
- This is normal - agents debate in multiple rounds
- Use `--max-prs N` to review in batches

---

## Cleanup & Maintenance

### Remove Temporary Files

```bash
python cleanup.py
```

Removes:
- API capture files
- Batch review results
- Fine-tuning datasets
- Python caches
- IDE cache

Safe to run anytime - only removes temp/cache files.

### Save Important Outputs

Before cleanup, save outputs you want to keep:

```bash
# Save fine-tuning dataset
cp fine_tuning_dataset.jsonl backups/dataset_$(date +%Y%m%d).jsonl

# Save batch results
cp batch_review_results_enhanced.json backups/results_$(date +%Y%m%d).json

# Then cleanup
python cleanup.py
```

### Git Configuration

A `.gitignore` file is included to exclude:
- Python cache (`__pycache__`, `*.pyc`)
- Virtual environment (`.venv`)
- Temporary outputs
- IDE files (`.vscode`, `.idea`)
- Environment files (`.env`)

---

## What the System Does

### Multi-Agent Review Process

1. **OpenAI Architect** - Correctness, design, maintainability
2. **Anthropic Security** - Vulnerabilities, threat modeling
3. **Gemini Runtime** - Tests, performance, deployability

### Consensus Requirements

- ✅ All 3 agents must approve
- ✅ No critical/high severity issues
- ✅ Configurable confidence threshold (default 80%)
- ✅ Up to 3 debate rounds if agents disagree

### Output Example

```
# ✅ APPROVED

All agents approved this PR.

Confidence Metrics:
  Average: 92.3%
  Correctness: 100%
  Security: 100%
  Tests: 85%

By Agent:
  OpenAI Architect: 95% confidence, approved
  Anthropic Security: 88% confidence, approved
  Gemini Runtime: 92% confidence, approved
```

---

## Performance & Costs

### Performance

- Per PR review: 30-60 seconds
- 10 PRs: ~5-10 minutes
- 40 PRs: ~20-40 minutes
- Parallel agent processing maximizes efficiency

### Costs

Typical costs per review:
- OpenAI GPT-4o: ~$0.02-0.10
- Anthropic Claude: ~$0.03-0.08
- Google Gemini: ~$0.01-0.05
- **Total per PR: ~$0.10-0.30**

For 40 PRs: expect ~$5-15 in API costs

---

## Next Steps

1. **Complete setup**: Follow "Initial Setup" above
2. **Test**: Run first review with `--no-post --max-prs 1`
3. **Review all PRs**: Run full batch review
4. **Analyze results**: Check confidence metrics and findings
5. **Fine-tune (optional)**: Use generated dataset to train models

---

## Additional Resources

- **Development Details**: See `FEATURES.md` for architecture and workflow details
- **Configuration Details**: See `.env.example` for all options
- **API Capture**: Fine-tuning datasets are in JSONL format ready for training

For questions or issues, check `.gitignore` is present and `cleanup.py` works to maintain a clean workspace.
