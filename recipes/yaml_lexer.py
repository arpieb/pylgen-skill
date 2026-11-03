"""IdentedLexer for a YAML-like configuration language.

Supported surface syntax:

    # comment                      full-line or trailing (" #...")
    server:                        mapping key opening a nested block
      host: "localhost"            "..." (no escapes) or '...' ('' = literal ')
      port: 8080                   ints / floats, optionally negative
      debug: true                  true | false | yes | no | on | off
      fallback: null               null | ~
      name: web-01                 bare words (letters, digits, _ - . /)
      tags: [a, b, "c d"]          flow lists
      limits: {cpu: 2, mem: 512}   flow maps
      users:
        - alice                    block list items
        - name: bob
          admin: yes

Indentation is a fixed unit of INDENT_UNIT spaces (2). Tabs or indentation
that is not a multiple of the unit are reported in ``lexer.errors``.

Token stream shape (Python-style): each logical line ends with NEWLINE;
INDENT / DEDENT come right before the first token of a line whose depth
changed; the stream ends with any pending DEDENTs and then EOF ("$").
Blank and comment-only lines produce no tokens at all.
"""

from __future__ import annotations

from typing import Set

from pylgen.common.enums import TokenType
from pylgen.common.types import LexicalError, Symbol
from pylgen.lexer import IdentedLexer

INDENT_UNIT = 2
_BLANK_MARKER = "#blank#"  # written over blank/comment lines by the sanitizer


class YamlTok(TokenType):
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    NULL = "NULL"
    WORD = "WORD"
    STRING = "STRING"
    COLON = "COLON"
    DASH = "DASH"
    COMMA = "COMMA"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    NEWLINE = "NEWLINE"
    INDENTATION = "INDENTATION"  # one indent unit at line start
    SPACE = "SPACE"              # in-line whitespace; dropped by IdentedLexer
    BLANK = "BLANK"              # sanitizer marker; matched by ignore pattern
    EOF = "EOF"


# Terminal symbols, shared with whatever grammar consumes this lexer.
number = Symbol("number", True)
boolean = Symbol("boolean", True)
null = Symbol("null", True)
word = Symbol("word", True)
string = Symbol("string", True)
colon = Symbol(":", True)
dash = Symbol("-", True)
comma = Symbol(",", True)
lbracket = Symbol("[", True)
rbracket = Symbol("]", True)
lbrace = Symbol("{", True)
rbrace = Symbol("}", True)
newline = Symbol("newline", True)
indent = Symbol("INDENT", True)
dedent = Symbol("DEDENT", True)
EOF_SYMBOL = "$"  # use as AttributedGrammar(..., end_symbol=EOF_SYMBOL)

_SYMBOLS = {
    YamlTok.NUMBER: number, YamlTok.BOOLEAN: boolean, YamlTok.NULL: null,
    YamlTok.WORD: word, YamlTok.STRING: string, YamlTok.COLON: colon,
    YamlTok.DASH: dash, YamlTok.COMMA: comma, YamlTok.LBRACKET: lbracket,
    YamlTok.RBRACKET: rbracket, YamlTok.LBRACE: lbrace, YamlTok.RBRACE: rbrace,
    YamlTok.NEWLINE: newline, YamlTok.INDENTATION: indent,
}


def to_symbol(t: YamlTok, text: str) -> Symbol:
    return _SYMBOLS.get(t, Symbol(text, True))


def _strip_comment(line: str) -> str:
    """Drop a '#' comment that starts a line or follows whitespace, outside quotes."""
    quote = None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i]
    return line


