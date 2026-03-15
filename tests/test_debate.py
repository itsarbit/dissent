from dissent.debate import _build_consensus, _build_summary, _challenge_is_grounded


class TestBuildConsensus:
    def test_empty_reviews(self):
        result = _build_consensus({}, {}, {"a": {}})
        assert result["findings"] == []
        assert result["withdrawn"] == []

    def test_single_finding_no_debate(self):
        reviews = {
            "security": [
                {"title": "SQL Injection", "severity": "high", "detail": "bad"},
            ],
        }
        result = _build_consensus(reviews, {}, {"security": {}})
        assert len(result["findings"]) == 1
        assert result["findings"][0]["title"] == "SQL Injection"
        assert result["findings"][0]["consensus_score"] == 3  # (1+0-0)*3

    def test_endorsement_increases_score(self):
        reviews = {
            "security": [
                {"title": "XSS", "severity": "high", "detail": "bad"},
            ],
        }
        debate = {
            "performance": {
                "endorsements": [
                    {"finding_title": "XSS", "comment": "agree"},
                ],
                "challenges": [],
                "withdrawn": [],
                "new_findings": [],
            },
        }
        result = _build_consensus(reviews, debate, {"security": {}, "performance": {}})
        assert result["findings"][0]["consensus_score"] == 6  # (1+1-0)*3

    def test_challenge_decreases_score(self):
        reviews = {
            "security": [
                {"title": "Minor", "severity": "low", "detail": "meh"},
            ],
        }
        debate = {
            "readability": {
                "endorsements": [],
                "challenges": [
                    {"finding_title": "Minor", "reason": "not real"},
                ],
                "withdrawn": [],
                "new_findings": [],
            },
        }
        result = _build_consensus(reviews, debate, {"security": {}, "readability": {}})
        assert result["findings"][0]["consensus_score"] == 0  # (1+0-1)*1

    def test_withdrawn_findings_are_separated(self):
        reviews = {
            "testing": [
                {"title": "Flaky", "severity": "low", "detail": "maybe"},
            ],
        }
        debate = {
            "testing": {
                "endorsements": [],
                "challenges": [],
                "withdrawn": ["Flaky"],
                "new_findings": [],
            },
        }
        result = _build_consensus(reviews, debate, {"testing": {}})
        assert len(result["findings"]) == 0
        assert len(result["withdrawn"]) == 1

    def test_deduplicates_findings_at_same_file_and_line(self):
        reviews = {
            "security": [
                {
                    "title": "Global mutable state",
                    "severity": "medium",
                    "detail": "thread unsafe",
                    "file": "router.py",
                    "line": 49,
                    "source": "security",
                },
            ],
            "readability": [
                {
                    "title": "Global dict is confusing",
                    "severity": "low",
                    "detail": "hard to follow",
                    "file": "router.py",
                    "line": 49,
                    "source": "readability",
                },
            ],
        }
        result = _build_consensus(reviews, {}, {"security": {}, "readability": {}})
        # Two findings at the same file:line should be merged into one
        assert len(result["findings"]) == 1
        assert result["findings"][0]["title"] == "Global mutable state"
        assert "readability" in result["findings"][0].get("co_authors", [])

    def test_new_findings_from_debate(self):
        reviews = {"security": []}
        debate = {
            "performance": {
                "endorsements": [],
                "challenges": [],
                "withdrawn": [],
                "new_findings": [
                    {"title": "N+1 Query", "severity": "medium", "detail": "loop"},
                ],
            },
        }
        result = _build_consensus(reviews, debate, {"security": {}, "performance": {}})
        assert len(result["findings"]) == 1
        assert result["findings"][0]["from_debate"] is True


class TestChallengeIsGrounded:
    def test_no_quoted_claim_is_accepted(self):
        challenge = {"reason": "doesn't matter"}
        finding = {"title": "Cache bug", "detail": "bad cache"}
        assert _challenge_is_grounded(challenge, finding) is True

    def test_quoted_claim_matching_finding_is_accepted(self):
        challenge = {
            "quoted_claim": "required_capability is missing from the cache key",
            "reason": "actually it is included",
        }
        finding = {
            "title": "Cache key missing required_capability",
            "detail": "required_capability is not included in the cache key tuple",
        }
        assert _challenge_is_grounded(challenge, finding) is True

    def test_hallucinated_claim_not_in_finding_is_rejected(self):
        challenge = {
            "quoted_claim": "tuples are mutable and can lead to unexpected behavior",
            "reason": "tuples are immutable in Python",
        }
        finding = {
            "title": "Cache key does not include required_capability",
            "detail": "The cache key is missing the required_capability parameter",
            "suggestion": "Add required_capability to the cache key",
        }
        assert _challenge_is_grounded(challenge, finding) is False

    def test_hallucinated_challenge_filtered_from_consensus(self):
        reviews = {
            "security": [
                {
                    "title": "Missing param in cache key",
                    "severity": "medium",
                    "detail": "required_capability is not in the cache key",
                }
            ]
        }
        debate = {
            "performance": {
                "endorsements": [],
                "challenges": [
                    {
                        "finding_title": "Missing param in cache key",
                        "quoted_claim": "tuples are mutable objects that can change",
                        "reason": "tuples are immutable in Python",
                    }
                ],
                "withdrawn": [],
                "new_findings": [],
            }
        }
        result = _build_consensus(reviews, debate, {"security": {}, "performance": {}})
        # Hallucinated challenge should be filtered - score unaffected
        finding = result["findings"][0]
        assert len(finding["challenges"]) == 0
        assert finding["consensus_score"] == 2  # (1+0-0)*2, challenge was discarded


class TestBuildSummary:
    def test_clean_verdict_when_no_high_severity(self):
        findings = [{"severity": "low", "endorsements": [], "challenges": []}]
        summary = _build_summary(findings, [], {})
        assert "minor" in summary["verdict"]

    def test_high_severity_verdict(self):
        findings = [
            {
                "severity": "high",
                "title": "A",
                "endorsements": [1, 2, 3],
                "challenges": [],
            },
            {
                "severity": "high",
                "title": "B",
                "endorsements": [1, 2],
                "challenges": [],
            },
            {"severity": "high", "title": "C", "endorsements": [1], "challenges": []},
        ]
        summary = _build_summary(findings, [], {})
        assert "3 high-severity" in summary["verdict"]

    def test_consensus_findings(self):
        findings = [
            {
                "title": "Agreed",
                "severity": "high",
                "endorsements": [1, 2, 3],
                "challenges": [],
            },
        ]
        summary = _build_summary(findings, [], {})
        assert "Agreed" in summary["consensus"]

    def test_split_findings(self):
        findings = [
            {
                "title": "Debated",
                "severity": "medium",
                "endorsements": [1],
                "challenges": [2],
            },
        ]
        summary = _build_summary(findings, [], {})
        assert "Debated" in summary["split"]

    def test_emergent_findings(self):
        findings = [
            {
                "title": "New",
                "severity": "low",
                "endorsements": [],
                "challenges": [],
                "from_debate": True,
            },
        ]
        summary = _build_summary(findings, [], {})
        assert "New" in summary["emergent"]
