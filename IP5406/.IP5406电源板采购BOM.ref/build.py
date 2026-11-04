# -*- coding: utf-8 -*-
"""Build the IP5406 power board purchasing BOM workbook."""
import os

try:
    import openpyxl
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "openpyxl>=3.1.0"])
    import openpyxl

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule
from openpyxl.utils import get_column_letter

OUT_XLSX = os.path.join("D:\\IP5406电源模块", "IP5406电源板采购BOM.xlsx")
TITLE = "IP5406电源板采购BOM"


def xl_color(css_hex: str) -> str:
    value = css_hex.removeprefix("#").upper()
    if len(value) != 6:
        raise ValueError(f"Expected #RRGGBB, got: {css_hex}")
    return "FF" + value


XL_HEADER_BG = xl_color("#4472C4")
XL_HEADER_FG = xl_color("#FFFFFF")
XL_INPUT_BG = xl_color("#D9E2F3")
XL_TOTAL_BG = xl_color("#2F5597")
XL_BORDER = xl_color("#BFBFBF")
XL_FORMULA_BG = xl_color("#F2F2F2")

thin = Side(style="thin", color=XL_BORDER)
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)

wb = Workbook()
wb.properties.title = TITLE

# ============================================================
# Sheet 1: 采购BOM
# 锚点：第1行表头 / 第2~19行数据 / 第20行合计
# ============================================================
ws = wb.active
ws.title = "采购BOM"

HEADERS = ["序号", "类别", "位号", "名称", "规格参数", "封装/尺寸",
           "单板用量", "建议采购量", "属性", "用途与选型要点", "备注"]
WIDTHS = [5, 8, 7, 15, 30, 18, 8, 10, 8, 46, 24]
for i, (h, w) in enumerate(zip(HEADERS, WIDTHS), start=1):
    c = ws.cell(row=1, column=i, value=h)
    c.font = Font(bold=True, color=XL_HEADER_FG, size=10)
    c.fill = PatternFill("solid", fgColor=XL_HEADER_BG)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = BORDER
    ws.column_dimensions[get_column_letter(i)].width = w
ws.row_dimensions[1].height = 26

