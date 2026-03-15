import asyncio
import json
import re
from collections.abc import Callable

from dissent.llm import chat_json, create_client
from dissent.personas import DEFAULT_PERSONAS

_STOPWORDS = {
    "a",
    "an",
    "the",
    "is",
    "it",
    "in",
    "of",
    "to",
    "that",
    "this",
    "are",
    "be",
    "by",
    "or",
    "and",
    "not",
    "if",
    "so",
    "as",
    "at",
    "on",
    "for",
    "its",
    "was",
    "has",
    "with",
    "can",
    "but",
    "may",
}


def _challenge_is_grounded(challenge: dict, finding: dict) -> bool:
    """Return False if the challenge quotes a claim that doesn't appear in the finding.

    Agents sometimes challenge a premise they invented rather than something the
    finding actually says. If they provided a `quoted_claim`, we check that at
    least one meaningful word from the quote exists in the finding text. If zero
    meaningful words match, the challenge is almost certainly hallucinated.
    """
    quoted = challenge.get("quoted_claim", "").strip()
    if not quoted:
        return True  # No quote provided - accept, the prompt-level fix handles this

    finding_text = " ".join(
        [
            finding.get("title", ""),
            finding.get("detail", ""),
            finding.get("suggestion", ""),
        ]
    ).lower()

    words = {
        w for w in re.findall(r"[a-z_`']{4,}", quoted.lower()) if w not in _STOPWORDS
    }
    if not words:
        return True  # Quote too short to judge

    return any(w in finding_text for w in words)


REVIEW_PROMPT = """\
Review the following code diff. Return your findings as JSON:

{{
  "findings": [
    {{
      "severity": "high | medium | low",
      "file": "path/to/file",
      "line": <line number as integer, or null>,
      "title": "Short specific title naming the exact problem (not the category)",
      "detail": "Explain the issue with a concrete scenario: what input or condition triggers it, what goes wrong, and why it matters.",
      "suggestion": "Specific fix at the code level - name the function, pattern, or change needed, not just a vague direction."
    }}
  ]
}}

Guidelines:
- Title must be specific. Bad: "Cache issue". Good: "`required_capability` missing from cache key".
- Detail must include a concrete scenario showing when the bug triggers or the risk materializes.
- Suggestion must be actionable at the code level - name the specific function, pattern, or line change needed.
- Skip pure style preferences and formatting nitpicks. Focus on bugs, risks, and correctness issues.
- If you find no real issues from your perspective, return {{"findings": []}}.

DIFF:
{diff}"""

DEBATE_PROMPT = """\
You previously reviewed a code diff. Now other reviewers have shared their findings.

Your original findings:
{own_findings}

All findings from other reviewers:
{other_findings}

Review all findings and respond with JSON:

{{
  "endorsements": [
    {{
      "reviewer": "persona_name",
      "finding_title": "exact title of the finding you are endorsing",
      "comment": "one sentence on why this is a real issue from your domain"
    }}
  ],
  "challenges": [
    {{
      "reviewer": "persona_name",
      "finding_title": "exact title of the finding you are challenging",
      "quoted_claim": "copy the exact sentence or phrase from the finding that you believe is wrong",
      "reason": "why that specific claim is incorrect - the bug doesn't exist, the scenario is impossible, or the quoted claim is factually wrong"
    }}
  ],
  "new_findings": [
    {{
      "severity": "high | medium | low",
      "file": "path/to/file",
      "line": <line number as integer, or null>,
      "title": "Short specific title naming the exact problem",
      "detail": "Concrete scenario showing when and how this breaks",
      "suggestion": "Specific code-level fix"
    }}
  ],
  "withdrawn": ["exact titles of your own findings you now withdraw"]
}}

Rules:
- Only endorse findings you are genuinely confident are real issues from your domain.
- Before challenging, re-read the finding text carefully. Only challenge claims the finding explicitly makes - do not challenge your own interpretation or an assumption you've added.
- Challenge findings if: the bug doesn't actually exist, the scenario is impossible in this codebase, or a specific claim in the finding is factually wrong.
- Add new findings only if seeing the other reviews revealed a real issue you missed - and only if it meets the same bar as round 1.
- Withdraw your own findings if another reviewer made a convincing case they are wrong or not applicable.
- Do not rubber-stamp. A low-quality endorsement hurts signal more than it helps."""


