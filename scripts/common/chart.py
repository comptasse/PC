"""Build the flat and nested representations of a chart of accounts.

Account numbers are strings so that numbers with leading zeros
("0", "00", "000") stay distinct. A range account such as "164-165"
is attached under the longest existing prefix common to both bounds.
"""

from __future__ import annotations

import os
from typing import Any

Account = dict[str, Any]


def range_bounds(number: str) -> tuple[str, str] | None:
    """Return (from, to) for a range number like "164-165", else None."""
    if "-" not in number:
        return None
    low, high = number.split("-", 1)
    return low, high


def parent_of(number: str, existing: set[str]) -> str | None:
    """Longest strict prefix of `number` present in `existing`, or None."""
    bounds = range_bounds(number)
    if bounds is not None:
        # Every prefix of the common part is a strict prefix of the range.
        key = os.path.commonprefix(bounds)
        candidates = [key[:i] for i in range(len(key), 0, -1)]
    else:
        candidates = [number[:i] for i in range(len(number) - 1, 0, -1)]
    return next((c for c in candidates if c in existing), None)


def sort_key(number: str) -> tuple[str, str]:
    """Lexical order, with a range sorted right after its lower bound."""
    bounds = range_bounds(number)
    return (bounds[0], number) if bounds else (number, "")


def build_flat(accounts: list[Account]) -> list[Account]:
    """Sort accounts and add the `parent` key to each one."""
    numbers = {a["number"] for a in accounts}
    if len(numbers) != len(accounts):
        raise ValueError("duplicate account numbers")
    flat = []
    for account in sorted(accounts, key=lambda a: sort_key(a["number"])):
        flat.append({**account, "parent": parent_of(account["number"], numbers)})
    return flat


def build_nested(flat: list[Account]) -> list[Account]:
    """Turn a flat list (with `parent`) into a tree with `accounts` children."""
    nodes: dict[str, Account] = {}
    roots: list[Account] = []
    for account in flat:
        node = {k: v for k, v in account.items() if k != "parent"}
        node["accounts"] = []
        nodes[account["number"]] = node
    for account in flat:
        node = nodes[account["number"]]
        parent = account["parent"]
        if parent is None:
            roots.append(node)
        else:
            nodes[parent]["accounts"].append(node)
    return roots
