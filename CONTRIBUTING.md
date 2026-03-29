# Contributing to NL2CMD

Thanks for your interest in contributing! Here's how you can help.

## Adding Rules (No Python Required)

The easiest way to contribute is by adding new translation rules. Rules are defined in YAML files in `nl2cmd/rules/`.

### Rule Format

```yaml
- intent: unique_intent_name
  patterns:
    - "natural language pattern with {slot}"
    - "alternative phrasing {slot}"
  slots:
    slot: { type: string, default: "value" }
  command: "shell command with {slot}"
  tags: [category, subcategory]
```

### Slot Types

| Type | Description | Example |
|------|-------------|---------|
| `string` | Any text | `{name}` |
| `filesize` | File sizes | `1gb` -> `1G` |
| `port` | Port numbers | `port 3000` -> `3000` |
| `path` | File/directory paths | `/var/log` |
| `package` | Package names | `nginx` |
| `duration` | Time durations | `7 days` -> `7` |
| `filename` | File names | `README.md` |
| `number` | Numeric values | `10` |

### Steps

1. Fork the repository
2. Add or edit a YAML file in `nl2cmd/rules/`
3. Run the tests: `pytest tests/test_rule_engine.py`
4. Submit a pull request

## Code Contributions

1. Fork and clone the repo
2. Install dev dependencies: `pip install -e ".[dev]"`
3. Create a feature branch: `git checkout -b feature/my-feature`
4. Make your changes
5. Run tests: `pytest`
6. Run linter: `ruff check nl2cmd/ tests/`
7. Submit a pull request

## What to Contribute

- **Rule packs** — new YAML rule files for additional command categories
- **Slot type parsers** — new slot types in `nl2cmd/utils.py`
- **Safety rules** — additional dangerous command patterns in `nl2cmd/safety.py`
- **Distro support** — package manager mappings in `nl2cmd/distro.py`
- **Tests** — more test coverage
- **Documentation** — usage examples, guides

## Guidelines

- Keep rules simple and focused on common use cases
- Prefer standard coreutils over third-party tools
- Never add rules that implicitly use `sudo`
- Test your patterns with both exact and fuzzy matching
- Follow existing code style (enforced by ruff)