async def run_review(
    diff: str,
    model: str,
    base_url: str | None = None,
    api_key: str | None = None,
    rounds: int = 2,
    persona_names: list[str] | None = None,
    personas_dict: dict | None = None,
    on_status: Callable[[str], None] | None = None,
) -> dict:
    client = create_client(base_url=base_url, api_key=api_key)

    all_personas = personas_dict or DEFAULT_PERSONAS
    personas = {
        k: v
        for k, v in all_personas.items()
        if persona_names is None or k in persona_names
    }

    # -- Round 1: Independent review ------------------------------------------
    if on_status:
        on_status("Round 1: Independent review")

    async def review_one(name: str, persona: dict) -> tuple[str, list]:
        system = persona["system"] + "\n\nYou MUST respond with valid JSON only."
        user = REVIEW_PROMPT.format(diff=diff)
        result = await chat_json(client, model, system, user)
        return name, result.get("findings", [])

    tasks = [review_one(n, p) for n, p in personas.items()]
    round1 = dict(await asyncio.gather(*tasks))

    # -- Debate rounds ---------------------------------------------------------
    reviews = dict(round1)
    all_debate_responses: dict[str, dict] = {}

    for round_num in range(2, rounds + 2):
        if on_status:
            on_status(f"Round {round_num}: Debate")

        async def debate_one(name: str, persona: dict) -> tuple[str, dict]:
            own = json.dumps(reviews.get(name, []), indent=2)
            others = {
                other: findings for other, findings in reviews.items() if other != name
            }
            system = persona["system"] + "\n\nYou MUST respond with valid JSON only."
            user = DEBATE_PROMPT.format(
                own_findings=own,
                other_findings=json.dumps(others, indent=2),
            )
            result = await chat_json(client, model, system, user)
            return name, result

        tasks = [debate_one(n, p) for n, p in personas.items()]
        debate_results = dict(await asyncio.gather(*tasks))
        all_debate_responses.update(debate_results)

    return _build_consensus(round1, all_debate_responses, personas)


