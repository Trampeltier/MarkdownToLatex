from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import re

import yaml
from markdown_it import MarkdownIt
from markdown_it.token import Token
from mdit_py_plugins.tasklists import tasklists_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.deflist import deflist_plugin


LATEX_SPECIAL_CHARS = {
    "\\": r"\\textbackslash{}",
    "{": r"\\{",
    "}": r"\\}",
    "#": r"\\#",
    "%": r"\\%",
    "&": r"\\&",
    "_": r"\\_",
    "^": r"\\textasciicircum{}",
    "~": r"\\textasciitilde{}",
}


LISTINGS_SAFE_LANGUAGES = {
    "python",
    "py",
    "javascript",
    "js",
    "typescript",
    "ts",
    "json",
    "bash",
    "sh",
    "shell",
    "yaml",
    "yml",
    "toml",
    "ini",
    "html",
    "css",
    "c",
    "cpp",
    "c++",
    "java",
    "go",
    "rust",
    "latex",
    "tex",
 }


CODE_UNICODE_TO_ASCII = {
    "Ŷ": "Yhat",
    "Ẑ": "Zhat",
    "X̂": "Xhat",
    "Ŷ": "Yhat",
    "Ẑ": "Zhat",
    "χ": "chi",
    "ℓ": "l",
    "λ": "lambda",
    "δ": "delta",
    "∇": "nabla",
    "∂": "d",
    "θ": "theta",
    "Δ": "Delta",
    "⊤": "T",
    "ᵀ": "^T",
    "⁻": "-",
    "⁺": "+",
    "⁰": "0",
    "¹": "1",
    "²": "2",
    "³": "3",
    "⁴": "4",
    "⁵": "5",
    "⁶": "6",
    "⁷": "7",
    "⁸": "8",
    "⁹": "9",
    "₀": "0",
    "₁": "1",
    "₂": "2",
    "₃": "3",
    "₄": "4",
    "₅": "5",
    "₆": "6",
    "₇": "7",
    "₈": "8",
    "₉": "9",
    "×": "x",
    "→": "->",
    "←": "<-",
    "↔": "<->",
    "—": "---",
    "–": "--",
 }


def _normalize_code_text(s: str) -> str:
    out: list[str] = []
    for ch in s:
        if "\ufe00" <= ch <= "\ufe0f":
            continue
        mapped = CODE_UNICODE_TO_ASCII.get(ch)
        if mapped is not None:
            out.append(mapped)
            continue
        if ord(ch) > 127:
            out.append("?")
            continue
        out.append(ch)
    return "".join(out)


def _normalize_math_content(s: str) -> str:
    # Undo common Markdown escapes inside math, so TeX sees literal symbols.
    # Example: s^\*  ->  s^*
    s = s.replace(r"\*", "*")
    s = s.replace(r"\_", "_")
    s = s.replace(r"\^", "^")
    return s


_CITATION_ARTIFACT_RE = re.compile(r"[\uE000-\uF8FF]cite[\uE000-\uF8FF].*?[\uE000-\uF8FF]", re.DOTALL)
_CITATION_TURN_TOKEN_RE = re.compile(r"\??\bturn\d+(?:view\d+|search\d+)\b\??")
_CITATION_QMARK_CLEANUP_RE = re.compile(r"[ \t]*\?{1,6}[ \t]*(?=\n\n)")
_PRIVATE_USE_RE = re.compile(r"[\uE000-\uF8FF]+")


def _strip_citation_artifacts(md_text: str) -> str:
    md_text = _CITATION_ARTIFACT_RE.sub("", md_text)
    md_text = _CITATION_TURN_TOKEN_RE.sub("", md_text)
    md_text = _CITATION_QMARK_CLEANUP_RE.sub("", md_text)
    md_text = _PRIVATE_USE_RE.sub("", md_text)
    return md_text


_PAREN_MATH_RE = re.compile(r"\\\((.+?)\\\)", re.DOTALL)
_BRACKET_MATH_RE = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)