# (类别, 位号, 名称, 规格, 封装, 单板用量, 采购量, 属性, 要点, 备注)
ROWS = [
    ("芯片", "U1", "IP5406 电源管理", "5V UPS 升压充电管理，2A 充电 / 2.4A 放电",
     "ESOP8 (3.9×4.9mm，含底部散热焊盘)", 1, 3, "必买",
     "核心芯片。IP5407、IP5406T 引脚完全一致，任一款都能焊；买 3 只（一只焊、一只备用、一只可能拆坏）",
     "不要买 IP5506（ESOP16，带负载检测会自动休眠，与常开输出冲突）"),
    ("电感", "L1", "1µH 屏蔽功率电感", "1µH ±20%，Isat≥4.5A，Irms≥3A，DCR≤30mΩ",
     "5.0×5.0×3.0mm", 1, 5, "必买",
     "开关电感，原装模块上印着 1R0。焊盘中心距 3.2mm，引脚距 3.0–3.6mm 都能焊",
     "必须屏蔽型；6×6 装不下；饱和电流低于 4A 会发热掉压"),
    ("电容", "C1", "22µF 陶瓷电容", "22µF / 16V X5R", "0805", 1, 10, "必买",
     "VIN 输入滤波，尽量靠近 U1 第 1 脚", "必须 0805（焊盘间距 1.8mm），1206 装不下"),
    ("电容", "C2", "10µF 陶瓷电容", "10µF / 16V X5R", "0805", 1, 10, "必买",
     "BAT 端滤波，靠近电感第 2 脚", "与 22µF 不可混用位号，容量按 10µF 选"),
    ("电容", "C3", "22µF 陶瓷电容", "22µF / 16V X5R", "0805", 1, 10, "必买",
     "VOUT 储能", "与 C4 并联，同规格"),
    ("电容", "C4", "22µF 陶瓷电容", "22µF / 16V X5R", "0805", 1, 10, "必买",
     "VOUT 储能", "与 C3 并联，同规格"),
    ("电容", "C5", "100nF 陶瓷电容", "100nF / 50V X7R", "0603", 1, 20, "必买",
     "VOUT 高频旁路", "★ 是 0603（焊盘间距 1.5mm），别买成 0805"),
    ("连接器", "J1", "2.54mm 单排针 1×6", "2.54mm 间距，针长 ≥11mm", "1×6 THT", 1, 2, "必买",
     "主接口：OUT-5V / GND / BAT / GND / GND / VIN", "与原 IP5306 模块同序同位，可直接替换"),
    ("连接器", "J2", "2.54mm 单排针 1×4", "2.54mm 间距", "1×4 THT", 1, 2, "必买",
     "扩展接口：DCP / KEY / LED1 / LED2", "电量灯从 LED1/LED2 外接，板上无 LED"),
    ("连接器", "J4", "2.54mm 单排针 1×2", "2.54mm 间距", "1×2 THT", 1, 2, "必买",
     "外接电源开关（VOUT / OUT_SW）", "不接开关时插短接帽，输出常开"),
    ("连接器", "J3", "PH2.0 2P 卧式母座", "PH2.0 间距 2.0mm，卧式，本体探出板边", "PH2.0-2P", 1, 2, "必买",
     "电池直插口，1 脚 BAT+ / 2 脚 GND−", "电池包直接插，不用另焊线"),
    ("连接器", "JP1", "2.54mm 短接帽", "2.54mm 跳线帽", "—", 1, 5, "可选",
     "不接外接开关时短接 J4，实现上电即输出", "买排针时通常一包多个"),
    ("耗材", "—", "有铅焊锡丝", "Sn63Pb37，线径 0.6mm，含松香芯", "—", None, 1, "必买",
     "手焊 0805 / 0603 / 排针的主用料", "熔点 183℃，比无铅好焊；配 300–320℃ 烙铁"),
    ("耗材", "—", "有铅锡膏", "Sn63Pb37，针管装", "—", None, 1, "必买",
     "吹 U1 底部 2.2×2.6mm 散热焊盘用", "配热风枪 280–300℃、小风量"),
    ("耗材", "—", "免洗助焊剂", "助焊笔或松香膏", "—", None, 1, "必买",
     "拖焊排针、补焊、拆件", "有铅工艺全程用免洗型即可"),
    ("备件", "—", "贴片电阻 1kΩ", "1kΩ ±1% 1/8W", "0805", 0, 10, "可选",
     "板上不用（本设计电阻数量为 0）", "外接 LED1/LED2 电量灯时串在 LED 上限流"),
    ("备件", "—", "贴片电阻 10kΩ", "10kΩ ±1% 1/8W", "0805", 0, 10, "可选",
     "板上不用", "想用 NTC 做温度保护时，与 NTC 分压后接 KEY"),
    ("备件", "—", "NTC 热敏电阻", "10kΩ B=3950", "0603 / 0805", 0, 2, "可选",
     "板上不用", "贴在电池上做充电温度保护，接 KEY 脚"),
]

FIRST_DATA_ROW = 2
LAST_DATA_ROW = FIRST_DATA_ROW + len(ROWS) - 1   # 19
TOTAL_ROW = LAST_DATA_ROW + 1                    # 20

for idx, row in enumerate(ROWS):
    r = FIRST_DATA_ROW + idx
    values = [idx + 1] + list(row)
    for col, val in enumerate(values, start=1):
        c = ws.cell(row=r, column=col, value=val)
        c.border = BORDER
        c.font = Font(size=10)
        if col in (1, 3, 7, 8, 9):
            c.alignment = Alignment(horizontal="center", vertical="center")
        elif col in (5, 6, 10, 11):
            c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        else:
            c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    # 采购量是可填写区，浅底提示
    ws.cell(row=r, column=8).fill = PatternFill("solid", fgColor=XL_INPUT_BG)
    ws.cell(row=r, column=7).number_format = "0"
    ws.cell(row=r, column=8).number_format = "0"

# 合计行
ws.cell(row=TOTAL_ROW, column=4, value="单板元件合计")
ws.cell(row=TOTAL_ROW, column=7, value=f"=SUM(G{FIRST_DATA_ROW}:G{LAST_DATA_ROW})")
ws.cell(row=TOTAL_ROW, column=10,
        value="不含耗材与备件：贴片 7 只 + 连接器 4 只 + 短接帽 1 只 = 12 只")
for col in range(1, 12):
    c = ws.cell(row=TOTAL_ROW, column=col)
    c.fill = PatternFill("solid", fgColor=XL_TOTAL_BG)
    c.font = Font(bold=True, color=XL_HEADER_FG, size=10)
    c.border = BORDER
    if col in (7,):
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.number_format = "0"
    elif col == 10:
        c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    else:
        c.alignment = Alignment(horizontal="center", vertical="center")

