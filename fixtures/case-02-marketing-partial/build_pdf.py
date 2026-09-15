"""Build cv.pdf from cv.md for this fixture.

The generated cv.pdf is committed next to this script; rerun it only when
cv.md changes. Requires fpdf2 (declared in backend/requirements.txt once the
backend lands):

    pip install fpdf2
    python build_pdf.py
"""

from pathlib import Path

from fpdf import FPDF

HERE = Path(__file__).resolve().parent
CV_MD = HERE / "cv.md"
CV_PDF = HERE / "cv.pdf"


def build_pdf(cv_md: Path, cv_pdf: Path) -> None:
    """Render a fixture cv.md into a one-page A4 PDF."""
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(20, 20, 20)
    pdf.add_page()

    for raw in cv_md.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            pdf.ln(4)
        elif line.startswith("# "):
            pdf.set_font("helvetica", "B", 20)
            pdf.multi_cell(0, 9, line[2:].strip(), new_x="LMARGIN", new_y="NEXT")
        elif line.startswith("## "):
            pdf.ln(3)
            pdf.set_font("helvetica", "B", 13)
            pdf.cell(0, 8, line[3:].strip().upper(), new_x="LMARGIN", new_y="NEXT")
        elif line.startswith("### "):
            pdf.ln(2)
            pdf.set_font("helvetica", "B", 11.5)
            pdf.multi_cell(0, 6.5, line[4:].strip(), new_x="LMARGIN", new_y="NEXT")
        elif line.startswith("- "):
            pdf.set_font("helvetica", "", 10.5)
            pdf.multi_cell(0, 5.5, "-   " + line[2:].strip(), new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.set_font("helvetica", "", 10.5)
            pdf.multi_cell(0, 5.5, line, new_x="LMARGIN", new_y="NEXT")

    pdf.output(str(cv_pdf))


if __name__ == "__main__":
    build_pdf(CV_MD, CV_PDF)
    print(f"Wrote {CV_PDF}")