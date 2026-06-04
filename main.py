import streamlit as st
import pandas as pd
from io import BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.graphics.barcode import code128
from reportlab.lib import colors


# -----------------------------
# Read uploaded file
# -----------------------------
def read_ids(uploaded_file):
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file, header=None)
        ids = df.iloc[:, 0].astype(str).tolist()
    else:
        content = uploaded_file.read().decode("utf-8")
        ids = [line.strip() for line in content.splitlines() if line.strip()]
    return ids


# -----------------------------
# Generate PDF
# -----------------------------
def generate_pdf(ids, cols, rows):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    page_width, page_height = A4

    cell_width = page_width / cols
    cell_height = page_height / rows

    items_per_page = cols * rows

    def draw_cut_lines():
        c.setStrokeColor(colors.grey)
        c.setDash(2, 2)

        # vertical lines
        for i in range(1, cols):
            x = i * cell_width
            c.line(x, 0, x, page_height)

        # horizontal lines
        for j in range(1, rows):
            y = j * cell_height
            c.line(0, y, page_width, y)

        c.setDash()

    for idx, id_value in enumerate(ids):

        pos = idx % items_per_page

        # new page
        if idx > 0 and pos == 0:
            draw_cut_lines()
            c.showPage()

        col = pos % cols
        row = pos // cols

        x = col * cell_width
        y = page_height - (row + 1) * cell_height

        # -----------------------------
        # Layout spacing (IMPORTANT)
        # -----------------------------
        top_padding = cell_height * 0.10
        bottom_padding = cell_height * 0.10

        usable_height = cell_height - (top_padding + bottom_padding)

        # -----------------------------
        # Barcode
        # -----------------------------
        barcode_height = cell_height * 0.55

        barcode = code128.Code128(
            id_value,
            barHeight=barcode_height,
            barWidth=1.1
        )

        barcode_x = x + (cell_width - barcode.width) / 2
        barcode_y = y + bottom_padding + (usable_height * 0.45)

        barcode.drawOn(c, barcode_x, barcode_y)

        # -----------------------------
        # Human-readable text
        # -----------------------------
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.black)

        text_y = y + bottom_padding + 5

        c.drawCentredString(
            x + cell_width / 2,
            text_y,
            id_value
        )

    # final page cut lines
    draw_cut_lines()
    c.save()

    buffer.seek(0)
    return buffer


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="A4 Barcode Generator", layout="centered")

st.title("📦 A4 Barcode PDF Generator")

uploaded_file = st.file_uploader("Upload CSV or TXT file (one ID per line)", type=["csv", "txt"])

cols = st.number_input("Columns per A4 page", min_value=1, max_value=10, value=3)
rows = st.number_input("Rows per A4 page", min_value=1, max_value=15, value=8)

if uploaded_file:

    ids = read_ids(uploaded_file)

    st.success(f"Loaded {len(ids)} IDs")

    if st.button("Generate PDF"):

        pdf_buffer = generate_pdf(ids, cols, rows)

        st.success("PDF generated successfully!")

        st.download_button(
            label="⬇ Download Barcode PDF",
            data=pdf_buffer,
            file_name="a4_barcodes.pdf",
            mime="application/pdf"
        )
