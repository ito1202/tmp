import openpyxl
from openpyxl.styles import (
    PatternFill, Font, Alignment, Border, Side, numbers
)
from openpyxl.utils import get_column_letter

wb = openpyxl.Workbook()

# ============================================================
# スタイル定義
# ============================================================
AZURE_BLUE   = "00539C"
HEADER_BG    = "00539C"
SECTION_BG   = "D6E4F0"
ALT_ROW_BG   = "F5F9FF"
WHITE        = "FFFFFF"
DUMMY_BG     = "FFF3CD"   # ダミー値セルは黄色
FIXED_BG     = "E8F5E9"   # 変更不要の固定値は薄緑
BORDER_COLOR = "CCCCCC"

def style_header(cell, text, bg=HEADER_BG, fg=WHITE, size=11):
    cell.value = text
    cell.font = Font(bold=True, color=fg, size=size)
    cell.fill = PatternFill("solid", fgColor=bg)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin = Side(style="thin", color=BORDER_COLOR)
    cell.border = Border(top=thin, left=thin, right=thin, bottom=thin)

def style_section(cell, text):
    cell.value = text
    cell.font = Font(bold=True, color=AZURE_BLUE, size=10)
    cell.fill = PatternFill("solid", fgColor=SECTION_BG)
    cell.alignment = Alignment(horizontal="left", vertical="center")
    thin = Side(style="thin", color=BORDER_COLOR)
    cell.border = Border(top=thin, left=thin, right=thin, bottom=thin)

def style_cell(cell, text, dummy=False, fixed=False, row_idx=0):
    cell.value = text
    bg = DUMMY_BG if dummy else (FIXED_BG if fixed else (ALT_ROW_BG if row_idx % 2 == 0 else WHITE))
    cell.fill = PatternFill("solid", fgColor=bg)
    cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    thin = Side(style="thin", color=BORDER_COLOR)
    cell.border = Border(top=thin, left=thin, right=thin, bottom=thin)
    cell.font = Font(size=10)

def write_row(ws, row, cols, dummy=False, fixed=False, row_idx=0):
    for ci, val in enumerate(cols, start=1):
        style_cell(ws.cell(row=row, column=ci), val,
                   dummy=dummy, fixed=fixed, row_idx=row_idx)

def write_section(ws, row, text, ncols=5):
    style_section(ws.cell(row=row, column=1), text)
    for ci in range(2, ncols+1):
        ws.cell(row=row, column=ci).fill = PatternFill("solid", fgColor=SECTION_BG)
        thin = Side(style="thin", color=BORDER_COLOR)
        ws.cell(row=row, column=ci).border = Border(
            top=thin, left=thin, right=thin, bottom=thin)
    ws.merge_cells(start_row=row, start_column=1,
                   end_row=row, end_column=ncols)

# ============================================================
# シート 1: ネットワーク
# ============================================================
ws1 = wb.active
ws1.title = "ネットワーク"

ws1.row_dimensions[1].height = 30
ws1.column_dimensions["A"].width = 28
ws1.column_dimensions["B"].width = 28
ws1.column_dimensions["C"].width = 24
ws1.column_dimensions["D"].width = 14
ws1.column_dimensions["E"].width = 36

# タイトル行
for ci, h in enumerate(["リソース", "パラメータ", "設定値", "要変更", "備考"], 1):
    style_header(ws1.cell(row=1, column=ci), h)

