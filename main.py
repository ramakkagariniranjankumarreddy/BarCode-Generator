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
st.title("📦 Barcode Label PDF Generator")

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
# DOTTED CUT LINES
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

        # =========================================
        # CUT LINES (only internal)
        # =========================================

        c.setLineWidth(0.3)

        for i in range(1, cols):
            x = margin + i * cell_w
            dotted_line(c, x, margin, x, page_h - margin)

        for i in range(1, rows):
            y = margin + i * cell_h
            dotted_line(c, margin, y, page_w - margin, y)

        # =========================================
        # LABELS
        # =========================================

        for slot in range(per_page):

            if idx >= len(ids):
                break

            value = ids[idx]

            r = slot // cols
            col = slot % cols

            x0 = margin + col * cell_w
            y0 = page_h - margin - (r + 1) * cell_h

            # -----------------------------------------
            # Create barcode (natural size first)
            # -----------------------------------------

            barcode = code128.Code128(
                value,
                barHeight=cell_h * 0.50,   # let it decide natural width
                barWidth=0.5
            )

            bw = barcode.width
            bh = barcode.height

            # -----------------------------------------
            # FIT TO CELL (no ratio constraints)
            # -----------------------------------------

            max_w = cell_w * 0.90
            max_h = cell_h * 0.55

            scale = min(max_w / bw, max_h / bh)

            final_w = bw * scale
            final_h = bh * scale

            # -----------------------------------------
            # CENTER POSITION
            # -----------------------------------------

            bx = x0 + (cell_w - final_w) / 2
            by = y0 + (cell_h - final_h) / 2 + 5  # slight lift

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
# RUN
# =========================================================

if generate:

    if uploaded_file is None:
        st.error("Upload a file first")
        st.stop()

    content = uploaded_file.read().decode("utf-8")

    ids = [x.strip() for x in content.splitlines() if x.strip()]

    if not ids:
        st.error("No IDs found")
        st.stop()

    st.info(f"Total IDs: {len(ids)} | Per page: {rows*cols}")

    with st.spinner("Generating PDF..."):

        pdf = generate_pdf(ids, rows, cols)

    st.success("Done!")

    st.download_button(
        "Download PDF",
        pdf,
        file_name="barcodes.pdf",
        mime="application/pdf"
    )
