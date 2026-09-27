from pathlib import Path
from fpdf import FPDF
from docx import Document as DocxDocument


def convert_txt_to_pdf(txt_file_path: Path | str, output_pdf_path: Path | str) -> Path:
    txt_path = Path(txt_file_path)
    out_path = Path(output_pdf_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("helvetica", size=12)

    with txt_path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            clean_line = line.encode("latin-1", "replace").decode("latin-1")
            pdf.multi_cell(w=0, h=6, text=clean_line)

    pdf.output(str(out_path))
    return out_path


def convert_docx_to_pdf(docx_file_path: Path | str, output_pdf_path: Path | str) -> Path:
    docx_path = Path(docx_file_path)
    out_path = Path(output_pdf_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("helvetica", size=12)

    docx_doc = DocxDocument(docx_path)
    for p in docx_doc.paragraphs:
        p_text = p.text.strip()
        if p_text:
            clean_text = p_text.encode("latin-1", "replace").decode("latin-1")
            pdf.multi_cell(w=0, h=6, text=clean_text)
            pdf.ln(2)

    pdf.output(str(out_path))
    return out_path