rows = [
    # (セクション名, None) or (リソース, パラメータ, 値, 要変更, 備考, dummy, fixed)
    ("■ リソースグループ", None),
    ("リソースグループ", "名前", "ito1202", "✓ 要変更", "Azure 上で管理する全リソースの親", True, False),
    ("リソースグループ", "リージョン", "japaneast（東日本）", "不要", "リージョンは東日本で統一", False, True),

    ("■ VNet", None),
    ("Virtual Network", "名前", "vnet-ito1202", "✓ 要変更", "resource_group_name から自動生成", False, False),
    ("Virtual Network", "アドレス空間", "10.0.0.0/16", "不要", "65,536 IP アドレスが使用可能", False, True),

    ("■ Subnet（4つ）", None),
    ("GatewaySubnet", "アドレス範囲", "10.0.255.0/27", "不要", "VPN Gateway 専用。名前・用途とも Azure 固定", False, True),
    ("subnet-pe", "アドレス範囲", "10.0.2.0/24", "不要", "Private Endpoint 置き場（インバウンド受け口）", False, True),
    ("subnet-integration", "アドレス範囲", "10.0.1.0/24", "不要", "App Service VNet Integration（アウトバウンド出口）", False, True),
    ("subnet-func-integration", "アドレス範囲", "10.0.4.0/24", "不要", "Functions VNet Integration（アウトバウンド出口）", False, True),

    ("■ NSG（Network Security Group）", None),
    ("NSG", "名前", "nsg-app", "不要", "subnet-pe に適用", False, True),
    ("NSG ルール", "オンプレ HTTPS 許可", "送信元: 203.0.113.10/32（ダミー）", "✓ 要変更", "実際のオンプレ グローバル IP に変更", True, False),
    ("NSG ルール", "その他インバウンド", "拒否（deny-all）", "不要", "ホワイトリスト以外は全拒否", False, True),

    ("■ VPN Gateway", None),
    ("VPN Gateway", "名前", "vpngw-main", "不要", "", False, True),
    ("VPN Gateway", "SKU", "VpnGw1", "不要", "RouteBased / 月額 ~$32", False, True),
    ("VPN Gateway", "Public IP", "terraform apply 後に確認", "—", "terraform output vpn_gateway_public_ip で取得", False, False),
    ("VPN Gateway", "オンプレ デバイス IP", "203.0.113.10（ダミー）", "✓ 要変更", "オンプレ VPN ルーターのグローバル IP", True, False),
    ("VPN Gateway", "オンプレ アドレス空間", "192.168.1.0/24（ダミー）", "✓ 要変更", "オンプレのプライベート IP レンジ", True, False),
    ("VPN Gateway", "共有キー（PSK）", "***** （要設定）", "✓ 要変更", "オンプレ VPN と Azure で同じ値を設定", True, False),
]

r = 2
ri = 0
for row in rows:
    if row[1] is None:
        write_section(ws1, r, row[0])
    else:
        res, param, val, change, note, dummy, fixed = row
        write_row(ws1, r, [res, param, val, change, note],
                  dummy=dummy, fixed=fixed, row_idx=ri)
        ri += 1
    r += 1

# ============================================================
# シート 2: アプリケーション
# ============================================================
ws2 = wb.create_sheet("アプリケーション")

ws2.row_dimensions[1].height = 30
ws2.column_dimensions["A"].width = 28
ws2.column_dimensions["B"].width = 28
ws2.column_dimensions["C"].width = 28
ws2.column_dimensions["D"].width = 14
ws2.column_dimensions["E"].width = 36

for ci, h in enumerate(["リソース", "パラメータ", "設定値", "要変更", "備考"], 1):
    style_header(ws2.cell(row=1, column=ci), h)

rows2 = [
    ("■ App Service Plan（FE・BE 共用）", None),
    ("App Service Plan", "名前", "asp-main", "不要", "FE と BE が同一 Plan を共用", False, True),
    ("App Service Plan", "SKU", "B1", "不要", "月額 ~$13。本番では P1v3 以上を検討", False, True),
    ("App Service Plan", "OS", "Linux", "不要", "", False, True),

    ("■ App Service — Frontend", None),
    ("App Service Frontend", "名前", "app-fe-yourname（ダミー）", "✓ 要変更", "Azure 全体でユニーク。URL になる", True, False),
    ("App Service Frontend", "Public Endpoint", "無効", "不要", "社外から存在が見えない", False, True),
    ("App Service Frontend", "Managed ID", "システム割り当て", "不要", "terraform apply 後に Principal ID を確認", False, True),
    ("App Service Frontend", "VNet Integration", "subnet-integration", "不要", "アウトバウンド通信の出口", False, True),
    ("App Service Frontend", "Private Endpoint", "subnet-pe 内に配置", "不要", "インバウンドの受け口", False, True),

    ("■ App Service — Backend", None),
    ("App Service Backend", "名前", "app-be-yourname（ダミー）", "✓ 要変更", "Azure 全体でユニーク", True, False),
    ("App Service Backend", "Public Endpoint", "無効", "不要", "", False, True),
    ("App Service Backend", "Managed ID", "システム割り当て", "不要", "", False, True),
    ("App Service Backend", "VNet Integration", "subnet-integration", "不要", "", False, True),
    ("App Service Backend", "Private Endpoint", "subnet-pe 内に配置", "不要", "", False, True),

    ("■ Azure Functions（RAG ツール）", None),
    ("Azure Functions", "名前", "func-rag-yourname（ダミー）", "✓ 要変更", "Azure 全体でユニーク", True, False),
    ("Azure Functions", "プラン", "Flex Consumption（FC1）", "不要", "従量課金 + VNet Integration 対応", False, True),
    ("Azure Functions", "Public Endpoint", "無効", "不要", "", False, True),
    ("Azure Functions", "Managed ID", "システム割り当て", "不要", "", False, True),
    ("Azure Functions", "VNet Integration", "subnet-func-integration", "不要", "委任: Microsoft.App/environments", False, True),
    ("Azure Functions", "Private Endpoint", "subnet-pe 内に配置", "不要", "", False, True),
    ("Azure Functions", "専用 Storage（内部用）", "stfuncyourname（ダミー）", "✓ 要変更", "Functions 動作に必要。小文字英数字・24 文字以内", True, False),
]

