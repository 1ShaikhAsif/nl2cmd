"""Offline rule engine — pattern matching with YAML-defined rules."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from thefuzz import fuzz

from nl2cmd.utils import SLOT_PARSERS

# Bundled rules ship with the package
BUNDLED_RULES_DIR = Path(__file__).parent.parent / "rules"
# User-defined rules override/extend bundled ones
USER_RULES_DIR = Path.home() / ".nl2cmd" / "rules"

# Minimum fuzzy match score to consider a pattern a match
FUZZY_THRESHOLD = 65


@dataclass
class SlotDef:
    """Definition of a slot (placeholder) in a rule pattern."""

    name: str
    type: str = "string"
    default: str | None = None


@dataclass
class Rule:
    """A single translation rule loaded from YAML."""

    intent: str
    patterns: list[str]
    command: str
    slots: dict[str, SlotDef] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


@dataclass
class MatchResult:
    """Result of matching user input against rules."""

    matched: bool
    command: str = ""
    rule: Rule | None = None
    score: float = 0.0
    slot_values: dict[str, str] = field(default_factory=dict)


def _parse_slot_defs(raw: dict[str, Any] | None) -> dict[str, SlotDef]:
    """Parse slot definitions from YAML."""
    if not raw:
        return {}
    slots = {}
    for name, config in raw.items():
        if isinstance(config, dict):
            slots[name] = SlotDef(
                name=name,
                type=config.get("type", "string"),
                default=config.get("default"),
            )
        else:
            slots[name] = SlotDef(name=name, type="string", default=str(config))
    return slots


def load_rules(extra_dirs: list[Path] | None = None) -> list[Rule]:
    """Load all rules from bundled and user directories.

    User rules take precedence (loaded last). Additional directories
    can be provided for testing.
    """
    dirs = [BUNDLED_RULES_DIR, USER_RULES_DIR]
    if extra_dirs:
        dirs.extend(extra_dirs)

    rules: list[Rule] = []
    seen_intents: set[str] = set()

    # Load in order; later dirs override earlier ones
    all_rule_dicts: list[tuple[str, dict]] = []
    for rule_dir in dirs:
        if not rule_dir.is_dir():
            continue
        for yaml_file in sorted(rule_dir.glob("*.yaml")):
            try:
                data = yaml.safe_load(yaml_file.read_text())
            except (yaml.YAMLError, OSError):
                continue
            if not isinstance(data, list):
                continue
            for entry in data:
                if isinstance(entry, dict) and "intent" in entry:
                    all_rule_dicts.append((entry["intent"], entry))

    # Deduplicate by intent (last one wins)
    intent_map: dict[str, dict] = {}
    for intent, entry in all_rule_dicts:
        intent_map[intent] = entry

    for entry in intent_map.values():
        rules.append(Rule(
            intent=entry["intent"],
            patterns=entry.get("patterns", []),
            command=entry.get("command", ""),
            slots=_parse_slot_defs(entry.get("slots")),
            tags=entry.get("tags", []),
        ))

    return rules


def _pattern_to_regex(pattern: str, slots: dict[str, SlotDef]) -> re.Pattern:
    """Convert a rule pattern with {slot} placeholders to a regex."""
    # Escape regex special chars but preserve {slot} placeholders
    parts = re.split(r"(\{[^}]+\})", pattern)
    regex_parts = []
    for part in parts:
        if part.startswith("{") and part.endswith("}"):
            slot_name = part[1:-1]
            # Named capture group for the slot
            regex_parts.append(f"(?P<{slot_name}>.+?)")
        else:
            # Escape literal text, but allow flexible whitespace
            escaped = re.escape(part)
            escaped = escaped.replace(r"\ ", r"\s+")
            regex_parts.append(escaped)
    return re.compile("^" + "".join(regex_parts) + "$", re.IGNORECASE)


def _try_regex_match(
    user_input: str, rule: Rule
) -> MatchResult | None:
    """Try to match user input against a rule's patterns using regex."""
    for pattern in rule.patterns:
        regex = _pattern_to_regex(pattern, rule.slots)
        match = regex.match(user_input.strip())
        if match:
            slot_values = {}
            for slot_name, slot_def in rule.slots.items():
                raw_value = match.group(slot_name) if slot_name in match.groupdict() else None
                if raw_value:
                    parser = SLOT_PARSERS.get(slot_def.type, lambda x: x)
                    slot_values[slot_name] = parser(raw_value)
                elif slot_def.default:
                    slot_values[slot_name] = slot_def.default
            return MatchResult(
                matched=True,
                command=rule.command.format(**slot_values) if slot_values else rule.command,
                rule=rule,
                score=100.0,
                slot_values=slot_values,
            )
    return None


