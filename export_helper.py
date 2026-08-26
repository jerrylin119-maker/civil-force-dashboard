"""
民力科業務執行與督勤彙整看板系統 - 檔案匯出工具 (Word .docx, Markdown, CSV, iCalendar .ics)
"""
import io
import csv
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, color_hex: str):
    """設定 Word 表格單元格背景色"""
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def generate_inspection_docx(
    unit_name: str,
    inspect_date: str,
    inspector: str,
    focus_items: List[Dict[str, Any]],
    strengths: str,
    deficiencies: str,
    merit_status: str = "口頭嘉勉",
    demerit_status: str = "無重大缺失",
    score: int = 0,
    report_text: str = ""
) -> io.BytesIO:
    """
    生成標準公務格式之「臺東縣消防局民力科 督勤與業務查核紀錄表」Word (.docx) 文件
    """
    doc = docx.Document()
    
    # 版面設定 (邊界)
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # 主標題
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = title_p.add_run("臺東縣消防局民力科 督勤與業務查核紀錄表")
    run_title.font.name = "微軟正黑體"
    run_title.font.size = Pt(18)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(30, 58, 138) # Deep Blue

    # 副標題/日期
    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = sub_p.add_run(f"督勤日期：{inspect_date} ｜ 產生時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    run_sub.font.name = "微軟正黑體"
    run_sub.font.size = Pt(10)
    run_sub.font.color.rgb = RGBColor(100, 116, 139)

    doc.add_paragraph() # 空行

    # 基本資訊表格 (無評分，改為優良處置與缺失處置結論)
    table = doc.add_table(rows=2, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True

    cells = table.rows[0].cells
    cells[0].text = "受督導單位"
    cells[1].text = unit_name
    cells[2].text = "督勤同仁"
    cells[3].text = inspector

    cells2 = table.rows[1].cells
    cells2[0].text = "查核日期"
    cells2[1].text = inspect_date
    cells2[2].text = "綜合督勤處置"
    cells2[3].text = f"🌟 {merit_status} ｜ ⚠️ {demerit_status}"

    for r_idx, row in enumerate(table.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.paragraphs[0].paragraph_format.space_before = Pt(4)
            cell.paragraphs[0].paragraph_format.space_after = Pt(4)
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.name = "微軟正黑體"
                    r.font.size = Pt(10.5)
            if c_idx % 2 == 0:
                set_cell_background(cell, "E2E8F0") # Light Gray header
                for r in cell.paragraphs[0].runs:
                    r.font.bold = True

    doc.add_paragraph() # 空行

    # 查核重點項目清單表格
    h2 = doc.add_paragraph()
    r_h2 = h2.add_run("一、 督導重點事項查核與宣導紀要")
    r_h2.font.name = "微軟正黑體"
    r_h2.font.size = Pt(13)
    r_h2.font.bold = True
    r_h2.font.color.rgb = RGBColor(15, 23, 42)

    item_table = doc.add_table(rows=1, cols=4)
    item_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = item_table.rows[0].cells
    hdr_cells[0].text = "項次 / 分類"
    hdr_cells[1].text = "重點查核項目"
    hdr_cells[2].text = "查核評核結果"
    hdr_cells[3].text = "備註與現場查核狀況說明"

    for c in hdr_cells:
        set_cell_background(c, "1E3A8A")
        for p in c.paragraphs:
            for r in p.runs:
                r.font.name = "微軟正黑體"
                r.font.size = Pt(10)
                r.font.bold = True
                r.font.color.rgb = RGBColor(255, 255, 255)

    for idx, item in enumerate(focus_items, 1):
        row_cells = item_table.add_row().cells
        cat = item.get("category", "重點督勤")
        name = item.get("name", item.get("item_name", "查核項目"))
        result = item.get("result", "符合規範")
        note = item.get("note", "現場運作良好")

        row_cells[0].text = f"{idx}. [{cat}]"
        row_cells[1].text = name
        row_cells[2].text = result
        row_cells[3].text = note

        for c_idx, cell in enumerate(row_cells):
            cell.paragraphs[0].paragraph_format.space_before = Pt(3)
            cell.paragraphs[0].paragraph_format.space_after = Pt(3)
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.name = "微軟正黑體"
                    r.font.size = Pt(9.5)
            if c_idx == 2:
                if "符合" in result or "良好" in result or "優" in result:
                    set_cell_background(cell, "DCFCE7") # Green tint
                elif "待改善" in result or "劣" in result or "缺失" in result:
                    set_cell_background(cell, "FEE2E2") # Red tint
                elif "宣導" in result:
                    set_cell_background(cell, "FEF3C7") # Yellow tint

    doc.add_paragraph()

    # 優點與具體事蹟 (優績 / 口頭嘉勉)
    h3 = doc.add_paragraph()
    r_h3 = h3.add_run(f"二、 現場優良事蹟與獎勵處置（處置判定：【{merit_status}】）")
    r_h3.font.name = "微軟正黑體"
    r_h3.font.size = Pt(13)
    r_h3.font.bold = True
    r_h3.font.color.rgb = RGBColor(15, 23, 42)

    p_str = doc.add_paragraph(strengths if strengths else "現場運作良好，無特別註記。")
    for r in p_str.runs:
        r.font.name = "微軟正黑體"
        r.font.size = Pt(10.5)

    doc.add_paragraph()

    # 缺失與建議改善事項 (劣蹟註記 / 請主管立即改善)
    h4 = doc.add_paragraph()
    r_h4 = h4.add_run(f"三、 缺失改善建議與處置要求（處置判定：【{demerit_status}】）")
    r_h4.font.name = "微軟正黑體"
    r_h4.font.size = Pt(13)
    r_h4.font.bold = True
    r_h4.font.color.rgb = RGBColor(15, 23, 42)

    p_def = doc.add_paragraph(deficiencies if deficiencies else "本次查核無重大缺失事項。")
    for r in p_def.runs:
        r.font.name = "微軟正黑體"
        r.font.size = Pt(10.5)

    doc.add_paragraph()

    # 簽章核閱欄
    p_sign = doc.add_paragraph()
    r_sign = p_sign.add_run(f"督勤同仁簽章：{inspector}　　　　受督單位主管簽章：___________　　　　科長核閱：___________")
    r_sign.font.name = "微軟正黑體"
    r_sign.font.size = Pt(11)
    r_sign.font.italic = True

    doc.add_paragraph()
    doc.add_paragraph()

    # 簽章欄位
    sign_table = doc.add_table(rows=2, cols=3)
    sign_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    s_hdr = sign_table.rows[0].cells
    s_hdr[0].text = "受督導單位主管"
    s_hdr[1].text = "督勤人員簽章"
    s_hdr[2].text = "民力科長核閱"

    for c in s_hdr:
        set_cell_background(c, "F1F5F9")
        for p in c.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.name = "微軟正黑體"
                r.font.size = Pt(10.5)
                r.font.bold = True

    s_body = sign_table.rows[1].cells
    s_body[0].text = "\n\n\n（職章/簽名）"
    s_body[1].text = f"\n\n\n{inspector}（簽章）"
    s_body[2].text = "\n\n\n（核章）"

    for c in s_body:
        for p in c.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.name = "微軟正黑體"
                r.font.size = Pt(9.5)
                r.font.color.rgb = RGBColor(100, 116, 139)

    # 儲存至 BytesIO
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

def generate_speech_docx(
    title: str,
    content_type: str,
    tone: str,
    body_text: str
) -> io.BytesIO:
    """生成講稿或新聞稿之 Word (.docx) 文件"""
    doc = docx.Document()
    
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # 標題
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run(title)
    r_title.font.name = "微軟正黑體"
    r_title.font.size = Pt(18)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(30, 58, 138)

    # 標籤列
    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_meta = p_meta.add_run(f"【{content_type}】 ｜ 風格設定：{tone} ｜ 產生日期：{datetime.now().strftime('%Y-%m-%d')}")
    r_meta.font.name = "微軟正黑體"
    r_meta.font.size = Pt(10)
    r_meta.font.color.rgb = RGBColor(100, 116, 139)

    doc.add_paragraph()

    # 正文段落
    paragraphs = body_text.split("\n")
    for para in paragraphs:
        if para.strip():
            p = doc.add_paragraph()
            p.paragraph_format.line_spacing = 1.25
            p.paragraph_format.space_after = Pt(6)
            
            # 若為標題格式
            if para.startswith("#") or para.startswith("【"):
                r = p.add_run(para.replace("#", "").strip())
                r.font.name = "微軟正黑體"
                r.font.size = Pt(13)
                r.font.bold = True
                r.font.color.rgb = RGBColor(15, 23, 42)
            else:
                r = p.add_run(para)
                r.font.name = "微軟正黑體"
                r.font.size = Pt(11)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

def generate_documents_csv(documents: List[Any]) -> str:
    """生成 UTF-8 BOM 格式之重要計畫及公文續辦清單 CSV (支援 Excel 開啟繁體中文不亂碼)"""
    output = io.StringIO()
    # 寫入 UTF-8 BOM
    output.write('\ufeff')
    writer = csv.writer(output)
    
    writer.writerow(["序號", "項目類型", "公文字號/計畫編號", "來文/主辦機關", "計畫名稱/公文主旨", "目前辦理狀況", "執行期限", "時限依據/里程碑", "主責同仁", "管制狀態", "急迫等級", "業務類別", "續辦/實施步驟清單", "進度備註"])
    
    for idx, doc in enumerate(documents, 1):
        writer.writerow([
            idx,
            getattr(doc, 'item_type', '公文續辦') or "公文續辦",
            doc.doc_number,
            getattr(doc, 'issuing_unit', '') or "",
            doc.subject,
            getattr(doc, 'current_progress', '') or doc.notes or "",
            doc.deadline.strftime("%Y-%m-%d") if doc.deadline else "",
            getattr(doc, 'deadline_desc', '') or "",
            doc.assignee,
            doc.status,
            doc.priority,
            doc.category,
            getattr(doc, 'followup_actions', '') or "",
            doc.notes or ""
        ])
        
    return output.getvalue()

def generate_calendar_ics(events: List[Any]) -> str:
    """生成標準 iCalendar (.ics) 行事曆格式檔案"""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Civil Force Division//Operations Dashboard//ZH",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]
    
    for ev in events:
        d_str = ev.event_date.strftime("%Y%m%d")
        t_str = ev.event_time.replace(":", "") if ev.event_time else "090000"
        if len(t_str) == 4:
            t_str += "00"
            
        dt_start = f"{d_str}T{t_str}"
        
        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:civil-force-{ev.id}@{d_str}")
        lines.append(f"DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}")
        lines.append(f"DTSTART:{dt_start}")
        lines.append(f"SUMMARY:{ev.title}")
        lines.append(f"LOCATION:{ev.location or '消防局'}")
        lines.append(f"DESCRIPTION:類別: {ev.event_type} | 出席同仁: {ev.attendees or '無'} | 備註: {ev.notes or '無'}")
        lines.append("STATUS:CONFIRMED")
        lines.append("END:VEVENT")
        
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)
