"""Post-order (children-before-parent) TraversalStrategy for pylgen's ASTWalker."""

from __future__ import annotations

from pylgen.analysis import TraversalStrategy
from pylgen.analysis.context import Context
from pylgen.common.types import AST


class _Frame:
    """One pending node on the traversal stack."""

    __slots__ = ("node", "children", "index")

    def __init__(self, node: AST) -> None:
        self.node = node
        self.children: list[AST] | None = None  # selected lazily (needs context)
        self.index = 0


class PostOrderStrategy(TraversalStrategy):
    """Yields every node after all of its selected children, left to right.

    - Iterative: deep ASTs don't hit Python's recursion limit.
    - Children come from the registered ASTChildrenSelector for each node type
      (add_selector / set_default_selector), chosen when the node is first
      expanded, so a selector can look at context state that earlier visits set.
    - Reusable: ASTWalker.walk() calls init() before and reset() after each walk.
    """

    def __init__(self, context_type: type[Context] = Context) -> None:
        super().__init__(context_type)
        self._stack: list[_Frame] = []

    def init(self, root: AST) -> None:
        super().init(root)
        self._stack = [_Frame(root)] if root is not None else []

    def has_next(self) -> bool:
        return bool(self._stack)

    def current(self, context: Context) -> AST:
        self._check_context_type(context)  # required first by the base contract
        if not self._stack:
            raise StopIteration("PostOrderStrategy exhausted; call init() first")

        while True:
            frame = self._stack[-1]
            if frame.children is None:
                frame.children = [
                    c for c in self._select(frame.node, context) if c is not None
                ]
            if frame.index < len(frame.children):
                child = frame.children[frame.index]
                frame.index += 1
                self._stack.append(_Frame(child))
            else:
                self._stack.pop()
                return frame.node

    def reset(self) -> None:
        self._stack = []

    def _select(self, ast: AST, context: Context) -> list[AST]:
        try:
            selector = self._get_selector(ast)
        except KeyError:
            raise KeyError(
                f"No ASTChildrenSelector registered for {type(ast).__name__} "
                "and no default selector set"
            ) from None
        return list(selector.select_children(ast, context))