r = 2
ri = 0
for row in rows2:
    if row[1] is None:
        write_section(ws2, r, row[0])
    else:
        res, param, val, change, note, dummy, fixed = row
        write_row(ws2, r, [res, param, val, change, note],
                  dummy=dummy, fixed=fixed, row_idx=ri)
        ri += 1
    r += 1

# ============================================================
# シート 3: データ・AI
# ============================================================
ws3 = wb.create_sheet("データ・AI")

ws3.row_dimensions[1].height = 30
ws3.column_dimensions["A"].width = 28
ws3.column_dimensions["B"].width = 28
ws3.column_dimensions["C"].width = 28
ws3.column_dimensions["D"].width = 14
ws3.column_dimensions["E"].width = 36

for ci, h in enumerate(["リソース", "パラメータ", "設定値", "要変更", "備考"], 1):
    style_header(ws3.cell(row=1, column=ci), h)

rows3 = [
    ("■ Storage Account（RAG ファイル置き場）", None),
    ("Storage Account", "名前", "stragyourname（ダミー）", "✓ 要変更", "小文字英数字のみ・24 文字以内・Azure 全体でユニーク", True, False),
    ("Storage Account", "種別", "Standard LRS", "不要", "ローカル冗長。本番では GRS を検討", False, True),
    ("Storage Account", "Public Endpoint", "無効", "不要", "", False, True),
    ("Storage Account", "Private Endpoint", "subnet-pe 内（blob）", "不要", "DNS Zone: privatelink.blob.core.windows.net", False, True),
    ("Storage Account", "コンテナ名", "rag-documents（ダミー）", "✓ 要変更", "RAG 用 PDF などを置くコンテナ名", True, False),

    ("■ Azure AI Search", None),
    ("Azure AI Search", "名前", "srch-rag-yourname（ダミー）", "✓ 要変更", "Azure 全体でユニーク", True, False),
    ("Azure AI Search", "SKU", "basic", "不要", "月額 ~$73。ベクトル検索に対応", False, True),
    ("Azure AI Search", "Public Endpoint", "無効", "不要", "", False, True),
    ("Azure AI Search", "Managed ID", "システム割り当て", "不要", "Storage への読み取り権限付与に使用", False, True),
    ("Azure AI Search", "Private Endpoint", "subnet-pe 内", "不要", "DNS Zone: privatelink.search.windows.net", False, True),
    ("Azure AI Search", "インデックス名", "rag-index（ダミー）", "✓ 要変更", "ベクトル検索のインデックス名", True, False),
    ("Azure AI Search", "Storage 接続", "Microsoft backbone 経由", "不要", "同一リージョンのため Shared Private Link 不要", False, True),

    ("■ Azure AI Foundry", None),
    ("Foundry Hub", "名前", "foundry-hub-yourname（ダミー）", "✓ 要変更", "Hub と Project それぞれに PE が必要", True, False),
    ("Foundry Hub", "Private Endpoint", "subnet-pe 内", "不要", "DNS Zone: privatelink.services.ai.azure.com", False, True),
    ("Foundry Project", "名前", "foundry-proj-yourname（ダミー）", "✓ 要変更", "", True, False),
    ("Foundry Project", "Private Endpoint", "subnet-pe 内", "不要", "", False, True),
    ("LLM", "モデル", "GPT-5.2", "不要", "", False, True),
    ("Embedding", "モデル", "Embedding 003", "不要", "", False, True),
    ("Foundry Managed Network", "Managed PE", "Functions へ設定", "✓ 要設定", "Foundry → Functions の通信に必要。Portal から設定", True, False),
]

r = 2
ri = 0
for row in rows3:
    if row[1] is None:
        write_section(ws3, r, row[0])
    else:
        res, param, val, change, note, dummy, fixed = row
        write_row(ws3, r, [res, param, val, change, note],
                  dummy=dummy, fixed=fixed, row_idx=ri)
        ri += 1
    r += 1

# ============================================================
# シート 4: IAM・監視
# ============================================================
ws4 = wb.create_sheet("IAM・監視")

