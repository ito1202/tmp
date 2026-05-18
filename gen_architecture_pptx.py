from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import pptx.oxml.ns as nsmap
from lxml import etree

# ============================================================
# カラーパレット（Azure ブルー系）
# ============================================================
C_AZURE_BLUE   = RGBColor(0x00, 0x78, 0xD4)  # Azure ブランドカラー
C_VNET_BG      = RGBColor(0xE8, 0xF4, 0xFD)  # VNet 背景
C_SUBNET_BG    = RGBColor(0xD0, 0xE8, 0xF8)  # Subnet 背景
C_ONPREM_BG    = RGBColor(0xF0, 0xF0, 0xF0)  # オンプレ背景
C_AI_BG        = RGBColor(0xFD, 0xF0, 0xFF)  # AI サービス背景
C_WHITE        = RGBColor(0xFF, 0xFF, 0xFF)
C_DARK_TEXT    = RGBColor(0x1A, 0x1A, 0x1A)
C_GRAY_TEXT    = RGBColor(0x60, 0x60, 0x60)
C_ORANGE       = RGBColor(0xFF, 0x8C, 0x00)
C_GREEN        = RGBColor(0x10, 0x7C, 0x10)
C_BORDER       = RGBColor(0x00, 0x78, 0xD4)

# ============================================================
# ヘルパー
# ============================================================
def add_rect(slide, x, y, w, h, fill_rgb, border_rgb=None, border_pt=1.5, radius=False):
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        Inches(x), Inches(y), Inches(w), Inches(h)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_rgb
    if border_rgb:
        shape.line.color.rgb = border_rgb
        shape.line.width = Pt(border_pt)
    else:
        shape.line.fill.background()
    return shape

def add_textbox(slide, x, y, w, h, text, font_size=11, bold=False,
                color=None, align=PP_ALIGN.CENTER, wrap=True):
    txb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    txb.word_wrap = wrap
    tf = txb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = color if color else C_DARK_TEXT
    return txb

def add_labeled_box(slide, x, y, w, h, label, sublabel=None,
                    fill=C_WHITE, border=C_BORDER, label_size=10, sub_size=8):
    box = add_rect(slide, x, y, w, h, fill, border)
    # ラベル
    add_textbox(slide, x, y + 0.05, w, 0.25, label,
                font_size=label_size, bold=True, color=C_DARK_TEXT)
    if sublabel:
        add_textbox(slide, x, y + 0.28, w, 0.2, sublabel,
                    font_size=sub_size, color=C_GRAY_TEXT)
    return box

def add_arrow(slide, x1, y1, x2, y2):
    """水平または垂直の矢印（connectorで近似）"""
    from pptx.util import Inches
    connector = slide.shapes.add_connector(
        2,  # MSO_CONNECTOR_TYPE.STRAIGHT
        Inches(x1), Inches(y1), Inches(x2), Inches(y2)
    )
    connector.line.color.rgb = C_AZURE_BLUE
    connector.line.width = Pt(1.5)
    return connector

# ============================================================
# プレゼンテーション作成
# ============================================================
prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)

# ============================================================
# スライド 1: アーキテクチャ全体図
# ============================================================
slide1 = prs.slides.add_slide(prs.slide_layouts[6])  # 空白レイアウト

# タイトル
add_textbox(slide1, 0.2, 0.1, 12.9, 0.4,
            "Azure 最小構成 — アーキテクチャ全体図",
            font_size=16, bold=True, color=C_AZURE_BLUE)

# ---- オンプレミスエリア ----
add_rect(slide1, 0.2, 0.6, 2.0, 2.2, C_ONPREM_BG, RGBColor(0x80,0x80,0x80), 1.5)
add_textbox(slide1, 0.2, 0.62, 2.0, 0.25, "オンプレミス",
            font_size=9, bold=True, color=C_GRAY_TEXT)
