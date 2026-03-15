<p align="center">
  <h1 align="center">Dissent</h1>
  <p align="center">
    Swarm intelligence for code review - diverse expert agents that debate your diffs.
  </p>
  <p align="center">
    <a href="https://github.com/itsarbit/dissent/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/itsarbit/dissent/actions/workflows/ci.yml/badge.svg"></a>
    <a href="https://pypi.org/project/dissent/"><img alt="PyPI" src="https://img.shields.io/pypi/v/dissent.svg?cacheSeconds=300"></a>
    <a href="https://www.python.org/downloads/"><img alt="Python" src="https://img.shields.io/pypi/pyversions/dissent.svg?cacheSeconds=300"></a>
    <a href="https://github.com/itsarbit/dissent/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
    <a href="https://github.com/itsarbit/dissent/stargazers"><img alt="GitHub Stars" src="https://img.shields.io/github/stars/itsarbit/dissent.svg?style=social"></a>
    <a href="https://github.com/itsarbit/dissent/issues"><img alt="GitHub Issues" src="https://img.shields.io/github/issues/itsarbit/dissent.svg"></a>
    <a href="https://github.com/itsarbit/dissent/pulls"><img alt="PRs Welcome" src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg"></a>
  </p>
  <p align="center">
    <a href="#quickstart">Quickstart</a> · <a href="#github-action">GitHub Action</a> · <a href="#custom-personas">Custom Personas</a> · <a href="https://github.com/itsarbit/dissent/issues">Report a Bug</a>
  </p>
</p>

## What is Dissent?

Dissent spawns a swarm of AI reviewer agents - each with a different expertise (security, performance, readability, architecture, testing) - and lets them review your code independently, then debate each other's findings. The result is consensus-ranked insights that no single reviewer would catch alone.

