# Roadmap

## v0.1.0 (current)

- [x] 5 built-in reviewer personas (security, performance, readability, architecture, testing)
- [x] Multi-round adversarial debate with endorsements, challenges, and withdrawals
- [x] Consensus scoring and swarm summary
- [x] Custom persona support via YAML
- [x] Rich terminal, JSON, and Markdown output
- [x] OpenAI, Ollama, and OpenAI-compatible API support

## v0.2.0 (next)

- [ ] GitHub Action for PR reviews
- [ ] GitHub PR comment output format
- [ ] Configurable debate strategies (round-robin, tournament, free-for-all)
- [ ] Cost tracking and token usage reporting
- [ ] `--verbose` flag showing raw agent reasoning

## Future

- [ ] Streaming output during review and debate
- [ ] Agent memory across reviews (learn codebase patterns)
- [ ] Pre-built persona packs (react, django, go, rust, etc.)
- [ ] Web UI for browsing review results
- [ ] VS Code / IDE extension
- [ ] Support for Anthropic and Google APIs directly (not just OpenAI-compatible)
