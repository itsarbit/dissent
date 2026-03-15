import asyncio
import json
from collections.abc import Callable

from dissent.llm import chat_json, create_client
from dissent.personas import DEFAULT_PERSONAS

REVIEW_PROMPT = """\
Review the following code diff. Return your findings as JSON:

{{
  "findings": [
    {{
      "severity": "high | medium | low",
      "file": "path/to/file",
      "line": null,
      "title": "Short description",
      "detail": "Explanation of the issue",
      "suggestion": "What to do instead"
    }}
  ]
}}

If you find no real issues from your perspective, return {{"findings": []}}.

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
      "finding_title": "title of the finding",
      "comment": "why you agree (brief, optional)"
    }}
  ],
  "challenges": [
    {{
      "reviewer": "persona_name",
      "finding_title": "title of the finding",
      "reason": "why you disagree"
    }}
  ],
  "new_findings": [
    {{
      "severity": "high | medium | low",
      "file": "path/to/file",
      "line": null,
      "title": "Short description",
      "detail": "Explanation",
      "suggestion": "What to do instead"
    }}
  ],
  "withdrawn": ["titles of your own findings you now withdraw"]
}}

Rules:
- Endorse findings you genuinely agree are real issues.
- Challenge findings you believe are wrong, exaggerated, or not applicable.
- Also challenge findings whose technical reasoning is factually incorrect, even if the general concern area is valid.
- Add new findings only if the discussion revealed something you missed.
- Withdraw your own findings if other reviewers convinced you otherwise.
- Be honest and specific. Don't rubber-stamp everything."""


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

    # Apply debate responses
    for reviewer, response in debate_responses.items():
        for e in response.get("endorsements", []):
            title = e.get("finding_title", "")
            if title in index:
                findings[index[title]]["endorsements"].append(
                    {"reviewer": reviewer, "comment": e.get("comment", "")}
                )

        for c in response.get("challenges", []):
            title = c.get("finding_title", "")
            if title in index:
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
            if f.get("source") and f["source"] not in primary.get("co_authors", [primary["source"]]):
                primary.setdefault("co_authors", [primary["source"]]).append(f["source"])
            # Absorb endorsements and challenges from the duplicate
            primary["endorsements"].extend(f.get("endorsements", []))
            primary["challenges"].extend(f.get("challenges", []))
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
