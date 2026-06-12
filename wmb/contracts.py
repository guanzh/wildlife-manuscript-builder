"""JSON Schema validation for canonical WMB contracts."""

from __future__ import annotations

import json
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

CONTRACT_KINDS = frozenset(
    {"run", "event", "task", "result", "analysis_run", "review"}
)

_DATE_TIME_PATTERN = re.compile(
    r"\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})"
)


def _is_date_time(value: object) -> bool:
    if not isinstance(value, str) or not _DATE_TIME_PATTERN.fullmatch(value):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00").replace("z", "+00:00"))
    except ValueError:
        return False
    return True


if "date-time" not in Draft202012Validator.FORMAT_CHECKER.checkers:
    Draft202012Validator.FORMAT_CHECKER.checks("date-time")(_is_date_time)


class ContractError(ValueError):
    """Raised when a WMB contract or contract kind is invalid."""

    def __init__(self, kind: str, errors: list[tuple[str, str]]) -> None:
        self.kind = kind
        self.errors = tuple(sorted(errors))
        details = "\n".join(f"- {path}: {message}" for path, message in self.errors)
        super().__init__(f"invalid {kind} contract:\n{details}")


@lru_cache(maxsize=None)
def _validator(kind: str) -> Draft202012Validator:
    if kind not in CONTRACT_KINDS:
        raise ContractError(kind, [("kind", f"unknown contract kind: {kind}")])

    schema_path = Path(__file__).with_name("schemas") / f"{kind}.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ContractError(kind, [("<schema>", exc.message)]) from exc
    return Draft202012Validator(
        schema,
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )


def _field_path(error: ValidationError) -> str:
    parts = [str(part) for part in error.absolute_path]
    if error.validator == "required":
        match = re.match(r"'(.+)' is a required property", error.message)
        if match:
            parts.append(match.group(1))
    return ".".join(parts) if parts else "<root>"


def validate_contract(kind: str, payload: Any) -> None:
    """Validate a payload against a named WMB contract schema."""

    errors = [
        (_field_path(error), error.message)
        for error in _validator(kind).iter_errors(payload)
    ]
    if errors:
        raise ContractError(kind, errors)