def _normalize_latex_math_delimiters(md_text: str) -> str:
    # Convert LaTeX-style delimiters to the ones texmath_plugin reliably detects.
    # Keep this conservative (non-greedy), and allow newlines for block math.

    def paren_repl(m: re.Match[str]) -> str:
        inner = m.group(1).strip()
        inner = inner.replace("\\\\", "\\")
        return f"${inner}$"

    def bracket_repl(m: re.Match[str]) -> str:
        inner = m.group(1).strip()
        inner = inner.replace("\\\\", "\\")
        return f"\n\n$$\n{inner}\n$$\n\n"

    md_text = _PAREN_MATH_RE.sub(paren_repl, md_text)
    md_text = _BRACKET_MATH_RE.sub(bracket_repl, md_text)
    return md_text


UNICODE_TO_LATEX = {
    "—": "---",
    "–": "--",
    "−": "-",
    "‑": "-",
    "‐": "-",
    "‒": "-",
    "…": r"\ldots{}",
    "±": r"$\pm$",
    "“": "``",
    "”": "''",
    "‘": "`",
    "’": "'",
    "ï": r"\"{i}",
    "é": r"\'{e}",
    "ö": r"\"{o}",
    "ü": r"\"{u}",
    "á": r"\'{a}",
    "ó": r"\'{o}",
    "í": r"\'{i}",
    "ú": r"\'{u}",
    "χ": r"$\chi$",
    "α": r"$\alpha$",
    "β": r"$\beta$",
    "γ": r"$\gamma$",
    "δ": r"$\delta$",
    "ε": r"$\epsilon$",
    "ζ": r"$\zeta$",
    "η": r"$\eta$",
    "θ": r"$\theta$",
    "Θ": r"$\Theta$",
    "ι": r"$\iota$",
    "κ": r"$\kappa$",
    "λ": r"$\lambda$",
    "Λ": r"$\Lambda$",
    "μ": r"$\mu$",
    "ν": r"$\nu$",
    "ξ": r"$\xi$",
    "Ξ": r"$\Xi$",
    "π": r"$\pi$",
    "Π": r"$\Pi$",
    "ρ": r"$\rho$",
    "σ": r"$\sigma$",
    "Σ": r"$\Sigma$",
    "τ": r"$\tau$",
    "υ": r"$\upsilon$",
    "Υ": r"$\Upsilon$",
    "φ": r"$\phi$",
    "ϕ": r"$\varphi$",
    "Φ": r"$\Phi$",
    "ψ": r"$\psi$",
    "Ψ": r"$\Psi$",
    "ω": r"$\omega$",
    "Ω": r"$\Omega$",
    "ℓ": r"$\ell$",
    "·": r"$\cdot$",
    "→": r"$\rightarrow$",
    "←": r"$\leftarrow$",
    "↔": r"$\leftrightarrow$",
    "↑": r"$\uparrow$",
    "↓": r"$\downarrow$",
    "↕": r"$\updownarrow$",
    "↖": r"$\nwarrow$",
    "↗": r"$\nearrow$",
    "↘": r"$\searrow$",
    "↙": r"$\swarrow$",
    "⇒": r"$\Rightarrow$",
    "⇐": r"$\Leftarrow$",
    "⇑": r"$\Uparrow$",
    "⇓": r"$\Downarrow$",
    "⇔": r"$\Leftrightarrow$",
    "⟶": r"$\longrightarrow$",
    "⟵": r"$\longleftarrow$",
    "⟷": r"$\longleftrightarrow$",
    "⟹": r"$\Longrightarrow$",
    "⟸": r"$\Longleftarrow$",
    "⟺": r"$\Longleftrightarrow$",
    "≤": r"$\leq$",
    "≥": r"$\geq$",
    "∈": r"$\in$",
    "∑": r"$\sum$",
    "∞": r"$\infty$",
    "∂": r"$\partial$",
    "∇": r"$\nabla$",
    "∥": r"$\parallel$",
    "⟂": r"$\perp$",
    "∧": r"$\wedge$",
    "∨": r"$\vee$",
    "∩": r"$\cap$",
    "∪": r"$\cup$",
    "∅": r"$\emptyset$",
    "✓": r"$\checkmark$",
    "✔": r"$\checkmark$",
    "✗": r"$\times$",
    "✘": r"$\times$",
    "✕": r"$\times$",
    "✖": r"$\times$",
    "△": r"$\triangle$",
    "▲": r"$\triangle$",
    "▼": r"$\triangledown$",
    "•": r"$\bullet$",
    "◦": r"$\circ$",
    "●": r"$\bullet$",
    "○": r"$\circ$",
    "★": r"$\star$",
    "☆": r"$\star$",
    "♥": r"$\heartsuit$",
    "♦": r"$\diamondsuit$",
    "◆": r"$\diamond$",
    "◇": r"$\diamond$",
    "§": r"\S{}",
    "¶": r"\P{}",
    "†": r"\dagger{}",
    "‡": r"\ddagger{}",
    "™": r"\texttrademark{}",
    "®": r"\textregistered{}",
    "©": r"\copyright{}",
    "№": "No.",
    "⚠": "[WARN]",
    "❗": "!",
    "❓": "?",
    "ℹ": "[i]",
    "💡": "[idea]",
    "🔥": "[fire]",
    "⚡": "[zap]",
    "📌": "[pin]",
    "📎": "[paperclip]",
    "🔎": "[search]",
    "🟢": "(green)",
    "🟡": "(yellow)",
    "🔴": "(red)",
    "⚫": "(black)",
    "⚪": "(white)",
    # Box drawing (fallback to ASCII)
    "─": "-",
    "│": "|",
    "┌": "+",
    "┐": "+",
    "└": "+",
    "┘": "+",
    "├": "+",
    "┤": "+",
    "┬": "+",
    "┴": "+",
    "┼": "+",
    "═": "=",
    "║": "|",
    "╔": "+",
    "╗": "+",
    "╚": "+",
    "╝": "+",
    "╠": "+",
    "╣": "+",
    "╦": "+",
    "╩": "+",
    "╬": "+",
}

