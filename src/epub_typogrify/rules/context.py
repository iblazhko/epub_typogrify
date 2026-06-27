"""Cross-node transformation state and the ``Rule`` signature.

``ContextState`` carries the small amount of context that a context-sensitive
rule (chiefly the quote engine) needs to thread from one text run to the next —
so a quotation opened in one inline element can be closed correctly in another.
In Phase 1 a fresh state is used per run; Phase 3's ``TextWalker`` threads a
single state across the text nodes of a block.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from epub_typogrify.locales.profile import LocaleProfile


@dataclass
class ContextState:
    """Mutable state threaded through a pipeline run.

    ``prev_char`` is the last character emitted *before* the current run (used to
    decide whether a quote opens or closes). ``quote_stack`` records the kinds of
    quotation marks currently open (``'"'`` or ``"'"``) to track nesting depth.
    """

    prev_char: str | None = None
    quote_stack: list[str] = field(default_factory=list)


# A rule maps text to text given the active locale profile and the running state.
Rule = Callable[[str, "LocaleProfile", ContextState], str]
