# -*- coding: utf-8 -*-
"""
IP5406 minimal power board - KiCad project generator (rev 1.5)
Outputs: .kicad_pro / .kicad_sch / .kicad_pcb  (KiCad 10 compatible, self-contained)

Board: 25.00 x 16.00 mm  (same envelope as the original IP5306 module)
  J1 (right, 6 x 2.54 THT)  : OUT-5V / GND / BAT / GND / GND / VIN   (1:1 with IP5306 module)
  J2 (left,  4 x 2.54 THT)  : DCP / KEY / LED1 / LED2               (spare header)
  J4 (bottom, 2 x 2.54 THT) : VOUT / OUT_SW   (external switch or jumper, 2.54 grid)
  J3 (bottom right, PH2.0)  : BAT / GND       (battery socket, plug goes in horizontally)
  Row-to-row spacing        : 22.86 mm = 9 x 2.54 mm   (perfboard friendly)
  Edge margin               : 1.07 mm each side (25 - 9 x 2.54 = 2.14 mm)
  F.Silk assembly marks      : U1/L1 outlines + pin-1 notch, +/- on C1-C4, C2, J3
"""
import os
import json
import uuid

OUT = os.path.dirname(os.path.abspath(__file__))
PROJ = "IP5406_PSU"
ROOT = "8f3c2a10-1111-4222-8333-abcdef012345"


def u():
    return str(uuid.uuid4())


# ----------------------------------------------------------------------------
# 1. Schematic library symbols (embedded into .kicad_sch -> self-contained)
# ----------------------------------------------------------------------------
def sym_header(name, ref_prefix, show_pin_names=False):
    return f'''\t\t(symbol "{name}"
\t\t\t(pin_numbers (hide yes))
\t\t\t(pin_names (offset 0.508) (hide {"no" if show_pin_names else "yes"}))
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "{ref_prefix}" (at 0 4 0)
\t\t\t\t(effects (font (size 1.27 1.27))))
\t\t\t(property "Value" "{ref_prefix}" (at 0 -4 0)
\t\t\t\t(effects (font (size 1.27 1.27))))
\t\t\t(property "Footprint" "" (at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Datasheet" "" (at 0 0 0)
\t\t\t\t(effects (font (size 1.27 1.27)) (hide yes)))'''


def pin(num, name, x, y, angle, typ="passive"):
    return f'''\t\t\t\t(pin {typ} line (at {x:.3f} {y:.3f} {angle}) (length 2.54)
\t\t\t\t\t(name "{name}" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "{num}" (effects (font (size 1.27 1.27)))))'''


def rect_symbol(name, ref_prefix, left_pins, right_pins, width=7.62, height=None,
                show_names=False, body_text=None):
    """left_pins/right_pins: list of (num, name). Pins on both sides."""
    n = max(len(left_pins), len(right_pins))
    if height is None:
        height = max(5.08, (n - 1) * 2.54 + 2.54)
    half_h = height / 2.0
    half_w = width / 2.0
    short = name.split(":")[-1]

    def ypos(i, count):
        if count == 1:
            return 0.0
        return -half_h + 1.27 + i * ((height - 2.54) / (count - 1))

    lines = []
    lines.append(sym_header(name, ref_prefix, show_names))
    lines.append(f'\t\t\t(symbol "{short}_0_1"')
    lines.append(f'''\t\t\t\t(rectangle (start {-half_w:.3f} {-half_h:.3f}) (end {half_w:.3f} {half_h:.3f})
\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type background)))''')
    lines.append('\t\t\t)')
    lines.append(f'\t\t\t(symbol "{short}_1_1"')
    for i, (num, nm) in enumerate(left_pins):
        lines.append(pin(num, nm, -half_w - 2.54, ypos(i, len(left_pins)), 0))
    for i, (num, nm) in enumerate(right_pins):
        lines.append(pin(num, nm, half_w + 2.54, ypos(i, len(right_pins)), 180))
    lines.append('\t\t\t)')
    lines.append('\t\t)')
    return "\n".join(lines)


LIB = []
LIB.append(rect_symbol(
    "IP5406_Lib:IP5406", "U",
    left_pins=[("1", "VIN"), ("2", "DCP"), ("3", "KEY"), ("4", "LED1"), ("9", "GND")],
    right_pins=[("8", "VOUT"), ("7", "SW"), ("6", "BAT"), ("5", "LED2")],
    width=10.16, height=12.7, show_names=True, body_text="IP5406"))
