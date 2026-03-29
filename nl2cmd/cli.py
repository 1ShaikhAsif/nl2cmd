"""CLI entry point for nl2cmd."""

from __future__ import annotations

import shlex
import subprocess
import sys

import click
from rich.console import Console
from rich.text import Text

from nl2cmd import __version__
from nl2cmd.engine.hybrid import translate
from nl2cmd.history import HistoryEntry, log_translation, search_history
from nl2cmd.safety import check_command
from nl2cmd.utils import is_tty

console = Console(stderr=True)

PROVIDER_MODELS = {
    "anthropic": ["claude-sonnet-4-20250514", "claude-haiku-4-5-20251001", "claude-opus-4-20250514"],
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o3-mini"],
    "gemini": ["gemini-2.0-flash", "gemini-2.5-pro", "gemini-2.5-flash"],
    "ollama": ["llama3.2", "llama3.1", "mistral", "phi3", "qwen2.5", "gemma2", "codellama", "deepseek-r1"],
    "groq": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"],
}


def _print_command(command: str, source: str) -> None:
    if not is_tty():
        print(command)
        return
    console.print()
    label = Text(f"  [{source}] ", style="dim")
    cmd_text = Text(command, style="bold green")
    console.print(label, cmd_text, sep="")
    console.print()


def _print_danger_warning(warnings: list[str]) -> None:
    console.print()
    console.print("  [bold red]DANGEROUS COMMAND[/bold red]", highlight=False)
    for warning in warnings:
        console.print(f"  [red]  {warning}[/red]", highlight=False)
    console.print()


def _confirm_execution(dangerous: bool = False) -> bool:
    if dangerous:
        try:
            response = console.input('  Type [bold]"confirm"[/bold] to proceed: ')
            return response.strip().lower() == "confirm"
        except (EOFError, KeyboardInterrupt):
            return False
    else:
        try:
            response = console.input("  Run it? [y/N] ")
            return response.strip().lower() in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            return False


def _execute_command(command: str) -> int:
    try:
        args = shlex.split(command)
    except ValueError:
        result = subprocess.run(command, shell=True, executable="/bin/bash")
        return result.returncode

    if "|" in command or "&&" in command or "||" in command or "$(" in command or ";" in command:
        result = subprocess.run(command, shell=True, executable="/bin/bash")
        return result.returncode

    result = subprocess.run(args)
    return result.returncode


# ---------------------------------------------------------------------------
# CLI Group
# ---------------------------------------------------------------------------

class NL2CMDGroup(click.Group):
    """Custom group that routes unknown subcommands to translate."""

    def parse_args(self, ctx, args):
        if args and args[0] in ("--version", "-v", "--help", "-h"):
            return super().parse_args(ctx, args)
        if args and args[0] in self.commands:
            return super().parse_args(ctx, args)
        args = ["translate"] + list(args)
        return super().parse_args(ctx, args)