def _try_fuzzy_match(
    user_input: str, rule: Rule
) -> MatchResult | None:
    """Try to match user input against a rule's patterns using fuzzy matching."""
    best_score = 0.0
    user_lower = user_input.strip().lower()

    for pattern in rule.patterns:
        # Strip slot placeholders for fuzzy comparison
        clean_pattern = re.sub(r"\{[^}]+\}", "", pattern).strip().lower()
        # Use token_set_ratio for flexible word-order matching
        score = fuzz.token_set_ratio(user_lower, clean_pattern)
        best_score = max(best_score, score)

    if best_score >= FUZZY_THRESHOLD:
        # For fuzzy matches, apply defaults for all slots
        slot_values = {}
        for slot_name, slot_def in rule.slots.items():
            # Try to extract slot value from input
            extracted = _extract_slot_from_input(user_input, slot_name, slot_def)
            if extracted:
                parser = SLOT_PARSERS.get(slot_def.type, lambda x: x)
                slot_values[slot_name] = parser(extracted)
            elif slot_def.default:
                slot_values[slot_name] = slot_def.default

        try:
            command = rule.command.format(**slot_values) if slot_values else rule.command
        except KeyError:
            # Missing slot values — can't form the command
            return None

        return MatchResult(
            matched=True,
            command=command,
            rule=rule,
            score=best_score,
            slot_values=slot_values,
        )
    return None


def _extract_slot_from_input(
    user_input: str, slot_name: str, slot_def: SlotDef
) -> str | None:
    """Try to extract a slot value from user input based on its type."""
    text = user_input.lower()

    if slot_def.type == "filesize":
        match = re.search(r"(\d+\s*(?:gb|mb|kb|tb|g|m|k|t|b))\b", text, re.IGNORECASE)
        return match.group(1) if match else None

    if slot_def.type == "port":
        match = re.search(r"(?:port\s+)?(\d{1,5})\b", text)
        return match.group(1) if match else None

    if slot_def.type == "duration":
        match = re.search(r"(\d+\s*(?:days?|weeks?|months?|hours?|minutes?|mins?))", text)
        return match.group(1) if match else None

    if slot_def.type == "path":
        match = re.search(r"((?:/[\w._-]+)+/?|~/[\w._/-]*)", user_input)
        return match.group(1) if match else None

    if slot_def.type == "package":
        # Last word is often the package name
        words = user_input.strip().split()
        return words[-1] if words else None

    if slot_def.type == "number":
        match = re.search(r"\b(\d+)\b", text)
        return match.group(1) if match else None

    if slot_def.type == "filename":
        match = re.search(r"[\w._-]+\.\w+", user_input)
        return match.group(0) if match else None

    return None


def match_input(user_input: str, rules: list[Rule] | None = None) -> MatchResult:
    """Match user input against all loaded rules.

    Tries exact regex match first, then falls back to fuzzy matching.
    Returns the best match found, or a non-matched result.
    """
    if rules is None:
        rules = load_rules()

    # Phase 1: Try exact regex matches
    for rule in rules:
        result = _try_regex_match(user_input, rule)
        if result:
            return result

    # Phase 2: Try fuzzy matches, keep the best one
    best_result: MatchResult | None = None
    for rule in rules:
        result = _try_fuzzy_match(user_input, rule)
        if result and (best_result is None or result.score > best_result.score):
            best_result = result

    if best_result:
        return best_result

    return MatchResult(matched=False)
