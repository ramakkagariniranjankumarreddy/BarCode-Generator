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

    page_width, page_height = A4

    # =========================
    # GRID CONFIG
    # =========================
    cols = 4
    rows = 14

    label_width = 48 * mm
    label_height = 20 * mm

    items_per_page = cols * rows

    # FIXED OUTER MARGINS
    top_margin = 4.25 * mm
    bottom_margin = 4.25 * mm
    left_margin = 9 * mm
    right_margin = 9 * mm

    # =========================
    # AVAILABLE SPACE
    # =========================
    usable_width = page_width - left_margin - right_margin
    usable_height = page_height - top_margin - bottom_margin

    # =========================
    # REMAINING SPACE DISTRIBUTION
    # =========================
    total_label_width = cols * label_width
    total_label_height = rows * label_height

    col_gap = (usable_width - total_label_width) / (cols - 1) if cols > 1 else 0
    row_gap = (usable_height - total_label_height) / (rows - 1) if rows > 1 else 0

    # start origin (top-left of grid)
    start_x = left_margin
    start_y = page_height - top_margin

    for idx, id_value in enumerate(ids):

        pos = idx % items_per_page

        if idx > 0 and pos == 0:
            c.showPage()

        col = pos % cols
        row = pos // cols

        x = start_x + col * (label_width + col_gap)
        y = start_y - (row + 1) * label_height - row * row_gap

        center_x = x + label_width / 2

        # =========================
        # ZONES (20 mm LABEL HEIGHT)
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
