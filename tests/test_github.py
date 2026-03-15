import json
from unittest.mock import MagicMock, patch

import pytest

from dissent.github import (
    _build_inline_comments,
    _build_review_body,
    _find_existing_review,
    _findings_as_body,
    parse_pr_url,
)


class TestParsePrUrl:
    def test_valid_url(self):
        owner, repo, num = parse_pr_url("https://github.com/itsarbit/dissent/pull/42")
        assert owner == "itsarbit"
        assert repo == "dissent"
        assert num == 42

    def test_valid_url_http(self):
        owner, repo, num = parse_pr_url("http://github.com/org/repo/pull/1")
        assert owner == "org"
        assert repo == "repo"
        assert num == 1

    def test_invalid_url(self):
        with pytest.raises(ValueError, match="Invalid GitHub PR URL"):
            parse_pr_url("https://gitlab.com/org/repo/merge_requests/1")

    def test_not_a_pr_url(self):
        with pytest.raises(ValueError, match="Invalid GitHub PR URL"):
            parse_pr_url("https://github.com/org/repo/issues/5")


class TestBuildReviewBody:
    def test_basic_body(self):
        consensus = {
            "findings": [{"title": "Bug"}],
            "reviewer_count": 5,
        }
        summary = {
            "verdict": "1 high-severity issue(s) need attention",
            "consensus": ["SQL Injection"],
            "split": ["N+1 Query"],
            "emergent": ["Error Handling"],
            "withdrawn_count": 2,
        }
        body = _build_review_body(consensus, summary)
        assert "Dissent Review" in body
        assert "5 agents" in body
        assert "1 issue(s)" in body
        assert "SQL Injection" in body
        assert "N+1 Query" in body
        assert "Error Handling" in body
        assert "2 finding(s) withdrawn" in body

    def test_empty_summary(self):
        consensus = {"findings": [], "reviewer_count": 3}
        body = _build_review_body(consensus, {})
        assert "3 agents" in body
        assert "0 issue(s)" in body


class TestBuildInlineComments:
    def test_creates_comments_for_findings_with_lines(self):
        findings = [
            {
                "file": "app.py",
                "line": 42,
                "severity": "high",
                "title": "SQL Injection",
                "detail": "User input in query",
                "suggestion": "Use params",
                "source": "security",
                "endorsements": [{"reviewer": "perf", "comment": "agree"}],
                "challenges": [],
                "consensus_score": 6,
            }
        ]
        comments = _build_inline_comments(findings)
        assert len(comments) == 1
        assert comments[0]["path"] == "app.py"
        assert comments[0]["line"] == 42
        assert "SQL Injection" in comments[0]["body"]
        assert "Endorsed by: perf" in comments[0]["body"]

    def test_skips_findings_without_file_or_line(self):
        findings = [
            {"file": None, "line": None, "severity": "low", "title": "X"},
            {"file": "a.py", "line": None, "severity": "low", "title": "Y"},
            {"severity": "low", "title": "Z"},
        ]
        comments = _build_inline_comments(findings)
        assert len(comments) == 0

    def test_includes_challenges(self):
        findings = [
            {
                "file": "a.py",
                "line": 10,
                "severity": "medium",
                "title": "Perf",
                "detail": "Slow",
                "source": "performance",
                "endorsements": [],
                "challenges": [{"reviewer": "security", "reason": "not relevant"}],
                "consensus_score": 0,
            }
        ]
        comments = _build_inline_comments(findings)
        assert "Challenged by security" in comments[0]["body"]


class TestFindExistingReview:
    def _make_run(self, reviews):
        mock = MagicMock()
        mock.returncode = 0
        mock.stdout = json.dumps(reviews)
        return mock

    def test_returns_none_when_no_reviews(self):
        with patch("dissent.github.subprocess.run", return_value=self._make_run([])):
            assert _find_existing_review("o", "r", 1) is None

    def test_returns_none_when_no_dissent_review(self):
        reviews = [{"id": 1, "body": "Some other review"}]
        with patch(
            "dissent.github.subprocess.run", return_value=self._make_run(reviews)
        ):
            assert _find_existing_review("o", "r", 1) is None

    def test_returns_id_of_dissent_review(self):
        reviews = [
            {"id": 99, "body": "## Dissent Review\n\n**3 agents**"},
        ]
        with patch(
            "dissent.github.subprocess.run", return_value=self._make_run(reviews)
        ):
            assert _find_existing_review("o", "r", 1) == 99

    def test_returns_most_recent_when_multiple(self):
        reviews = [
            {"id": 10, "body": "## Dissent Review\n\nfirst"},
            {"id": 20, "body": "## Dissent Review\n\nsecond"},
        ]
        with patch(
            "dissent.github.subprocess.run", return_value=self._make_run(reviews)
        ):
            assert _find_existing_review("o", "r", 1) == 20

    def test_returns_none_on_api_error(self):
        mock = MagicMock()
        mock.returncode = 1
        mock.stdout = ""
        with patch("dissent.github.subprocess.run", return_value=mock):
            assert _find_existing_review("o", "r", 1) is None


class TestFindingsAsBody:
    def test_empty_findings(self):
        assert _findings_as_body([]) == ""

    def test_renders_findings(self):
        findings = [
            {
                "file": "app.py",
                "line": 5,
                "severity": "high",
                "title": "Bug",
                "detail": "Broken",
                "suggestion": "Fix it",
            }
        ]
        body = _findings_as_body(findings)
        assert "Bug" in body
        assert "`app.py:5`" in body
        assert "Fix it" in body