LIB.append(rect_symbol("IP5406_Lib:L", "L", [("1", "SW")], [("2", "BAT")],
                       width=6.35, height=5.08, show_names=True, body_text="1uH"))
LIB.append(rect_symbol("IP5406_Lib:C", "C", [("1", "~")], [("2", "~")],
                       width=5.08, height=3.81, body_text="C"))
LIB.append(rect_symbol(
    "IP5406_Lib:Conn_01x06", "J",
    left_pins=[], right_pins=[("1", "OUT-5V"), ("2", "GND"), ("3", "BAT"),
                              ("4", "GND"), ("5", "GND"), ("6", "VIN")],
    width=5.08, height=15.24, show_names=True, body_text="6-PAD"))
LIB.append(rect_symbol(
    "IP5406_Lib:Conn_01x04", "J",
    left_pins=[], right_pins=[("1", "DCP"), ("2", "KEY"),
                              ("3", "LED1"), ("4", "LED2")],
    width=5.08, height=10.16, show_names=True, body_text="SPARE"))
LIB.append(rect_symbol("IP5406_Lib:Conn_01x02", "J",
                       [("1", "A")], [("2", "B")],
                       width=5.08, height=5.08, show_names=True, body_text="SW"))

# ----------------------------------------------------------------------------
# 2. Schematic instances
# ----------------------------------------------------------------------------
COMPONENTS = [
    ("U1", "IP5406", "IP5406_Lib:IP5406", 135.89, 88.9,
     [("1", "VIN"), ("2", "DCP"), ("3", "KEY"), ("4", "LED1"), ("9", "GND"),
      ("8", "VOUT"), ("7", "SW"), ("6", "BAT"), ("5", "LED2")], False),
    ("L1", "1uH/4A", "IP5406_Lib:L", 190.5, 55.88,
     [("1", "SW"), ("2", "BAT")], False),
    ("C1", "22uF", "IP5406_Lib:C", 63.5, 55.88,
     [("1", "VIN"), ("2", "GND")], False),
    ("C2", "10uF", "IP5406_Lib:C", 63.5, 76.2,
     [("1", "BAT"), ("2", "GND")], False),
    ("C3", "22uF", "IP5406_Lib:C", 190.5, 76.2,
     [("1", "VOUT"), ("2", "GND")], False),
    ("C4", "22uF", "IP5406_Lib:C", 190.5, 96.52,
     [("1", "VOUT"), ("2", "GND")], False),
    ("C5", "100nF", "IP5406_Lib:C", 190.5, 116.84,
     [("1", "VOUT"), ("2", "GND")], False),
    ("J1", "IN/OUT 6PAD", "IP5406_Lib:Conn_01x06", 135.89, 137.16,
     [("1", "OUT_SW"), ("2", "GND"), ("3", "BAT"),
      ("4", "GND"), ("5", "GND"), ("6", "VIN")], False),
    ("J2", "SPARE 4P", "IP5406_Lib:Conn_01x04", 135.89, 172.72,
     [("1", "DCP"), ("2", "KEY"), ("3", "LED1"), ("4", "LED2")], False),
    ("J4", "SW JUMPER", "IP5406_Lib:Conn_01x02", 240.03, 96.52,
     [("1", "VOUT"), ("2", "OUT_SW")], False),
    ("J3", "PH2.0 BAT", "IP5406_Lib:Conn_01x02", 240.03, 116.84,
     [("1", "BAT"), ("2", "GND")], False),
]