ws4.row_dimensions[1].height = 30
ws4.column_dimensions["A"].width = 28
ws4.column_dimensions["B"].width = 32
ws4.column_dimensions["C"].width = 28
ws4.column_dimensions["D"].width = 14
ws4.column_dimensions["E"].width = 36

for ci, h in enumerate(["対象", "ロール / 設定", "スコープ / 値", "要変更", "備考"], 1):
    style_header(ws4.cell(row=1, column=ci), h)

rows4 = [
    ("■ Managed ID ロール付与", None),
    ("Backend Managed ID", "Azure AI Developer", "Foundry リソース", "✓ 要設定", "terraform output backend_principal_id で ID 確認後に付与", True, False),
    ("Functions Managed ID", "Search Index Data Reader", "AI Search リソース", "✓ 要設定", "terraform output functions_principal_id で ID 確認後に付与", True, False),
    ("Functions Managed ID", "Storage Blob Data Reader", "Storage Account", "✓ 要設定", "", True, False),
    ("AI Search Managed ID", "Storage Blob Data Reader", "Storage Account", "✓ 要設定", "terraform output ai_search_principal_id で ID 確認後に付与", True, False),

    ("■ EntraID（FE ↔ BE 認証）", None),
    ("App Registration: frontend-app", "Redirect URI", "https://app-fe-yourname.azurewebsites.net（ダミー）", "✓ 要変更", "FE のデプロイ後に確定", True, False),
    ("App Registration: frontend-app", "Client ID", "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx（ダミー）", "✓ 要変更", "App Registration 作成後に取得", True, False),
    ("App Registration: backend-app", "Client ID", "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx（ダミー）", "✓ 要変更", "", True, False),
    ("EntraID", "Tenant ID", "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx（ダミー）", "✓ 要変更", "az account show で確認", True, False),

    ("■ EntraID ユーザー権限", None),
    ("開発者アカウント", "Contributor", "リソースグループ: ito1202", "✓ 要設定", "構築・変更作業用", True, False),
    ("運用担当者アカウント", "Reader", "リソースグループ: ito1202", "✓ 要設定", "参照・監視のみ", True, False),
    ("運用担当者アカウント", "Search Index Data Contributor", "AI Search リソース", "✓ 要設定", "インデックス管理用", True, False),

    ("■ Azure Monitor / Log Analytics", None),
    ("Log Analytics Workspace", "名前", "law-ito1202", "不要", "resource_group_name から自動生成", False, True),
    ("Log Analytics Workspace", "保持期間", "30 日", "不要", "コスト節約のため最小に設定", False, True),
    ("診断設定: Frontend", "ログ", "AppServiceHTTPLogs / AppServiceAppLogs", "不要", "", False, True),
    ("診断設定: Backend", "ログ", "AppServiceHTTPLogs / AppServiceAppLogs", "不要", "", False, True),
    ("診断設定: Functions", "ログ", "FunctionAppLogs", "不要", "", False, True),
    ("診断設定: AI Search", "ログ", "OperationLogs", "不要", "", False, True),
]

r = 2
ri = 0
for row in rows4:
    if row[1] is None:
        write_section(ws4, r, row[0])
    else:
        target, role, scope, change, note, dummy, fixed = row
        write_row(ws4, r, [target, role, scope, change, note],
                  dummy=dummy, fixed=fixed, row_idx=ri)
        ri += 1
    r += 1

# ============================================================
# 凡例シート
# ============================================================
ws0 = wb.create_sheet("凡例", 0)
ws0.column_dimensions["A"].width = 20
ws0.column_dimensions["B"].width = 50

style_header(ws0.cell(row=1, column=1), "色", size=10)
style_header(ws0.cell(row=1, column=2), "意味", size=10)

legends = [
    (DUMMY_BG,  "黄色：ダミー値。あとで実際の値に要変更"),
    (FIXED_BG,  "緑色：固定値。変更不要"),
    (ALT_ROW_BG,"青白：通常行（偶数行）"),
    (WHITE,     "白：通常行（奇数行）"),
    (SECTION_BG,"水色：セクション区切り"),
]
for ri, (bg, txt) in enumerate(legends, start=2):
    ws0.cell(row=ri, column=1).fill = PatternFill("solid", fgColor=bg)
    ws0.cell(row=ri, column=1).value = "　"
    thin = Side(style="thin", color=BORDER_COLOR)
    ws0.cell(row=ri, column=1).border = Border(
        top=thin, left=thin, right=thin, bottom=thin)
    style_cell(ws0.cell(row=ri, column=2), txt, row_idx=ri)

# ============================================================
# 保存
# ============================================================
out = "/home/user/tmp/azure-test-environment/docs/parameter-sheet.xlsx"
wb.save(out)
print(f"Saved: {out}")
