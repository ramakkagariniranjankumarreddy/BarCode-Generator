import streamlit as st
from io import BytesIO
import math

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.graphics.barcode import code128
from reportlab.lib.units import mm

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Barcode Sheet Generator",
    layout="wide"
)

st.title("📦 Barcode Sheet Generator")

st.markdown(
    """
Upload a TXT/CSV file containing one ID per line.

Example:

H1100022867  
H1100022868  
H1100022869
"""
)

# ============================================================
# INPUTS
# ============================================================

uploaded_file = st.file_uploader(
    "Upload TXT/CSV",
    type=["txt", "csv"]
)

col1, col2 = st.columns(2)

with col1:
    rows = st.number_input(
        "Rows",
        min_value=1,
        max_value=50,
        value=8
    )

with col2:
    cols = st.number_input(
        "Columns",
        min_value=1,
        max_value=20,
        value=3
    )

generate = st.button("Generate PDF")


# ============================================================
# DOTTED LINE
# ============================================================

def draw_dotted_line(c, x1, y1, x2, y2,
                     dash_length=2 * mm,
                     gap_length=1 * mm):

    if abs(x1 - x2) < 0.1:
        y = y1

        while y < y2:
            c.line(
                x1,
                y,
                x2,
                min(y + dash_length, y2)
            )

            y += dash_length + gap_length

    elif abs(y1 - y2) < 0.1:

        x = x1

        while x < x2:
            c.line(
                x,
                y1,
                min(x + dash_length, x2),
                y2
            )

            x += dash_length + gap_length


# ============================================================
# PDF GENERATOR
# ============================================================

def generate_pdf(ids, rows, cols):

    pdf_buffer = BytesIO()

    page_width, page_height = A4

    c = canvas.Canvas(
        pdf_buffer,
        pagesize=A4
    )

    # margins
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

        # ------------------------------------------------
        # Internal vertical dotted cut lines
        # ------------------------------------------------

        for col in range(1, cols):

            x = margin + (col * cell_width)

            draw_dotted_line(
                c,
                x,
                margin,
                x,
                page_height - margin
            )

        # ------------------------------------------------
        # Internal horizontal dotted cut lines
        # ------------------------------------------------

        for row in range(1, rows):

            y = margin + (row * cell_height)

            draw_dotted_line(
                c,
                margin,
                y,
                page_width - margin,
                y
            )

        # ------------------------------------------------
        # Draw labels
        # ------------------------------------------------

        for slot in range(labels_per_page):

            if current_idx >= len(ids):
                break

            value = ids[current_idx]

            row_no = slot // cols
            col_no = slot % cols

            x0 = margin + (col_no * cell_width)

            y0 = (
                page_height
                - margin
                - ((row_no + 1) * cell_height)
            )

            # ----------------------------------------
            # Padding
            # ----------------------------------------

            padding_x = cell_width * 0.08
            padding_y = cell_height * 0.08

            # ----------------------------------------
            # Barcode
            # ----------------------------------------

            barcode = code128.Code128(
                value,
                barHeight=cell_height * 0.35,
                barWidth=0.45
            )

            barcode_width = barcode.width

            available_width = (
                cell_width
                - (2 * padding_x)
            )

            scale = min(
                1.0,
                available_width / barcode_width
            )

            barcode_x = (
                x0
                + (cell_width / 2)
                - ((barcode_width * scale) / 2)
            )

            barcode_y = (
                y0
                + (cell_height * 0.35)
            )

            c.saveState()

            c.translate(
                barcode_x,
                barcode_y
            )

            c.scale(
                scale,
                scale
            )

            barcode.drawOn(
                c,
                0,
                0
            )

            c.restoreState()

            # ----------------------------------------
            # Human readable text
            # ----------------------------------------

            font_size = max(
                6,
                min(
                    10,
                    cell_height / 8
                )
            )

            c.setFont(
                "Helvetica",
                font_size
            )

            text_y = y0 + (cell_height * 0.15)

            c.drawCentredString(
                x0 + (cell_width / 2),
                text_y,
                value
            )

            current_idx += 1

        c.showPage()

    c.save()

    pdf_buffer.seek(0)

    return pdf_buffer


# ============================================================
# PROCESS
# ============================================================

if generate:

    if uploaded_file is None:

        st.error(
            "Please upload a file."
        )

        st.stop()

    content = uploaded_file.read().decode(
        "utf-8"
    )

    ids = [
        line.strip()
        for line in content.splitlines()
        if line.strip()
    ]

    if not ids:

        st.error(
            "No IDs found in file."
        )

        st.stop()

    capacity = rows * cols

    pages = math.ceil(
        len(ids) / capacity
    )

    st.info(
        f"""
Loaded {len(ids)} IDs

Labels per page: {capacity}

Pages required: {pages}
"""
    )

    with st.spinner(
        "Generating PDF..."
    ):

        pdf = generate_pdf(
            ids,
            rows,
            cols
        )

    st.success(
        "PDF generated successfully."
    )

    st.download_button(
        label="📄 Download PDF",
        data=pdf,
        file_name="barcode_labels.pdf",
        mime="application/pdf"
    )
