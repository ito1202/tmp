from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

C_AZURE       = RGBColor(0x00, 0x78, 0xD4)
C_VNET_BG     = RGBColor(0xE3, 0xF2, 0xFD)
C_GW_BG       = RGBColor(0xE8, 0xEA, 0xED)
C_PE_BG       = RGBColor(0xB2, 0xDF, 0xDB)
C_INT_BG      = RGBColor(0xB3, 0xD9, 0xF7)
C_FUNC_BG     = RGBColor(0xC8, 0xE6, 0xC9)
C_ONPREM_BG   = RGBColor(0xF5, 0xF5, 0xF5)
C_AI_BG       = RGBColor(0xF3, 0xE5, 0xF5)
C_PE_BOX      = RGBColor(0xE0, 0xF7, 0xFA)
C_WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
C_DARK        = RGBColor(0x1A, 0x1A, 0x1A)
C_GRAY        = RGBColor(0x60, 0x60, 0x60)
C_RED         = RGBColor(0xC6, 0x28, 0x28)
C_GREEN       = RGBColor(0x1B, 0x5E, 0x20)
C_PURPLE      = RGBColor(0x6A, 0x1A, 0x9A)
C_ORANGE      = RGBColor(0xE6, 0x51, 0x00)
C_GW_BORDER   = RGBColor(0x90, 0x90, 0x90)
C_PE_BORDER   = RGBColor(0x00, 0x69, 0x5C)
C_INT_BORDER  = RGBColor(0x01, 0x57, 0x9B)
C_FUNC_BORDER = RGBColor(0x1B, 0x5E, 0x20)

prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)

def rect(slide, x, y, w, h, fill, border=None, bw=1.5):
    s = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = fill
    if border:
        s.line.color.rgb = border; s.line.width = Pt(bw)
    else:
        s.line.fill.background()
    return s

def txt(slide, x, y, w, h, text, size=9, bold=False,
        color=None, align=PP_ALIGN.CENTER, wrap=True):
    t = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    t.word_wrap = wrap
    tf = t.text_frame; tf.word_wrap = wrap
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = bold
    r.font.color.rgb = color or C_DARK

def box(slide, x, y, w, h, label, sub=None,
        fill=C_WHITE, border=C_AZURE, ls=9, ss=7.5):
    rect(slide, x, y, w, h, fill, border, 1.2)
    txt(slide, x, y+0.04, w, 0.24, label, ls, True, C_DARK)
    if sub:
        txt(slide, x, y+0.27, w, 0.2, sub, ss, False, C_GRAY)

