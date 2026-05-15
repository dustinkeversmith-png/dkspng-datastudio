"""Fuzzy column name resolution for forgiving chart/pipeline references."""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field


@dataclass
class FuzzyColumnResolver:
    """
    Map user tokens to the closest known column when exact matches fail.

    ``close_matches`` uses ``difflib``; raise if nothing clears ``cutoff``.
    """

    known_columns: list[str]
    cutoff: float = 0.55
    _warned: list[str] = field(default_factory=list, repr=False)

    def resolve(self, token: str | int) -> str:
        if isinstance(token, int):
            if 0 <= token < len(self.known_columns):
                return self.known_columns[token]
            raise IndexError(f"Column index {token} out of range for {len(self.known_columns)} columns")

        s = str(token).strip()
        if s in self.known_columns:
            return s

        if s.isdigit():
            return self.resolve(int(s))

        matches = difflib.get_close_matches(s, self.known_columns, n=1, cutoff=self.cutoff)
        if matches:
            best = matches[0]
            if best != s:
                self._warned.append(f"{s!r} → {best!r}")
            return best

        raise LookupError(
            f"No column similar to {s!r}; known: {self.known_columns[:24]}"
            + ("…" if len(self.known_columns) > 24 else "")
        )

    def try_resolve(self, token: str | int, *, fallback: str | None = None) -> str:
        try:
            return self.resolve(token)
        except (LookupError, IndexError):
            if fallback is not None:
                return fallback
            raise