for i, d in enumerate("①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳", start=1):
    UNICODE_TO_LATEX[d] = f"({i})"


def _escape_latex_text(s: str) -> str:
    out: list[str] = []
    for ch in s:
        if "\ufe00" <= ch <= "\ufe0f":
            continue
        mapped = UNICODE_TO_LATEX.get(ch)
        if mapped is not None:
            out.append(mapped)
            continue
        if ord(ch) > 127:
            out.append("?")
            continue
        out.append(LATEX_SPECIAL_CHARS.get(ch, ch))
    return "".join(out)


@dataclass(frozen=True)
class Rules:
    documentclass: str
    preamble: str
    tokens: dict[str, dict[str, Any]]
    heading_levels: dict[int, str]


def generate_main_tex(*, included_tex: Path, rules_path: Path) -> str:
    rules = _load_rules(rules_path)
    include_target = included_tex.as_posix()
    if include_target.endswith(".tex"):
        include_target = include_target[:-4]

    parts: list[str] = []
    parts.append(f"\\documentclass{{{rules.documentclass}}}\n")
    if rules.preamble:
        parts.append(rules.preamble.rstrip() + "\n")
    parts.append("\\begin{document}\n")
    parts.append(f"\\input{{{include_target}}}\n")
    parts.append("\\end{document}\n")
    return "".join(parts)


_INLINE_MATH_RE = re.compile(r"(?<!\$)\$(?!\$)([^\n$]*?)(?<!\$)\$(?!\$)")


