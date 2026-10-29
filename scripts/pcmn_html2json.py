"""Convert the Belgian PCMN source pages to JSON.

Reads the CNC/CBN "multilingual comparison" snapshots saved in
PCMN/sources/<version>/ and writes one JSON file per plan, with labels
in French, Dutch, German and English, footnotes, annual-accounts
rubrics (associations only) and the descriptions of class 0 accounts.

The comparison view aligns languages per block of text (a whole class
table per cell), not per account, so each language column is parsed on
its own and the languages are joined on the account number.

Usage:
    uv run pcmn_html2json.py [--plan {entreprises,asbl}] [--output-dir DIR]

Examples:
    uv run pcmn_html2json.py                    # Both plans
    uv run pcmn_html2json.py --plan asbl        # Associations and foundations only
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from common.chart import build_flat, build_nested, range_bounds
from common.html_tree import Node, parse_html

PCMN_DIR = Path(__file__).resolve().parent.parent / "PCMN"
VERSION = 2019
COORDINATED = "2019-05-07"

LANGUAGES = ("fr", "nl", "de", "en")

# Obvious numbering errors in the CNC pages, corrected before merging:
# (plan, language, printed number, label) -> correct number.
ERRATA = {
    ("asbl", "nl", "6701", "Geraamde belastingen"): "6702",
}

# Accounts missing from one language version of the CNC pages. They are
# kept, with a null label in that language.
SOURCE_GAPS = {
    ("asbl", "fr"): {"550-559"},
}

# Source snapshots per plan: views of the CNC page, each listing its columns.
VIEWS = {
    "entreprises": {"fr-nl-de": ("fr", "nl", "de"), "fr-en": ("fr", "en")},
    "asbl": {"fr-nl-de": ("fr", "nl", "de"), "fr-en": ("fr", "en")},
}

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------
_NUMBER_RE = re.compile(r"^(\d+(?:-\d+)?)\.?$")
# Range connectors used by each language: "164 à 165", "164 tot 165", "164 bis 165"…
_RANGE_WORD = r"(?:à|a|tot|bis|to|-|–)"
_ACCOUNT_LINE_RE = re.compile(rf"^(\d+)(?:-(\d+)|\s+{_RANGE_WORD}\s+(\d+))?\.?(?:\s+(\S.*))?$")
# A range alone in a cell: "164 à 165".
_CELL_RANGE_RE = re.compile(rf"^(\d+)\s+{_RANGE_WORD}\s+(\d+)$")
# An account without label followed by its first sub-account: "669 6690 …".
_STACKED_RE = re.compile(r"^(\d+)\s+(\1\d+\b.*)$")
_RANGE_WORD_RE = re.compile(rf"^{_RANGE_WORD}$")
_FOOTNOTE_START_RE = re.compile(r"^\((\d+(?:bis|ter)?)\)\s*(.*)$")
_NOTE_RE = re.compile(r"\s*\((\d+(?:bis|ter)?)\)")
# Annual-accounts rubric: "I", "VII.A.1", "IX. A", "IX.F.", or two
# alternatives "II.I ou V.D" (ou / of / oder / or).
_RUBRIC_PART = r"[IVX]+(?:\.\s?[A-Z0-9]+)*\.?"
_RUBRIC = rf"{_RUBRIC_PART}(?:\s+(?:ou|of|oder|or)\s+{_RUBRIC_PART})?"
_RUBRIC_CELL_RE = re.compile(rf"^({_RUBRIC})((?:\s*\(\d+\))*)$")
_TRAILING_RUBRIC_RE = re.compile(rf"\s+({_RUBRIC})$")
# Text removed by an amendment, printed as "[...]".
_ELLIPSIS_RE = re.compile(r"\s*\[(?:\.\.\.|…)\]\s*")
_SUBDIVISION_RE = re.compile(r"^(?:\.{3}|…)(\d+)\s+(\S.*)$")
_DESCRIPTION_HEADING_RE = re.compile(r"^(\d{2,})\.?\s+(\S.*)$")
# Title of the section describing the content of some class 0 accounts.
_DESCRIPTIONS_TITLE_RE = re.compile(
    r"(Détermination du contenu|Bepaling van de inhoud|Bestimmung des Inhalts|Determination of the content|Definition of the content)",
    re.IGNORECASE,
)
# Amendment markers left in some translations: "1[413 Subsidies to be received]1".
_AMENDMENT_RE = re.compile(r"(?<![\w(])\d+\[|\]\d+(?![\w)])")
# Ranges printed with a typographic dash: "164–165".
_NUMBER_DASH_RE = re.compile(r"^(\d+)\s*[‐‑–—]\s*(\d+)(?=\.?(\s|$))")
_BLOCK_TAGS = frozenset({"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "div"})


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
@dataclass
class Line:
    """One logical line of a language column."""

    segment: int
    text: str
    # Table rows keep their cells as (grid column, text) for rubric lookup.
    cells: list[tuple[int, str]] | None = None
    bullet: bool = False


@dataclass
class ParsedSubdivision:
    """A generic subdivision such as "...1 Chèques émis" under 550-559."""

    suffix: str
    label: str
    notes: list[str] = field(default_factory=list)


@dataclass
class ParsedAccount:
    number: str
    label: str
    notes: list[str] = field(default_factory=list)
    rubric: dict[str, str] = field(default_factory=dict)
    subdivisions: list[ParsedSubdivision] = field(default_factory=list)
    # Label printed as "[...]": the account was repealed.
    repealed: bool = False


@dataclass
class ParsedColumn:
    accounts: list[ParsedAccount] = field(default_factory=list)
    # Subdivisions printed after a non-range account (its range row is
    # missing from the source), keyed by that account number.
    orphan_subdivisions: dict[str, list[ParsedSubdivision]] = field(default_factory=dict)
    footnotes: dict[str, str] = field(default_factory=dict)
    descriptions: dict[str, str] = field(default_factory=dict)
    repealed_footnotes: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _clean(text: str) -> str:
    text = _AMENDMENT_RE.sub("", text.replace("\xa0", " "))
    text = re.sub(r"\s+", " ", _NUMBER_DASH_RE.sub(r"\1-\2", text)).strip()
    return _CELL_RANGE_RE.sub(r"\1-\2", text)


def _normalize_signs(label: str) -> str:
    """Use one dash form for the sign markers, e.g. "(-)" → "(–)"."""
    return re.sub(r"\(\s*[-‐‑–—]\s*\)", "(–)", label)


def _normalize_rubric(rubric: str) -> str:
    """"IX. A" → "IX.A", "IX.F." → "IX.F", "II.I ou V.D" → "II.I/V.D"."""
    parts = re.split(r"\s+(?:ou|of|oder|or)\s+", rubric)
    return "/".join(re.sub(r"\s+", "", p).rstrip(".") for p in parts)


def _clean_label(label: str) -> str:
    """Drop "[...]" amendment markers and a trailing colon."""
    return _ELLIPSIS_RE.sub(" ", label).strip().rstrip(":").strip()


def _split_notes(text: str) -> tuple[str, list[str]]:
    """Remove footnote references such as "(1)(2)" from `text`."""
    notes = _NOTE_RE.findall(text)
    return _clean(_NOTE_RE.sub("", text)), notes


def _comparison_columns(path: Path, languages: tuple[str, ...]) -> dict[str, list[Node]]:
    """Return, per language, the cells of the comparison table in order."""
    root = parse_html(path.read_text(encoding="utf-8"))
    table = next(root.find_all(lambda n: n.tag == "table" and n.has_class("legal-text-multilingual-comparison")), None)
    if table is None:
        raise ValueError(f"{path.name}: no multilingual comparison table")
    rows = [tr for tr in table.find_all(lambda n: n.tag == "tr") if tr.parent is not None and tr.parent.parent is table]
    columns: dict[str, list[Node]] = {lang: [] for lang in languages}
    for row in rows:
        cells = [c for c in row.elements() if c.tag == "td"]
        if len(cells) != len(languages):
            raise ValueError(f"{path.name}: expected {len(languages)} columns, got {len(cells)}")
        for lang, cell in zip(languages, cells):
            columns[lang].append(cell)
    return columns


def _cell_paragraphs(cell: Node) -> list[str]:
    """Non-empty paragraphs of a table cell (<p> blocks or <br> lines)."""
    blocks = [p.text() for p in cell.find_all(lambda n: n.tag == "p")] or cell.text().split("\n")
    return [text for text in (_clean(b) for b in blocks) if text]


def _row_lines(row: Node) -> list[list[tuple[int, str]]]:
    """Split a table row into account lines of (grid column, text) cells.

    Most rows hold one account. Some rows of the source stack several
    accounts in one cell (one paragraph each), or put a sub-account in
    the label cell of an account that has no label of its own.
    """
    cells: list[tuple[int, list[str]]] = []
    column = 0
    for cell in row.elements():
        if cell.tag not in ("td", "th"):
            continue
        paragraphs = _cell_paragraphs(cell)
        if paragraphs:
            cells.append((column, paragraphs))
        column += int(cell.attrs.get("colspan") or 1)
    if not cells:
        return []

    if all(len(p) == 1 for _, p in cells):
        flat = [(c, p[0]) for c, p in cells]
        # "669" followed by "6690 Charges…" (or by a "6690" cell): two
        # accounts on one row.
        for i, (_, text) in enumerate(flat[:-1]):
            following = flat[i + 1][1]
            if _NUMBER_RE.match(text) and (_ACCOUNT_LINE_RE.match(following) or _NUMBER_RE.match(following)):
                return [flat[: i + 1], flat[i + 1:]]
        return [flat]

    numbers = next(((c, p) for c, p in cells if all(_NUMBER_RE.match(t) for t in p)), None)
    if numbers is None:
        return [[(c, " ".join(p)) for c, p in cells]]
    others = [(c, p) for c, p in cells if c != numbers[0]]
    if not others:
        return [[(numbers[0], n)] for n in numbers[1]]
    label_column, labels = max(others, key=lambda cell: len(cell[1]))
    queue = list(numbers[1])
    lines: list[list[tuple[int, str]]] = []
    for text in labels:
        if _ACCOUNT_LINE_RE.match(text):
            lines.append([(label_column, text)])
        elif queue:
            lines.append([(numbers[0], queue.pop(0)), (label_column, text)])
        elif lines:
            column, previous = lines[-1][-1]
            lines[-1][-1] = (column, f"{previous} {text}")
    lines += [[(numbers[0], n)] for n in queue]
    lines[0] += [(c, " ".join(p)) for c, p in others if c != label_column]
    return lines


def _linearize(node: Node, segment: int, out: list[Line]) -> None:
    """Flatten a column cell into lines: table rows and text blocks."""
    for child in node.elements():
        if child.tag == "tr":
            for cells in _row_lines(child):
                out.append(Line(segment, " ".join(t for _, t in cells), cells))
        elif child.tag in _BLOCK_TAGS and not any(True for _ in child.find_all(lambda n: n.tag in ("tr", "p", "li"))):
            for part in child.text().split("\n"):
                text = _clean(part)
                stacked = _STACKED_RE.match(text)
                for piece in stacked.groups() if stacked else [text]:
                    if piece:
                        out.append(Line(segment, piece, bullet=child.tag == "li"))
        else:
            _linearize(child, segment, out)


def _column_lines(cells: list[Node]) -> list[Line]:
    lines: list[Line] = []
    for segment, cell in enumerate(cells):
        _linearize(cell, segment, lines)
    return lines


# ---------------------------------------------------------------------------
# Column parsing
# ---------------------------------------------------------------------------
class _RubricColumns:
    """Tracks the grid columns of the "Actifs" / "Passifs" headers."""

    def __init__(self, strict: bool) -> None:
        # Only the French column provides rubric values; other columns
        # just need rubric cells removed from their labels.
        self.strict = strict
        self.asset: int | None = None
        self.liability: int | None = None

    def update(self, line: Line) -> None:
        if not line.cells:
            return
        texts = {t: c for c, t in line.cells}
        if "Actifs" in texts and "Passifs" in texts:
            self.asset, self.liability = texts["Actifs"], texts["Passifs"]

    def side(self, number: str, column: int) -> str:
        if number[0] in "67":
            return "income_statement"
        if self.asset is None or self.liability is None:
            if not self.strict:
                return "asset"
            raise ValueError(f"rubric for {number} before the Actifs/Passifs header")
        return "asset" if column < self.liability else "liability"


def _parse_account_row(line: Line, rubrics: _RubricColumns | None) -> ParsedAccount | None:
    """Parse a table row or text line holding an account, else None."""
    if line.cells:
        index = next((i for i, (_, t) in enumerate(line.cells) if _NUMBER_RE.match(t)), None)
        if index is None or index > 1:
            # Number and label in the same cell: "6630 Moins-values…".
            merged = _ACCOUNT_LINE_RE.match(line.cells[0][1])
            if not merged:
                return None
            high = merged.group(2) or merged.group(3)
            number = f"{merged.group(1)}-{high}" if high else merged.group(1)
            column = line.cells[0][0]
            cells = [(column, number), (column, merged.group(4) or ""), *line.cells[1:]]
            line = Line(line.segment, line.text, cells, line.bullet)
            index = 0
        assert line.cells is not None
        number = _NUMBER_RE.match(line.cells[index][1]).group(1)  # type: ignore[union-attr]
        rest = line.cells[index + 1:]
        if len(rest) >= 2 and _RANGE_WORD_RE.match(rest[0][1]) and _NUMBER_RE.match(rest[1][1]):
            number = f"{number}-{_NUMBER_RE.match(rest[1][1]).group(1)}"  # type: ignore[union-attr]
            rest = rest[2:]
        label_parts: list[str] = []
        notes: list[str] = []
        rubric: dict[str, str] = {}
        for column, text in rest:
            rubric_match = _RUBRIC_CELL_RE.match(text)
            if rubric_match and (label_parts or rubrics is not None):
                if rubrics is not None:
                    rubric[rubrics.side(number, column)] = _normalize_rubric(rubric_match.group(1))
                notes += re.findall(r"\((\d+)\)", rubric_match.group(2))
            elif re.fullmatch(r"(\(\d+\)\s*)+", text):
                notes += re.findall(r"\((\d+)\)", text)
            else:
                label_parts.append(text)
        label = " ".join(label_parts)
    else:
        match = _ACCOUNT_LINE_RE.match(line.text)
        if not match:
            return None
        high = match.group(2) or match.group(3)
        number = f"{match.group(1)}-{high}" if high else match.group(1)
        label = match.group(4) or ""
        notes, rubric = [], {}
    label, trailing = _split_notes(label)
    notes = trailing + notes
    if rubrics is not None:
        # Rubric printed in the label cell, e.g. "Production immobilisée I.C".
        match = _TRAILING_RUBRIC_RE.search(label)
        if match:
            label = label[: match.start()].strip()
            if line.cells:
                rubric.setdefault(rubrics.side(number, -1), _normalize_rubric(match.group(1)))
            label, more = _split_notes(label)
            notes = more + notes
    repealed = bool(_ELLIPSIS_RE.fullmatch(label))
    return ParsedAccount(number, _normalize_signs(_clean_label(label)), notes, rubric, repealed=repealed)


def parse_column(lines: list[Line], *, with_rubrics: bool, rubric_values: bool = True) -> ParsedColumn:
    """Parse one language column into accounts, footnotes and descriptions."""
    result = ParsedColumn()
    rubrics = _RubricColumns(strict=rubric_values) if with_rubrics else None
    footnote: tuple[str, int] | None = None   # (number, segment) being read
    in_descriptions = False
    description: str | None = None
    paragraphs: dict[str, list[str]] = {}
    last_segment = -1

    for line in lines:
        if in_descriptions:
            heading = _DESCRIPTION_HEADING_RE.match(line.text)
            known = {a.number for a in result.accounts}
            if heading and heading.group(1) in known and heading.group(1) not in paragraphs:
                description = heading.group(1)
                paragraphs[heading.group(1)] = []
            elif description is not None:
                paragraphs[description].append(("- " if line.bullet else "") + line.text)
            continue

        if _DESCRIPTIONS_TITLE_RE.search(line.text):
            in_descriptions = True
            footnote = None
            continue

        if rubrics is not None:
            rubrics.update(line)

        start = _FOOTNOTE_START_RE.match(line.text)
        if start and re.fullmatch(r"(\.{3}|…|\[(\.{3}|…)\])?", start.group(2).strip()):
            result.repealed_footnotes.add(start.group(1))   # e.g. "(27bis) ..."
            footnote = None
            continue
        if start:
            number = start.group(1)
            if number in result.footnotes:
                raise ValueError(f"footnote ({number}) defined twice")
            result.footnotes[number] = start.group(2)
            footnote = (number, line.segment)
            continue

        last = result.accounts[-1] if result.accounts else None
        subdivision = _SUBDIVISION_RE.match(line.text)
        if subdivision and last is not None:
            label, notes = _split_notes(subdivision.group(2))
            item = ParsedSubdivision(subdivision.group(1), _normalize_signs(_clean_label(label)), notes)
            if range_bounds(last.number):
                last.subdivisions.append(item)
            else:
                result.orphan_subdivisions.setdefault(last.number, []).append(item)
            continue

        account = _parse_account_row(line, rubrics)
        if account is not None:
            result.accounts.append(account)
            last_segment = line.segment
            footnote = None
            continue

        # Label continued on its own row: "(même subdivision que le compte 17)(19)".
        if footnote is None and last is not None and line.text.startswith("(") and line.segment == last_segment:
            label, notes = _split_notes(line.text)
            last.label = f"{last.label} {_normalize_signs(_clean_label(label))}".strip()
            last.notes += notes
            continue

        if footnote is not None and footnote[1] == line.segment:
            number = footnote[0]
            result.footnotes[number] = f"{result.footnotes[number]}\n\n{line.text}".strip()

    result.descriptions = {n: "\n\n".join(p) for n, p in paragraphs.items() if p}
    result.footnotes = {n: _clean_paragraphs(t) for n, t in result.footnotes.items()}
    return result


def _clean_paragraphs(text: str) -> str:
    return "\n\n".join(_clean(p) for p in text.split("\n\n") if _clean(p))


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------
def _footnote_key(number: str) -> tuple[int, str]:
    match = re.match(r"(\d+)(.*)", number)
    assert match is not None
    return int(match.group(1)), match.group(2)


def _check_same(name: str, reference: list[str], other: list[str], errors: list[str]) -> None:
    if reference != other:
        missing = sorted(set(reference) - set(other))
        extra = sorted(set(other) - set(reference))
        errors.append(f"{name}: missing {missing[:20]} extra {extra[:20]}"
                      + (" (same set, different order)" if not missing and not extra else ""))


def _merge_subdivisions(number: str, reference: ParsedAccount,
                        by_lang: dict[str, dict[str, ParsedAccount]], errors: list[str]) -> list[dict]:
    suffixes = [s.suffix for s in reference.subdivisions]
    labels: dict[str, dict[str, str]] = {}
    for lang in LANGUAGES:
        if number not in by_lang[lang]:
            continue
        found = {s.suffix: s.label for s in by_lang[lang][number].subdivisions}
        if sorted(found) != sorted(suffixes):
            errors.append(f"{lang} {number}: subdivisions {sorted(found)} instead of {sorted(suffixes)}")
        for suffix, label in found.items():
            labels.setdefault(suffix, {})[lang] = label
    merged = []
    for sub in reference.subdivisions:
        item: dict = {"suffix": sub.suffix,
                      "label": {lang: labels.get(sub.suffix, {}).get(lang) for lang in LANGUAGES}}
        if sub.notes:
            item["notes"] = sub.notes
        merged.append(item)
    return merged


def build_plan(plan: str, sources_dir: Path) -> dict:
    with_rubrics = plan == "asbl"
    columns: dict[str, ParsedColumn] = {}
    french_views: list[ParsedColumn] = []
    for view, languages in VIEWS[plan].items():
        path = sources_dir / f"pcmn_{plan}_{view}.html"
        for lang, cells in _comparison_columns(path, languages).items():
            parsed = parse_column(_column_lines(cells), with_rubrics=with_rubrics, rubric_values=lang == "fr")
            for item in parsed.accounts:
                corrected = ERRATA.get((plan, lang, item.number, item.label))
                if corrected:
                    item.number = corrected
            if lang == "fr":
                french_views.append(parsed)
            columns.setdefault(lang, parsed)

    errors: list[str] = []
    warnings: list[str] = []
    fr = columns["fr"]
    for lang in LANGUAGES:
        numbers = [a.number for a in columns[lang].accounts]
        if len(set(numbers)) != len(numbers):
            errors.append(f"{lang}: duplicate numbers {sorted({n for n in numbers if numbers.count(n) > 1})}")
    for other in french_views[1:]:
        _check_same("fr (second view)", [a.number for a in fr.accounts], [a.number for a in other.accounts], errors)
        if [a.label for a in other.accounts] != [a.label for a in fr.accounts]:
            errors.append("fr: labels differ between the two views")
    all_numbers = {a.number for c in columns.values() for a in c.accounts}
    for lang in LANGUAGES:
        missing = all_numbers - {a.number for a in columns[lang].accounts}
        expected = SOURCE_GAPS.get((plan, lang), set())
        if missing != expected:
            errors.append(f"{lang}: missing accounts {sorted(missing - expected)}"
                          + (f", expected gaps not found {sorted(expected - missing)}" if expected - missing else ""))
        elif missing:
            warnings.append(f"{lang}: accounts missing from the source, kept with a null label {sorted(missing)}")
    for lang in LANGUAGES[1:]:
        # The CNC language versions do not all carry the same footnotes:
        # keep every footnote and report the differences.
        _check_same(f"{lang} footnotes", sorted(fr.footnotes, key=_footnote_key), sorted(columns[lang].footnotes, key=_footnote_key), warnings)
        _check_same(f"{lang} descriptions", sorted(fr.descriptions), sorted(columns[lang].descriptions), errors)

    all_footnotes = sorted({n for c in columns.values() for n in c.footnotes}, key=_footnote_key)
    # References to repealed footnotes are dropped.
    repealed_notes = {n for c in columns.values() for n in c.repealed_footnotes} - set(all_footnotes)
    for column in columns.values():
        for item in column.accounts:
            if set(item.notes) & repealed_notes:
                warnings.append(f"{item.number}: reference to repealed footnote {sorted(set(item.notes) & repealed_notes)} removed")
                item.notes = [n for n in item.notes if n not in repealed_notes]
    for lang in LANGUAGES:
        referenced = {n for a in columns[lang].accounts for n in [*a.notes, *(x for s in a.subdivisions for x in s.notes)]}
        if referenced - set(all_footnotes):
            errors.append(f"{lang}: footnotes referenced without definition {sorted(referenced - set(all_footnotes), key=_footnote_key)}")
        unused = set(columns[lang].footnotes) - referenced
        if unused:
            warnings.append(f"{lang}: footnotes defined but not referenced {sorted(unused, key=_footnote_key)}")
    for lang in LANGUAGES:
        for a in columns[lang].accounts:
            if re.search(r"\(\d+\)", a.label):
                errors.append(f"{lang} {a.number}: footnote reference left in label {a.label!r}")
    if errors:
        raise ValueError(f"{plan}:\n  " + "\n  ".join(errors))

    by_lang = {lang: {a.number: a for a in columns[lang].accounts} for lang in LANGUAGES}
    # Give orphan subdivisions back to the range account missing from that
    # language, when it sits under the account they were printed after.
    for lang in LANGUAGES:
        for after, subdivisions in columns[lang].orphan_subdivisions.items():
            gaps = [n for n in SOURCE_GAPS.get((plan, lang), set()) if n.startswith(after)]
            if len(gaps) != 1:
                errors.append(f"{lang}: subdivisions after {after} without a range account")
                continue
            by_lang[lang][gaps[0]] = ParsedAccount(gaps[0], "", subdivisions=subdivisions)
    # Accounts repealed in some language and without a label anywhere.
    repealed = {
        n for n in all_numbers
        if any(n in by_lang[lang] and by_lang[lang][n].repealed for lang in LANGUAGES)
        and not any(n in by_lang[lang] and by_lang[lang][n].label for lang in LANGUAGES)
        and not any(m != n and m.startswith(n) for m in all_numbers)
    }
    if repealed:
        warnings.append(f"repealed accounts left out {sorted(repealed)}")
    accounts = []
    for number in sorted(all_numbers - repealed):
        # French is the reference for rubrics and notes; fall back to the
        # first language that has the account when French lacks it.
        a = next(by_lang[lang][number] for lang in LANGUAGES if number in by_lang[lang])
        account: dict = {
            "number": a.number,
            "label": {lang: (by_lang[lang][number].label or None) if number in by_lang[lang] else None
                      for lang in LANGUAGES},
        }
        bounds = range_bounds(a.number)
        if bounds:
            account["range"] = {"from": bounds[0], "to": bounds[1]}
        if a.rubric:
            account["rubric"] = {k: a.rubric[k] for k in ("asset", "liability", "income_statement") if k in a.rubric}
        if a.notes:
            account["notes"] = a.notes
        if a.subdivisions:
            account["subdivisions"] = _merge_subdivisions(number, a, by_lang, errors)
        if a.number in fr.descriptions:
            account["description"] = {lang: columns[lang].descriptions[a.number] for lang in LANGUAGES}
        accounts.append(account)

    for warning in warnings:
        print(f"  warning ({plan}): {warning}", file=sys.stderr)
    if errors:
        raise ValueError(f"{plan}:\n  " + "\n  ".join(errors))

    flat = build_flat(accounts)
    return {
        "version": VERSION,
        "plan": plan,
        "coordinated": COORDINATED,
        "footnotes": {
            n: {lang: columns[lang].footnotes.get(n) for lang in LANGUAGES}
            for n in all_footnotes
        },
        "flat": flat,
        "nested": build_nested(flat),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _schema_validator(schema_path: Path):  # noqa: ANN202
    """Return a JSON Schema validator, or None if jsonschema is missing."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        print("  jsonschema is not installed: skipping schema validation", file=sys.stderr)
        return None
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert the PCMN source pages to JSON.")
    parser.add_argument("--plan", choices=sorted(VIEWS), help="Plan to convert (default: all)")
    parser.add_argument("--output-dir", help="Output directory (default: PCMN/versions/<version>)")
    args = parser.parse_args()

    sources_dir = PCMN_DIR / "sources" / str(VERSION)
    out_dir = Path(args.output_dir) if args.output_dir else PCMN_DIR / "versions" / str(VERSION)
    out_dir.mkdir(parents=True, exist_ok=True)

    schema_path = PCMN_DIR / "versions" / str(VERSION) / f"pcmn_{VERSION}.schema.json"
    validator = _schema_validator(schema_path)

    for plan in [args.plan] if args.plan else sorted(VIEWS):
        try:
            data = build_plan(plan, sources_dir)
        except ValueError as error:
            print(f"Error: {error}", file=sys.stderr)
            sys.exit(1)
        if validator is not None:
            problems = [f"{'/'.join(map(str, e.absolute_path))}: {e.message}" for e in validator.iter_errors(data)]
            if problems:
                print(f"Error: {plan} does not match {schema_path.name}:\n  " + "\n  ".join(problems[:20]), file=sys.stderr)
                sys.exit(1)
        out_path = out_dir / f"pcmn_{plan}_{VERSION}.json"
        out_path.write_text(json.dumps(data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
        print(f"  {plan}: {len(data['flat'])} accounts, {len(data['footnotes'])} footnotes -> {out_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