def arrow(slide, x1, y1, x2, y2, color=C_AZURE, w=1.5):
    c = slide.shapes.add_connector(2,
        Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = color; c.line.width = Pt(w)

# ============================================================
# スライド 1: 全体アーキテクチャ
# ============================================================
s1 = prs.slides.add_slide(prs.slide_layouts[6])
txt(s1, 0.2, 0.05, 12.9, 0.38,
    "全体アーキテクチャ — リソースと Subnet の配置",
    15, True, C_AZURE)

# オンプレ
rect(s1, 0.15, 0.52, 1.85, 2.0, C_ONPREM_BG, C_GW_BORDER, 1.2)
txt(s1, 0.15, 0.53, 1.85, 0.22, "オンプレミス", 8, True, C_GRAY)
box(s1, 0.25, 0.82, 1.6, 0.52, "ユーザー PC", "ブラウザ",
    fill=C_WHITE, border=C_GW_BORDER)
box(s1, 0.25, 1.45, 1.6, 0.52, "VPN デバイス", "IPsec",
    fill=C_WHITE, border=C_GW_BORDER)

# VNet 全体
rect(s1, 2.2, 0.45, 8.15, 6.75, C_VNET_BG, C_AZURE, 2.2)
txt(s1, 2.2, 0.47, 8.15, 0.25,
    "Virtual Network  10.0.0.0/16", 9, True, C_AZURE)

# GatewaySubnet
rect(s1, 2.38, 0.8, 2.3, 0.95, C_GW_BG, C_GW_BORDER, 1.2)
txt(s1, 2.38, 0.82, 2.3, 0.22,
    "GatewaySubnet  10.0.255.0/27", 7.5, True, C_GRAY)
box(s1, 2.48, 1.1, 2.1, 0.52, "VPN Gateway", "",
    fill=C_WHITE, border=C_GW_BORDER)

# subnet-pe
rect(s1, 2.38, 1.88, 2.3, 5.1, C_PE_BG, C_PE_BORDER, 1.5)
txt(s1, 2.38, 1.9, 2.3, 0.22,
    "subnet-pe  10.0.2.0/24", 7.5, True, C_PE_BORDER)
txt(s1, 2.42, 2.13, 2.22, 0.2,
    "Private Endpoint 置き場", 7, False, C_PE_BORDER)

for i, (label, sub) in enumerate([
    ("PE: Frontend", ""),
    ("PE: Backend", ""),
    ("PE: Functions", ""),
    ("PE: Storage", ""),
    ("PE: AI Search", ""),
    ("PE: Foundry", ""),
]):
    box(s1, 2.45, 2.38 + i * 0.72, 2.15, 0.58,
        label, sub, fill=C_PE_BOX, border=C_PE_BORDER, ls=8)

# subnet-integration
rect(s1, 4.85, 1.88, 2.5, 2.5, C_INT_BG, C_INT_BORDER, 1.5)
txt(s1, 4.85, 1.9, 2.5, 0.22,
    "subnet-integration  10.0.1.0/24", 7.5, True, C_INT_BORDER)
txt(s1, 4.9, 2.13, 2.4, 0.2,
    "App Service VNet Integration（出口）", 7, False, C_INT_BORDER)

box(s1, 4.93, 2.38, 2.3, 0.65, "App Service", "Frontend / assistant-ui",
    fill=C_WHITE, border=C_AZURE)
box(s1, 4.93, 3.12, 2.3, 0.65, "App Service", "Backend / FastAPI",
    fill=C_WHITE, border=C_AZURE)

# Managed ID バッジ
rect(s1, 4.93, 3.83, 1.1, 0.22, RGBColor(0xE8,0xF5,0xE9), C_GREEN, 0.8)
txt(s1, 4.93, 3.84, 1.1, 0.2, "Managed ID", 7, True, C_GREEN)
rect(s1, 4.93, 3.12+0.65+0.06, 1.1, 0.22, RGBColor(0xE8,0xF5,0xE9), C_GREEN, 0.8)

# subnet-func-integration
rect(s1, 4.85, 4.55, 2.5, 1.65, C_FUNC_BG, C_FUNC_BORDER, 1.5)
txt(s1, 4.85, 4.57, 2.5, 0.22,
    "subnet-func-integration  10.0.4.0/24", 7.5, True, C_FUNC_BORDER)
txt(s1, 4.9, 4.8, 2.4, 0.2,
    "Functions VNet Integration（出口）", 7, False, C_FUNC_BORDER)
box(s1, 4.93, 5.05, 2.3, 0.65, "Azure Functions", "Flex Consumption / RAG",
    fill=C_WHITE, border=C_FUNC_BORDER)
rect(s1, 4.93, 5.76, 1.1, 0.22, RGBColor(0xE8,0xF5,0xE9), C_GREEN, 0.8)
txt(s1, 4.93, 5.77, 1.1, 0.2, "Managed ID", 7, True, C_GREEN)

# Azure マネージドゾーン
rect(s1, 7.55, 0.45, 3.9, 6.75, C_AI_BG, C_PURPLE, 1.5)
txt(s1, 7.55, 0.47, 3.9, 0.25,
    "Azure マネージドゾーン（VNet 外）", 8.5, True, C_PURPLE)

box(s1, 7.7, 0.82, 3.6, 0.65, "Storage Account", "RAG 用 blob",
    fill=C_WHITE, border=C_AZURE)
box(s1, 7.7, 1.58, 3.6, 0.65, "Azure AI Search", "ベクトル検索 / RAG",
    fill=C_WHITE, border=C_AZURE)
box(s1, 7.7, 2.34, 3.6, 0.65, "App Service Frontend", "Public 無効",
    fill=C_WHITE, border=C_AZURE)
box(s1, 7.7, 3.1, 3.6, 0.65, "App Service Backend", "Public 無効",
    fill=C_WHITE, border=C_AZURE)
box(s1, 7.7, 3.86, 3.6, 0.65, "Azure Functions", "Public 無効",
    fill=C_WHITE, border=C_FUNC_BORDER)

rect(s1, 7.7, 4.62, 3.6, 2.3, RGBColor(0xEE,0xE0,0xF8), C_PURPLE, 1.2)
txt(s1, 7.7, 4.64, 3.6, 0.24, "Azure AI Foundry", 8.5, True, C_PURPLE)
box(s1, 7.8, 4.94, 1.65, 0.52, "親エージェント", "", fill=C_WHITE, border=C_PURPLE)
box(s1, 9.55, 4.94, 1.65, 0.52, "子エージェント", "", fill=C_WHITE, border=C_PURPLE)
box(s1, 7.8, 5.55, 1.65, 0.52, "GPT-5.2", "LLM", fill=C_WHITE, border=C_PURPLE)
box(s1, 9.55, 5.55, 1.65, 0.52, "Embedding 003", "", fill=C_WHITE, border=C_PURPLE)

# Log Analytics（右下）
rect(s1, 7.7, 7.0, 3.6, 0.38, RGBColor(0xFF, 0xF8, 0xE1), RGBColor(0xF5,0x7F,0x17), 1.0)
txt(s1, 7.7, 7.01, 3.6, 0.3,
    "Log Analytics Workspace（監視）", 8, True, RGBColor(0xE6,0x51,0x00))

# 矢印
arrow(s1, 2.0, 1.71, 2.38, 1.35)   # VPN デバイス → VPN GW
arrow(s1, 2.58, 1.62, 2.58, 1.88)   # GW → subnet-pe
arrow(s1, 4.6, 2.68, 4.85, 2.68)    # PE:FE → App Service FE
arrow(s1, 4.6, 3.44, 4.85, 3.44)    # PE:BE → App Service BE
arrow(s1, 4.6, 4.2, 4.85, 5.37)     # PE:Func → Functions
arrow(s1, 7.35, 1.11, 7.55, 1.11)   # PE:Storage → Storage
arrow(s1, 7.35, 1.87, 7.55, 1.87)   # PE:Search → AI Search
arrow(s1, 7.35, 4.86, 7.55, 4.9)    # PE:Foundry → Foundry

# Public 無効バッジ
for yr in [2.5, 3.26, 4.02]:
    rect(s1, 10.8, yr+0.15, 0.6, 0.22, C_RED, None)
    txt(s1, 10.8, yr+0.16, 0.6, 0.2, "PUB×", 6.5, True, C_WHITE)

txt(s1, 0.15, 7.25, 13.0, 0.22,
    "※ App Service / Functions は Public Endpoint 無効 — 社外から DNS 解決不可・接続不可",
    8, False, C_RED)

# ============================================================
# スライド 2: Subnet 役割と Private Endpoint 一覧
# ============================================================
s2 = prs.slides.add_slide(prs.slide_layouts[6])
txt(s2, 0.2, 0.05, 12.9, 0.38,
    "Subnet の役割と Private Endpoint 一覧",
    15, True, C_AZURE)

# Subnet 表
sub_headers = ["Subnet 名", "アドレス", "役割", "委任", "中に置くもの"]
sub_rows = [
    ("GatewaySubnet",           "10.0.255.0/27", "VPN Gateway 専用（名前固定）",             "なし",                       "VPN Gateway のみ"),
    ("subnet-pe",               "10.0.2.0/24",   "外→リソースへの入口\n（インバウンド受け口）", "なし",                       "Private Endpoint 全て"),
    ("subnet-integration",      "10.0.1.0/24",   "App Service→VNet の出口\n（アウトバウンド）", "Microsoft.Web/serverFarms",  "App Service FE / BE"),
    ("subnet-func-integration", "10.0.4.0/24",   "Functions→VNet の出口\n（アウトバウンド）",  "Microsoft.App/environments", "Azure Functions"),
]
col_w = [2.3, 1.4, 2.6, 2.3, 2.4]
col_x = [0.25, 2.6, 4.05, 6.7, 9.05]
hdr_colors = [C_AZURE]*5
row1 = 0.52

for ci, (h, cx, cw) in enumerate(zip(sub_headers, col_x, col_w)):
    rect(s2, cx, row1, cw, 0.35, C_AZURE, None)
    txt(s2, cx, row1+0.05, cw, 0.28, h, 9, True, C_WHITE)

row_colors = [C_GW_BG, C_PE_BG, C_INT_BG, C_FUNC_BG]
row_borders = [C_GW_BORDER, C_PE_BORDER, C_INT_BORDER, C_FUNC_BORDER]
for ri, (row, rc, rb) in enumerate(zip(sub_rows, row_colors, row_borders)):
    y = row1 + 0.35 + ri * 0.62
    for ci, (val, cx, cw) in enumerate(zip(row, col_x, col_w)):
        rect(s2, cx, y, cw, 0.58, rc if ci == 0 else C_WHITE,
             rb if ci == 0 else RGBColor(0xCC,0xCC,0xCC), 0.8)
        txt(s2, cx+0.05, y+0.04, cw-0.1, 0.52, val, 8.5,
            ci == 0, rb if ci == 0 else C_DARK, PP_ALIGN.LEFT)

# PE 表
txt(s2, 0.25, 3.15, 12.7, 0.3,
    "Private Endpoint 一覧（全て subnet-pe に配置）",
    10, True, C_PE_BORDER)

pe_headers = ["PE 名", "接続先リソース", "Private DNS Zone", "備考"]
pe_rows = [
    ("PE: Frontend",  "App Service Frontend",  "privatelink.azurewebsites.net",       "Public 無効"),
    ("PE: Backend",   "App Service Backend",   "privatelink.azurewebsites.net",       "Public 無効"),
    ("PE: Functions", "Azure Functions",       "privatelink.azurewebsites.net",       "Public 無効 / Flex Consumption"),
    ("PE: Storage",   "Storage Account",       "privatelink.blob.core.windows.net",   "blob サブリソース"),
    ("PE: AI Search", "Azure AI Search",       "privatelink.search.windows.net",      "searchService サブリソース"),
    ("PE: Foundry",   "Azure AI Foundry",      "privatelink.services.ai.azure.com",   "Hub・Project 各 1 個（TODO）"),
]
pe_col_w = [1.7, 2.5, 3.5, 3.9]
pe_col_x = [0.25, 2.0, 4.55, 8.1]

for ci, (h, cx, cw) in enumerate(zip(pe_headers, pe_col_x, pe_col_w)):
    rect(s2, cx, 3.48, cw, 0.32, C_PE_BORDER, None)
    txt(s2, cx, 3.5, cw, 0.28, h, 9, True, C_WHITE)

for ri, row in enumerate(pe_rows):
    y = 3.8 + ri * 0.5
    bg = RGBColor(0xE0,0xF7,0xFA) if ri % 2 == 0 else C_WHITE
    for ci, (val, cx, cw) in enumerate(zip(row, pe_col_x, pe_col_w)):
        rect(s2, cx, y, cw, 0.46, bg,
             RGBColor(0xCC,0xCC,0xCC), 0.6)
        txt(s2, cx+0.05, y+0.04, cw-0.1, 0.38, val, 8.5,
            False, C_DARK, PP_ALIGN.LEFT)

# ============================================================
# スライド 3: 通信フロー
# ============================================================
s3 = prs.slides.add_slide(prs.slide_layouts[6])
txt(s3, 0.2, 0.05, 12.9, 0.38,
    "通信フロー — チャット回答が返るまで",
    15, True, C_AZURE)

steps = [
    ("①", "オンプレ PC → VPN デバイス",
     "オンプレ内通信",
     C_GW_BORDER, C_ONPREM_BG),
    ("②", "VPN デバイス → VPN Gateway（GatewaySubnet）",
     "IPsec 暗号化トンネル経由で Azure VNet に入る",
     C_GW_BORDER, C_GW_BG),
    ("③④", "VPN GW → PE:Frontend（subnet-pe）→ App Service Frontend",
     "Private Endpoint がインバウンドを受け、Azure 内部プライベート回線でFrontend に転送。Public 無効のため社外からは DNS 解決すら不可",
     C_PE_BORDER, C_PE_BG),
    ("⑤⑥", "Frontend → subnet-integration（出口）→ PE:Backend → App Service Backend",
     "VNet Integration で subnet-integration を出口として使い、Private DNS が Backend の PE プライベート IP に解決",
     C_INT_BORDER, C_INT_BG),
    ("⑦⑧", "Backend → subnet-integration（出口）→ PE:Foundry → Azure AI Foundry",
     "Managed ID 認証。Backend が Foundry 親エージェントを呼ぶ",
     C_PURPLE, RGBColor(0xF3,0xE5,0xF5)),
    ("⑨⑩", "Foundry → PE:Functions（subnet-pe）→ Azure Functions（RAGツール）",
     "Foundry Managed Network 経由で Functions を呼ぶ。Functions は subnet-func-integration を出口として AI Search へ",
     C_FUNC_BORDER, C_FUNC_BG),
    ("⑪⑫", "Functions → subnet-func-integration → PE:AI Search → Azure AI Search → 回答生成",
     "ベクトル検索結果を Foundry に返す。回答は逆経路で Frontend → オンプレ PC に返る",
     C_INT_BORDER, RGBColor(0xE8,0xF5,0xE9)),
]

for i, (num, title, desc, tc, bg) in enumerate(steps):
    y = 0.52 + i * 0.86
    rect(s3, 0.25, y, 12.8, 0.8, bg, tc, 1.0)
    txt(s3, 0.28, y+0.04, 0.5, 0.35, num, 13, True, tc)
    txt(s3, 0.85, y+0.04, 11.8, 0.28, title, 10, True, C_DARK, PP_ALIGN.LEFT)
    txt(s3, 0.85, y+0.36, 11.8, 0.36, desc, 8.5, False, C_GRAY, PP_ALIGN.LEFT)

txt(s3, 0.25, 7.5-0.28, 12.8, 0.24,
    "社外からは全 App Service / Functions の Public Endpoint が無効 → DNS 解決不可・存在が見えない",
    8, False, C_RED)

# ============================================================
# 保存
# ============================================================
out = "/home/user/tmp/azure-test-environment/docs/architecture.pptx"
prs.save(out)
print(f"Saved: {out}")