def pin_geometry(lib_id, pin_num):
    """Return (dx, dy) of the electrical connection point, and which side."""
    specs = {
        "IP5406_Lib:IP5406": (10.16, 12.7,
            [("1", "VIN"), ("2", "DCP"), ("3", "KEY"), ("4", "LED1"), ("9", "GND")],
            [("8", "VOUT"), ("7", "SW"), ("6", "BAT"), ("5", "LED2")]),
        "IP5406_Lib:L": (6.35, 5.08, [("1", "SW")], [("2", "BAT")]),
        "IP5406_Lib:C": (5.08, 3.81, [("1", "~")], [("2", "~")]),
        "IP5406_Lib:Conn_01x06": (5.08, 15.24, [],
            [("1", "OUT-5V"), ("2", "GND"), ("3", "BAT"),
             ("4", "GND"), ("5", "GND"), ("6", "VIN")]),
        "IP5406_Lib:Conn_01x04": (5.08, 10.16, [],
            [("1", "DCP"), ("2", "KEY"), ("3", "LED1"), ("4", "LED2")]),
        "IP5406_Lib:Conn_01x02": (5.08, 5.08, [("1", "A")], [("2", "B")]),
    }
    w, h, left, right = specs[lib_id]
    hw, hh = w / 2.0, h / 2.0

    def ypos(i, count):
        if count == 1:
            return 0.0
        return -hh + 1.27 + i * ((h - 2.54) / (count - 1))

    for i, (num, _) in enumerate(left):
        if num == pin_num:
            return (-hw - 2.54, ypos(i, len(left)), "L")
    for i, (num, _) in enumerate(right):
        if num == pin_num:
            return (hw + 2.54, ypos(i, len(right)), "R")
    raise ValueError((lib_id, pin_num))


sch = []
sch.append('(kicad_sch')
sch.append('\t(version 20250114)')
sch.append('\t(generator "eeschema")')
sch.append('\t(generator_version "10.0")')
sch.append(f'\t(uuid "{ROOT}")')
sch.append('\t(paper "A4")')
sch.append('\t(title_block')
sch.append('\t\t(title "IP5406 5V UPS Power Board")')
sch.append('\t\t(date "2026-11-03")')
sch.append('\t\t(rev "1.5")')
sch.append('\t\t(comment 1 "25.0x16.0mm (same as IP5306 module); J1 6P 1:1 pin-compatible")')
sch.append('\t\t(comment 2 "Row pitch 22.86mm = 9x2.54mm; J4 on the 2.54 grid; PH2.0 battery socket")')
sch.append('\t)')
sch.append('\t(lib_symbols')
for s in LIB:
    sch.append(s)
sch.append('\t)')

notes = [
    (63.5, 160.02, "POWER PATH: VIN -> load + charge; unplug -> battery boost, seamless"),
    (63.5, 165.1, "5V OUTPUT ALWAYS ON (no light-load shutdown). DCP pin 2 -> J2-1."),
    (63.5, 170.18, "J4: external ON/OFF switch (2.54 grid); fit a jumper for always-on output."),
    (63.5, 175.26, "J2: DCP / KEY(NTC or button) / LED1 / LED2 = battery gauge LEDs."),
    (63.5, 180.34, "LEDs (external): 2 pcs anti-parallel between LED1 and LED2 (A/K crossed)."),
    (63.5, 185.42, "J3: PH2.0 battery socket (BAT/GND) - plug the pack in directly."),
    (63.5, 190.5, "F.Silk: U1/L1 outlines + pin-1 notch; +/- on C1-C4, C2, J3."),
]
for x, y, txt in notes:
    sch.append(f'''\t(text "{txt}"
\t\t(exclude_from_sim no) (at {x:.2f} {y:.2f} 0)
\t\t(effects (font (size 1.27 1.27)) (justify left bottom))
\t\t(uuid "{u()}"))''')

for ref, val, lib_id, X, Y, pins, dnp in COMPONENTS:
    for pnum, net in pins:
        dx, dy, side = pin_geometry(lib_id, pnum)
        ax, ay = X + dx, Y - dy   # library Y is up, sheet Y is down
        if side == "L":
            bx, by = ax - 7.62, ay
        else:
            bx, by = ax + 7.62, ay
        if net is None:
            sch.append(f'\t(no_connect (at {ax:.3f} {ay:.3f}) (uuid "{u()}"))')
            continue
        sch.append(f'''\t(wire (pts (xy {ax:.3f} {ay:.3f}) (xy {bx:.3f} {by:.3f}))
\t\t(stroke (width 0) (type default)) (uuid "{u()}"))''')
        sch.append(f'''\t(label "{net}" (at {bx:.3f} {by:.3f} 0)
\t\t(effects (font (size 1.27 1.27)) (justify left bottom))
\t\t(uuid "{u()}"))''')

    sch.append(f'''\t(symbol (lib_id "{lib_id}") (at {X:.2f} {Y:.2f} 0) (unit 1)
\t\t(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp {"yes" if dnp else "no"})
\t\t(uuid "{u()}")
\t\t(property "Reference" "{ref}" (at {X:.2f} {Y-2:.2f} 0)
\t\t\t(effects (font (size 1.27 1.27))))
\t\t(property "Value" "{val}" (at {X:.2f} {Y+2:.2f} 0)
\t\t\t(effects (font (size 1.27 1.27))))
\t\t(property "Footprint" "" (at {X:.2f} {Y:.2f} 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes)))
\t\t(property "Datasheet" "" (at {X:.2f} {Y:.2f} 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes)))''')
    for pnum, _ in pins:
        sch.append(f'\t\t(pin "{pnum}" (uuid "{u()}"))')
    sch.append(f'''\t\t(instances (project "{PROJ}"
\t\t\t(path "/{ROOT}" (reference "{ref}") (unit 1)))))''')

