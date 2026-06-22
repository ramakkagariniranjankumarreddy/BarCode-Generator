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
        return df.iloc[:, 0].astype(str).tolist()
    else:
        content = uploaded_file.read().decode("utf-8")
        return [line.strip() for line in content.splitlines() if line.strip()]


# -----------------------------
# Generate PDF
# -----------------------------
def generate_pdf(ids):

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    page_width, page_height = A4

    # LABEL SIZE
    label_width = 48 * mm
    label_height = 20 * mm

    cols = 4
    rows = 14
    items_per_page = cols * rows

    # MARGINS
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
        # ZONE DEFINITIONS (20 mm LABEL)
        # =========================

        top_zone = y + label_height - 4 * mm        # DTDC header zone (top 4mm safe area)
        barcode_zone = y + 6 * mm                   # barcode starts around lower-middle
        number_zone = y + 2 * mm                    # bottom 5mm zone approx

        # -------------------------
        # HEADER (DTDC NEHRU BAZAAR)
        # -------------------------
        c.setFont("Helvetica-Bold", 5)
        c.drawCentredString(center_x, top_zone, "DTDC- Nehru Bazaar")

        # -------------------------
        # BARCODE (9 mm height, 0.55 factor)
        # -------------------------
        barcode = code128.Code128(
            id_value,
            barHeight=9 * mm,
            barWidth=0.55
        )

        barcode_x = x + (label_width - barcode.width) / 2
        barcode_y = barcode_zone

        barcode.drawOn(c, barcode_x, barcode_y)

        # -------------------------
        # LABEL NUMBER (5 mm zone)
        # -------------------------
        c.setFont("Helvetica", 6)
        c.drawCentredString(center_x, number_zone, id_value)

    draw_cut_lines()
    c.save()

    buffer.seek(0)
    return buffer


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(
    page_title="DTDC Barcode Generator",
    layout="centered"
)

st.title("DTDC Barcode Generator (48×20 mm Layout Fixed)")

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
            file_name="DTDC_barcodes_fixed.pdf",
            mime="application/pdf"
        )
