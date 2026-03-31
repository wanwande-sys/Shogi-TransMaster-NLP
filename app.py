# app.py
import streamlit as st
import os
import json
import shutil
import webvtt
import pandas as pd
import tkinter as tk
from tkinter import filedialog

# 导入拆分后的模块
from core.config import DOMAIN_PROFILES, SUBTITLE_PRESETS, GLOSSARY_FILE
from core.utils import extract_urls
from core.core_engine import download_video, burn_subtitles_nvenc_with_progress, run_full_pipeline

st.set_page_config(page_title="视听自动化工作台", page_icon="🎬", layout="wide")

if 'processed_done' not in st.session_state: st.session_state.processed_done = False
if 'selected_path' not in st.session_state: st.session_state.selected_path = ""

# --- 侧边栏配置 ---
with st.sidebar:
    st.header("⚙️ 领域与底层配置")
    selected_domain = st.selectbox("当前视频类型 (切换预设)", list(DOMAIN_PROFILES.keys()), index=0)
    active_profile = DOMAIN_PROFILES[selected_domain]

    st.divider()
    if st.button("🗑️ 清空系统状态并重置", type="secondary", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    st.divider()
    is_test_mode = st.toggle("🧪 急速测试模式 (仅处理前20句)")

    if "将棋" in selected_domain:
        with st.expander("📖 局部术语注入面板 (将棋)"):
            if os.path.exists(GLOSSARY_FILE):
                with open(GLOSSARY_FILE, 'r', encoding='utf-8-sig') as f:
                    current_glossary = json.load(f)
            else:
                current_glossary = {"居飛車": "居飞车"}
            edited_df_gloss = st.data_editor([{"日文": k, "中文": v} for k, v in current_glossary.items()],
                                             num_rows="dynamic")
            full_glossary = {r["日文"]: r["中文"] for r in edited_df_gloss if r["日文"] and r["中文"]}
            if st.button("保存本地词库"):
                with open(GLOSSARY_FILE, 'w', encoding='utf-8') as f: json.dump(full_glossary, f, ensure_ascii=False)
    else:
        full_glossary = {}

st.title("🎬 视听自动化工作台 V24.1 (架构重构版)")

tab_download, tab_translate, tab_pipeline = st.tabs(
    ["📥 1. 独立下载终端", "🎛️ 2. 独立翻译压制", "🚀 3. 端到端流水线 (全自动)"])


def render_input_hub(key_prefix):
    st.markdown("##### 📥 数据源输入 (支持单链接 / 多行批量 / 专栏 / 播放列表)")
    with st.container(border=True):
        txt_input = st.text_area("在下方粘贴链接：", height=100, key=f"{key_prefix}_text",
                                 placeholder="https://youtube.com/...")
        st.markdown("<div style='text-align: center; color: gray;'>--- 或者 ---</div>", unsafe_allow_html=True)
        file_input = st.file_uploader("将包含链接的 .txt 文件拖拽到此处：", type=['txt'], key=f"{key_prefix}_file")
    return txt_input, file_input


# ====== TAB 1: 下载 ======
with tab_download:
    dl_txt, dl_file = render_input_hub("tab1")
    c1, c2 = st.columns(2)
    with c1:
        dl_mode = st.selectbox("下载配置", ["视频 + 日文字幕 (标准工作流)", "纯音频提取 (MP3 最高音质)"])
    if st.button("⬇️ 开始下载", use_container_width=True):
        urls = extract_urls(dl_txt, dl_file)
        if urls:
            paths = download_video(urls, dl_mode, "1080P", st.progress(0.0), st.empty())
            if paths and "视频" in dl_mode: st.session_state.selected_path = paths[0]
        else:
            st.warning("请输入有效链接或上传 txt 文件！")

# ====== TAB 2: 独立压制 ======
with tab_translate:
    st.markdown("### 🔧 压制控制台")
    col_p1, col_p2 = st.columns([5, 1])
    with col_p1:
        local_path = st.text_input("📍 视频绝对路径", value=st.session_state.selected_path)
    with col_p2:
        st.write("");
        st.write("")
        if st.button("📁 浏览视频", use_container_width=True):
            root = tk.Tk();
            root.attributes('-topmost', True);
            root.withdraw()
            p = filedialog.askopenfilename(filetypes=[("视频", "*.mp4 *.mkv *.webm")])
            root.destroy()
            if p: st.session_state.selected_path = p.replace("/", "\\"); st.rerun()

    st.divider()
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        tr_mode = st.selectbox("工作模式", ["自动识别 (听写翻译全流程)", "自由挂载/重压制 (读取/编辑外部字幕)"])
    with c2:
        tr_out = st.selectbox("最终格式", ["仅中文字幕", "双语对照"])
    with c3:
        engine = st.selectbox("大模型引擎", ["DeepSeek Pro", "Gemini 1.5 Flash"])

    c_p1, c_p2 = st.columns([3, 1])
    with c_p1:
        selected_preset = st.selectbox("字幕排版与滤镜", list(SUBTITLE_PRESETS.keys()))
    with c_p2:
        local_font_size = st.number_input("基准字号 (建议18-24)", min_value=12, max_value=40, value=22)

    st.divider()
    edited_df = None

    if tr_mode == "自由挂载/重压制 (读取/编辑外部字幕)":
        st.info("💡 如果留空，系统将自动读取和视频同名的 `.vtt` 翻译稿。")
        uploaded_sub = st.file_uploader("📤 (可选) 上传外部 .vtt 或 .srt 格式字幕文件", type=['vtt', 'srt'])

        physical_vtt_path, tmp_vtt_to_delete = None, None
        if uploaded_sub:
            import tempfile

            with tempfile.NamedTemporaryFile(delete=False, suffix=".vtt") as tmp:
                tmp.write(uploaded_sub.getvalue())
                physical_vtt_path = tmp_vtt_to_delete = tmp.name
        elif local_path and os.path.exists(local_path):
            auto_vtt_path = os.path.splitext(local_path)[0] + ".zh.vtt"
            if os.path.exists(auto_vtt_path):
                physical_vtt_path = auto_vtt_path
            else:
                backup_vtt_path = os.path.join(os.path.dirname(local_path), "生肉备份_Backup",
                                               os.path.basename(auto_vtt_path))
                if os.path.exists(backup_vtt_path): physical_vtt_path = backup_vtt_path

        if physical_vtt_path:
            st.caption("📝 **可视化精修台**")
            try:
                vtt = webvtt.read(physical_vtt_path)
                df = pd.DataFrame([{"时间轴": f"{c.start} --> {c.end}", "字幕内容": c.text} for c in vtt])
                edited_df = st.data_editor(df, column_config={"时间轴": st.column_config.TextColumn(disabled=True)},
                                           use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"解析失败: {e}")
            finally:
                if tmp_vtt_to_delete and os.path.exists(tmp_vtt_to_delete): os.remove(tmp_vtt_to_delete)

        if st.button("🚀 确认烧录", type="primary", use_container_width=True):
            if local_path and os.path.exists(local_path) and edited_df is not None:
                new_vtt_content = "WEBVTT\n\n"
                for index, row in edited_df.iterrows():
                    if str(row['时间轴']).strip(): new_vtt_content += f"{row['时间轴']}\n{row['字幕内容']}\n\n"

                local_vtt_target = os.path.splitext(local_path)[0] + ".zh.vtt"
                try:
                    with open(local_vtt_target, 'w', encoding='utf-8') as f:
                        f.write(new_vtt_content)
                except:
                    try:
                        with open(os.path.join(os.path.dirname(local_path), os.path.basename(local_vtt_target)), 'w',
                                  encoding='utf-8') as f:
                            f.write(new_vtt_content)
                    except:
                        pass

                out_vid = burn_subtitles_nvenc_with_progress(local_path, new_vtt_content, tr_out, selected_preset,
                                                             local_font_size, st.progress(0.0), st.empty())
                if out_vid:
                    st.success(f"重新压制完成！成品视频：{os.path.basename(out_vid)}")
                    st.balloons()
            else:
                st.error("请确认已指定视频路径，并且字幕数据加载成功。")
    else:
        if st.button("🚀 启动自动化处理流程", type="primary", use_container_width=True):
            if local_path and os.path.exists(local_path):
                run_full_pipeline(local_path, engine, tr_out, is_test_mode, active_profile, full_glossary,
                                  selected_preset, local_font_size)

# ====== TAB 3: 流水线 ======
with tab_pipeline:
    st.markdown("### ⚙️ 自动化流水线")
    pipe_txt, pipe_file = render_input_hub("tab3")
    c_a, c_b, c_c, c_d = st.columns(4)
    with c_a:
        pipe_out = st.selectbox("最终格式 (流水线)", ["仅中文字幕", "双语对照"])
    with c_b:
        pipe_eng = st.selectbox("AI 引擎 (流水线)", ["DeepSeek Pro", "Gemini 1.5 Flash"])
    with c_c:
        pipe_preset = st.selectbox("字幕排版 (流水线)", list(SUBTITLE_PRESETS.keys()))
    with c_d:
        pipe_font_size = st.number_input("基准字号 (流水线)", min_value=12, max_value=40, value=22)

    if st.button("🔥 启动批量自动化流水线", type="primary", use_container_width=True):
        urls = extract_urls(pipe_txt, pipe_file)
        if urls:
            prog_dl, stat_dl = st.progress(0.0), st.empty()
            downloaded_paths = download_video(urls, "视频 + 日文字幕 (标准工作流)", "1080P", prog_dl, stat_dl)
            if downloaded_paths:
                for idx, path in enumerate(downloaded_paths):
                    st.write(f"**正在处理 ({idx + 1}/{len(downloaded_paths)}):** `{os.path.basename(path)}`")
                    run_full_pipeline(path, pipe_eng, pipe_out, is_test_mode, active_profile, full_glossary,
                                      pipe_preset, pipe_font_size)
                st.success("✅ 所有队列任务均已执行完毕。")
        else:
            st.warning("请输入链接或上传 txt 文件。")