sch.append('\t(sheet_instances (path "/" (page "1")))')
sch.append('\t(embedded_fonts no)')
sch.append(')')

with open(os.path.join(OUT, PROJ + ".kicad_sch"), "w", encoding="utf-8") as f:
    f.write("\n".join(sch))

# ----------------------------------------------------------------------------
# 3. Project file
# ----------------------------------------------------------------------------
pro = {
    "meta": {"filename": PROJ + ".kicad_pro", "version": 3},
    "sheets": [[ROOT, ""]],
    "text_variables": {},
    "board": {
        "design_settings": {
            "defaults": {},
            "drc_exclusions": [],
            "meta": {"version": 2},
            "rule_severities": {
                "silk_edge_clearance": "warning",
                "silk_over_copper": "warning",
                "silk_overlap": "warning",
                "text_height": "warning",
                "text_thickness": "warning",
                "solder_mask_bridge": "error",
            },
            "rules": {
                # 25 mm board width + 2.54 mm grid headers -> pad copper sits
                # 0.27 mm from the board edge; 0.2 mm is the JLC process limit
                "min_copper_edge_clearance": 0.2,
                "min_clearance": 0.2,
                "min_hole_clearance": 0.25,
                "min_hole_to_hole": 0.5,
                "min_silk_clearance": 0.0,
                "min_text_height": 0.6,
                "min_text_thickness": 0.08,
                "solder_mask_to_copper_clearance": 0.0,
            },
        }
    },
    "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
}
with open(os.path.join(OUT, PROJ + ".kicad_pro"), "w", encoding="utf-8") as f:
    json.dump(pro, f, indent=2, ensure_ascii=False)

# ----------------------------------------------------------------------------
# 4. PCB via pcbnew
# ----------------------------------------------------------------------------
import pcbnew

MM = pcbnew.FromMM


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


board = pcbnew.BOARD()
nets = {}
for n in ["VIN", "BAT", "SW", "VOUT", "OUT_SW", "GND", "KEY", "LED1", "LED2",
          "DCP"]:
    ni = pcbnew.NETINFO_ITEM(board, n)
    board.Add(ni)
    nets[n] = ni


def make_fp(ref, val, cx, cy, pads, ref_dy=-2.2):
    """pads: list of (number, net, dx, dy, w, h, kind) kind='smd'|'pth'|'epad'"""
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference(ref)
    fp.SetValue(val)
    fp.SetPosition(V(cx, cy))
    fp.SetFPID(pcbnew.LIB_ID("", ref))
    for (num, net, dx, dy, w, h, kind) in pads:
        p = pcbnew.PAD(fp)
        p.SetNumber(num)
        p.SetSize(V(w, h))
        p.SetPosition(V(cx + dx, cy + dy))
        if kind == "pth":
            p.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
            p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
            p.SetDrillSize(V(1.0, 1.0))
            # PTH must have a solder-mask opening on BOTH sides, otherwise the
            # fab (JLC) sees an all-tented through-hole pad and asks about it.
            pth_layers = pcbnew.LSET.AllCuMask()
            pth_layers.AddLayer(pcbnew.F_Mask)
            pth_layers.AddLayer(pcbnew.B_Mask)
            p.SetLayerSet(pth_layers)
        else:
            p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
            p.SetShape(pcbnew.PAD_SHAPE_ROUNDRECT)
            smd_layers = pcbnew.LSET()
            smd_layers.AddLayer(pcbnew.F_Cu)
            smd_layers.AddLayer(pcbnew.F_Paste)
            smd_layers.AddLayer(pcbnew.F_Mask)
            p.SetLayerSet(smd_layers)
        if net:
            p.SetNet(nets[net])
        if net == "GND":
            p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
        fp.Add(p)
    r = fp.Reference()
    r.SetPosition(V(cx, cy + ref_dy))
    r.SetLayer(pcbnew.F_Fab)
    r.SetTextSize(V(0.8, 0.8))
    r.SetTextThickness(MM(0.12))
    board.Add(fp)
    return fp


