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
    <a href="#quickstart">Quickstart</a> · <a href="examples/">Examples</a> · <a href="https://github.com/itsarbit/dissent/issues">Report a Bug</a>
  </p>
</p>

## What is Dissent?

Dissent spawns a swarm of AI reviewer agents, each with a different expertise (security, performance, readability, architecture, testing), and lets them review your code independently before debating each other's findings. The result is consensus-ranked insights that no single reviewer would catch alone.

Inspired by [MiroFish](https://github.com/666ghj/MiroFish), which applies swarm intelligence to predict real-world events by simulating thousands of interacting agents, Dissent brings the same principle to code review: **diverse perspectives + interaction = emergent intelligence**.

### How it works

1. **Independent review** - Each agent reviews the diff through their specialized lens
2. **Debate** - Agents see each other's findings and endorse, challenge, or build on them
3. **Consensus** - Findings are ranked by cross-agent agreement, with dissenting opinions preserved

```
$ dissent HEAD~1

Dissent  5 agents, 9 finding(s)

#1  HIGH  SQL Injection Vulnerability
    Endorsed by: Security, Performance, Readability, Architecture

#2  HIGH  Weak Password Hashing (MD5)
    Endorsed by: Performance, Readability, Architecture

#3  MEDIUM  N+1 Query Problem
    Challenged by Security: not a security issue unless it causes DoS

--- Swarm Summary ---
Swarm agrees on: SQL Injection, Weak Password Hashing
Swarm split on: N+1 Query Problem, Missing Input Validation
Emerged from debate: Lack of Error Handling
2 finding(s) withdrawn (agents changed their minds)
```

### Why Dissent?

- **Swarm intelligence**: Multiple specialized agents that interact, not just run independently
- **Adversarial debate**: Agents challenge each other's findings, reducing false positives
- **Emergent insights**: New findings surface only through agent interaction
- **Custom personas**: Define your own reviewer personas via YAML
- **Any LLM**: Works with OpenAI, Ollama, or any OpenAI-compatible API
- **Multiple outputs**: Rich terminal, JSON, or Markdown output

## Quickstart

### Install

```bash
pip install dissent
```

### Set up credentials

```bash
export OPENAI_API_KEY="your-key"
```

### Run

```bash
# Review the last commit
dissent HEAD~1

# Review staged changes
dissent --staged

# Review a commit range
dissent abc123..def456

# Pipe in a diff
git diff main | dissent -

# Use Ollama (local, no API key needed)
dissent --model llama3 --base-url http://localhost:11434/v1 HEAD~1

# Pick specific personas
dissent --personas security,performance HEAD~1

# Fewer debate rounds for speed
dissent --rounds 1 HEAD~1
```

## Custom Personas

Dissent ships with 5 built-in personas: `security`, `performance`, `readability`, `architecture`, and `testing`.

You can define your own by creating a `.dissent.yaml` in your project root (auto-loaded) or passing `--persona-file`:

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
    Be precise. Only flag real a11y violations.

hooks:
  name: React Hooks
  color: yellow
  prompt: |
    You are a React hooks expert reviewing code changes. Focus on:
    - Missing or incorrect dependency arrays
    - Stale closure bugs
    - Rules of hooks violations
    Be precise. Reference specific lines.
```

```bash
# Use custom personas
dissent --persona-file my_team.yaml HEAD~1
```

See [examples/](examples/) for ready-made persona files for React, Django, Go, and more.

## Configuration

### CLI Options

| Option | Env var | Default | Description |
|--------|---------|---------|-------------|
| `--model` | `DISSENT_MODEL` | `gpt-4o` | LLM model to use |
| `--base-url` | `DISSENT_BASE_URL` | - | API base URL (for Ollama, etc.) |
| `--api-key` | `OPENAI_API_KEY` | - | API key |
| `--rounds` | - | `2` | Number of debate rounds |
| `--personas` | - | all | Comma-separated persona list |
| `--persona-file` | - | `.dissent.yaml` | Custom persona YAML file |
| `--output` | - | `terminal` | Output format: `terminal`, `json`, `markdown` |

### Using with Ollama

```bash
# Start Ollama
ollama serve

# Pull a model
ollama pull llama3

# Run dissent
export DISSENT_MODEL=llama3
export DISSENT_BASE_URL=http://localhost:11434/v1
dissent HEAD~1
```

## How the Swarm Works

Dissent's review process mirrors [MiroFish](https://github.com/666ghj/MiroFish)'s approach to swarm intelligence:

**Round 1 - Independent review**: Each agent reviews the diff in isolation, producing findings from their specialized perspective. All agents run in parallel.

**Round 2+ - Debate**: Each agent sees every other agent's findings and responds with:
- **Endorsements** - "I agree this is a real issue"
- **Challenges** - "I disagree, here's why"
- **New findings** - "Seeing your findings made me notice something else"
- **Withdrawals** - "You convinced me, I'm dropping my finding"

**Consensus scoring**: Each finding is scored based on `(1 + endorsements - challenges) * severity_weight`. Findings with broad cross-domain agreement rise to the top. Findings that get challenged heavily sink. Withdrawn findings are removed entirely.

**Swarm summary**: The final output categorizes findings into what the swarm agrees on, what it's split on, and what emerged only through debate.

## Development

```bash
git clone https://github.com/itsarbit/dissent.git
cd dissent
pip install -e ".[dev]"
pre-commit install
pytest tests/
```

Linting and formatting:

```bash
ruff check .
ruff format .
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Inspired By

- [MiroFish](https://github.com/666ghj/MiroFish) - A swarm intelligence engine that predicts real-world events by simulating thousands of interacting AI agents. Dissent applies the same principle (diverse agents + interaction = emergent intelligence) to code review.

## License

MIT. See [LICENSE](LICENSE).
