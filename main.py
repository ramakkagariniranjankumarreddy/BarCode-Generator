import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.graphics.barcode import code128
from reportlab.lib import colors
from io import BytesIO

# ----------------------------
# Read uploaded file
# ----------------------------
def read_ids(uploaded_file):
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file, header=None)
        ids = df.iloc[:, 0].astype(str).tolist()
    else:
        content = uploaded_file.read().decode("utf-8")
        ids = [line.strip() for line in content.splitlines() if line.strip()]
    return ids


# ----------------------------
# Generate PDF
# ----------------------------
def generate_pdf(ids, cols, rows):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    page_width, page_height = A4

    cell_width = page_width / cols
    cell_height = page_height / rows

    def draw_cut_lines():
        # vertical lines
        for i in range(1, cols):
            x = i * cell_width
            c.setStrokeColor(colors.grey)
            c.setDash(2, 2)
            c.line(x, 0, x, page_height)

        # horizontal lines
        for j in range(1, rows):
            y = j * cell_height
            c.setStrokeColor(colors.grey)
            c.setDash(2, 2)
            c.line(0, y, page_width, y)

        c.setDash()  # reset

    x = 0
    y = 0
    count = 0

    for idx, id_value in enumerate(ids):
        col = count % cols
        row = count // cols

        if count > 0 and count % (cols * rows) == 0:
            draw_cut_lines()
            c.showPage()

        col = count % cols
        row = (count // cols) % rows

        x = col * cell_width
        y = page_height - (row + 1) * cell_height

        # Generate barcode
        barcode = code128.Code128(id_value, barHeight=cell_height * 0.6, barWidth=1)

        # Center barcode in cell
        barcode_x = x + (cell_width - barcode.width) / 2
        barcode_y = y + (cell_height - barcode.height) / 2

        barcode.drawOn(c, barcode_x, barcode_y)

        count += 1

    draw_cut_lines()
    c.save()

    buffer.seek(0)
    return buffer


# ----------------------------
# Streamlit UI
# ----------------------------
st.title("📦 A4 Barcode PDF Generator")

uploaded_file = st.file_uploader("Upload CSV/TXT file (one ID per line)", type=["csv", "txt"])

cols = st.number_input("Columns per A4 page", min_value=1, max_value=10, value=3)
rows = st.number_input("Rows per A4 page", min_value=1, max_value=15, value=8)

if uploaded_file:
    ids = read_ids(uploaded_file)
    st.write(f"Total IDs loaded: {len(ids)}")

    if st.button("Generate Barcode PDF"):
        pdf_file = generate_pdf(ids, cols, rows)

        st.success("PDF generated successfully!")

        st.download_button(
            label="⬇ Download PDF",
            data=pdf_file,
            file_name="barcodes_a4.pdf",
            mime="application/pdf"
        )