add_labeled_box(slide1, 0.35, 0.95, 1.7, 0.55,
                "ユーザー PC", "ブラウザ", fill=C_WHITE, border=RGBColor(0x80,0x80,0x80))
add_labeled_box(slide1, 0.35, 1.65, 1.7, 0.55,
                "VPN デバイス", "IPsec", fill=C_WHITE, border=RGBColor(0x80,0x80,0x80))

# ---- VPN Gateway ----
add_labeled_box(slide1, 2.7, 1.1, 1.6, 0.7,
                "VPN Gateway", "pip: output で確認",
                fill=RGBColor(0xE0,0xF0,0xFF), border=C_AZURE_BLUE)

# ---- VNet エリア ----
add_rect(slide1, 4.7, 0.55, 5.5, 5.5, C_VNET_BG, C_AZURE_BLUE, 2.0)
add_textbox(slide1, 4.7, 0.57, 5.5, 0.28,
            "Virtual Network  10.0.0.0/16",
            font_size=9, bold=True, color=C_AZURE_BLUE)

# GatewaySubnet
add_rect(slide1, 4.9, 0.9, 2.4, 0.55,
         RGBColor(0xC8,0xDC,0xF0), C_AZURE_BLUE, 1.0)
add_textbox(slide1, 4.9, 0.92, 2.4, 0.2,
            "GatewaySubnet  10.0.255.0/27",
            font_size=8, bold=True, color=C_AZURE_BLUE)

# Subnet-app
add_rect(slide1, 4.9, 1.6, 5.1, 4.2, C_SUBNET_BG, C_AZURE_BLUE, 1.0)
add_textbox(slide1, 4.9, 1.62, 5.1, 0.22,
            "subnet-app  10.0.1.0/24",
            font_size=8, bold=True, color=C_AZURE_BLUE)

# NSG バッジ
add_rect(slide1, 9.5, 1.62, 0.45, 0.22,
         RGBColor(0xFF,0xC0,0x00), None)
add_textbox(slide1, 9.5, 1.62, 0.45, 0.22, "NSG",
            font_size=7, bold=True, color=C_DARK_TEXT)

# Private DNS Zone
add_rect(slide1, 5.05, 1.9, 4.8, 0.45,
         RGBColor(0xD8,0xF0,0xE8), RGBColor(0x10,0x7C,0x10), 1.0)
add_textbox(slide1, 5.05, 1.92, 4.8, 0.2,
            "Private DNS Zone  privatelink.azurewebsites.net",
            font_size=8, color=C_GREEN)

# Frontend App Service
add_labeled_box(slide1, 5.05, 2.5, 2.2, 0.8,
                "App Service (Frontend)", "assistant-ui / Node",
                fill=C_WHITE, border=C_AZURE_BLUE)
add_rect(slide1, 5.05, 3.35, 2.2, 0.35, RGBColor(0xE8,0xF8,0xFF), C_AZURE_BLUE, 0.8)
add_textbox(slide1, 5.05, 3.37, 2.2, 0.22,
            "Private Endpoint", font_size=7, color=C_AZURE_BLUE)

# Backend App Service
add_labeled_box(slide1, 5.05, 3.9, 2.2, 0.8,
                "App Service (Backend)", "FastAPI / Python",
                fill=C_WHITE, border=C_AZURE_BLUE)
add_rect(slide1, 5.05, 4.75, 2.2, 0.35, RGBColor(0xE8,0xF8,0xFF), C_AZURE_BLUE, 0.8)
add_textbox(slide1, 5.05, 4.77, 2.2, 0.22,
            "Private Endpoint", font_size=7, color=C_AZURE_BLUE)

# Managed ID バッジ（Frontend）
add_rect(slide1, 7.3, 2.6, 0.9, 0.22,
         RGBColor(0xC0,0xFF,0xC0), None)
add_textbox(slide1, 7.3, 2.6, 0.9, 0.22,
            "Managed ID", font_size=7, bold=True, color=C_GREEN)

