"""Minimal HTML tree built on the standard library HTMLParser.

Only what the source parsers need: a forgiving tree builder, text
extraction (with <br> rendered as a newline) and recursive search.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from html.parser import HTMLParser

_VOID_TAGS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
})


class Node:
    """An HTML element with its attributes and children (nodes or text)."""

    def __init__(self, tag: str, attrs: dict[str, str], parent: Node | None) -> None:
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children: list[Node | str] = []

    def elements(self) -> list[Node]:
        """Direct child elements, without text nodes."""
        return [c for c in self.children if isinstance(c, Node)]

    def text(self) -> str:
        """Concatenated text content; <br> becomes a newline."""
        parts: list[str] = []
        for child in self.children:
            if isinstance(child, str):
                parts.append(child)
            elif child.tag == "br":
                parts.append("\n")
            else:
                parts.append(child.text())
        return "".join(parts)

    def find_all(self, predicate: Callable[[Node], bool]) -> Iterator[Node]:
        """Depth-first search of descendants matching `predicate`."""
        for child in self.elements():
            if predicate(child):
                yield child
            yield from child.find_all(predicate)

    def has_class(self, name: str) -> bool:
        return name in self.attrs.get("class", "").split()


class _TreeBuilder(HTMLParser):

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None)
        self._current = self.root

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Node(tag, {k: v or "" for k, v in attrs}, self._current)
        self._current.children.append(node)
        if tag not in _VOID_TAGS:
            self._current = node

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._current.children.append(Node(tag, {k: v or "" for k, v in attrs}, self._current))

    def handle_endtag(self, tag: str) -> None:
        # Close up to the matching open element; ignore stray end tags.
        node: Node | None = self._current
        while node is not None and node.tag != tag:
            node = node.parent
        if node is not None and node.parent is not None:
            self._current = node.parent

    def handle_data(self, data: str) -> None:
        self._current.children.append(data)


def parse_html(source: str) -> Node:
    """Parse an HTML document and return the root node."""
    builder = _TreeBuilder()
    builder.feed(source)
    builder.close()
    return builder.root
