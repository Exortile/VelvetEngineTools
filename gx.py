# Display list opcodes:
# -------------------------------

GX_NOP = 0x00
GX_DRAW_QUADS = 0x80
GX_DRAW_TRIANGLES = 0x90
GX_DRAW_TRIANGLE_STRIP = 0x98
GX_DRAW_TRIANGLE_FAN = 0xA0
GX_DRAW_LINES = 0xA8
GX_DRAW_LINE_STRIP = 0xB0
GX_DRAW_POINTS = 0xB8

GX_LOAD_BP_REG = 0x61
GX_LOAD_CP_REG = 0x08
GX_LOAD_XF_REG = 0x10
GX_LOAD_INDX_A = 0x20
GX_LOAD_INDX_B = 0x28
GX_LOAD_INDX_C = 0x30
GX_LOAD_INDX_D = 0x38

GX_CMD_CALL_DL = 0x40
GX_CMD_INVL_VC = 0x48

GX_OPCODE_MASK = 0xF8
GX_VAT_MASK = 0x07

# -------------------------------

GX_VTXFMT0 = 0
GX_VTXFMT1 = 1
GX_VTXFMT2 = 2
GX_VTXFMT3 = 3
GX_VTXFMT4 = 4
GX_VTXFMT5 = 5
GX_VTXFMT6 = 6
GX_VTXFMT7 = 7
