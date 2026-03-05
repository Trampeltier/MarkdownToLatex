# md2latex

A small rule-driven Markdown to LaTeX converter.

## Install

```bash
python -m pip install -e .
```

## Usage

```bash
md2latex input.md -o output.tex
```

Use a custom rule file:

```bash
md2latex input.md -o output.tex --rules rules.yml
```

Standalone LaTeX document (adds preamble + `\\begin{document}` / `\\end{document}`):

```bash
md2latex input.md -o output.tex --standalone
```

## Rules file

Rules are YAML mapping **markdown-it token types** to LaTeX templates.

- For container tokens you typically set `open` and `close`.
- For leaf tokens you typically set `template`.

Templates can use placeholders:

- `{content}` rendered children content
- `{level}` heading level (1-6)
- `{lang}` code fence language (if present)
- `{href}` link destination
- `{title}` link title (if present)

See `rules/default.yml`.
