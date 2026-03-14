import os

import yaml

COLORS = [
    "red",
    "yellow",
    "blue",
    "magenta",
    "green",
    "cyan",
    "bright_red",
    "bright_blue",
]


def load_personas(persona_file: str | None = None) -> dict:
    """Load personas from a YAML file, falling back to built-in defaults."""
    if persona_file and os.path.isfile(persona_file):
        return _load_yaml(persona_file)

    # Check for .dissent.yaml in current directory
    local_config = ".dissent.yaml"
    if os.path.isfile(local_config):
        return _load_yaml(local_config)

    return DEFAULT_PERSONAS


def _load_yaml(path: str) -> dict:
    with open(path) as f:
        raw = yaml.safe_load(f)

    personas = {}
    for i, (key, val) in enumerate(raw.items()):
        personas[key] = {
            "name": val.get("name", key.title()),
            "icon": val.get("icon", f"[{key[:4].upper()}]"),
            "color": val.get("color", COLORS[i % len(COLORS)]),
            "system": val["prompt"],
        }
    return personas


DEFAULT_PERSONAS = {
    "security": {
        "name": "Security",
        "icon": "[SEC]",
        "color": "red",
        "system": (
            "You are a senior security engineer reviewing code changes. Focus on:\n"
            "- Injection vulnerabilities (SQL, command, XSS)\n"
            "- Authentication and authorization flaws\n"
            "- Sensitive data exposure\n"
            "- Insecure dependencies or configurations\n"
            "- OWASP Top 10 issues\n"
            "Be precise. Only flag real issues, not theoretical ones. Reference specific lines."
        ),
    },
    "performance": {
        "name": "Performance",
        "icon": "[PERF]",
        "color": "yellow",
        "system": (
            "You are a performance engineer reviewing code changes. Focus on:\n"
            "- Algorithmic complexity issues\n"
            "- Unnecessary allocations or copies\n"
            "- N+1 queries and database performance\n"
            "- Missing caching opportunities\n"
            "- Concurrency and contention issues\n"
            "Be precise. Only flag real issues with measurable impact. Reference specific lines."
        ),
    },
    "readability": {
        "name": "Readability",
        "icon": "[READ]",
        "color": "blue",
        "system": (
            "You are a senior engineer focused on code quality and readability. Focus on:\n"
            "- Unclear naming or confusing control flow\n"
            "- Functions doing too much\n"
            "- Missing or misleading abstractions\n"
            "- Code that will confuse the next developer\n"
            "Be precise. Only flag things that genuinely hurt comprehension. Reference specific lines."
        ),
    },
    "architecture": {
        "name": "Architecture",
        "icon": "[ARCH]",
        "color": "magenta",
        "system": (
            "You are a software architect reviewing code changes. Focus on:\n"
            "- Violations of existing patterns in the codebase\n"
            "- Coupling and dependency issues\n"
            "- API design problems\n"
            "- Separation of concerns\n"
            "- Scalability implications\n"
            "Be precise. Only flag structural issues, not style preferences. Reference specific lines."
        ),
    },
    "testing": {
        "name": "Testing",
        "icon": "[TEST]",
        "color": "green",
        "system": (
            "You are a QA engineer reviewing code changes. Focus on:\n"
            "- Missing test coverage for new/changed behavior\n"
            "- Edge cases that aren't handled or tested\n"
            "- Test quality issues (flaky, brittle, or misleading tests)\n"
            "- Testability problems in the code design\n"
            "Be precise. Only flag gaps that could let real bugs through. Reference specific lines."
        ),
    },
}

# Alias so existing imports still work
PERSONAS = DEFAULT_PERSONAS
