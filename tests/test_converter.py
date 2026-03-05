from __future__ import annotations

from pathlib import Path

import pytest

from md2latex.converter import convert_markdown_to_latex, generate_main_tex


def rules_path() -> Path:
    return Path(__file__).resolve().parents[1] / "rules" / "default.yml"


def test_heading_bold_italic_strike() -> None:
    md = "# Title\n\nSome *it* and **bd** and ~~st~~.\n"
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=False)
    assert "\\section{Title}" in tex
    assert "\\emph{" in tex
    assert "\\textbf{" in tex
    assert "\\sout{" in tex


def test_strong_closes() -> None:
    md = "**F**\n"
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=False)
    assert "\\textbf{F}" in tex


def test_link_rendering() -> None:
    md = "A [link](https://example.com).\n"
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=False)
    assert "\\href" in tex
    assert "https://example.com" in tex


def test_fenced_code_block() -> None:
    md = "```python\nprint('hi')\n```\n"
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=False)
    assert "\\begin{lstlisting}" in tex
    assert "print('hi')" in tex
    assert "language=python" in tex


def test_task_list_items() -> None:
    md = "- [ ] todo\n- [x] done\n"
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=False)
    assert "\\begin{itemize}" in tex
    assert "\\item[$\\square$]" in tex
    assert "\\item[$\\boxtimes$]" in tex


def test_table_renders_longtable() -> None:
    md = "| a | b |\n|---|---|\n| 1 | 2 |\n"
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=False)
    assert "\\begin{longtable}" in tex
    assert "\\toprule" in tex
    assert "a" in tex and "b" in tex
    assert "1" in tex and "2" in tex


def test_wide_table_scales_down() -> None:
    long = "x" * 200
    md = f"| col1 | col2 |\n|---|---|\n| {long} | {long} |\n"
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=False)
    assert "\\begin{longtable}" in tex
    assert ("{\\small" in tex) or ("{\\scriptsize" in tex)


def test_very_wide_table_splits_into_multiple_tables() -> None:
    header = "| id | " + " | ".join([f"c{i}" for i in range(1, 11)]) + " |\n"
    sep = "|---|" + "|".join(["---"] * 10) + "|\n"
    row = "| r1 | " + " | ".join(["x" * 30] * 10) + " |\n"
    md = header + sep + row
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=False)
    assert tex.count("\\begin{longtable}") >= 2


def test_html_fallback_to_verbatim() -> None:
    md = "<div>hi</div>\n"
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=False)
    assert "\\begin{verbatim}" in tex
    assert "<div>hi</div>" in tex


def test_html_inline_is_escaped_text() -> None:
    md = "<span>hi</span>\n"
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=False)
    assert "\\begin{verbatim}" not in tex
    assert "<span>hi</span>" in tex


def test_standalone_document_wrap() -> None:
    md = "Hello\n"
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=True)
    assert "\\documentclass" in tex
    assert "\\begin{document}" in tex
    assert "\\end{document}" in tex
    assert "Hello" in tex


def test_main_tex_wrapper() -> None:
    main_tex = generate_main_tex(included_tex=Path("deep-research-report.tex"), rules_path=rules_path())
    assert "\\documentclass" in main_tex
    assert "\\begin{document}" in main_tex
    assert "\\input{deep-research-report}" in main_tex
    assert "\\end{document}" in main_tex
    assert "\\\\usepackage" not in main_tex
    assert "\\usepackage" in main_tex


def test_escapes_latex_special_chars_in_text() -> None:
    md = "100% & {braces} _underscore_\\n"
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=False)
    assert "\\%" in tex
    assert "\\&" in tex
    assert "\\{" in tex
    assert "\\}" in tex


def test_math_backslashes_are_preserved() -> None:
    md = "Layerwise fusion $\\chi(\\cdot,\\cdot)$.\n"
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=False)
    assert "$\\chi(\\cdot,\\cdot)$" in tex


def test_math_with_spaces_in_delimiters_is_preserved() -> None:
    md = "Fusion $ \\chi(\\cdot,\\cdot) $ end.\n"
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=False)
    assert "$\\chi(\\cdot,\\cdot)$" in tex
    assert "textbackslash" not in tex


def test_unicode_chi_is_mapped() -> None:
    md = "chi: χ\n"
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=False)
    assert "$\\chi$" in tex
    assert "textbackslash" not in tex


def test_unicode_legend_symbols_are_mapped() -> None:
    md = "Legend: ✓ △ ✗\n"
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=False)
    assert "$\\checkmark$" in tex
    assert "$\\triangle$" in tex
    assert "$\\times$" in tex


def test_unicode_arrow_and_warning_are_mapped() -> None:
    md = "Go ⇒ now ⚠\n"
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=False)
    assert "$\\Rightarrow$" in tex
    assert "[WARN]" in tex


def test_circled_number_is_mapped() -> None:
    md = "Step ①\n"
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=False)
    assert "(1)" in tex


def test_unmapped_unicode_falls_back_to_question_mark() -> None:
    md = "Weird: 𝛁\n"
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=False)
    assert "?" in tex


def test_non_breaking_hyphen_is_mapped() -> None:
    md = "post‑convergence\n"
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=False)
    assert "post-convergence" in tex
    assert "?" not in tex


def test_math_block_renders_display_math() -> None:
    md = "$$\\chi + 1$$\n"
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=False)
    assert "$$" not in tex
    assert "\\[" in tex
    assert "\\]" in tex
    assert "\\chi" in tex


def test_math_unescapes_markdown_asterisk() -> None:
    md = "Star: $s^\\*$\n"
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=False)
    assert "$s^*$" in tex


def test_mermaid_fence_falls_back_to_verbatim() -> None:
    md = "```mermaid\nflowchart TB\n  A-->B\n```\n"
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=False)
    assert "\\begin{verbatim}" in tex
    assert "language=mermaid" not in tex


def test_fence_with_non_ascii_falls_back_to_verbatim() -> None:
    md = "```python\nprint('Ŷ')\n```\n"
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=False)
    assert "\\begin{verbatim}" in tex
    assert "\\begin{lstlisting}" not in tex
    assert "Ŷ" not in tex
    assert "Yhat" in tex


@pytest.mark.parametrize(
    "md,expected",
    [
        ("---\n", "\\hrulefill"),
        ("> quote\n", "\\begin{quote}"),
    ],
)
def test_misc_blocks(md: str, expected: str) -> None:
    tex = convert_markdown_to_latex(md, rules_path=rules_path(), standalone=False)
    assert expected in tex
