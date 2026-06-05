import streamlit as st
import pandas as pd
from io import BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.graphics.barcode import code128
from reportlab.lib import colors


# -----------------------------
# Read file (CSV/TXT)
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

        # Vertical cut lines
        for i in range(1, cols):
            x = i * cell_width
            c.line(x, 0, x, page_height)

        # Horizontal cut lines
        for j in range(1, rows):
            y = j * cell_height
            c.line(0, y, page_width, y)

        c.setDash()

    for idx, id_value in enumerate(ids):

        pos = idx % items_per_page

        if idx > 0 and pos == 0:
            draw_cut_lines()
            c.showPage()

        col = pos % cols
        row = pos // cols

        x = col * cell_width
        y = page_height - (row + 1) * cell_height

        center_x = x + cell_width / 2

        # -----------------------------
        # Dynamic sizes based on cell
        # -----------------------------
        header_font_size = cell_height * 0.08  # Header font
        main_barcode_height = cell_height * 0.30
        main_label_font = cell_height * 0.08
        small_barcode_height = cell_height * 0.10
        small_label_font = cell_height * 0.06
        gap = cell_height * 0.03  # gap between elements

        # =====================================
        # DTDC Header above Main Barcode
        # =====================================
        header_text = "DTDC Nehru Bazaar"
        c.setFont("Helvetica-Bold", header_font_size)
        header_y = y + cell_height - header_font_size - gap
        c.drawCentredString(center_x, header_y, header_text)

        # =====================================
        # Main Barcode
        # =====================================
        main_barcode = code128.Code128(
            id_value,
            barHeight=main_barcode_height,
            barWidth=1.1
        )
        main_x = x + (cell_width - main_barcode.width) / 2
        main_y = header_y - main_barcode_height - gap
        main_barcode.drawOn(c, main_x, main_y)

        # Value below main barcode
        c.setFillColor(colors.black)
        c.setFont("Helvetica", main_label_font)
        c.drawCentredString(center_x, main_y - main_label_font - gap, id_value)

        # =====================================
        # Small Dashed Cut Mark
        # =====================================
        cut_y = y + cell_height * 0.32
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.5)
        c.setDash(2, 2)
        c.line(center_x - 30, cut_y, center_x + 30, cut_y)
        c.setDash()

        # =====================================
        # DTDC Text below cut mark
        # =====================================
        c.setFont("Helvetica-Bold", small_label_font)
        c.drawCentredString(center_x, cut_y - small_label_font - gap, "DTDC - Nehru Bazaar")

        # =====================================
        # Smaller Barcode at bottom
        # =====================================
        small_barcode = code128.Code128(
            id_value,
            barHeight=small_barcode_height,
            barWidth=0.6
        )
        small_x = x + (cell_width - small_barcode.width) / 2
        small_y = y + cell_height * 0.12
        small_barcode.drawOn(c, small_x, small_y)

        # Value below small barcode
        c.setFont("Helvetica", small_label_font)
        c.drawCentredString(center_x, small_y - small_label_font - gap, id_value)

    draw_cut_lines()
    c.save()

    buffer.seek(0)
    return buffer


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(
    page_title="Bar Code Generator (DTDC - Nehru Bazaar)",
    layout="centered"
)

st.title("Bar Code Generator (DTDC - Nehru Bazaar)")

uploaded_file = st.file_uploader(
    "Upload CSV or TXT file (one ID per line)",
    type=["csv", "txt"]
)

cols = st.number_input(
    "Columns per A4 page",
    min_value=1,
    max_value=10,
    value=3
)

rows = st.number_input(
    "Rows per A4 page",
    min_value=1,
    max_value=15,
    value=8
)

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