@click.group(cls=NL2CMDGroup, invoke_without_command=True, context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "-v", "--version", prog_name="nl2cmd")
@click.pass_context
def main(ctx):
    """NL2CMD — Type what you want. Get the command. Run it.

    \b
    Usage:
      nl2cmd show open ports
      nl2cmd find large files over 1gb
      nl2cmd --dry disk usage by folder sorted by size
      nl2cmd --explain compress logs older than 7 days
      nl2cmd --offline undo last commit
      nl2cmd -p ollama -M phi3 find zombie processes
    \b
    Config (set once, use forever):
      nl2cmd config set provider gemini
      nl2cmd config set gemini_api_key YOUR_KEY
      nl2cmd config show
      nl2cmd config providers
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# ---------------------------------------------------------------------------
# translate (default command — hidden, invoked automatically)
# ---------------------------------------------------------------------------

@main.command(name="translate", hidden=True)
@click.argument("query", nargs=-1, required=False)
@click.option("--offline", "-o", is_flag=True, help="Rules only, no AI calls.")
@click.option("--provider", "-p", type=click.Choice(["anthropic", "openai", "gemini", "ollama", "groq"], case_sensitive=False), default=None, help="Override LLM provider.")
@click.option("--model", "-M", default=None, help="Override model (e.g. gpt-4o, phi3).")
@click.option("--explain", "-e", is_flag=True, help="Explain the command flag by flag.")
@click.option("--dry", "-d", is_flag=True, help="Output raw command only (pipe-friendly).")
@click.option("--history", "-H", is_flag=True, help="Search translation history.")
def translate_cmd(query, offline, provider, model, explain, dry, history):
    """Translate natural language to a shell command."""
    from nl2cmd import config

    # Handle history search
    if history:
        search_term = " ".join(query) if query else ""
        entries = search_history(search_term)
        if not entries:
            console.print("  No history entries found.", style="dim")
            return
        for entry in entries:
            ts = entry.get("timestamp", "")[:19]
            q = entry.get("query", "")
            cmd = entry.get("command", "")
            src = entry.get("mode", "?")
            console.print(f"  [dim]{ts}[/dim]  [cyan]{q}[/cyan]")
            console.print(f"           [green]{cmd}[/green]  [dim]({src})[/dim]")
        return

    if not query:
        click.echo("Usage: nl2cmd <description>")
        click.echo("Try: nl2cmd --help")
        return

    user_input = " ".join(query)

    # Load defaults from config (flags override config)
    cfg = config.load()
    if not provider:
        provider = cfg.get("provider")
    if not model:
        model = cfg.get("model")

    # Translate
    try:
        result = translate(user_input, offline=offline, provider=provider, model=model)
    except ValueError as e:
        console.print(f"  [yellow]{e}[/yellow]")
        sys.exit(1)
    except (EnvironmentError, ImportError) as e:
        console.print(f"  [red]{e}[/red]")
        sys.exit(1)

    command = result.command

    # Dry run
    if dry:
        print(command)
        log_translation(HistoryEntry(
            query=user_input, command=command, mode=result.source,
            executed=False, rule_intent=result.rule_intent,
        ))
        return

    safety = check_command(command)
    _print_command(command, result.source)

    # Explain mode
    if explain:
        try:
            from nl2cmd.engine.ai_engine import explain as ai_explain
            explanation = ai_explain(command, provider_name=provider, model=model)
            console.print("  [bold]Explanation:[/bold]")
            for line in explanation.splitlines():
                console.print(f"  {line}")
            console.print()
        except (EnvironmentError, ImportError) as e:
            console.print(f"  [yellow]Cannot explain (AI unavailable): {e}[/yellow]")

    # Non-TTY: log and exit
    if not is_tty():
        log_translation(HistoryEntry(
            query=user_input, command=command, mode=result.source,
            executed=False, rule_intent=result.rule_intent,
        ))
        return

    if safety.is_dangerous:
        _print_danger_warning(safety.warnings)

    executed = False
    if _confirm_execution(dangerous=safety.is_dangerous):
        exit_code = _execute_command(command)
        executed = True
        if exit_code != 0:
            console.print(f"  [yellow]Command exited with code {exit_code}[/yellow]")

    log_translation(HistoryEntry(
        query=user_input, command=command, mode=result.source,
        executed=executed, rule_intent=result.rule_intent,
    ))


# ---------------------------------------------------------------------------
# config subcommand group
# ---------------------------------------------------------------------------

@main.group()
def config():
    """Manage nl2cmd configuration.

    \b
    Examples:
      nl2cmd config set provider gemini
      nl2cmd config set gemini_api_key YOUR_KEY
      nl2cmd config show
      nl2cmd config providers
    """


@config.command(name="set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """Set a config value.

    \b
    Keys:
      provider          Default LLM provider
      model             Default model name
      anthropic_api_key Anthropic API key
      openai_api_key    OpenAI API key
      gemini_api_key    Google Gemini API key
      groq_api_key      Groq API key
      ollama_host       Ollama server URL
    """
    from nl2cmd import config as cfg

    try:
        cfg.set_value(key, value)
        display = value if "api_key" not in key else value[:8] + "..." + value[-4:]
        console.print(f"  [green]Set {key} = {display}[/green]")
        console.print(f"  [dim]Saved to {cfg.CONFIG_FILE}[/dim]")
    except ValueError as e:
        console.print(f"  [red]{e}[/red]")
        sys.exit(1)


@config.command(name="get")
@click.argument("key")
def config_get(key: str):
    """Get a config value."""
    from nl2cmd import config as cfg

    value = cfg.get(key)
    if value is None:
        console.print(f"  [dim]{key} is not set[/dim]")
    else:
        display = value if "api_key" not in key else value[:8] + "..." + value[-4:]
        console.print(f"  {key} = {display}")


@config.command(name="show")
def config_show():
    """Show all config values."""
    from nl2cmd import config as cfg

    data = cfg.load()
    if not data:
        console.print("  [dim]No config set. Run: nl2cmd config set <key> <value>[/dim]")
        console.print()
        console.print("  [bold]Available keys:[/bold]")
        for k, desc in cfg.CONFIG_KEYS.items():
            console.print(f"    [cyan]{k:<22}[/cyan] {desc}")
        return

    console.print(f"\n  [bold]Config[/bold] [dim]({cfg.CONFIG_FILE})[/dim]\n")
    for k, v in sorted(data.items()):
        display = v if "api_key" not in k else v[:8] + "..." + v[-4:]
        console.print(f"  [cyan]{k:<22}[/cyan] {display}")
    console.print()

    unset = [k for k in cfg.CONFIG_KEYS if k not in data]
    if unset:
        console.print("  [dim]Unset:[/dim]")
        for k in unset:
            console.print(f"    [dim]{k}[/dim]")
        console.print()


@config.command(name="delete")
@click.argument("key")
def config_delete(key: str):
    """Delete a config value."""
    from nl2cmd import config as cfg

    if cfg.delete(key):
        console.print(f"  [green]Deleted {key}[/green]")
    else:
        console.print(f"  [dim]{key} was not set[/dim]")


@config.command(name="reset")
def config_reset():
    """Reset all config to defaults."""
    from nl2cmd import config as cfg

    cfg.reset()
    console.print("  [green]Config reset. All values cleared.[/green]")


@config.command(name="path")
def config_path():
    """Show config file path."""
    from nl2cmd import config as cfg

    console.print(f"  {cfg.CONFIG_FILE}")


@config.command(name="providers")
def config_providers():
    """List available providers and models."""
    console.print("\n  [bold]Available Providers & Models:[/bold]\n")
    for name in sorted(PROVIDER_MODELS.keys()):
        models = PROVIDER_MODELS[name]
        console.print(f"  [cyan]{name}[/cyan]")
        for m in models:
            console.print(f"    - {m}")
    console.print()
    console.print("  [dim]Set your default: nl2cmd config set provider <name>[/dim]")
    console.print("  [dim]Ollama runs locally (free). Others need API keys.[/dim]\n")


if __name__ == "__main__":
    main()