# Managed ID バッジ（Backend）
add_rect(slide1, 7.3, 4.0, 0.9, 0.22,
         RGBColor(0xC0,0xFF,0xC0), None)
add_textbox(slide1, 7.3, 4.0, 0.9, 0.22,
            "Managed ID", font_size=7, bold=True, color=C_GREEN)

# ---- AI サービスエリア ----
add_rect(slide1, 10.5, 2.8, 2.5, 2.5, C_AI_BG, RGBColor(0x80,0x00,0x80), 1.5)
add_textbox(slide1, 10.5, 2.82, 2.5, 0.25,
            "Microsoft Foundry", font_size=9, bold=True,
            color=RGBColor(0x60,0x00,0x60))
add_labeled_box(slide1, 10.65, 3.1, 2.15, 0.55,
                "GPT-5.2", "LLM",
                fill=C_WHITE, border=RGBColor(0x80,0x00,0x80))
add_labeled_box(slide1, 10.65, 3.8, 2.15, 0.55,
                "Embedding 003", "埋め込みモデル",
                fill=C_WHITE, border=RGBColor(0x80,0x00,0x80))
add_labeled_box(slide1, 10.65, 4.5, 2.15, 0.55,
                "Foundry Agent", "agent-parent",
                fill=C_WHITE, border=RGBColor(0x80,0x00,0x80))

# ---- 矢印 ----
# ユーザー → VPN デバイス
add_arrow(slide1, 1.2, 1.65, 1.2, 1.92)
# VPN デバイス → VPN Gateway
add_arrow(slide1, 2.05, 1.92, 2.7, 1.45)
# VPN Gateway → GatewaySubnet
add_arrow(slide1, 4.3, 1.45, 4.9, 1.17)
# Frontend → Backend
add_arrow(slide1, 6.15, 3.3, 6.15, 3.9)
# Backend → AI
add_arrow(slide1, 7.25, 4.3, 10.5, 3.85)

# ---- 凡例 ----
add_textbox(slide1, 0.2, 5.5, 12.9, 0.25,
            "※ Public Network Access: Disabled（社外から DNS 解決不可・接続不可）",
            font_size=8, color=RGBColor(0xC0,0x00,0x00))

# ============================================================
# スライド 2: ネットワーク設計（アドレス一覧）
# ============================================================
slide2 = prs.slides.add_slide(prs.slide_layouts[6])

add_textbox(slide2, 0.2, 0.1, 12.9, 0.4,
            "ネットワーク設計 — アドレス・リソース一覧",
            font_size=16, bold=True, color=C_AZURE_BLUE)

# テーブル風に手動描画
headers = ["カテゴリ", "リソース名", "設定値", "備考"]
rows = [
    ["VNet",       "vnet-rg-azure-test",      "10.0.0.0/16",          "リージョン: Japan East"],
    ["Subnet",     "GatewaySubnet",            "10.0.255.0/27",        "VPN Gateway 専用（名前固定）"],
    ["Subnet",     "subnet-app",               "10.0.1.0/24",          "App Service 用"],
    ["NSG",        "nsg-app",                  "Inbound 許可: 443",    "送信元: オンプレIP（tfvars 参照）"],
    ["VPN GW",     "vpngw-main",               "SKU: VpnGw1",          "Public IP は output で確認"],
    ["App Service","app-fe-test",              "B1 / Linux",           "Frontend（Public 無効）"],
    ["App Service","app-be-test",              "B1 / Linux",           "Backend（Public 無効）"],
    ["PE",         "pe-app-fe-test",           "subnet-app に配置",    "Frontend Private Endpoint"],
    ["PE",         "pe-app-be-test",           "subnet-app に配置",    "Backend Private Endpoint"],
    ["DNS Zone",   "privatelink.azurewebsites.net", "VNet リンク済み", "VNet 内の名前解決"],
]

col_x = [0.3, 1.8, 4.0, 6.8]
col_w = [1.4, 2.1, 2.7, 5.8]
row_h = 0.38
header_y = 0.65

