# -----------------------------------------
# AVAILABLE SPACE INSIDE CELL
# -----------------------------------------

max_w = cell_w * 0.92
max_h = cell_h * 0.55

# -----------------------------------------
# WE CONTROL BARCODE DENSITY HERE
# (THIS IS THE REAL FIX)
# -----------------------------------------

# Estimate module width so barcode fills full width
# Code128 has ~11 modules per character average
estimated_modules = len(value) * 11

module_width = max_w / estimated_modules

# clamp module width so barcode doesn't break
module_width = max(0.25, min(module_width, 1.2))

barcode = code128.Code128(
    value,
    barHeight=max_h,
    barWidth=module_width
)

bw = barcode.width
bh = barcode.height

# -----------------------------------------
# FINAL FIT (safety scaling)
# -----------------------------------------

scale = min(
    max_w / bw,
    max_h / bh
)

final_w = bw * scale
final_h = bh * scale
