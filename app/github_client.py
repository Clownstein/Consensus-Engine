import os
import time

import httpx
import jwt


class GitHubAppClient:
    def __init__(self, token: str):
        self.token = token
        self.client = httpx.Client(
            base_url="https://api.github.com",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30,
        )

    @classmethod
    def for_installation(cls, installation_id: int) -> "GitHubAppClient":
        app_id = os.environ["GITHUB_APP_ID"]
        with open(os.environ["GITHUB_PRIVATE_KEY_PATH"], "rb") as f:
            private_key = f.read()
        now = int(time.time())
        app_jwt = jwt.encode(
            {"iat": now - 60, "exp": now + 9 * 60, "iss": app_id},
            private_key,
            algorithm="RS256",
        )

        response = httpx.post(
            f"https://api.github.com/app/installations/{installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {app_jwt}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30,
        )
        response.raise_for_status()
        return cls(response.json()["token"])

    def get_pr(self, owner: str, repo: str, pr_number: int) -> dict:
        r = self.client.get(f"/repos/{owner}/{repo}/pulls/{pr_number}")
        r.raise_for_status()
        return r.json()

    def get_pr_files(self, owner: str, repo: str, pr_number: int) -> list[dict]:
        files = []
        page = 1
        while True:
            r = self.client.get(
                f"/repos/{owner}/{repo}/pulls/{pr_number}/files",
                params={"per_page": 100, "page": page},
            )
            r.raise_for_status()
            chunk = r.json()
            files.extend(chunk)
            if len(chunk) < 100:
                return files
            page += 1

    def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        r = self.client.get(
            f"/repos/{owner}/{repo}/pulls/{pr_number}",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github.v3.diff",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        r.raise_for_status()
        return r.text

    def create_check_run(self, owner: str, repo: str, sha: str, name: str) -> int:
        r = self.client.post(
            f"/repos/{owner}/{repo}/check-runs",
            json={
                "name": name,
                "head_sha": sha,
                "status": "in_progress",
                "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
        )
        r.raise_for_status()
        return r.json()["id"]

    def update_check_run(
        self,
        owner: str,
        repo: str,
        check_run_id: int,
        conclusion: str,
        summary: str,
    ) -> None:
        r = self.client.patch(
            f"/repos/{owner}/{repo}/check-runs/{check_run_id}",
            json={
                "status": "completed",
                "conclusion": conclusion,
                "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "output": {
                    "title": "Multi-agent LLM review",
                    "summary": summary[:65000],
                },
            },
        )
        r.raise_for_status()

    def create_pull_request_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        event: str,
        body: str,
    ) -> None:
        r = self.client.post(
            f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
            json={"event": event, "body": body[:65000]},
        )
        r.raise_for_status()