# --- U1: ESOP8 (3.9x4.9, 1.27 pitch) + exposed thermal pad ---
UX, UY = 109.8, 108.2
u1_pads = []
for i, (num, net) in enumerate([("1", "VIN"), ("2", "DCP"), ("3", "KEY"), ("4", "LED1")]):
    u1_pads.append((num, net, -2.7, -1.905 + i * 1.27, 0.6, 0.9, "smd"))
for i, (num, net) in enumerate([("8", "VOUT"), ("7", "SW"), ("6", "BAT"), ("5", "LED2")]):
    u1_pads.append((num, net, 2.7, -1.905 + i * 1.27, 0.6, 0.9, "smd"))
u1_pads.append(("9", "GND", 0, 0, 2.2, 2.6, "epad"))
make_fp("U1", "IP5406", UX, UY, u1_pads)

# --- L1: 1uH power inductor; raised to 107.4 so the BAT trunk at y=110.1 fits
#     between the inductor body (..109.9) and U1's pads (110.555) ---
make_fp("L1", "1uH/4A", 116.2, 107.4,
        [("1", "SW", -1.6, 0, 1.6, 3.4, "smd"),
         ("2", "BAT", 1.6, 0, 1.6, 3.4, "smd")])


def cap(ref, val, x, y, net1, net2, pitch=0.9, w=1.0, h=1.3, ref_dy=-2.2):
    make_fp(ref, val, x, y,
            [("1", net1, -pitch, 0, w, h, "smd"),
             ("2", net2, pitch, 0, w, h, "smd")], ref_dy=ref_dy)


cap("C1", "22uF", 104.6, 102.9, "VIN", "GND")          # pads 103.7 / 105.5
cap("C3", "22uF", 111.2, 102.7, "VOUT", "GND")         # pads 110.3 / 112.1
cap("C4", "22uF", 114.6, 102.7, "VOUT", "GND")         # pads 113.7 / 115.5
cap("C5", "100nF", 117.4, 102.7, "VOUT", "GND", pitch=0.75, w=0.8, h=0.9)
cap("C2", "10uF", 120.4, 109.6, "BAT", "GND")          # pads 119.5 / 121.3

# --- J1: 6 through-hole pads on the right edge (1:1 with the IP5306 module) ---
JX = 123.93
j1 = [
    ("1", "OUT_SW", 101.65),
    ("2", "GND", 104.19),
    ("3", "BAT", 106.73),
    ("4", "GND", 109.27),
    ("5", "GND", 111.81),
    ("6", "VIN", 114.35),
]
make_fp("J1", "6PAD", JX, 108.0,
        [(n, net, 0, y - 108.0, 1.6, 1.6, "pth") for (n, net, y) in j1])

# --- J2: spare 4-pin header on the left, same 2.54 grid rows as J1 pins 2..5 ---
J2X = JX - 22.86          # 22.86 mm = 9 x 2.54 -> perfboard friendly
j2 = [("1", "DCP", 104.19), ("2", "KEY", 106.73),
      ("3", "LED1", 109.27), ("4", "LED2", 111.81)]
make_fp("J2", "SPARE4", J2X, 108.0,
        [(n, net, 0, y - 108.0, 1.6, 1.6, "pth") for (n, net, y) in j2])

# --- J4: external ON/OFF switch header, ON THE 2.54 GRID ---
# pins at x = 103.61 / 106.15, y = 114.35 -> both land on the same 2.54 lattice
# as J1/J2, so the board can also be plugged into a 2.54 perfboard.
J4X = 104.88
make_fp("J4", "SW_JUMPER", J4X, 114.35,
        [("1", "VOUT", -1.27, 0, 1.6, 1.6, "pth"),
         ("2", "OUT_SW", 1.27, 0, 1.6, 1.6, "pth")])

# --- J3: PH2.0 battery socket (2.0 mm pitch, right-angle THT) ---
# The plastic body hangs over the bottom board edge so the pack plugs in
# horizontally from outside the board - it costs almost no board area.
make_fp("J3", "PH2.0", 117.4, 114.2,
        [("1", "BAT", -1.0, 0, 1.6, 1.6, "pth"),
         ("2", "GND", 1.0, 0, 1.6, 1.6, "pth")])

