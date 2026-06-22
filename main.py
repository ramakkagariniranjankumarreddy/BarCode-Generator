import streamlit as st
import pandas as pd
from io import BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.graphics.barcode import code128
from reportlab.lib.units import mm
from reportlab.lib import colors


# -----------------------------
# Read file
# -----------------------------
def read_ids(uploaded_file):
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file, header=None)
        return df.iloc[:, 0].astype(str).tolist()
    else:
        content = uploaded_file.read().decode("utf-8")
        return [line.strip() for line in content.splitlines() if line.strip()]


# =========================================================
# FORMAT A (Fixed Grid DTDC Layout)
# =========================================================
def generate_format_a(ids):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    page_width, page_height = A4

    cols = 4
    rows = 14

    label_width = 48 * mm
    label_height = 20 * mm

    items_per_page = cols * rows

    top_margin = 2 * mm
    left_margin = 6 * mm

    col_gap = 2 * mm
    row_gap = 1 * mm

    start_x = left_margin
    start_y = page_height - top_margin

    for idx, id_value in enumerate(ids):

        pos = idx % items_per_page

        if idx > 0 and pos == 0:
            c.showPage()

        col = pos % cols
        row = pos // cols

        x = start_x + col * (label_width + col_gap)
        y = start_y - (row * (label_height + row_gap)) - label_height

        center_x = x + label_width / 2

        top_zone = y + label_height - 4 * mm
        barcode_zone = y + 6 * mm
        number_zone = y + 2 * mm

        c.setFont("Helvetica-Bold", 5)
        c.drawCentredString(center_x, top_zone, "DTDC- Nehru Bazaar")

        barcode = code128.Code128(
            id_value,
            barHeight=9 * mm,
            barWidth=0.9
        )

        barcode_x = x + (label_width - barcode.width) / 2
        barcode.drawOn(c, barcode_x, barcode_zone)

        c.setFont("Helvetica", 6)
        c.drawCentredString(center_x, number_zone, id_value)

    c.save()
    buffer.seek(0)
    return buffer


# =========================================================
# FORMAT B (Dynamic Grid + Dual Barcode + Cut Lines)
# =========================================================
def generate_format_b(ids, cols, rows):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    page_width, page_height = A4

    cell_width = page_width / cols
    cell_height = page_height / rows

    items_per_page = cols * rows

    def draw_cut_lines():
        c.setStrokeColor(colors.grey)
        c.setDash(2, 2)

        for i in range(1, cols):
            x = i * cell_width
            c.line(x, 0, x, page_height)

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

        header_font = cell_height * 0.08
        main_barcode_h = cell_height * 0.30
        small_barcode_h = cell_height * 0.10
        gap = cell_height * 0.03

        header_y = y + cell_height - header_font - gap

        c.setFont("Helvetica-Bold", header_font)
        c.drawCentredString(center_x, header_y, "DTDC Nehru Bazaar")

        main_barcode = code128.Code128(
            id_value,
            barHeight=main_barcode_h,
            barWidth=1.1
        )

        main_x = x + (cell_width - main_barcode.width) / 2
        main_y = header_y - main_barcode_h - gap
        main_barcode.drawOn(c, main_x, main_y)

        c.setFont("Helvetica", header_font * 0.9)
        c.drawCentredString(center_x, main_y - gap, id_value)

        small_barcode = code128.Code128(
            id_value,
            barHeight=small_barcode_h,
            barWidth=0.6
        )

        small_x = x + (cell_width - small_barcode.width) / 2
        small_y = y + cell_height * 0.12
        small_barcode.drawOn(c, small_x, small_y)

        c.setFont("Helvetica", header_font * 0.7)
        c.drawCentredString(center_x, small_y - gap, id_value)

    draw_cut_lines()
    c.save()
    buffer.seek(0)
    return buffer


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="DTDC Barcode Generator", layout="centered")

st.title("DTDC Barcode Generator (Multi Format)")

uploaded_file = st.file_uploader("Upload CSV or TXT file", type=["csv", "txt"])

# FORMAT DROPDOWN (KEY ADDITION)
format_type = st.selectbox(
    "Select Format",
    ["Format A (Fixed Grid)", "Format B (Dynamic Grid)"]
)

cols, rows = None, None

if format_type == "Format B (Dynamic Grid)":
    cols = st.number_input("Columns per page", 1, 10, 3)
    rows = st.number_input("Rows per page", 1, 15, 8)

if uploaded_file:

    ids = read_ids(uploaded_file)
    st.success(f"Loaded {len(ids)} IDs")

    if st.button("Generate PDF"):

        if format_type == "Format A (Fixed Grid)":
            pdf_buffer = generate_format_a(ids)
            file_name = "format_a_barcodes.pdf"
        else:
            pdf_buffer = generate_format_b(ids, cols, rows)
            file_name = "format_b_barcodes.pdf"

        st.success("PDF generated successfully!")

        st.download_button(
            "⬇ Download PDF",
            pdf_buffer,
            file_name=file_name,
            mime="application/pdf"
        )
