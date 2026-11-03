# pylgen-skill — LLM-friendly PyLGEN reference bundle

Generated 2026-11-03 from `pylgen-core` 0.7.3 (https://github.com/yonyuk/pylgen, BSD-3-Clause).
Docs text is the upstream mkdocs source with tabs/admonitions flattened to plain markdown.

## Layout

```
SKILL.md                         cheat sheet + routing table — Claude reads this first
reference/
  00-readme-and-changelog.md     PyPI README + CHANGELOG (breaking changes)
  01-getting-started.md          install, key concepts, quick start
  02-user-guide.md               per-module usage guide (common, lexer, grammar, parser, analysis, regex, automaton, visual)
  03-api-reference-python.md     every class/method/property (Python API)
  04-api-reference-cython.md     Cython API
  05-formal-foundations.md       theory background
  06-benchmark.md                VecLang vs Lark benchmark
  tutorials/                     foundations, arithmetic-repl, config-dsl-indented, mini-python, veclang
examples/                        runnable example sources from the repo
  arithmetic_interpreter/        visitors, context, runtime errors (best small reference)
  idented_dsl/                   IdentedLexer usage
  mini-python/                   scopes, functions, ErrorAST
```

## Install as a Claude Code skill

Project-scoped (checked into the repo you're building with PyLGEN):

```bash
mkdir -p .claude/skills
cp -r pylgen-skill .claude/skills/pylgen
```

User-scoped (available in every project):

```bash
mkdir -p ~/.claude/skills
cp -r pylgen-skill ~/.claude/skills/pylgen
```

Claude Code picks it up from the `SKILL.md` frontmatter; invoke explicitly with `/pylgen` or just ask about PyLGEN.
The folder name becomes the skill name, so keep it `pylgen`.

## Alternative: plain context file

If you'd rather not use skills, drop `SKILL.md` content into your project's `CLAUDE.md` (or `@`-import it:
`@docs/pylgen/SKILL.md`) and keep `reference/` beside it so the relative paths in the routing table resolve.

## Refreshing

```bash
git clone --depth 1 https://github.com/yonyuk/pylgen.git
python build_bundle.py pylgen ./pylgen-skill   # then re-check SKILL.md against the changelog
```