# --- board outline 25.00 x 16.00 mm (same envelope as the IP5306 module) ---
X0, Y0, X1, Y1 = 100.0, 100.0, 125.0, 116.0
corners = [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1), (X0, Y0)]
for a, b in zip(corners, corners[1:]):
    seg = pcbnew.PCB_SHAPE(board)
    seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
    seg.SetStart(V(*a))
    seg.SetEnd(V(*b))
    seg.SetLayer(pcbnew.Edge_Cuts)
    seg.SetWidth(MM(0.1))
    board.Add(seg)

# --- silkscreen ---
def silk(txt, x, y, size=0.8, right=False, layer=pcbnew.F_SilkS, mirror=False,
         center=False):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt)
    t.SetPosition(V(x, y))
    t.SetLayer(layer)
    t.SetTextSize(V(size, size))
    t.SetTextThickness(MM(0.11))
    t.SetTextAngle(pcbnew.EDA_ANGLE(0, pcbnew.DEGREES_T))
    if center:
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    else:
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_RIGHT if right
                          else pcbnew.GR_TEXT_H_ALIGN_LEFT)
    if mirror:
        t.SetMirrored(True)
    board.Add(t)
    return t


def silk_seg(x1, y1, x2, y2, w=0.12):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(V(x1, y1))
    s.SetEnd(V(x2, y2))
    s.SetLayer(pcbnew.F_SilkS)
    s.SetWidth(MM(w))
    board.Add(s)
    return s


def silk_poly(pts, w=0.12):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        silk_seg(x1, y1, x2, y2, w)


def silk_dot(x, y, r=0.28):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_CIRCLE)
    s.SetCenter(V(x, y))
    s.SetEnd(V(x + r, y))
    s.SetLayer(pcbnew.F_SilkS)
    s.SetWidth(MM(0.01))
    s.SetFilled(True)
    board.Add(s)
    return s


# J1 pad labels on the back (same side as the markings on the original module)
# "VIN" is pushed right to x=122.0 so it clears J3's mask opening at 117.6..119.2
for txt, y, x in [("OUT-5V", 101.65, 120.9), ("GND", 104.19, 120.9),
                  ("BAT", 106.73, 120.9), ("GND", 109.27, 120.9),
                  ("GND", 111.81, 120.9), ("VIN", 114.35, 122.0)]:
    silk(txt, x, y - 0.36, size=0.8, right=False,
         layer=pcbnew.B_SilkS, mirror=True)

silk("J2", 101.3, 102.55, size=0.8)
silk("J4", 108.6, 114.9, size=0.8, right=True)
silk("J3", 113.9, 114.8, size=0.8, right=True)

# title block on the back (same side as the original module's markings)
silk("IP5406 5V UPS", 113.2, 100.72, size=0.8, layer=pcbnew.B_SilkS, mirror=True)
silk("Lambilly @2026.11", 113.2, 101.82, size=0.8, layer=pcbnew.B_SilkS, mirror=True)

# --- front-side assembly markings -------------------------------------------
# U1 (ESOP8): body outline with a chamfered top-left = pin-1 notch.
# Pin 1 = VIN (upper left), pin 8 = VOUT (upper right).  The dot and "1"
# sit just OUTSIDE the body so they stay visible after the chip is soldered.
silk_poly([(107.75, 106.40), (108.45, 105.70), (111.85, 105.70),
           (111.85, 110.70), (107.75, 110.70), (107.75, 106.40)])
silk_dot(108.25, 105.30)
silk("1", 109.15, 105.05, size=0.65, center=True)

# L1 (1uH inductor): outline + chamfered top-left corner pointing at pad 1
# (SW side).  The inductor itself is non-polar; the notch is only a direction
# mark so it is not mounted "backwards" relative to the printed layout.
silk_poly([(113.60, 106.00), (114.10, 105.50), (118.80, 105.50),
           (118.80, 109.30), (113.60, 109.30), (113.60, 106.00)])

