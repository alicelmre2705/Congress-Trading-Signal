"""Convertit un rapport Markdown (ex. docs/RAPPORT_QUALITE.md) en PDF imprimable A4.

Aucune dépendance externe (pandoc/wkhtmltopdf/weasyprint absents de la machine) : petit convertisseur
maison Markdown→HTML du sous-ensemble utilisé par le rapport (titres, gras/italique, `code`, tables
`|…|`, blocs ```` ``` ````, blockquote `>`, listes `-`/`1.`, images `![]()`), puis rendu PDF via
**Google Chrome headless**. Les **figures sont incluses en petit format** (CSS `img.fig` plafonnée) —
contrairement à l'ancienne version texte-seul.

Usage : `python -m common.report_pdf`  (→ docs/RAPPORT_QUALITE.pdf)
        `python -m common.report_pdf docs/AUTRE.md`
"""
import html
import re
import subprocess
import sys
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CSS = """
@page { size: A4; margin: 12mm; }
* { box-sizing: border-box; }
body { font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif; font-size: 10px;
       color: #111; line-height: 1.38; }
h1 { font-size: 18px; margin: 0 0 6px; }
h2 { font-size: 14px; margin: 16px 0 4px; border-bottom: 1px solid #ccc; padding-bottom: 2px; }
h3 { font-size: 11.5px; margin: 11px 0 3px; color: #222; }
p  { margin: 4px 0; }
ul, ol { margin: 4px 0 4px 18px; }
li { margin: 1px 0; }
blockquote { border-left: 3px solid #bbb; background: #fafafa; margin: 6px 0; padding: 3px 9px;
             color: #333; }
code { font-family: Menlo, Consolas, monospace; font-size: 8px; background: #f2f2f2; padding: 0 2px;
       border-radius: 2px; }
pre { background: #f5f5f5; padding: 6px 8px; font-size: 8px; line-height: 1.3; overflow: hidden;
      page-break-inside: avoid; border: 1px solid #e2e2e2; border-radius: 3px; }
pre code { background: none; padding: 0; font-size: 8px; }
table { border-collapse: collapse; font-size: 7.5px; width: 100%; margin: 5px 0; }
th, td { border: 1px solid #bbb; padding: 2px 4px; text-align: left; vertical-align: top; }
th { background: #eee; }
table, tr { page-break-inside: avoid; }
em { color: #555; }
/* Figures : PETITES et centrées, jamais coupées entre deux pages. */
.figwrap { text-align: center; page-break-inside: avoid; margin: 7px 0; }
img.fig { max-width: 330px; width: auto; height: auto; }
"""


def _inline(s: str) -> str:
    """Formatage inline : échappe le HTML, protège les `code`, puis gras/italique/liens."""
    s = html.escape(s, quote=False)
    codes = []

    def _stash(m):
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    s = re.sub(r"`([^`]+)`", _stash, s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)   # liens
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)            # gras
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", s)  # italique
    s = re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{html.escape(codes[int(m.group(1))], quote=False)}</code>", s)
    return s


def _cells(row: str):
    """Découpe une ligne de table sur les `|` NON échappés, puis rétablit les `\\|` littéraux."""
    parts = re.split(r"(?<!\\)\|", row.strip())
    parts = [p for p in parts]
    if parts and parts[0] == "":
        parts = parts[1:]
    if parts and parts[-1] == "":
        parts = parts[:-1]
    return [c.strip().replace("\\|", "|") for c in parts]


def md_to_html(md: str, base_dir: Path) -> str:
    lines = md.split("\n")
    out, i, n = [], 0, len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        # bloc de code ``` … ```
        if stripped.startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(html.escape(lines[i], quote=False))
                i += 1
            i += 1
            out.append("<pre><code>" + "\n".join(buf) + "</code></pre>")
            continue

        # image seule sur sa ligne  ![alt](src)
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", stripped)
        if m:
            src = m.group(2)
            if not src.startswith(("http", "file:", "/")):
                src = "file://" + str((base_dir / src).resolve())
            out.append(f'<div class="figwrap"><img class="fig" alt="{html.escape(m.group(1))}" src="{src}"></div>')
            i += 1
            continue

        # table : lignes consécutives commençant par |
        if stripped.startswith("|"):
            tbl = []
            while i < n and lines[i].strip().startswith("|"):
                tbl.append(lines[i])
                i += 1
            rows = [r for r in tbl if not re.match(r"^\s*\|[\s:|-]+\|\s*$", r)]  # retire le séparateur ---
            if rows:
                head = _cells(rows[0])
                out.append("<table><thead><tr>" + "".join(f"<th>{_inline(c)}</th>" for c in head) + "</tr></thead><tbody>")
                for r in rows[1:]:
                    out.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in _cells(r)) + "</tr>")
                out.append("</tbody></table>")
            continue

        # titres
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{_inline(m.group(2))}</h{lvl}>")
            i += 1
            continue

        # blockquote (lignes > consécutives)
        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(_inline(re.sub(r"^\s*>\s?", "", lines[i])))
                i += 1
            out.append("<blockquote>" + "<br>".join(buf) + "</blockquote>")
            continue

        # listes (- …  ou  1. …)
        if re.match(r"^(\-|\d+\.)\s+", stripped):
            ordered = bool(re.match(r"^\d+\.\s+", stripped))
            tag = "ol" if ordered else "ul"
            buf = []
            while i < n and re.match(r"^(\-|\d+\.)\s+", lines[i].strip()):
                buf.append("<li>" + _inline(re.sub(r"^(\-|\d+\.)\s+", "", lines[i].strip())) + "</li>")
                i += 1
            out.append(f"<{tag}>" + "".join(buf) + f"</{tag}>")
            continue

        # ligne vide / paragraphe
        if stripped:
            out.append(f"<p>{_inline(stripped)}</p>")
        i += 1

    body = "\n".join(out)
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"


def build_pdf(md_path: Path) -> Path:
    md_path = Path(md_path).resolve()
    pdf_path = md_path.with_suffix(".pdf")
    html_path = md_path.with_name(md_path.stem + "_print.html")
    html_path.write_text(md_to_html(md_path.read_text(encoding="utf-8"), md_path.parent), encoding="utf-8")
    subprocess.run([
        CHROME, "--headless=new", "--no-pdf-header-footer",
        "--run-all-compositor-stages-before-draw", "--virtual-time-budget=10000",
        f"--print-to-pdf={pdf_path}", "file://" + str(html_path),
    ], check=True, capture_output=True)
    html_path.unlink(missing_ok=True)   # HTML intermédiaire jetable
    return pdf_path


def main():
    md = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "docs" / "RAPPORT_QUALITE.md"
    pdf = build_pdf(md)
    print(f"PDF écrit : {pdf}")


if __name__ == "__main__":
    main()
