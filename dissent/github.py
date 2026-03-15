"""GitHub PR integration - fetch diffs and post inline review comments."""

import json
import re
import subprocess


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Extract owner, repo, pr_number from a GitHub PR URL."""
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not match:
        raise ValueError(
            f"Invalid GitHub PR URL: {url}\n"
            "Expected: https://github.com/owner/repo/pull/123"
        )
    return match.group(1), match.group(2), int(match.group(3))


def get_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetch PR diff using the gh CLI."""
    result = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{owner}/{repo}/pulls/{pr_number}",
            "-H",
            "Accept: application/vnd.github.v3.diff",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to fetch PR diff: {result.stderr.strip()}")
    if not result.stdout.strip():
        raise RuntimeError("PR has no diff (empty changeset).")
    return result.stdout


def post_review(
    owner: str,
    repo: str,
    pr_number: int,
    consensus: dict,
) -> str:
    """Post a PR review with inline comments and a swarm summary."""
    findings = consensus["findings"]
    summary = consensus.get("summary", {})

    body = _build_review_body(consensus, summary)
    comments = _build_inline_comments(findings)

    review_payload = {
        "body": body,
        "event": "COMMENT",
        "comments": comments,
    }

    result = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{owner}/{repo}/pulls/{pr_number}/reviews",
            "--method",
            "POST",
            "--input",
            "-",
        ],
        input=json.dumps(review_payload),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        # If inline comments fail (line not in diff), retry without them
        if "pull_request_review_thread.line" in result.stderr:
            review_payload["comments"] = []
            review_payload["body"] = body + _findings_as_body(findings)
            result = subprocess.run(
                [
                    "gh",
                    "api",
                    f"repos/{owner}/{repo}/pulls/{pr_number}/reviews",
                    "--method",
                    "POST",
                    "--input",
                    "-",
                ],
                input=json.dumps(review_payload),
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Failed to post review: {result.stderr.strip()}")

        else:
            raise RuntimeError(f"Failed to post review: {result.stderr.strip()}")

    response = json.loads(result.stdout)
    return response.get("html_url", "Review posted successfully.")


def _build_review_body(consensus: dict, summary: dict) -> str:
    reviewer_count = consensus["reviewer_count"]
    finding_count = len(consensus["findings"])

    parts = [
        "## Dissent Review",
        "",
        f"**{reviewer_count} agents** reviewed this PR "
        f"and found **{finding_count} issue(s)** after debate.",
        "",
    ]

    if summary:
        verdict = summary.get("verdict", "")
        if verdict:
            parts.append(f"**Verdict:** {verdict}")

        consensus_items = summary.get("consensus", [])
        if consensus_items:
            parts.append(f"**Swarm agrees on:** {', '.join(consensus_items[:5])}")

        split_items = summary.get("split", [])
        if split_items:
            parts.append(f"**Swarm split on:** {', '.join(split_items[:5])}")

        emergent_items = summary.get("emergent", [])
        if emergent_items:
            parts.append(f"**Emerged from debate:** {', '.join(emergent_items[:5])}")

        withdrawn = summary.get("withdrawn_count", 0)
        if withdrawn:
            parts.append(
                f"\n*{withdrawn} finding(s) withdrawn during debate "
                f"(agents changed their minds)*"
            )

    parts.append("")
    parts.append(
        "*Powered by [Dissent](https://github.com/itsarbit/dissent) "
        "- swarm intelligence for code review*"
    )

    return "\n".join(parts)


def _build_inline_comments(findings: list[dict]) -> list[dict]:
    comments = []
    for f in findings:
        file_path = f.get("file")
        line = f.get("line")
        if not file_path or not line:
            continue

        severity = f.get("severity", "low").upper()
        source = f.get("source", "unknown")
        endorsements = f.get("endorsements", [])
        challenges = f.get("challenges", [])
        score = f.get("consensus_score", 0)

        parts = [
            f"**\\[{severity}\\] {f.get('title', '')}**",
            "",
            f.get("detail", ""),
        ]

        if f.get("suggestion"):
            parts.append(f"\n**Suggestion:** {f['suggestion']}")

        if endorsements:
            names = ", ".join(e["reviewer"] for e in endorsements)
            parts.append(f"\n*Endorsed by: {names}*")

        if challenges:
            for c in challenges:
                parts.append(
                    f"\n*Challenged by {c['reviewer']}:* {c.get('reason', '')}"
                )

        parts.append(f"\n---\n*Found by {source} | Consensus score: {score}*")

        comments.append(
            {
                "path": file_path,
                "line": int(line),
                "body": "\n".join(parts),
            }
        )

    return comments


def _findings_as_body(findings: list[dict]) -> str:
    """Fallback: render findings as text when inline comments fail."""
    if not findings:
        return ""

    parts = ["\n\n---\n### Findings\n"]
    for i, f in enumerate(findings, 1):
        severity = f.get("severity", "low").upper()
        loc = f.get("file", "")
        if f.get("line"):
            loc += f":{f['line']}"

        parts.append(f"**{i}. \\[{severity}\\] {f.get('title', '')}**")
        if loc:
            parts.append(f"`{loc}`")
        parts.append(f.get("detail", ""))
        if f.get("suggestion"):
            parts.append(f"**Suggestion:** {f['suggestion']}")
        parts.append("")

    return "\n".join(parts)
