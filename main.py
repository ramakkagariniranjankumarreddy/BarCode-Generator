import streamlit as st
from io import BytesIO
import math

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.graphics.barcode import code128
from reportlab.lib.units import mm


# =========================================================
# UI
# =========================================================

st.set_page_config(page_title="Barcode Generator", layout="wide")

st.title("📦 A4 Barcode Label Generator")

uploaded_file = st.file_uploader(
    "Upload TXT/CSV (one ID per line)",
    type=["txt", "csv"]
)

col1, col2 = st.columns(2)

with col1:
    rows = st.number_input("Rows per page", 1, 50, 8)

with col2:
    cols = st.number_input("Columns per page", 1, 20, 3)

generate = st.button("Generate PDF")


# =========================================================
# DOTTED LINE (CUT MARKS)
# =========================================================

def dotted_line(c, x1, y1, x2, y2, dash=2 * mm, gap=2 * mm):

    if abs(x1 - x2) < 0.1:
        y = y1
        while y < y2:
            c.line(x1, y, x2, min(y + dash, y2))
            y += dash + gap
    else:
        x = x1
        while x < x2:
            c.line(x, y1, min(x + dash, x2), y2)
            x += dash + gap


# =========================================================
# PDF GENERATION
# =========================================================

def generate_pdf(ids, rows, cols):

    buffer = BytesIO()
    page_w, page_h = A4

    c = canvas.Canvas(buffer, pagesize=A4)

    margin = 10 * mm

    usable_w = page_w - 2 * margin
    usable_h = page_h - 2 * margin

    cell_w = usable_w / cols
    cell_h = usable_h / rows

    per_page = rows * cols
    pages = math.ceil(len(ids) / per_page)

    idx = 0

    for _ in range(pages):

        # ============================
        # CUT LINES (ONLY INTERNAL)
        # ============================

        c.setLineWidth(0.3)

        for i in range(1, cols):
            x = margin + i * cell_w
            dotted_line(c, x, margin, x, page_h - margin)

        for i in range(1, rows):
            y = margin + i * cell_h
            dotted_line(c, margin, y, page_w - margin, y)

        # ============================
        # LABELS
        # ============================

        for slot in range(per_page):

            if idx >= len(ids):
                break

            value = ids[idx]

            r = slot // cols
            col = slot % cols

            x0 = margin + col * cell_w
            y0 = page_h - margin - (r + 1) * cell_h

            # -----------------------------------------
            # AVAILABLE SPACE INSIDE CELL
            # -----------------------------------------

            max_w = cell_w * 0.95   # almost full width
            max_h = cell_h * 0.55   # safe height

            # -----------------------------------------
            # FORCE FULL WIDTH BARCODE (CORE FIX)
            # -----------------------------------------

            barcode = code128.Code128(
                value,
                barHeight=max_h,
                barWidth=0.2  # start small, we scale later
            )

            bw = barcode.width
            bh = barcode.height

            # WIDTH-FIRST SCALING (KEY IDEA)
            scale = max_w / bw

            # HEIGHT SAFETY CLAMP
            scale = min(scale, max_h / bh)

            final_w = bw * scale
            final_h = bh * scale

            # -----------------------------------------
            # CENTERING
            # -----------------------------------------

            bx = x0 + (cell_w - final_w) / 2
            by = y0 + (cell_h - final_h) / 2 + (cell_h * 0.04)

            c.saveState()
            c.translate(bx, by)
            c.scale(scale, scale)
            barcode.drawOn(c, 0, 0)
            c.restoreState()

            # -----------------------------------------
            # TEXT
            # -----------------------------------------

            font_size = max(6, min(10, cell_h / 10))

            c.setFont("Helvetica", font_size)

            c.drawCentredString(
                x0 + cell_w / 2,
                y0 + cell_h * 0.12,
                value
            )

            idx += 1

        c.showPage()

    c.save()
    buffer.seek(0)

    return buffer


# =========================================================
# RUN APP
# =========================================================

if generate:

    if uploaded_file is None:
        st.error("Please upload a file")
        st.stop()

    content = uploaded_file.read().decode("utf-8")

    ids = [x.strip() for x in content.splitlines() if x.strip()]

    if not ids:
        st.error("No IDs found")
        st.stop()

    per_page = rows * cols
    pages = math.ceil(len(ids) / per_page)

    st.info(
        f"""
Total IDs: {len(ids)}
Labels per page: {per_page}
Pages: {pages}
"""
    )

    with st.spinner("Generating PDF..."):

        pdf = generate_pdf(ids, rows, cols)

    st.success("PDF generated successfully!")

    st.download_button(
        "Download PDF",
        pdf,
        file_name="barcode_labels.pdf",
        mime="application/pdf"
    )
