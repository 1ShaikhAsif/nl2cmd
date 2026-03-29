# NL2CMD

**Natural Language to Shell Commands**

Type what you want. Get the command. Run it.

NL2CMD is an open-source CLI tool that translates plain English into executable Linux shell commands. It tries built-in rules first (instant, offline), and falls back to AI if no rule matches — with support for 5 LLM providers.

## Installation

```bash
pip install nl2cmd
```

Install with your preferred LLM provider:

```bash
pip install nl2cmd[anthropic]   # Claude (Anthropic)
pip install nl2cmd[openai]      # GPT-4o (OpenAI)
pip install nl2cmd[gemini]      # Gemini (Google)
pip install nl2cmd[ollama]      # Local models (Llama, Mistral, Phi, etc.)
pip install nl2cmd[groq]        # Fast cloud inference (Llama, Mixtral)
pip install nl2cmd[all]         # All providers
```

Or install from source:

```bash
git clone https://github.com/10x-analysts/nl2cmd.git
cd nl2cmd
pip install -e ".[dev]"
```

## Quick Start

```bash
# One-time setup
nl2cmd config set provider gemini
nl2cmd config set gemini_api_key YOUR_KEY

# Now just use it — no flags needed
nl2cmd show open ports
nl2cmd find large files over 1gb
nl2cmd kill process on port 3000
nl2cmd disk usage sorted by size
nl2cmd compress logs older than 7 days
```

## Examples

```bash
$ nl2cmd find large files over 1gb
  [rule] find . -size +1G
  Run it? [y/N]

$ nl2cmd -d kill process on port 3000
fuser -k 3000/tcp

$ nl2cmd -o show open ports
  [rule] ss -tulnp
  Run it? [y/N]

$ nl2cmd delete everything in home folder
  [ai] rm -rf ~/*
  DANGEROUS COMMAND
    Recursive forced delete — can destroy entire directory trees
  Type "confirm" to proceed:
```

## How It Works

```
nl2cmd <your query>
        │
        ▼
  ┌─────────────┐
  │ Rule Engine  │  80+ built-in rules (instant, offline)
  └──────┬──────┘
    Match found?
    ├── YES → return command
    └── NO ──┐
             ▼
      ┌─────────────┐
      │ AI Provider  │  Falls back to your configured LLM
      └─────────────┘
             │
             ▼
       return command → safety check → confirm → execute
```

## CLI Reference

```
nl2cmd <query>                   # just works (config handles the rest)
  -o, --offline                  # rules only, no AI calls
  -d, --dry                      # pipe-friendly output, no prompt
  -e, --explain                  # explain the command flag by flag
  -H, --history                  # search translation history
  -p, --provider <name>          # one-off provider override
  -M, --model <name>             # one-off model override
  -v, --version                  # show version
  -h, --help                     # show help

nl2cmd config set <key> <value>  # save a setting
nl2cmd config show               # view all settings
nl2cmd config get <key>          # get a single value
nl2cmd config delete <key>       # remove a value
nl2cmd config reset              # clear all config
nl2cmd config providers          # list all providers and models
nl2cmd config path               # show config file location
```

## Features

- **Multi-LLM support** — Anthropic, OpenAI, Gemini, Ollama (local), Groq
- **80+ built-in rules** covering file ops, networking, processes, git, docker, systemd, and more
- **Fuzzy matching** for typo tolerance
- **Safety checks** for dangerous commands (rm -rf, dd, mkfs, chmod 777, fork bombs)
- **OS-aware** package manager detection (apt, dnf, pacman, zypper, apk)
- **Persistent config** — set once, use forever
- **History** with search
- **Pipe-friendly** output in non-TTY mode

## Configuration

### Setup (set once, use forever)

```bash
nl2cmd config set provider gemini
nl2cmd config set gemini_api_key YOUR_KEY
nl2cmd config set model gemini-2.5-pro   # optional
```

### Config Commands

```bash
nl2cmd config show              # View all settings
nl2cmd config get provider      # Get a single value
nl2cmd config set <key> <value> # Set a value
nl2cmd config delete <key>      # Remove a value
nl2cmd config reset             # Clear everything
nl2cmd config path              # Show config file location
nl2cmd config providers         # List all providers and models
```

### Config Keys

| Key | Description |
|-----|-------------|
| `provider` | Default LLM provider (anthropic, openai, gemini, ollama, groq) |
| `model` | Default model name (e.g. gpt-4o, llama3.2) |
| `anthropic_api_key` | Anthropic API key |
| `openai_api_key` | OpenAI API key |
| `gemini_api_key` | Google Gemini API key |
| `groq_api_key` | Groq API key |
| `ollama_host` | Ollama server URL (default: http://localhost:11434) |

Config is stored in `~/.nl2cmd/config.yaml`. Config values take precedence over environment variables.

## Providers & Models

| Provider | Models | Install |
|----------|--------|---------|
| **Anthropic** | claude-sonnet-4, claude-opus-4, claude-haiku-4.5 | `pip install nl2cmd[anthropic]` |
| **OpenAI** | gpt-4o, gpt-4o-mini, gpt-4-turbo, o3-mini | `pip install nl2cmd[openai]` |
| **Gemini** | gemini-2.0-flash, gemini-2.5-pro, gemini-2.5-flash | `pip install nl2cmd[gemini]` |
| **Ollama** | llama3.2, mistral, phi3, qwen2.5, gemma2, codellama, deepseek-r1 | `pip install nl2cmd[ollama]` |
| **Groq** | llama-3.3-70b, llama-3.1-8b, mixtral-8x7b, gemma2-9b | `pip install nl2cmd[groq]` |

Run `nl2cmd config providers` to see the full list.

### Custom Rules

Add custom YAML rules to `~/.nl2cmd/rules/`:

```yaml
- intent: my_custom_command
  patterns:
    - "deploy to {env}"
    - "push to {env}"
  slots:
    env: { type: string, default: "staging" }
  command: "./deploy.sh {env}"
  tags: [deploy, custom]
```

## Rule Categories

| Category | Examples |
|----------|----------|
| File Operations | find files, count files, permissions |
| Process Management | list/kill processes, top, process tree |
| Network | ports, IP addresses, DNS, connections |
| Disk & System | disk usage, memory, CPU info |
| Package Management | install, remove, search packages |
| Git | status, log, branch, stash, blame |
| Docker | containers, images, compose, logs |
| Text Processing | grep, sort, wc, head, tail |
| User Management | users, groups, logins |
| Systemd | services, journalctl |
| Archives | tar, gzip, zip |

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check nl2cmd/ tests/
```

## License

MIT License. See [LICENSE](LICENSE) for details.
