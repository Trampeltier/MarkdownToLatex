from __future__ import annotations

import argparse
from pathlib import Path

try:
    from .converter import convert_markdown_to_latex, generate_main_tex
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from md2latex.converter import convert_markdown_to_latex, generate_main_tex


def _default_rules_path() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "pyproject.toml").exists():
            return parent / "rules" / "default.yml"
    return Path.cwd() / "rules" / "default.yml"


def main() -> None:
    parser = argparse.ArgumentParser(prog="md2latex", description="Convert Markdown to LaTeX")
    parser.add_argument("input", type=Path, help="Input .md file")
    parser.add_argument("-o", "--output", type=Path, help="Output .tex file")
    parser.add_argument(
        "--rules",
        type=Path,
        default=_default_rules_path(),
        help="Path to YAML rules file",
    )
    parser.add_argument(
        "--standalone",
        action="store_true",
        help="Emit a complete LaTeX document (preamble + document env)",
    )
    parser.add_argument(
        "--write-main",
        action="store_true",
        help="Write a main.tex wrapper that \\input{}s the generated .tex output",
    )

    args = parser.parse_args()

    if args.standalone and args.write_main:
        parser.error("--write-main cannot be used with --standalone")

    md_text = args.input.read_text(encoding="utf-8")
    latex = convert_markdown_to_latex(md_text, rules_path=args.rules, standalone=args.standalone)

    out_path = args.output or args.input.with_suffix(".tex")
    out_path.write_text(latex, encoding="utf-8")

    if args.write_main:
        main_tex = generate_main_tex(included_tex=out_path, rules_path=args.rules)
        (out_path.parent / "main.tex").write_text(main_tex, encoding="utf-8")


if __name__ == "__main__":
    main()
