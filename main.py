import streamlit as st
import pandas as pd
from io import BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.graphics.barcode import code128
from reportlab.lib.units import mm


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


# -----------------------------
# Generate PDF
# -----------------------------
def generate_pdf(ids):

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    page_width, page_height = A4  # mm via reportlab points internally

    # =========================
    # GRID CONFIG (FIXED)
    # =========================
    cols = 4
    rows = 14

    label_width = 48 * mm
    label_height = 20 * mm

    items_per_page = cols * rows

    # =========================
    # MARGINS (UPDATED)
    # =========================
    top_margin = 2 * mm
    bottom_margin = 2 * mm
    left_margin = 6 * mm
    right_margin = 6 * mm

    # =========================
    # GAPS (FIXED AS REQUESTED)
    # =========================
    col_gap = 2 * mm
    row_gap = 1 * mm

    # =========================
    # START POSITION
    # =========================
    start_x = left_margin
    start_y = page_height - top_margin

    for idx, id_value in enumerate(ids):

        pos = idx % items_per_page

        if idx > 0 and pos == 0:
            c.showPage()

        col = pos % cols
        row = pos // cols

        # =========================
        # GRID POSITIONING
        # =========================
        x = start_x + col * (label_width + col_gap)
        y = start_y - (row * (label_height + row_gap)) - label_height

        center_x = x + label_width / 2

        # =========================
        # ZONES INSIDE LABEL
        # =========================
        top_zone = y + label_height - 4 * mm
        barcode_zone = y + 6 * mm
        number_zone = y + 2 * mm

        # -------------------------
        # HEADER
        # -------------------------
        c.setFont("Helvetica-Bold", 5)
        c.drawCentredString(center_x, top_zone, "DTDC- Nehru Bazaar")

        # -------------------------
        # BARCODE
        # -------------------------
        barcode = code128.Code128(
            id_value,
            barHeight=9 * mm,
            barWidth=0.9
        )

        barcode_x = x + (label_width - barcode.width) / 2
        barcode.drawOn(c, barcode_x, barcode_zone)

        # -------------------------
        # LABEL NUMBER
        # -------------------------
        c.setFont("Helvetica", 6)
        c.drawCentredString(center_x, number_zone, id_value)

    c.save()
    buffer.seek(0)
    return buffer


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="DTDC Barcode Generator", layout="centered")

st.title("DTDC Barcode Generator (Perfect Grid Aligned)")

uploaded_file = st.file_uploader(
    "Upload CSV or TXT file",
    type=["csv", "txt"]
)

if uploaded_file:

    ids = read_ids(uploaded_file)
    st.success(f"Loaded {len(ids)} IDs")

    if st.button("Generate PDF"):

        pdf_buffer = generate_pdf(ids)

        st.success("PDF generated successfully!")

        st.download_button(
            "⬇ Download PDF",
            pdf_buffer,
            file_name="DTDC_barcodes_aligned.pdf",
            mime="application/pdf"
        )