Inspired by [MiroFish](https://github.com/666ghj/MiroFish), which applies swarm intelligence to predict real-world events by simulating thousands of interacting agents, Dissent brings the same principle to code review: **diverse perspectives + interaction = emergent intelligence**.

### How it works

1. **Independent review** - Each agent reviews the diff through their specialized lens, in parallel
2. **Debate** - Agents see each other's findings and endorse, challenge, or surface new issues
3. **Consensus** - Findings are ranked by cross-agent agreement, with dissenting opinions preserved

### Why Dissent?

- **Swarm intelligence** - Agents interact and build on each other, not just run independently
- **Real debate** - Agents challenge false positives and endorse findings across domains
- **Emergent insights** - Issues surface only because agents saw each other's work
- **GitHub bot** - Post inline PR review comments directly on your diffs
- **Custom personas** - Define your own reviewer personas for any stack via YAML
- **Any LLM** - Works with OpenAI, Ollama, or any OpenAI-compatible API

## Quickstart

```bash
pip install dissent
export OPENAI_API_KEY="your-key"
```

### Review local diffs

```bash
# Last commit
dissent HEAD~1

# Staged changes
dissent --staged

# Commit range
dissent abc123..def456

# Pipe in a diff
git diff main | dissent -

# Use Ollama (fully local, no API key needed)
dissent --model llama3 --base-url http://localhost:11434/v1 HEAD~1
```

### Review a GitHub PR

```bash
dissent-pr https://github.com/owner/repo/pull/123

# Dry run - see results in terminal without posting
dissent-pr https://github.com/owner/repo/pull/123 --dry-run
```

`dissent-pr` fetches the PR diff, runs the swarm review, and posts inline comments directly on the PR at the relevant file and line.

## GitHub Action

Add Dissent to any repo with 3 lines. On every pull request, the swarm reviews the diff and posts inline comments:

```yaml
# .github/workflows/dissent.yml
name: Dissent Review

on:
  pull_request:

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: itsarbit/dissent@v1
        with:
          api-key: ${{ secrets.OPENAI_API_KEY }}
```

### Action inputs

| Input | Default | Description |
|-------|---------|-------------|
| `api-key` | required | OpenAI API key (or compatible provider) |
| `model` | `gpt-4o` | LLM model to use |
| `base-url` | - | API base URL (for Ollama, vLLM, etc.) |
| `rounds` | `2` | Number of debate rounds |
| `personas` | all | Comma-separated persona list |
| `persona-file` | - | Path to custom persona YAML file |
| `github-token` | `GITHUB_TOKEN` | Token for posting review comments |

## Custom Personas

Dissent ships with 6 built-in personas: `security`, `performance`, `readability`, `architecture`, `testing`, and `correctness`.

Define your own by creating a `.dissent.yaml` in your project root (auto-loaded) or by passing `--persona-file`:

```yaml
# .dissent.yaml
accessibility:
  name: Accessibility
  color: cyan
  prompt: |
    You are an accessibility expert reviewing code changes. Focus on:
    - Missing ARIA attributes and roles
    - Keyboard navigation issues
    - Screen reader compatibility
    Be precise. Only flag real violations. Reference specific lines.

react_hooks:
  name: React Hooks
  color: yellow
  prompt: |
    You are a React hooks expert reviewing code changes. Focus on:
    - Missing or incorrect dependency arrays in useEffect/useMemo/useCallback
    - Stale closure bugs
    - Rules of hooks violations
    Be precise. Reference specific lines.
```

```bash
dissent --persona-file .dissent.yaml HEAD~1
```

See [examples/react_team.yaml](examples/react_team.yaml) for a ready-made persona file for React projects.

## Configuration

### `dissent` options

| Option | Env var | Default | Description |
|--------|---------|---------|-------------|
| `--model` | `DISSENT_MODEL` | `gpt-4o` | LLM model |
| `--base-url` | `DISSENT_BASE_URL` | - | API base URL |
| `--api-key` | `OPENAI_API_KEY` | - | API key |
| `--rounds` | - | `2` | Debate rounds |
| `--personas` | - | all | Comma-separated persona list |
| `--persona-file` | - | `.dissent.yaml` | Custom persona YAML |
| `--output` | - | `terminal` | `terminal`, `json`, `markdown` |

### `dissent-pr` options

| Option | Default | Description |
|--------|---------|-------------|
| `--model` | `gpt-4o` | LLM model |
| `--rounds` | `2` | Debate rounds |
| `--personas` | all | Comma-separated persona list |
| `--dry-run` | false | Print results to terminal, don't post comments |

### Ollama (fully local)

```bash
ollama pull llama3

export DISSENT_MODEL=llama3
export DISSENT_BASE_URL=http://localhost:11434/v1

dissent HEAD~1
```

## How the Swarm Works

Dissent's review process mirrors [MiroFish](https://github.com/666ghj/MiroFish)'s approach to swarm intelligence:

**Round 1 - Independent review**: Each agent reviews the diff in isolation through their specialized lens. All agents run in parallel.

**Round 2+ - Debate**: Each agent sees every other agent's findings and responds with:
- **Endorsements** - "I agree, this is a real issue"
- **Challenges** - "I disagree, and here's why"
- **New findings** - "Seeing your findings made me notice something I missed"
- **Withdrawals** - "You convinced me, I'm dropping this finding"

**Consensus scoring**: Each finding is scored as `(1 + endorsements - challenges) * severity_weight`. Cross-domain agreement pushes findings to the top. Heavy challenges bury them. Withdrawn findings are removed.

**Swarm summary**: The final output shows what the swarm agrees on, what it's split on, and what emerged only through debate.

## Reading the Output

Each finding in the terminal output (and as a GitHub inline comment) looks like this:

```
╭─────────── #1  HIGH  SQL Injection in query builder ───────────╮
│ src/db.py:42                                                   │
│ User input is concatenated directly into a raw SQL string.     │
│                                                                │
│ Suggestion: Use parameterized queries or an ORM.               │
│                                                                │
│ Endorsed by: Performance, Architecture                         │
│ Challenged by Testing: this path is unreachable in production  │
│                                                                │
│ Found by Security  |  Consensus score: 6                       │
╰────────────────────────────────────────────────────────────────╯
```

**Consensus score** is calculated as:

```
(1 + endorsements - challenges) × severity_weight
```

Where `severity_weight` is `high=3`, `medium=2`, `low=1`. A finding endorsed by 2 agents with no challenges gets a score of `(1 + 2 - 0) × 3 = 9`. A finding that gets challenged twice scores `(1 + 0 - 2) × 3 = -3` and is buried at the bottom. Findings are sorted by score, so the most cross-domain-agreed issues always surface first.

**Endorsements** mean another agent - from a different domain - read the finding and confirmed it's a genuine issue. A security finding endorsed by performance and architecture carries more weight than one agent's opinion alone.

**Challenges** mean an agent pushed back with a reason. Challenges don't disqualify a finding - they reduce its score and are shown inline so you can read both sides and decide.

**Withdrawn** means the original agent retracted the finding after hearing the debate. Withdrawn findings are removed from the main list but counted in the swarm summary.

**Swarm summary categories** at the bottom of the output:

| Category | Meaning |
|----------|---------|
| **Swarm agrees on** | Endorsed by 2+ agents, no challenges - high confidence |
| **Swarm split on** | Both endorsed and challenged - read the debate, use your judgement |
| **Emerged from debate** | Not found in round 1 - only surfaced because an agent saw another's finding |

## Development

```bash
git clone https://github.com/itsarbit/dissent.git
cd dissent
pip install -e ".[dev]"
pre-commit install
pytest tests/
```

```bash
ruff check .   # lint
ruff format .  # format
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Inspired By

[MiroFish](https://github.com/666ghj/MiroFish) - a swarm intelligence engine that predicts real-world events by simulating thousands of interacting AI agents with distinct behavioral profiles and memory. Built by an undergraduate student in 10 days, it hit the top of GitHub trending with 18k stars. Dissent applies the same core idea - diverse agents that interact and converge - to code review.

## License

MIT. See [LICENSE](LICENSE).
