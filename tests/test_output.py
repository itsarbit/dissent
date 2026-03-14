import json

from dissent.output import print_results


def _make_consensus(findings=None, withdrawn=None):
    return {
        "findings": findings or [],
        "withdrawn": withdrawn or [],
        "reviewer_count": 3,
        "summary": {
            "consensus": ["SQL Injection"],
            "split": ["N+1 Query"],
            "emergent": ["Error Handling"],
            "verdict": "2 high-severity issue(s) need attention",
            "total": len(findings or []),
            "withdrawn_count": len(withdrawn or []),
        },
    }


def _sample_finding(**overrides):
    base = {
        "severity": "high",
        "file": "app.py",
        "line": 42,
        "title": "SQL Injection",
        "detail": "User input in query",
        "suggestion": "Use parameterized queries",
        "source": "security",
        "endorsements": [{"reviewer": "performance", "comment": "agree"}],
        "challenges": [],
        "consensus_score": 6,
    }
    base.update(overrides)
    return base


class TestPrintTerminal:
    def test_no_findings(self, capsys):
        print_results(_make_consensus(), fmt="terminal")
        out = capsys.readouterr().out
        assert "No issues found" in out

    def test_with_findings(self, capsys):
        findings = [_sample_finding()]
        print_results(_make_consensus(findings=findings), fmt="terminal")
        out = capsys.readouterr().out
        assert "SQL Injection" in out
        assert "Dissent" in out
        assert "Swarm Summary" in out

    def test_with_challenges(self, capsys):
        findings = [
            _sample_finding(
                challenges=[{"reviewer": "readability", "reason": "not a real issue"}],
            )
        ]
        print_results(_make_consensus(findings=findings), fmt="terminal")
        out = capsys.readouterr().out
        assert "Challenged by" in out

    def test_from_debate_label(self, capsys):
        findings = [_sample_finding(from_debate=True)]
        print_results(_make_consensus(findings=findings), fmt="terminal")
        out = capsys.readouterr().out
        assert "surfaced during debate" in out

    def test_withdrawn_count(self, capsys):
        withdrawn = [_sample_finding(title="Withdrawn")]
        findings = [_sample_finding()]
        print_results(
            _make_consensus(findings=findings, withdrawn=withdrawn), fmt="terminal"
        )
        out = capsys.readouterr().out
        assert "withdrawn" in out.lower()


class TestPrintJson:
    def test_json_output(self, capsys):
        consensus = _make_consensus(findings=[_sample_finding()])
        print_results(consensus, fmt="json")
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert parsed["findings"][0]["title"] == "SQL Injection"
        assert parsed["reviewer_count"] == 3


class TestPrintMarkdown:
    def test_no_findings(self, capsys):
        print_results(_make_consensus(), fmt="markdown")
        out = capsys.readouterr().out
        assert "No Issues Found" in out

    def test_with_findings(self, capsys):
        findings = [_sample_finding()]
        print_results(_make_consensus(findings=findings), fmt="markdown")
        out = capsys.readouterr().out
        assert "# Dissent Results" in out
        assert "SQL Injection" in out
        assert "`app.py:42`" in out

    def test_endorsed_and_challenged(self, capsys):
        findings = [
            _sample_finding(
                endorsements=[{"reviewer": "performance", "comment": "yes"}],
                challenges=[{"reviewer": "testing", "reason": "nah"}],
            )
        ]
        print_results(_make_consensus(findings=findings), fmt="markdown")
        out = capsys.readouterr().out
        assert "Endorsed by" in out
        assert "Challenged by" in out