def _build_consensus(
    reviews: dict[str, list],
    debate_responses: dict[str, dict],
    personas: dict,
) -> dict:
    findings: list[dict] = []
    index: dict[str, int] = {}  # title -> position in findings list

    # Collect initial findings
    for reviewer, reviewer_findings in reviews.items():
        for f in reviewer_findings:
            title = f.get("title", "")
            if title and title not in index:
                index[title] = len(findings)
                findings.append(
                    {
                        **f,
                        "source": reviewer,
                        "endorsements": [],
                        "challenges": [],
                        "withdrawn": False,
                    }
                )

    # Apply debate responses - deduplicate so each reviewer can only
    # endorse or challenge a given finding once, even across multiple rounds.
    endorsed: dict[str, set[str]] = {}  # finding_title -> set of reviewer names
    challenged: dict[str, set[str]] = {}

    for reviewer, response in debate_responses.items():
        for e in response.get("endorsements", []):
            title = e.get("finding_title", "")
            if title in index and reviewer not in endorsed.setdefault(title, set()):
                endorsed[title].add(reviewer)
                findings[index[title]]["endorsements"].append(
                    {"reviewer": reviewer, "comment": e.get("comment", "")}
                )

        for c in response.get("challenges", []):
            title = c.get("finding_title", "")
            if (
                title in index
                and reviewer not in challenged.setdefault(title, set())
                and _challenge_is_grounded(c, findings[index[title]])
            ):
                challenged[title].add(reviewer)
                findings[index[title]]["challenges"].append(
                    {"reviewer": reviewer, "reason": c.get("reason", "")}
                )

        for title in response.get("withdrawn", []):
            if title in index:
                findings[index[title]]["withdrawn"] = True

        for f in response.get("new_findings", []):
            title = f.get("title", "")
            if title and title not in index:
                index[title] = len(findings)
                findings.append(
                    {
                        **f,
                        "source": reviewer,
                        "endorsements": [],
                        "challenges": [],
                        "withdrawn": False,
                        "from_debate": True,
                    }
                )

    # Deduplicate findings that point to the same file+line - keep the one with
    # higher severity (or first seen), merge the other's source into co_authors.
    seen_locations: dict[tuple, int] = {}  # (file, line) -> index in findings
    deduped: list[dict] = []
    for f in findings:
        loc = (f.get("file"), f.get("line"))
        if loc[0] and loc[1] and loc in seen_locations:
            primary = deduped[seen_locations[loc]]
            # Merge: add the duplicate's source as a co-author if different
            if f.get("source") and f["source"] not in primary.get(
                "co_authors", [primary["source"]]
            ):
                primary.setdefault("co_authors", [primary["source"]]).append(
                    f["source"]
                )
            # Absorb endorsements and challenges, deduplicating by reviewer
            existing_endorsers = {e["reviewer"] for e in primary["endorsements"]}
            for e in f.get("endorsements", []):
                if e["reviewer"] not in existing_endorsers:
                    existing_endorsers.add(e["reviewer"])
                    primary["endorsements"].append(e)
            existing_challengers = {c["reviewer"] for c in primary["challenges"]}
            for c in f.get("challenges", []):
                if c["reviewer"] not in existing_challengers:
                    existing_challengers.add(c["reviewer"])
                    primary["challenges"].append(c)
        else:
            if loc[0] and loc[1]:
                seen_locations[loc] = len(deduped)
            deduped.append(f)
    findings = deduped

    # Score
    severity_weight = {"high": 3, "medium": 2, "low": 1}
    for f in findings:
        w = severity_weight.get(f.get("severity", "low"), 1)
        f["consensus_score"] = (1 + len(f["endorsements"]) - len(f["challenges"])) * w
        if f["withdrawn"]:
            f["consensus_score"] = -1

    active = sorted(
        [f for f in findings if not f["withdrawn"]],
        key=lambda f: f["consensus_score"],
        reverse=True,
    )
    withdrawn = [f for f in findings if f["withdrawn"]]

    # Build swarm summary
    summary = _build_summary(active, withdrawn, personas)

    return {
        "findings": active,
        "withdrawn": withdrawn,
        "reviewer_count": len(personas),
        "summary": summary,
    }


def _build_summary(active: list[dict], withdrawn: list[dict], personas: dict) -> dict:
    if not active:
        return {"consensus": [], "split": [], "emergent": [], "verdict": "clean"}

    consensus = []
    split = []
    emergent = []

    for f in active:
        title = f.get("title", "")
        endorsements = len(f.get("endorsements", []))
        challenges = len(f.get("challenges", []))

        if f.get("from_debate"):
            emergent.append(title)
        elif endorsements >= 2 and challenges == 0:
            consensus.append(title)
        elif challenges >= 1 and endorsements >= 1:
            split.append(title)

    high_count = sum(1 for f in active if f.get("severity") == "high")
    total = len(active)

    if high_count == 0:
        verdict = "mostly clean, minor issues"
    elif high_count <= 2:
        verdict = f"{high_count} high-severity issue(s) need attention"
    else:
        verdict = f"{high_count} high-severity issues - significant concerns"

    return {
        "consensus": consensus,
        "split": split,
        "emergent": emergent,
        "verdict": verdict,
        "total": total,
        "withdrawn_count": len(withdrawn),
    }
