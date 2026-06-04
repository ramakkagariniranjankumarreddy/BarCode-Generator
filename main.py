def generate_pdf(ids, cols, rows):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    page_width, page_height = A4

    cell_width = page_width / cols
    cell_height = page_height / rows

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

    items_per_page = cols * rows

    for idx, id_value in enumerate(ids):

        page_index = idx // items_per_page
        position_in_page = idx % items_per_page

        if idx > 0 and position_in_page == 0:
            draw_cut_lines()
            c.showPage()

        col = position_in_page % cols
        row = position_in_page // cols

        x = col * cell_width
        y = page_height - (row + 1) * cell_height

        # Generate barcode
        barcode = code128.Code128(
            id_value,
            barHeight=cell_height * 0.65,
            barWidth=1.1
        )

        # Center barcode horizontally
        barcode_x = x + (cell_width - barcode.width) / 2

        # Leave space at bottom for text
        text_space = 12
        barcode_y = y + (cell_height * 0.25)

        barcode.drawOn(c, barcode_x, barcode_y)

        # -----------------------------
        # ID text below barcode
        # -----------------------------
        c.setFont("Helvetica", 8)

        text_y = barcode_y - text_space
        c.setFillColor(colors.black)

        c.drawCentredString(
            x + cell_width / 2,
            text_y,
            id_value
        )

    draw_cut_lines()
    c.save()

    buffer.seek(0)
    return buffer
