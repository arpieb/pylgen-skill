"""Build an LLM-friendly PyLGEN docs bundle from the cloned repo.

Cleans mkdocs-material syntax (content tabs, admonitions, iframes) into plain markdown.
"""
import re, shutil, sys
from pathlib import Path

SRC = Path(sys.argv[1])          # cloned repo root
OUT = Path(sys.argv[2])          # bundle output dir
DOCS = SRC / "docs"

TAB_RE = re.compile(r'^(\s*)=== "([^"]+)"\s*$')
ADM_RE = re.compile(r'^(\s*)!!!\s*(\w+)(?:\s+"([^"]*)")?\s*$')
IFRAME_RE = re.compile(r'<iframe[^>]*>.*?</iframe>', re.S)
HTML_SPAN_RE = re.compile(r'</?span[^>]*>')


def clean(text: str) -> str:
    text = IFRAME_RE.sub('', text)
    text = HTML_SPAN_RE.sub('', text)
    out, i, lines = [], 0, text.splitlines()
    while i < len(lines):
        line = lines[i]
        m = TAB_RE.match(line) or ADM_RE.match(line)
        if m:
            base = len(m.group(1))
            if TAB_RE.match(line):
                header = f'{m.group(1)}**{m.group(2)}:**'
            else:
                title = m.group(3) or m.group(2).capitalize()
                header = f'{m.group(1)}> **{m.group(2).upper()}: {title}**' if m.group(3) else f'{m.group(1)}> **{m.group(2).upper()}**'
            out.append(header)
            i += 1
            # dedent the indented block that follows
            while i < len(lines):
                nxt = lines[i]
                if nxt.strip() == '':
                    out.append('')
                    i += 1
                    continue
                indent = len(nxt) - len(nxt.lstrip())
                if indent >= base + 4:
                    out.append(nxt[base + 4:] if nxt.startswith(' ' * (base + 4)) else nxt.lstrip())
                    i += 1
                else:
                    break
            continue
        out.append(line)
        i += 1
    # collapse 3+ blank lines
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'


def concat(paths, title):
    parts = [f'# {title}\n']
    for p in paths:
        parts.append(f'\n\n<!-- source: {p.relative_to(SRC)} -->\n\n' + clean(p.read_text()))
    return '\n'.join(parts)


if OUT.exists():
    shutil.rmtree(OUT)
ref = OUT / 'reference'
ref.mkdir(parents=True)

# README + changelog
(ref / '00-readme-and-changelog.md').write_text(clean((SRC / 'readme.md').read_text()))

# getting started
gs = DOCS / 'getting-started'
(ref / '01-getting-started.md').write_text(concat(
    [gs / 'installation.md', gs / 'key-concepts.md', gs / 'quick-start.md', gs / 'next-steps.md'],
    'PyLGEN — Getting Started'))

# user guide
ug = DOCS / 'user-guide'
order = ['intro', 'common', 'lexer', 'grammar', 'parser', 'analysis', 'regex', 'automaton', 'visual']
(ref / '02-user-guide.md').write_text(concat([ug / f'user-guide-{n}.md' for n in order], 'PyLGEN — User Guide'))

# API reference (python)
api = DOCS / 'api-reference' / 'python'
order = ['common', 'lexer', 'grammar', 'parser', 'analysis', 'regex', 'automaton', 'visual']
(ref / '03-api-reference-python.md').write_text(concat(
    [api / f'api-reference-python-{n}.md' for n in order], 'PyLGEN — Python API Reference'))

# API reference (cython)
capi = DOCS / 'api-reference' / 'cython'
(ref / '04-api-reference-cython.md').write_text(concat(sorted(capi.glob('*.md')), 'PyLGEN — Cython API Reference'))

# tutorials: one file per tutorial
tut_out = ref / 'tutorials'
tut_out.mkdir()
T = DOCS / 'tutorials'
(tut_out / 'foundations.md').write_text(concat(
    [T / 'foundations' / f'tutorials-foundations-{n}.md' for n in ['intro', 'building-a-lexer', 'building-a-parser']],
    'Tutorial — Foundations (lexer & parser from scratch)'))
cl = T / 'complete-languages'
(tut_out / 'arithmetic-repl.md').write_text(concat(
    [cl / 'arithmetic-repl' / f'arithmetic-repl-{n}.md' for n in ['intro', 'step-1', 'step-2', 'step-3', 'step-4']],
    'Tutorial — Arithmetic REPL'))
(tut_out / 'config-dsl-indented.md').write_text(clean((cl / 'config-dsl' / 'config-dsl.md').read_text()))
(tut_out / 'mini-python.md').write_text(clean((cl / 'mini-python' / 'mini-python.md').read_text()))
(tut_out / 'veclang.md').write_text(concat(
    [cl / 'veclang' / f'{n}.md' for n in ['veclang-intro', 'getting-to-know-veclang', 'veclang-step-1', 'veclang-step-2',
                                           'veclang-step-3', 'veclang-evolution', 'veclang-step-4', 'veclang-next-steps']],
    'Tutorial — VecLang (Cython-accelerated language)'))

# formal foundations + benchmark
ff = DOCS / 'formal-foundations'
(ref / '05-formal-foundations.md').write_text(concat(
    [ff / f'formal-foundations-{n}.md' for n in ['intro', 'regular-languages', 'automata', 'tokenization',
                                                 'context-free-grammars', 'lr-parsing']],
    'PyLGEN — Formal Foundations'))
(ref / '06-benchmark.md').write_text(clean((DOCS / 'benchmarks' / 'veclang-benchmark.md').read_text()))

# example sources (python only; skip pyc, build artifacts)
ex_out = OUT / 'examples'
for name in ['arithmetic_interpreter', 'idented_dsl', 'mini-python']:
    src = SRC / 'examples' / name
    if src.exists():
        shutil.copytree(src, ex_out / name,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.so', '*.c', '*.html', '*.pkl', 'build'))

print('done')
for p in sorted(OUT.rglob('*')):
    if p.is_file():
        print(f'{p.stat().st_size:>8}  {p.relative_to(OUT)}')