# ヘッダー行
for i, (hx, hw, ht) in enumerate(zip(col_x, col_w, headers)):
    add_rect(slide2, hx, header_y, hw, row_h,
             C_AZURE_BLUE, None)
    add_textbox(slide2, hx, header_y + 0.05, hw, row_h - 0.1,
                ht, font_size=10, bold=True, color=C_WHITE)

# データ行
for ri, row in enumerate(rows):
    y = header_y + row_h * (ri + 1)
    bg = C_WHITE if ri % 2 == 0 else RGBColor(0xF5, 0xF8, 0xFF)
    for ci, (cx, cw, cell) in enumerate(zip(col_x, col_w, row)):
        add_rect(slide2, cx, y, cw, row_h, bg, RGBColor(0xCC,0xCC,0xCC), 0.5)
        add_textbox(slide2, cx + 0.05, y + 0.05, cw - 0.1, row_h - 0.1,
                    cell, font_size=9, color=C_DARK_TEXT, align=PP_ALIGN.LEFT)

add_textbox(slide2, 0.3, 6.9, 12.0, 0.25,
            "※ terraform.tfvars の allowed_ip_ranges にオンプレのグローバルIPを設定すること",
            font_size=8, color=RGBColor(0xC0,0x00,0x00))

# ============================================================
# スライド 3: 通信フロー
# ============================================================
slide3 = prs.slides.add_slide(prs.slide_layouts[6])

add_textbox(slide3, 0.2, 0.1, 12.9, 0.4,
            "通信フロー",
            font_size=16, bold=True, color=C_AZURE_BLUE)

flows = [
    ("1. ユーザー → Frontend",
     "オンプレ PC  →  VPN（IPsec）  →  VPN Gateway  →  VNet  →  Private Endpoint  →  App Service Frontend",
     "社外からは DNS 解決不可。VPN 接続済みオンプレからのみ到達可能。"),
    ("2. Frontend → Backend",
     "App Service Frontend  →  VNet 内通信（VNet Integration）  →  App Service Backend",
     "同一 VNet 内の通信。インターネットを経由しない。"),
    ("3. Backend → AI（マネージドID 認証）",
     "App Service Backend  →  マネージドID で EntraID 認証  →  Foundry / Azure OpenAI",
     "キー・シークレット不要。Backend の Principal ID に Cognitive Services User ロールを付与。"),
    ("4. 社外からのアクセス（遮断）",
     "インターネット  →  DNS 解決不可（Public Endpoint 無効）  →  接続不可",
     "存在しないものとして扱われる。ログイン画面すら表示されない。"),
]

for i, (title, flow, note) in enumerate(flows):
    y = 0.7 + i * 1.5
    add_rect(slide3, 0.3, y, 12.5, 1.35,
             RGBColor(0xF5,0xF8,0xFF) if i != 3 else RGBColor(0xFF,0xF0,0xF0),
             C_AZURE_BLUE if i != 3 else RGBColor(0xC0,0x00,0x00), 1.0)
    add_textbox(slide3, 0.4, y + 0.05, 12.3, 0.3,
                title, font_size=11, bold=True,
                color=C_AZURE_BLUE if i != 3 else RGBColor(0xC0,0x00,0x00),
                align=PP_ALIGN.LEFT)
    add_textbox(slide3, 0.4, y + 0.35, 12.3, 0.45,
                flow, font_size=10, color=C_DARK_TEXT, align=PP_ALIGN.LEFT)
    add_textbox(slide3, 0.4, y + 0.8, 12.3, 0.4,
                f"補足: {note}", font_size=8, color=C_GRAY_TEXT, align=PP_ALIGN.LEFT)

# ============================================================
# 保存
# ============================================================
out_path = "/home/user/tmp/azure-test-environment/docs/architecture.pptx"
prs.save(out_path)
print(f"Saved: {out_path}")