# Polarity marks for the bulk caps (pad 1 = +, pad 2 = -).
# C5 is a 100nF MLCC (non-polar) so it is deliberately left unmarked.
for (px, nx, py) in [(103.7, 105.5, 101.45),   # C1 VIN / GND
                     (110.3, 112.1, 101.45),   # C3 VOUT / GND
                     (113.7, 115.5, 101.45),   # C4 VOUT / GND
                     ]:
    silk("+", px, py, size=0.7, center=True)
    silk("-", nx, py, size=0.7, center=True)
silk("+", 119.5, 110.75, size=0.65, center=True)   # C2 pad1 = BAT
silk("-", 121.3, 110.75, size=0.65, center=True)   # C2 pad2 = GND

# J3 PH2.0 battery socket: pad 1 = BAT+, pad 2 = GND-
silk("+", 116.4, 112.75, size=0.7, center=True)
silk("-", 118.4, 112.75, size=0.7, center=True)

# --- routing ---
def track(net, pts, width=0.4, layer=pcbnew.F_Cu):
    for a, b in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(V(*a))
        t.SetEnd(V(*b))
        t.SetWidth(MM(width))
        t.SetLayer(layer)
        t.SetNet(nets[net])
        board.Add(t)


def via(net, x, y, d=0.6, drill=0.3):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(V(x, y))
    v.SetWidth(MM(d))
    v.SetDrill(MM(drill))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(nets[net])
    board.Add(v)


# ---- top layer: power stage + the four J2 signals ----
# SW: U1 pin7 -> L1 pad1
track("SW", [(112.5, 107.565), (113.7, 107.565), (114.6, 107.4)], 0.5)

# VOUT trunk (y = 104.9) feeding C3 / C4 / C5
track("VOUT", [(112.5, 106.295), (112.5, 104.9)], 0.5)
track("VOUT", [(112.5, 104.9), (110.3, 104.9), (110.3, 103.35)], 0.5)
track("VOUT", [(110.3, 104.9), (116.65, 104.9)], 0.5)
track("VOUT", [(113.7, 104.9), (113.7, 103.35)], 0.4)
track("VOUT", [(116.65, 104.9), (116.65, 103.15)], 0.4)

# BAT: U1 pin6 -> around L1 -> L1 pad2 -> C2 -> J1-3 / J3-1
track("BAT", [(112.5, 108.835), (113.25, 108.835)], 0.5)
track("BAT", [(113.25, 108.835), (113.25, 110.1), (117.9, 110.1),
              (117.9, 108.8)], 0.5)
track("BAT", [(117.9, 108.8), (119.5, 109.6)], 0.5)          # into C2 pad1
# J1-3 and the PH2.0 socket are fed on the bottom layer so the top stays clear
track("BAT", [(119.5, 108.95), (119.5, 108.2)], 0.4)
via("BAT", 119.5, 108.2)
track("BAT", [(119.5, 108.2), (123.93, 106.73)], 0.5, pcbnew.B_Cu)
track("BAT", [(113.25, 110.1), (113.25, 110.8)], 0.4)
via("BAT", 113.25, 110.8)
track("BAT", [(113.25, 110.8), (113.25, 112.8), (116.4, 112.8),
              (116.4, 114.2)], 0.5, pcbnew.B_Cu)

# VIN: U1 pin1 -> straight up at x = 107.1 -> C1 pad1
# (the old left detour at x = 106.9 is now the DCP lane)
track("VIN", [(107.1, 106.295), (107.1, 104.9), (103.7, 104.9),
              (103.7, 103.55)], 0.4)

# DCP: U1 pin2 -> J2-1 (top layer, above KEY; runs between the VIN trunk and
# U1 pad1 without touching either)
track("DCP", [(107.1, 107.565), (106.45, 107.565), (106.45, 105.55),
              (101.6, 105.55), (101.6, 104.19), (101.07, 104.19)], 0.25)

# KEY / LED1: U1 -> J2 (top layer, they never reach the bottom corridor)
# KEY drops its vertical to x = 105.95 to leave the DCP lane at x = 106.45 free
track("KEY", [(107.1, 108.835), (105.95, 108.835), (105.95, 106.73),
              (101.07, 106.73)], 0.25)
track("LED1", [(107.1, 110.105), (105.3, 110.105), (105.3, 109.27),
               (101.07, 109.27)], 0.25)
track("LED2", [(112.5, 110.4), (112.5, 110.9), (103.0, 110.9),
               (103.0, 111.81), (101.07, 111.81)], 0.25)

