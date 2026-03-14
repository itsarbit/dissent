# Contributing to Dissent

Thank you for your interest in contributing to Dissent! This guide will help you get started.

## Getting Started

1. Fork the repository and clone your fork:

   ```bash
   git clone https://github.com/<your-username>/dissent.git
   cd dissent
   ```

2. Install in editable mode with dev dependencies:

   ```bash
   pip install -e ".[dev]"
   ```

3. Install pre-commit hooks:

   ```bash
   pre-commit install
   ```

4. Create a branch for your change:

   ```bash
   git checkout -b my-feature
   ```

## Development Workflow

### Running Tests

```bash
pytest tests/
```

### Linting and Formatting

We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
ruff check .    # Lint
ruff format .   # Format
```

Pre-commit hooks run both automatically on commit.

### Code Style

- Follow PEP 8 conventions
- Type hints encouraged for function signatures
- Use absolute imports over relative imports

### Commit Messages

```
<type>(<scope>): <description>
```

Examples:
- `feat: add custom persona loading from YAML`
- `fix(debate): handle empty findings list`
- `docs: update quickstart guide`

Keep the subject line under 72 characters, use lowercase, imperative mood.

## Submitting a Pull Request

1. Make sure all tests pass and linting is clean
2. Use the same format for your PR title as commit messages (CI enforces this)
3. Write a clear PR description explaining what changed and why
4. Keep PRs focused on a single change

## Reporting Issues

Open an issue at [github.com/itsarbit/dissent/issues](https://github.com/itsarbit/dissent/issues) with:

- A clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
