import streamlit as st
import pandas as pd
from io import BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.graphics.barcode import code128
from reportlab.lib import colors
from reportlab.lib.units import mm


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
# Generate PDF (FIXED NJ MPL 56L)
# -----------------------------
def generate_pdf(ids):

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    page_width, page_height = A4

    # =========================
    # FIXED LABEL SPEC
    # =========================
    label_width = 48 * mm
    label_height = 20 * mm

    cols = 4
    rows = 14

    items_per_page = cols * rows

    # =========================
    # FIXED MARGINS (NJ MPL)
    # =========================
    x_margin = 9 * mm
    y_margin = 4.25 * mm

    grid_width = cols * label_width
    grid_height = rows * label_height

    def draw_cut_lines():
        c.setStrokeColor(colors.lightgrey)
        c.setDash(2, 2)

        # vertical lines
        for i in range(1, cols):
            x = x_margin + i * label_width
            c.line(x, y_margin, x, y_margin + grid_height)

        # horizontal lines
        for j in range(1, rows):
            y = y_margin + j * label_height
            c.line(x_margin, y, x_margin + grid_width, y)

        c.setDash()

    for idx, id_value in enumerate(ids):

        pos = idx % items_per_page

        if idx > 0 and pos == 0:
            draw_cut_lines()
            c.showPage()

        col = pos % cols
        row = pos // cols

        x = x_margin + col * label_width
        y = page_height - y_margin - (row + 1) * label_height

        center_x = x + label_width / 2

        # =========================
        # CONTENT SETTINGS
        # =========================
        header_font = 5
        value_font = 6
        barcode_height = 8 * mm

        # HEADER
        c.setFont("Helvetica-Bold", header_font)
        c.drawCentredString(center_x, y + label_height - 6, "DTDC- Nehru Bazaar")

        # BARCODE
        barcode = code128.Code128(
            id_value,
            barHeight=barcode_height,
            barWidth=0.45
        )

        barcode_x = x + (label_width - barcode.width) / 2
        barcode_y = y + 5

        barcode.drawOn(c, barcode_x, barcode_y)

        # VALUE
        c.setFont("Helvetica", value_font)
        c.drawCentredString(center_x, barcode_y - 10, id_value)

    draw_cut_lines()
    c.save()

    buffer.seek(0)
    return buffer


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(
    page_title="DTDC Barcode Generator (NJ MPL 56L)",
    layout="centered"
)

st.title("DTDC Barcode Generator (NJ MPL 56L - 48×20mm Fixed Layout)")

uploaded_file = st.file_uploader(
    "Upload CSV or TXT file (one ID per line)",
    type=["csv", "txt"]
)

if uploaded_file:

    ids = read_ids(uploaded_file)
    st.success(f"Loaded {len(ids)} IDs")

    if st.button("Generate PDF"):

        pdf_buffer = generate_pdf(ids)

        st.success("PDF generated successfully!")

        st.download_button(
            label="⬇ Download Barcode PDF",
            data=pdf_buffer,
            file_name="NJ_MPL_56L_barcodes.pdf",
            mime="application/pdf"
        )
