import streamlit as st
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import math
import tempfile
import os

st.set_page_config(page_title="Barcode PDF Generator", layout="wide")

st.title("Multi-Page Barcode Sheet Generator")

uploaded_file = st.file_uploader(
    "Upload TXT/CSV File (one ID per line)",
    type=["txt", "csv"]
)

col1, col2 = st.columns(2)

with col1:
    rows = st.number_input(
        "Rows per page",
        min_value=1,
        max_value=50,
        value=8
    )

with col2:
    cols = st.number_input(
        "Columns per page",
        min_value=1,
        max_value=20,
        value=3
    )

generate_btn = st.button("Generate PDF")


# --------------------------------------------------
# Barcode Generator
# --------------------------------------------------
def create_barcode(code):

    buffer = BytesIO()

    barcode = Code128(
        str(code),
        writer=ImageWriter()
    )

    barcode.write(
        buffer,
        options={
            "module_width": 0.25,
            "module_height": 18,
            "font_size": 10,
            "text_distance": 2,
            "quiet_zone": 2
        }
    )

    buffer.seek(0)

    img = Image.open(buffer).convert("RGB")

    return img


# --------------------------------------------------
# PDF Creator
# --------------------------------------------------
def create_pdf(ids, rows, cols):

    pdf_buffer = BytesIO()

    # A4 size in points
    PAGE_WIDTH = 595
    PAGE_HEIGHT = 842

    margin = 20

    cell_width = (PAGE_WIDTH - 2 * margin) / cols
    cell_height = (PAGE_HEIGHT - 2 * margin) / rows

    c = canvas.Canvas(pdf_buffer, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))

    page_capacity = rows * cols

    total_pages = math.ceil(len(ids) / page_capacity)

    current_index = 0

    for page_no in range(total_pages):

        # Draw cut lines
        for col in range(cols + 1):
            x = margin + col * cell_width

            c.line(
                x,
                margin,
                x,
                PAGE_HEIGHT - margin
            )

        for row in range(rows + 1):
            y = margin + row * cell_height

            c.line(
                margin,
                y,
                PAGE_WIDTH - margin,
                y
            )

        for slot in range(page_capacity):

            if current_index >= len(ids):
                break

            barcode_img = create_barcode(ids[current_index])

            tmp = BytesIO()
            barcode_img.save(tmp, format="PNG")
            tmp.seek(0)

            row_num = slot // cols
            col_num = slot % cols

            x0 = margin + col_num * cell_width
            y0 = PAGE_HEIGHT - margin - ((row_num + 1) * cell_height)

            barcode_width = cell_width * 0.85
            barcode_height = cell_height * 0.60

            img_x = x0 + (cell_width - barcode_width) / 2
            img_y = y0 + (cell_height - barcode_height) / 2

            c.drawImage(
                ImageReader(tmp),
                img_x,
                img_y,
                width=barcode_width,
                height=barcode_height,
                preserveAspectRatio=True
            )

            current_index += 1

        c.showPage()

    c.save()

    pdf_buffer.seek(0)

    return pdf_buffer


# --------------------------------------------------
# Process
# --------------------------------------------------
if generate_btn:

    if uploaded_file is None:
        st.error("Upload a file first.")
        st.stop()

    content = uploaded_file.read().decode("utf-8")

    ids = [
        line.strip()
        for line in content.splitlines()
        if line.strip()
    ]

    if not ids:
        st.error("No IDs found.")
        st.stop()

    page_capacity = rows * cols
    total_pages = math.ceil(len(ids) / page_capacity)

    st.success(
        f"{len(ids)} IDs loaded. "
        f"Will generate {total_pages} A4 page(s)."
    )

    with st.spinner("Generating PDF..."):

        pdf_data = create_pdf(ids, rows, cols)

    st.download_button(
        label="📄 Download Barcode PDF",
        data=pdf_data,
        file_name="barcode_labels.pdf",
        mime="application/pdf"
    )