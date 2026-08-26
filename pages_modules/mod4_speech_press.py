"""
模組四：新聞稿與致詞稿智慧生成機
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date

from database import get_db, SpeechTemplate
from ai_helper import generate_speech, generate_press_release, get_gemini_api_key
from export_helper import generate_speech_docx

def render_speech_press_module():
    st.markdown(
        """
        <div class="main-header">
            <h1>✍️ 模組四：新聞稿與致詞稿智慧生成機</h1>
            <p>內建六大民力活動情境、三種長官講稿風格切換、公務媒體新聞稿生成、滿意稿件一鍵回存範本庫</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_speech, tab_press, tab_templates = st.tabs([
        "🎙️ 長官致詞講稿智慧生成 (溫馨/激勵/正式)",
        "📰 媒體發布公務新聞稿智慧生成",
        "📚 稿件典範與範本庫管理"
    ])

    db = get_db()
    try:
        api_key = get_gemini_api_key()
        if not api_key:
            st.info("💡 提示：您可至【系統設定】輸入 Gemini API Key 啟用最新 AI 文本生成；未輸入時系統將以智慧範本生成引擎運作。")

        # 預設活動情境選項
        scenario_options = [
            "裝備車輛捐贈 (善心企業/團體救災裝備、車輛捐贈典禮)",
            "常年訓練 (義勇消防人員常年訓練/專業技能開訓與結訓)",
            "防救災演練 (大規模跨機關防救災演習、兵棋推演)",
            "表揚餐會 (績優義消楷模表揚大會、顧問團聯誼餐會)",
            "慰問關懷 (因公傷病同仁/義消遺族慰問關懷訪視)",
            "組織人事 (義消新進人員授服典禮、顧問團聘書頒發)",
            "其他自訂業務活動"
        ]

        # ==========================================
        # TAB 1: 長官致詞講稿智慧生成
        # ==========================================
        with tab_speech:
            st.subheader("🎤 長官致詞講稿生成器")
            
            with st.form("speech_gen_form"):
                sc_col1, sc_col2 = st.columns(2)
                with sc_col1:
                    sel_scenario = st.selectbox("活動情境範本 *", scenario_options)
                    in_event_title = st.text_input("活動完整主題 *", placeholder="例：113年宏達科技捐贈消防特搜救災警備車典禮")
                    in_vip_name = st.text_input("致詞長官稱謂", value="消防局長", placeholder="例：消防局長、副市長、民力科長")
                
                with sc_col2:
                    in_tone = st.radio(
                        "指定長官演說語調風格 *",
                        ["溫馨感人 (真摯溫暖、感謝付出)", "激勵振奮 (熱情洋溢、鼓舞士氣)", "莊重正式 (沉穩典雅、展現成果)"],
                        horizontal=False
                    )
                    in_extra_vips = st.text_input("出席長官與貴賓 (用於開場致謝)", placeholder="例：市長、市議員、義消總隊長、捐贈企業董事長")

                in_key_facts = st.text_area(
                    "亮點數據與核心事蹟 (例如：捐贈金額、參訓人數、重大救災功績) *",
                    placeholder="例：宏達科技捐贈總值500萬元之救災警備車1輛及熱顯像儀5組；本市義消今年協勤出勤達3,200人次，救災表現深獲市民肯定。"
                )
                
                in_extra_notes = st.text_input("其他補充要求 (例如：特別致謝特定對象、加強強調火場安全宣導)", placeholder="例：特別感謝捐贈人陳董事長熱心公益、提醒同仁注意出勤同進同出安全。")

                btn_gen_speech = st.form_submit_button("✨ 立即生成長官致詞講稿", type="primary", use_container_width=True)

                if btn_gen_speech:
                    if not in_event_title:
                        st.error("請填寫活動完整主題！")
                    else:
                        tone_pure = in_tone.split(" (")[0]
                        category_pure = sel_scenario.split(" (")[0]
                        with st.spinner("🤖 Gemini 正在為長官量身撰寫具備層次感與感染力的致詞講稿..."):
                            speech_result = generate_speech(
                                event_title=in_event_title,
                                vip_name=in_vip_name,
                                key_facts=in_key_facts,
                                tone=tone_pure,
                                template_category=category_pure,
                                extra_notes=f"出席貴賓：{in_extra_vips}。{in_extra_notes}"
                            )
                            st.session_state["generated_speech"] = {
                                "title": f"【致詞稿】{in_event_title}",
                                "category": category_pure,
                                "tone": tone_pure,
                                "content": speech_result
                            }

            # 顯示生成結果與操作區
            if "generated_speech" in st.session_state and st.session_state["generated_speech"]:
                sp_data = st.session_state["generated_speech"]
                st.markdown("---")
                st.subheader("📝 生成講稿預覽與編輯")

                # 可編輯文字區塊
                edited_speech = st.text_area(
                    "可直接在此微調修訂講稿內容：",
                    value=sp_data["content"],
                    height=380,
                    key="edit_speech_box"
                )

                # 下載與回存按鈕
                s_c1, s_c2, s_c3 = st.columns(3)
                with s_c1:
                    speech_docx_buf = generate_speech_docx(
                        title=sp_data["title"],
                        content_type="長官致詞稿",
                        tone=sp_data["tone"],
                        body_text=edited_speech
                    )
                    st.download_button(
                        label="📥 下載講稿 Word (.docx) 檔",
                        data=speech_docx_buf,
                        file_name=f"{sp_data['title']}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="primary",
                        use_container_width=True
                    )
                with s_c2:
                    st.download_button(
                        label="📥 下載講稿 Markdown (.md) 檔",
                        data=edited_speech,
                        file_name=f"{sp_data['title']}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                with s_c3:
                    if st.button("💾 回存至科內範本庫供未來參考", use_container_width=True):
                        new_tmpl = SpeechTemplate(
                            category=sp_data["category"],
                            title=sp_data["title"],
                            content_type="致詞稿",
                            tone=sp_data["tone"],
                            template_structure="AI 智慧生成長官致詞講稿",
                            history_examples=edited_speech
                        )
                        db.add(new_tmpl)
                        db.commit()
                        st.success("🎉 講稿已成功回存至科內範本庫！")

        # ==========================================
        # TAB 2: 媒體發布公務新聞稿智慧生成
        # ==========================================
        with tab_press:
            st.subheader("📰 媒體發布新聞稿生成器")
            
            with st.form("press_gen_form"):
                p_c1, p_c2 = st.columns(2)
                with p_c1:
                    p_event_title = st.text_input("新聞發布活動名稱 *", placeholder="例：民間企業善心捐贈消防特搜裝備 守護市民生命財產")
                    p_chief_name = st.text_input("發言長官職銜姓名", value="消防局長", placeholder="例：消防局長")
                with p_c2:
                    p_scenario = st.selectbox("活動性質", scenario_options, key="press_scen")
                    p_quotes = st.text_input("長官發言/引言重點 (Quote)", placeholder="例：強調政府資源有限但民間力量無窮，感謝善心人士力挺第一線救災人員。")

                p_key_facts = st.text_area(
                    "新聞關鍵人事時地物與數據 *",
                    placeholder="例：今日上午10時於信義分隊舉行捐贈儀式；善心企業捐贈總值達350萬元之救災救護器材，包含熱顯像儀5台、頂級防護頭盔20頂。"
                )
                p_highlights = st.text_area(
                    "活動現場亮點與市民安全效益",
                    placeholder="例：新裝備將全數配發至東區各大隊及特搜義消分隊，能大幅縮短火場搜救時間，全面保障打火弟兄及市民生命安全。"
                )

                btn_gen_press = st.form_submit_button("✨ 立即生成標準媒體新聞稿", type="primary", use_container_width=True)

                if btn_gen_press:
                    if not p_event_title or not p_key_facts:
                        st.error("請務必填寫活動名稱與新聞關鍵數據！")
                    else:
                        with st.spinner("🤖 Gemini 正在撰寫具備倒金字塔結構與新聞張力的媒體新聞稿..."):
                            press_result = generate_press_release(
                                event_title=p_event_title,
                                chief_name=p_chief_name,
                                key_facts=p_key_facts,
                                main_highlights=p_highlights,
                                quote_content=p_quotes
                            )
                            st.session_state["generated_press"] = {
                                "title": f"【新聞稿】{p_event_title}",
                                "category": p_scenario.split(" (")[0],
                                "content": press_result
                            }

            # 顯示新聞稿生成結果與操作區
            if "generated_press" in st.session_state and st.session_state["generated_press"]:
                pr_data = st.session_state["generated_press"]
                st.markdown("---")
                st.subheader("📰 生成新聞稿預覽與編輯")

                edited_press = st.text_area(
                    "可直接在此修訂新聞稿內文與聯絡人資訊：",
                    value=pr_data["content"],
                    height=380,
                    key="edit_press_box"
                )

                pr_c1, pr_c2, pr_c3 = st.columns(3)
                with pr_c1:
                    press_docx_buf = generate_speech_docx(
                        title=pr_data["title"],
                        content_type="媒體發布新聞稿",
                        tone="莊重正式",
                        body_text=edited_press
                    )
                    st.download_button(
                        label="📥 下載新聞稿 Word (.docx) 檔",
                        data=press_docx_buf,
                        file_name=f"{pr_data['title']}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="primary",
                        use_container_width=True
                    )
                with pr_c2:
                    st.download_button(
                        label="📥 下載新聞稿 Markdown (.md) 檔",
                        data=edited_press,
                        file_name=f"{pr_data['title']}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                with pr_c3:
                    if st.button("💾 回存至科內新聞範本庫", use_container_width=True):
                        new_tmpl_pr = SpeechTemplate(
                            category=pr_data["category"],
                            title=pr_data["title"],
                            content_type="新聞稿",
                            tone="莊重正式",
                            template_structure="AI 智慧生成媒體新聞發布稿",
                            history_examples=edited_press
                        )
                        db.add(new_tmpl_pr)
                        db.commit()
                        st.success("🎉 新聞稿已成功回存至科內範本庫！")

        # ==========================================
        # TAB 3: 稿件典範與範本庫管理
        # ==========================================
        with tab_templates:
            st.subheader("📚 科內致詞稿與新聞稿範本庫典藏")
            
            all_templates = db.query(SpeechTemplate).order_by(SpeechTemplate.created_at.desc()).all()
            
            filter_cat = st.selectbox("依情境分類篩選", ["全部情境"] + sorted(list(set([t.category for t in all_templates]))))
            filter_type = st.radio("依稿件類型篩選", ["全部", "致詞稿", "新聞稿"], horizontal=True)

            filtered_tmpls = all_templates
            if filter_cat != "全部情境":
                filtered_tmpls = [t for t in filtered_tmpls if t.category == filter_cat]
            if filter_type != "全部":
                filtered_tmpls = [t for t in filtered_tmpls if t.content_type == filter_type]

            st.write(f"共典藏 **{len(filtered_tmpls)}** 篇公務稿件範本：")

            for tmpl in filtered_tmpls:
                with st.expander(f"📄 [{tmpl.content_type}] 【{tmpl.category}】 {tmpl.title} ({tmpl.tone})"):
                    st.markdown(f"**類別：** `{tmpl.content_type}` ｜ **情境：** `{tmpl.category}` ｜ **風格：** `{tmpl.tone}`")
                    st.markdown(f"**架構重點：** {tmpl.template_structure or '無'}")
                    st.markdown("---")
                    st.text_area("範本內文", value=tmpl.history_examples or "", height=200, key=f"t_view_{tmpl.id}")

                    # 重新下載 docx
                    t_docx = generate_speech_docx(
                        title=tmpl.title,
                        content_type=tmpl.content_type,
                        tone=tmpl.tone,
                        body_text=tmpl.history_examples or ""
                    )
                    st.download_button(
                        label="📥 下載此範本 Word (.docx)",
                        data=t_docx,
                        file_name=f"{tmpl.title}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"dl_t_{tmpl.id}"
                    )

    finally:
        db.close()
