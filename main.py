import streamlit as st
from io import BytesIO
import math

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.graphics.barcode import code128
from reportlab.lib.units import mm

# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="Barcode Sheet Generator",
    layout="wide"
)

st.title("📦 Barcode Sheet Generator")

st.markdown("""
Upload a TXT or CSV file with one ID per line.

Example:

H1100022867
H1100022868
H1100022869
""")

# ==========================================================
# INPUTS
# ==========================================================

uploaded_file = st.file_uploader(
    "Upload TXT / CSV",
    type=["txt", "csv"]
)

c1, c2 = st.columns(2)

with c1:
    rows = st.number_input(
        "Rows",
        min_value=1,
        max_value=50,
        value=8
    )

with c2:
    cols = st.number_input(
        "Columns",
        min_value=1,
        max_value=20,
        value=3
    )

st.subheader("Barcode Fit Settings")

c3, c4 = st.columns(2)

with c3:
    barcode_width_pct = st.slider(
        "Barcode Width %",
        min_value=50,
        max_value=95,
        value=90
    )

with c4:
    barcode_height_pct = st.slider(
        "Barcode Height %",
        min_value=20,
        max_value=70,
        value=40
    )

generate_btn = st.button("Generate PDF")

# ==========================================================
# DOTTED LINE
# ==========================================================

def draw_dotted_line(
    c,
    x1,
    y1,
    x2,
    y2,
    dash=2 * mm,
    gap=1 * mm
):
    if abs(x1 - x2) < 0.1:
        y = y1

        while y < y2:
            c.line(
                x1,
                y,
                x2,
                min(y + dash, y2)
            )
            y += dash + gap

    else:
        x = x1

        while x < x2:
            c.line(
                x,
                y1,
                min(x + dash, x2),
                y2
            )
            x += dash + gap

# ==========================================================
# PDF GENERATOR
# ==========================================================

def generate_pdf(
    ids,
    rows,
    cols,
    barcode_width_pct,
    barcode_height_pct
):

    buffer = BytesIO()

    page_width, page_height = A4

    pdf = canvas.Canvas(
        buffer,
        pagesize=A4
    )

    margin = 10 * mm

    usable_width = page_width - (2 * margin)
    usable_height = page_height - (2 * margin)

    cell_width = usable_width / cols
    cell_height = usable_height / rows

    labels_per_page = rows * cols

    total_pages = math.ceil(
        len(ids) / labels_per_page
    )

    current_idx = 0

    for page in range(total_pages):

        # ==========================================
        # DOTTED CUT LINES
        # ==========================================

        pdf.setLineWidth(0.3)

        # Internal vertical lines
        for col in range(1, cols):

            x = margin + col * cell_width

            draw_dotted_line(
                pdf,
                x,
                margin,
                x,
                page_height - margin
            )

        # Internal horizontal lines
        for row in range(1, rows):

            y = margin + row * cell_height

            draw_dotted_line(
                pdf,
                margin,
                y,
                page_width - margin,
                y
            )

        # ==========================================
        # LABELS
        # ==========================================

        for slot in range(labels_per_page):

            if current_idx >= len(ids):
                break

            value = ids[current_idx]

            row_num = slot // cols
            col_num = slot % cols

            x0 = margin + col_num * cell_width

            y0 = (
                page_height
                - margin
                - ((row_num + 1) * cell_height)
            )

            # ----------------------------------
            # Cell Padding
            # ----------------------------------

            pad_x = cell_width * 0.03
            pad_y = cell_height * 0.03

            # ----------------------------------
            # Desired Barcode Area
            # ----------------------------------

            target_width = (
                cell_width
                * barcode_width_pct
                / 100
            )

            target_height = (
                cell_height
                * barcode_height_pct
                / 100
            )

            # ----------------------------------
            # Initial Barcode
            # ----------------------------------

            barcode = code128.Code128(
                value,
                barWidth=0.5,
                barHeight=target_height
            )

            original_width = barcode.width
            original_height = barcode.height

            scale_x = target_width / original_width
            scale_y = target_height / original_height

            scale = min(scale_x, scale_y)

            final_width = original_width * scale
            final_height = original_height * scale

            # ----------------------------------
            # Center Barcode
            # ----------------------------------

            barcode_x = (
                x0
                + (cell_width - final_width) / 2
            )

            barcode_y = (
                y0
                + (cell_height * 0.35)
            )

            pdf.saveState()

            pdf.translate(
                barcode_x,
                barcode_y
            )

            pdf.scale(
                scale,
                scale
            )

            barcode.drawOn(
                pdf,
                0,
                0
            )

            pdf.restoreState()

            # ----------------------------------
            # Human Readable Text
            # ----------------------------------

            font_size = max(
                6,
                min(
                    10,
                    cell_height / 8
                )
            )

            pdf.setFont(
                "Helvetica",
                font_size
            )

            text_y = y0 + (cell_height * 0.15)

            pdf.drawCentredString(
                x0 + (cell_width / 2),
                text_y,
                value
            )

            current_idx += 1

        pdf.showPage()

    pdf.save()

    buffer.seek(0)

    return buffer

# ==========================================================
# PROCESS
# ==========================================================

if generate_btn:

    if uploaded_file is None:
        st.error("Please upload a file.")
        st.stop()

    try:

        content = uploaded_file.read().decode(
            "utf-8"
        )

        ids = [
            line.strip()
            for line in content.splitlines()
            if line.strip()
        ]

        if len(ids) == 0:
            st.error("No IDs found.")
            st.stop()

        labels_per_page = rows * cols

        total_pages = math.ceil(
            len(ids) / labels_per_page
        )

        st.info(
            f"""
IDs Loaded: {len(ids)}

Labels Per Page: {labels_per_page}

Pages Required: {total_pages}
"""
        )

        with st.spinner(
            "Generating PDF..."
        ):

            pdf_data = generate_pdf(
                ids,
                rows,
                cols,
                barcode_width_pct,
                barcode_height_pct
            )

        st.success("PDF generated successfully.")

        st.download_button(
            label="📄 Download Barcode PDF",
            data=pdf_data,
            file_name="barcode_labels.pdf",
            mime="application/pdf"
        )

    except Exception as e:
        st.error(str(e))