def _normalize_inline_math_delimiters(md_text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        inner = m.group(1)
        inner = inner.strip(" \t")
        return "$" + inner + "$"

    return _INLINE_MATH_RE.sub(repl, md_text)


@dataclass
class Node:
    token: Token
    children: list["Node"]
    close_token: Optional[Token] = None


def _load_rules(rules_path: Path) -> Rules:
    data = yaml.safe_load(rules_path.read_text(encoding="utf-8")) or {}
    tokens = data.get("tokens", {}) or {}
    heading_levels_raw = data.get("heading_levels", {}) or {}
    heading_levels: dict[int, str] = {}
    for k, v in heading_levels_raw.items():
        try:
            heading_levels[int(k)] = str(v)
        except ValueError:
            continue

    return Rules(
        documentclass=str(data.get("documentclass", "article")),
        preamble=str(data.get("preamble", "")),
        tokens=tokens,
        heading_levels=heading_levels,
    )


def _attrs_to_dict(tok: Token) -> dict[str, str]:
    attrs: dict[str, str] = {}
    if tok.attrs:
        for k, v in tok.attrs.items():
            attrs[str(k)] = "" if v is None else str(v)
    return attrs


def _get_heading_level(tok: Token) -> int:
    if tok.tag and tok.tag.startswith("h"):
        try:
            return int(tok.tag[1:])
        except ValueError:
            return 1
    return 1


def _apply_template(template: str, *, content: str = "", **kwargs: Any) -> str:
    rendered = template
    rendered = rendered.replace("{content}", content)
    for k, v in kwargs.items():
        rendered = rendered.replace("{" + str(k) + "}", str(v))
    return rendered


def _has_task_checkbox(node: Node) -> Optional[bool]:
    stack: list[Node] = [node]
    while stack:
        cur = stack.pop()
        if cur.token.type == "checkbox_input":
            return bool((cur.token.attrs or {}).get("checked", False))
        if cur.token.type == "html_inline":
            html = cur.token.content or ""
            if "type=\"checkbox\"" in html or "type='checkbox'" in html:
                return "checked" in html
        stack.extend(reversed(cur.children))
    return None


def _render_children_inline(node: Node, rules: Rules) -> str:
    rendered = "".join(_render_node(ch, rules) for ch in node.children)
    return rendered.replace("\n", " ").strip()


def _render_table(table_node: Node, rules: Rules) -> str:
    rows: list[list[str]] = []
    header_rows: list[list[str]] = []

    def walk(n: Node, in_head: bool) -> None:
        tok = n.token
        if tok.type == "thead_open":
            for ch in n.children:
                walk(ch, True)
            return
        if tok.type == "tbody_open":
            for ch in n.children:
                walk(ch, False)
            return

        if tok.type == "tr_open":
            row: list[str] = []
            for ch in n.children:
                if ch.token.type in {"th_open", "td_open"}:
                    row.append(_render_children_inline(ch, rules))
            if row:
                (header_rows if in_head else rows).append(row)
            return

        for ch in n.children:
            walk(ch, in_head)

    for ch in table_node.children:
        walk(ch, False)

    all_rows = header_rows + rows
    if not all_rows:
        return ""

    ncols = max(len(r) for r in all_rows)

    # Heuristic: estimate width by character count of the widest entry per column.
    col_max: list[int] = [0] * ncols
    for r in all_rows:
        for i, cell in enumerate(r[:ncols]):
            col_max[i] = max(col_max[i], len(cell))

    def estimate_cols(cols: list[int]) -> int:
        if not cols:
            return 0
        return sum(col_max[i] for i in cols) + 3 * (len(cols) - 1)

    def choose_font(est_chars: int) -> tuple[str, str]:
        if est_chars > 160:
            return "{\\scriptsize\n", "}\n"
        if est_chars > 110:
            return "{\\small\n", "}\n"
        return "", ""

    def render_longtable(cols: list[int]) -> str:
        cols_sorted = cols
        # Wrap cells by using p{..} columns (requires \usepackage{array}).
        # We allocate width proportional to estimated max-chars per column,
        # while capping each column to 0.5\linewidth to avoid a single column
        # consuming the whole page.
        widths = [max(1, col_max[i]) for i in cols_sorted]
        total = sum(widths)
        cap = 0.5
        colspec_parts: list[str] = []
        for w in widths:
            frac = (w / total) if total else (1.0 / max(1, len(widths)))
            if frac > cap:
                frac = cap
            colspec_parts.append(r">{\raggedright\arraybackslash}p{" + f"{frac:.3f}" + r"\linewidth}")
        colspec = "".join(colspec_parts)
        font_open, font_close = choose_font(estimate_cols(cols_sorted))

        def project_rows(src: list[list[str]]) -> list[list[str]]:
            out_rows: list[list[str]] = []
            for r in src:
                rr = r + [""] * (ncols - len(r))
                out_rows.append([rr[i] for i in cols_sorted])
            return out_rows

        header_proj = project_rows(header_rows)
        rows_proj = project_rows(rows)

        out: list[str] = []
        if font_open:
            out.append(font_open)
        out.append(f"\\begin{{longtable}}{{{colspec}}}\n")
        out.append("\\toprule\n")
        if header_proj:
            for r in header_proj:
                out.append(" {}\\\\\n".format(" & ".join(r)))
            out.append("\\midrule\n")
        for r in rows_proj:
            out.append(" {}\\\\\n".format(" & ".join(r)))
        out.append("\\bottomrule\n")
        out.append("\\end{longtable}\n")
        if font_close:
            out.append(font_close)
        return "".join(out)

    full_est = estimate_cols(list(range(ncols)))
    if ncols <= 3 or full_est <= 200:
        return render_longtable(list(range(ncols)))

    # Split into chunks of columns, repeating column 0 in each chunk.
    target = 140
    chunks: list[list[int]] = []
    current: list[int] = [0]
    for col in range(1, ncols):
        candidate = current + [col]
        if len(current) > 1 and estimate_cols(candidate) > target:
            chunks.append(current)
            current = [0, col]
        else:
            current = candidate
    if current:
        chunks.append(current)

    return "\n".join(render_longtable(cols) for cols in chunks)


def _build_tree(tokens: list[Token]) -> Node:
    root = Node(token=Token("root", "", 0), children=[])
    stack: list[Node] = [root]

    for tok in tokens:
        if tok.nesting == 1:
            node = Node(token=tok, children=[])
            stack[-1].children.append(node)
            stack.append(node)
            continue

        if tok.nesting == -1:
            if len(stack) > 1:
                stack[-1].close_token = tok
                stack.pop()
            continue

        if tok.type == "inline" and tok.children:
            inline_root = _build_tree(list(tok.children))
            stack[-1].children.append(Node(token=tok, children=inline_root.children))
        else:
            stack[-1].children.append(Node(token=tok, children=[]))

    return root


def convert_markdown_to_latex(md_text: str, *, rules_path: Path, standalone: bool = False) -> str:
    rules = _load_rules(rules_path)

    md_text = _strip_citation_artifacts(md_text)
    md_text = _normalize_latex_math_delimiters(md_text)
    md_text = _normalize_inline_math_delimiters(md_text)

    md = (
        MarkdownIt("default", {"html": True, "linkify": True, "typographer": True})
        .use(tasklists_plugin)
        .use(footnote_plugin)
        .use(deflist_plugin)
    )

    try:
        from mdit_py_plugins.table import table_plugin  # type: ignore

        md = md.use(table_plugin)
    except Exception:
        pass

    try:
        from mdit_py_plugins.texmath import texmath_plugin  # type: ignore

        md = md.use(texmath_plugin)
    except Exception:
        pass

    tokens = md.parse(md_text)
    tree = _build_tree(tokens)
    body = _render_node(tree, rules)

    if not standalone:
        return body

    parts = [f"\\documentclass{{{rules.documentclass}}}\n"]
    if rules.preamble:
        parts.append(rules.preamble.rstrip() + "\n")
    parts.append("\\begin{document}\n")
    parts.append(body.rstrip() + "\n")
    parts.append("\\end{document}\n")
    return "".join(parts)


def _render_tokens(tokens: list[Token], rules: Rules) -> str:
    tree = _build_tree(tokens)
    return _render_node(tree, rules)


def _render_node(node: Node, rules: Rules) -> str:
    if node.token.type == "root":
        return "".join(_render_node(ch, rules) for ch in node.children)

    tok = node.token
    rule = rules.tokens.get(tok.type, {}) or {}
    if rule.get("skip") is True:
        return ""

    if tok.type == "inline":
        return "".join(_render_node(ch, rules) for ch in node.children)

    if tok.type == "text":
        return _escape_latex_text(tok.content)

    if tok.type == "math_inline":
        return f"${_normalize_math_content(tok.content)}$"

    if tok.type == "math_block":
        content = _normalize_math_content((tok.content or "").strip("\n"))
        return "\\[\n" + content + "\n\\]\n"

    if tok.type == "code_inline":
        tmpl = str(rule.get("template", r"\\texttt{{content}}"))
        return _apply_template(tmpl, content=_escape_latex_text(tok.content))

    if tok.type == "code_block":
        tmpl = str(rule.get("template", "{content}"))
        return _apply_template(tmpl, content=_normalize_code_text(tok.content.rstrip("\n")))

    if tok.type == "fence":
        info = (tok.info or "").strip()
        lang_raw = info.split()[0].lower() if info else ""
        content = tok.content.rstrip("\n")

        has_non_ascii = any(ord(ch) > 127 for ch in content)
        lang_is_safe = (lang_raw in LISTINGS_SAFE_LANGUAGES) and not has_non_ascii

        if not lang_is_safe:
            code_rule = rules.tokens.get("code_block", {}) or {}
            code_tmpl = str(code_rule.get("template", "{content}"))
            return _apply_template(code_tmpl, content=_normalize_code_text(content)) + "\n"

        tmpl = str(rule.get("template", "{content}"))
        return _apply_template(
            tmpl,
            content=content,
            lang=_escape_latex_text(lang_raw),
        )

    if tok.type == "image":
        attrs = _attrs_to_dict(tok)
        src = _escape_latex_text(attrs.get("src", ""))
        tmpl = str(rule.get("template", r"\\includegraphics{{{src}}}"))
        return _apply_template(tmpl, src=src)

    if tok.type == "checkbox_input":
        return ""

    if tok.type == "html_inline":
        html_rule = rules.tokens.get(tok.type, {}) or {}
        if html_rule.get("skip") is True:
            return ""
        return _escape_latex_text(tok.content)

    if tok.type == "html_block":
        html_rule = rules.tokens.get(tok.type, {}) or {}
        if html_rule.get("skip") is True:
            return ""
        tmpl = str(html_rule.get("template", r"\\begin{verbatim}\n{content}\n\\end{verbatim}\n"))
        return _apply_template(tmpl, content=tok.content.rstrip("\n"))

    if tok.type == "table_open":
        return _render_table(node, rules)

    if tok.type == "heading_open":
        level = _get_heading_level(tok)
        section_cmd = rules.heading_levels.get(level, "section")
        tmpl = str(rule.get("template", r"\\{section_cmd}{content}\n"))
        content = "".join(_render_node(ch, rules) for ch in node.children)
        return _apply_template(tmpl, content=content, section_cmd=section_cmd)

    if tok.type == "link_open":
        attrs = _attrs_to_dict(tok)
        href = _escape_latex_text(attrs.get("href", ""))
        open_t = str(rule.get("open", r"\\href{{{href}}}{"))
        close_rule = rules.tokens.get("link_close", {}) or {}
        close_t = str(close_rule.get("close", "}"))
        inner = "".join(_render_node(ch, rules) for ch in node.children)
        return _apply_template(open_t, href=href) + inner + close_t

    if tok.type == "list_item_open":
        checked_opt = _has_task_checkbox(node)
        if checked_opt is not None:
            marker = r"$\boxtimes$" if checked_opt else r"$\square$"
            return f"\\item[{marker}] "

    if tok.nesting == 1:
        inner = "".join(_render_node(ch, rules) for ch in node.children)
        if "template" in rule:
            return _apply_template(str(rule.get("template", "{content}")), content=inner)

        open_t = str(rule.get("open", ""))
        close_t = ""
        if node.close_token is not None:
            close_rule = rules.tokens.get(node.close_token.type, {}) or {}
            close_t = str(close_rule.get("close", rule.get("close", "")))
        else:
            close_t = str(rule.get("close", ""))
        return open_t + inner + close_t

    if "template" in rule:
        return str(rule.get("template", ""))

    if tok.content:
        return _escape_latex_text(tok.content)

    return ""