# ---- bottom layer ----
# VOUT -> J4 pin1 (down the left channel, then along y = 113.2)
via("VOUT", 114.73, 104.9)
track("VOUT", [(114.73, 104.9), (103.2, 104.9)], 0.5, pcbnew.B_Cu)
track("VOUT", [(103.2, 104.9), (103.2, 113.2), (103.61, 113.2),
               (103.61, 114.35)], 0.5, pcbnew.B_Cu)

# VIN: C1 -> left edge -> bottom edge -> straight into J1-6
track("VIN", [(103.7, 102.9), (102.4, 102.9)], 0.4)
via("VIN", 102.4, 102.9)
track("VIN", [(102.4, 102.9), (102.4, 115.6), (122.6, 115.6),
              (123.93, 114.35)], 0.4, pcbnew.B_Cu)

# OUT_SW: J4 pin2 -> across the board -> up the right channel -> J1-1
# (top layer: keeps the bottom GND pour in one piece, so J1's GND pads are
#  connected straight to it without a bridge)
track("OUT_SW", [(106.15, 114.35), (106.15, 111.7), (122.5, 111.7),
                 (122.5, 101.65), (123.93, 101.65)], 0.8)

# --- GND stitching vias (SMD GND pads -> bottom pour) ---
for (px, py), (vx, vy) in [((105.5, 103.55), (105.5, 104.1)),
                           ((112.1, 103.35), (112.1, 103.9)),
                           ((115.5, 103.35), (115.5, 103.9)),
                           ((118.15, 103.15), (118.15, 103.9)),
                           ]:
    track("GND", [(px, py), (vx, vy)], 0.4)
    via("GND", vx, vy)
# C2 GND up and left, away from the OUT_SW climb at x = 121.9
track("GND", [(121.3, 108.95), (120.9, 108.6)], 0.4)
via("GND", 120.9, 108.6)

# U1 exposed pad -> pour through a via in the thermal pad
via("GND", 110.3, 108.9)


# --- GND pour (bottom layer) ---
for layer in (pcbnew.B_Cu,):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(nets["GND"])
    z.SetLocalClearance(MM(0.25))
    z.SetThermalReliefGap(MM(0.25))
    z.SetThermalReliefSpokeWidth(MM(0.3))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    ol = z.Outline()
    ol.NewOutline()
    for (x, y) in [(100.4, 100.4), (124.6, 100.4), (124.6, 115.6), (100.4, 115.6)]:
        ol.Append(MM(x), MM(y))
    board.Add(z)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
PCB_PATH = os.path.join(OUT, PROJ + ".kicad_pcb")
pcbnew.SaveBoard(PCB_PATH, board)


# ---- PTH pads must be mask-opened on BOTH sides ----------------------------
# KiCad 10's Python pad API silently drops F.Mask/B.Mask from a PTH pad's layer
# set when saving (it writes only "(layers "*.Cu")"), which leaves every
# through-hole pad fully tented and makes the fab ask "through-hole pads need a
# mask opening". Patch the serialized board text instead: a normal KiCad THT pad
# is written as (layers "*.Cu" "*.Mask").
def force_pth_mask_openings(path):
    import re
    with open(path, "r", encoding="utf-8") as f:
        txt = f.read()
    pattern = re.compile(
        r'(\(pad "[^"]*" thru_hole [^\n]*\n(?:[^\n]*\n)*?\t\t\t)(\(layers "\*\.Cu"\))')
    txt, n = pattern.subn(r'\1(layers "*.Cu" "*.Mask")', txt)
    with open(path, "w", encoding="utf-8") as f:
        f.write(txt)
    return n


_pthed = force_pth_mask_openings(PCB_PATH)

# pcbnew.SaveBoard() also rewrites .kicad_pro with KiCad's stock defaults.
# Re-apply our DRC constraints LAST so they are the ones kicad-cli and the
# KiCad GUI actually use (0.2 mm edge clearance, 0.2 mm min clearance,
# 0.6 mm minimum silkscreen text height).
with open(os.path.join(OUT, PROJ + ".kicad_pro"), "w", encoding="utf-8") as f:
    json.dump(pro, f, indent=2, ensure_ascii=False)

print("Generated:", PROJ + ".kicad_pro / .kicad_sch / .kicad_pcb")
print("Footprints:", len(board.GetFootprints()), " Tracks:", len(board.GetTracks()))
print("PTH pads with dual-side mask opening:", _pthed)