# 数据验证：类别 / 属性
dv_cat = DataValidation(type="list", formula1='"芯片,电感,电容,连接器,耗材,备件"', allow_blank=True)
dv_attr = DataValidation(type="list", formula1='"必买,可选"', allow_blank=True)
ws.add_data_validation(dv_cat)
ws.add_data_validation(dv_attr)
dv_cat.add(f"B{FIRST_DATA_ROW}:B{LAST_DATA_ROW}")
dv_attr.add(f"I{FIRST_DATA_ROW}:I{LAST_DATA_ROW}")

# 条件格式：属性列
ws.conditional_formatting.add(
    f"I{FIRST_DATA_ROW}:I{LAST_DATA_ROW}",
    CellIsRule(operator="equal", formula=['"必买"'],
               fill=PatternFill("solid", fgColor=xl_color("#C6EFCE")),
               font=Font(color=xl_color("#006100"), bold=True, size=10)))
ws.conditional_formatting.add(
    f"I{FIRST_DATA_ROW}:I{LAST_DATA_ROW}",
    CellIsRule(operator="equal", formula=['"可选"'],
               fill=PatternFill("solid", fgColor=xl_color("#F2F2F2")),
               font=Font(color=xl_color("#7F7F7F"), size=10)))

ws.auto_filter.ref = f"A1:K{LAST_DATA_ROW}"
ws.freeze_panes = "A2"

# ============================================================
# Sheet 2: 下单参数
# 锚点：第1行表头 / 第2行起数据
# ============================================================
ws2 = wb.create_sheet("下单参数")
H2 = ["项目", "选择", "说明"]
W2 = [18, 30, 58]
for i, (h, w) in enumerate(zip(H2, W2), start=1):
    c = ws2.cell(row=1, column=i, value=h)
    c.font = Font(bold=True, color=XL_HEADER_FG, size=10)
    c.fill = PatternFill("solid", fgColor=XL_HEADER_BG)
    c.alignment = Alignment(horizontal="center", vertical="center")
    c.border = BORDER
    ws2.column_dimensions[get_column_letter(i)].width = w
ws2.row_dimensions[1].height = 24

PARAMS = [
    ("上传文件", "IP5406_PSU_Gerber_JLC.zip", "已剔除 .gbrjob，避免上传时报“未知文件”；直接拖进嘉立创 PCB 下单页"),
    ("板材", "FR-4", "默认"),
    ("层数", "2", "上传后自动识别，核对显示为 2"),
    ("尺寸", "25 × 16 mm", "自动读出，不要手动改"),
    ("数量", "5 片", "免费打样起订量"),
    ("板厚", "1.6 mm", "默认免费；想严格按设计走可选 1.5，两者都能插排针"),
    ("铜厚", "1 oz", "默认"),
    ("阻焊颜色", "绿色", "其他颜色可能加价或加交期"),
    ("丝印颜色", "白色", "背面有 IP5406 5V UPS / Lambilly @2026.11"),
    ("表面处理", "有铅喷锡 Sn63/Pb37", "手焊首选（183℃）。要做成产品出售再改无铅喷锡"),
    ("最小线宽/线距", "0.2 / 0.2 mm", "实际设计 0.25 / 0.2，在免费范围内"),
    ("过孔", "0.3 mm，盖油", "板上有 10 个过孔（0.3 钻 / 0.6 盘）"),
    ("SMT 贴片", "不需要", "自己手焊，省贴片费"),
    ("交期", "免费打样通道", "1–2 层、≤100×100mm 免费打样，只付运费（约 10–15 元）"),
]
for idx, (a, b, c_) in enumerate(PARAMS):
    r = 2 + idx
    for col, val in enumerate([a, b, c_], start=1):
        cell = ws2.cell(row=r, column=col, value=val)
        cell.border = BORDER
        cell.font = Font(size=10)
        cell.alignment = Alignment(horizontal="left", vertical="center",
                                   wrap_text=(col == 3))
    ws2.cell(row=r, column=1).font = Font(size=10, bold=True)
ws2.freeze_panes = "A2"

wb.save(OUT_XLSX)
print("saved:", OUT_XLSX)
print("sheets:", wb.sheetnames, "rows:", LAST_DATA_ROW, "total row:", TOTAL_ROW)