class YamlLexer(IdentedLexer):
    """IdentedLexer preconfigured for the YAML-like config language.

    ``errors`` includes both pylgen's lexical errors and indentation errors
    found while sanitizing the text.
    """

    def __init__(self) -> None:
        super().__init__(to_symbol, f"{_BLANK_MARKER}\n?")
        self._indent_errors: Set[LexicalError] = set()

        # Lower number wins on equal-length matches: keywords before WORD.
        self[0, YamlTok.BLANK] = f"{_BLANK_MARKER}\n?"
        self[1, YamlTok.NUMBER] = r"\-?\d+(\.\d+)?"
        self[2, YamlTok.BOOLEAN] = "true|false|yes|no|on|off"
        self[3, YamlTok.NULL] = "null|~"
        # ':' may appear inside a word only when followed by a non-space,
        # so "key: v" splits but "http://x" and "a:b" stay one WORD (as in YAML).
        self[4, YamlTok.WORD] = r"[a-zA-Z_\./]([a-zA-Z0-9_\-\./#]|:[a-zA-Z0-9_\-\./#])*"
        # '...' supports '' as an escaped quote. "..." has no escapes: pylgen's
        # regex engine can't match a literal backslash ([^\\] raises / crashes).
        self[5, YamlTok.STRING] = "\"[^\"\n]*\"|'([^'\n]|'')*'"
        self[6, YamlTok.INDENTATION] = " " * INDENT_UNIT
        self[7, YamlTok.NEWLINE] = "\n"
        self[8, YamlTok.COLON] = ":"
        self[9, YamlTok.DASH] = r"\-"
        self[10, YamlTok.COMMA] = r"\,"
        self[11, YamlTok.LBRACKET] = r"\["
        self[12, YamlTok.RBRACKET] = r"\]"
        self[13, YamlTok.LBRACE] = r"\{"
        self[14, YamlTok.RBRACE] = r"\}"
        self[15, YamlTok.SPACE] = "[ \t]"  # single char so INDENTATION wins at line start

        self.set_ident(YamlTok.INDENTATION)
        self.set_indent_symbol(indent)
        self.set_dedent_symbol(dedent)
        self.set_eof_token(EOF_SYMBOL, YamlTok.EOF)
        self.set_text_sanitize_function(self._sanitize)

    @property
    def errors(self) -> Set[LexicalError]:
        return super().errors | self._indent_errors

    def clear_errors(self) -> None:
        super().clear_errors()
        self._indent_errors.clear()

    def load_text(self, text: str) -> None:
        self.clear_errors()  # pylgen keeps errors across load_text otherwise
        super().load_text(text)

    def _sanitize(self, text: str) -> str:
        """Blank out empty/comment lines, strip comments, check indentation.

        Line count is preserved so token positions match the original text.
        """
        out = []
        for lineno, raw in enumerate(text.split("\n"), start=1):
            line = _strip_comment(raw).rstrip()
            if not line:
                out.append(_BLANK_MARKER)
                continue
            body = line.lstrip(" \t")
            lead = line[: len(line) - len(body)]
            if "\t" in lead:
                self._indent_errors.add(LexicalError(
                    "Tabs are not allowed for indentation",
                    lineno, 1, lineno, len(lead) + 1))
            elif len(lead) % INDENT_UNIT:
                self._indent_errors.add(LexicalError(
                    f"Indentation must be a multiple of {INDENT_UNIT} spaces",
                    lineno, 1, lineno, len(lead) + 1))
            out.append(line)
        result = "\n".join(out)
        # Guarantee the last real line is terminated by NEWLINE.
        return result if result.endswith(_BLANK_MARKER) else result + "\n"


if __name__ == "__main__":
    SAMPLE = """\
# service config
server:
  host: "localhost"   # trailing comment
  port: 8080
  ratio: -0.75
  debug: yes
  fallback: ~

  tags: [web, "edge node", 3]
  limits: {cpu: 2, mem: 512}
  users:
    - alice
    - name: bob
      admin: true
log_path: /var/log/app.log
"""
    lexer = YamlLexer()
    lexer.load_text(SAMPLE)
    depth = 0
    line_buf: list[str] = []
    for tok in lexer.tokens:
        name = str(tok.symbol)
        if name == "newline":
            print("  " * depth + " ".join(line_buf)); line_buf = []
        elif name in ("INDENT", "DEDENT"):
            line_buf.append(name)
            depth += 1 if name == "INDENT" else -1
        else:
            line_buf.append(f"{tok.type}({tok.text!r})" if name not in "[]{}:,-$" else name)
    if line_buf:
        print(" ".join(line_buf))
    for e in sorted(lexer.errors, key=lambda e: e.start_position):
        print("ERROR", e.start_position, e.message)
