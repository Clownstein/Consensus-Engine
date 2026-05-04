from app.config import config

_SKIP_EXTENSIONS = {
    ".lock",
    ".min.js",
    ".min.css",
    ".map",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
}

_SKIP_PATTERNS = ("dist/", "vendor/", "node_modules/", ".yarn/")


def _should_skip(filename: str) -> bool:
    lower = filename.lower()
    if any(lower.endswith(ext) for ext in _SKIP_EXTENSIONS):
        return True
    if any(pat in lower for pat in _SKIP_PATTERNS):
        return True
    return False


def build_review_context(gh, owner: str, repo: str, pr_number: int) -> dict:
    pr = gh.get_pr(owner, repo, pr_number)
    all_files = gh.get_pr_files(owner, repo, pr_number)
    diff = gh.get_pr_diff(owner, repo, pr_number)

    # Filter out generated/vendored files, cap at max_files
    files = [f for f in all_files if not _should_skip(f["filename"])]
    files = files[: config.max_files_per_review]

    truncated = False
    diff_bytes = diff.encode("utf-8")
    if len(diff_bytes) > config.max_diff_bytes:
        diff = diff_bytes[: config.max_diff_bytes].decode("utf-8", errors="ignore")
        truncated = True

    return {
        "owner": owner,
        "repo": repo,
        "pr_number": pr_number,
        "title": pr["title"],
        "body": pr.get("body") or "",
        "base_branch": pr["base"]["ref"],
        "head_branch": pr["head"]["ref"],
        "head_sha": pr["head"]["sha"],
        "changed_files": [
            {
                "filename": f["filename"],
                "status": f["status"],
                "additions": f["additions"],
                "deletions": f["deletions"],
                "patch": f.get("patch", ""),
            }
            for f in files
        ],
        "diff": diff,
        "diff_truncated": truncated,
    }
