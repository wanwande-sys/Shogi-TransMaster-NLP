import streamlit as st
import os
import time
import json
import re
import webvtt
import httpx
import tempfile
import subprocess
import shutil
import tkinter as tk
from tkinter import filedialog
from openai import OpenAI
from google import genai
from dotenv import load_dotenv
import yt_dlp
import pandas as pd

st.set_page_config(page_title="视频处理工作台", page_icon="🎬", layout="wide")
load_dotenv()

os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"
BASE_DOWNLOAD_DIR = r"D:\YouTube下载器\已下载视频"
GLOSSARY_FILE = r"D:\YouTube下载器\将棋翻译\shogi_glossary.json"

if 'processed_done' not in st.session_state:
    st.session_state.processed_done = False
if 'selected_path' not in st.session_state:
    st.session_state.selected_path = ""

DOMAIN_PROFILES = {
    "♟️ 将棋专业解说 (带坐标纠正)": {
        "llm_sys": "你是一位拥有段位的专业将棋解说翻译。请严格遵守：\n1. 【坐标规范】：必须使用 [阿拉伯数字][汉字数字][棋子名]（如：7七金, 1四步）。严禁纯数字合并（如77金）。\n2. 【动作规范】：使用术语“打入”、“成（升变）”、“同（吃子）”。",
        "whisper_prompt": "将棋の解説動画です。藤井聡太、羽生善治、伊藤匠、居飛車、振り飛車、王将、飛車、角行、金将、銀将、桂馬、香車、歩兵、成銀、竜王、詰み、手筋、定跡、王手。7七金、2六歩。"
    },
    "🎮 游戏实况/VTuber (自然表述)": {
        "llm_sys": "你是一个精通二次元文化、游戏术语的同传翻译。请保持主播的语气，保留适当的语气助词，翻译要自然通俗。",
        "whisper_prompt": "ゲーム実況動画です。草、ヤバい、エグい、スパチャ、配信、耐久、初見、アーカイブ、ガチ、バフ、デバフ、エイム、ラグい、キル、チーター。"
    },
    "📰 综合日常/Vlog (常规翻译)": {
        "llm_sys": "你是一位专业的视频字幕翻译。请将视频翻译为自然流畅的中文，符合中文日常表达习惯，追求信达雅。",
        "whisper_prompt": "日常Vlog動画です。こんにちは、ありがとうございます、美味しい、旅行、おすすめ、カフェ、買い物、レビュー。"
    }
}

SUBTITLE_PRESETS = {
    "0️⃣ 原生纯净 (无背景/无厚重阴影)": {"margin_v": 40, "style": 1, "color": "&H00000000", "align": 2,
                                         "vertical": False, "margin_lr": 40},
    "1️⃣ 经典 B站风 (标准底部阴影)": {"margin_v": 40, "style": 1, "color": "&H99000000", "align": 2, "vertical": False,
                                      "margin_lr": 40},
    "2️⃣ 强力遮挡板 (带半透明黑底遮盖原文)": {"margin_v": 40, "style": 3, "color": "&H80000000", "align": 2,
                                              "vertical": False, "margin_lr": 40},
    "3️⃣ 高位防挡区 (强制抬高避开底部UI)": {"margin_v": 100, "style": 1, "color": "&H99000000", "align": 2,
                                            "vertical": False, "margin_lr": 40},
    "4️⃣ 真·竖排靠左 (垂直排版/自动分栏)": {"margin_v": 40, "style": 1, "color": "&H99000000", "align": 4,
                                            "vertical": True, "margin_lr": 40},
    "5️⃣ 真·竖排靠右 (垂直排版/自动分栏)": {"margin_v": 40, "style": 1, "color": "&H99000000", "align": 6,
                                            "vertical": True, "margin_lr": 40}
}

@st.cache_resource
def init_translation_clients():
    sf_client = OpenAI(api_key=os.getenv("SF_API_KEY"), base_url="https://api.siliconflow.cn/v1",
                       http_client=httpx.Client(proxy=None, trust_env=False))
    gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return sf_client, gemini_client

@st.cache_resource
def init_whisper_model():
    from faster_whisper import WhisperModel
    return WhisperModel("large-v3", device="cuda", compute_type="float16")

sf_client, gemini_client = init_translation_clients()

def format_time(seconds):
    return f"{int(seconds // 3600):02d}:{int((seconds % 3600) // 60):02d}:{seconds % 60:06.3f}"

def extract_urls(text_input, uploaded_file):
    urls = [line.strip() for line in text_input.split('\n') if line.strip()]
    if uploaded_file is not None:
        file_content = uploaded_file.getvalue().decode("utf-8")
        urls.extend([line.strip() for line in file_content.split('\n') if line.strip()])
    return list(dict.fromkeys(urls))

def download_video(urls, mode, quality, progress_ui, status_ui):
    outtmpl = os.path.join(BASE_DOWNLOAD_DIR, '%(uploader)s', '%(title)s', '%(title)s.%(ext)s')
    ydl_opts = {
        'proxy': 'http://127.0.0.1:7890', 'outtmpl': outtmpl,
        'sponsorblock_remove': ['sponsor', 'selfpromo', 'interaction'],
        'writethumbnail': True, 'quiet': True, 'no_warnings': True,
        'ignoreerrors': True,
        'postprocessors': [{'key': 'FFmpegMetadata', 'add_chapters': True, 'add_metadata': True},
                           {'key': 'EmbedThumbnail'}]
    }

    if mode == '纯音频提取 (MP3 最高音质)':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'].append(
            {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '0'})
    else:
        ydl_opts['format'] = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best'
        ydl_opts['merge_output_format'] = 'mp4'
        if "标准工作流" in mode:
            ydl_opts['writesubtitles'] = True
            ydl_opts['writeautomaticsub'] = True
            ydl_opts['subtitleslangs'] = ['ja']

    final_paths = []

    def my_hook(d):
        info = d.get('info_dict', {})
        p_index = info.get('playlist_index')
        p_count = info.get('playlist_count')
        title = info.get('title', '未知视频')

        prefix = f"[专栏进度: {p_index} / {p_count}]" if p_index and p_count else "[单集下载]"

        if d['status'] == 'downloading':
            try:
                pct_str = re.sub(r'\x1b\[[0-9;]*m', '', d.get('_percent_str', '0%').replace('%', '').strip())
                progress_ui.progress(float(pct_str) / 100.0)
            except:
                pass

            speed = re.sub(r'\x1b\[[0-9;]*m', '', d.get('_speed_str', 'N/A'))
            eta = re.sub(r'\x1b\[[0-9;]*m', '', d.get('_eta_str', 'N/A'))

            status_ui.markdown(
                f"### 下载中...\n**{prefix}** `{title}`\n**速度**: `{speed}` | **剩余时间**: `{eta}`")

        elif d['status'] == 'finished':
            progress_ui.progress(1.0)
            status_ui.success(f"✅ **{prefix}** `{title}` 下载完成")

    ydl_opts['progress_hooks'] = [my_hook]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for url in urls:
                status_ui.info(f"解析链接: {url}")
                info = ydl.extract_info(url, download=True)
                if not info: continue

                if 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            fp = ydl.prepare_filename(entry)
                            if 'merge_output_format' in ydl_opts and not fp.endswith('.mp4'):
                                fp = fp.rsplit('.', 1)[0] + '.mp4'
                            final_paths.append(fp)
                else:
                    fp = ydl.prepare_filename(info)
                    if 'merge_output_format' in ydl_opts and not fp.endswith('.mp4'):
                        fp = fp.rsplit('.', 1)[0] + '.mp4'
                    final_paths.append(fp)
        return final_paths
    except Exception as e:
        st.error(f"下载异常: {e}")
        return []

def enforce_line_breaks(vtt_str, is_vertical):
    if not is_vertical:
        return vtt_str
    lines = vtt_str.split('\n')
    new_lines = []
    for line in lines:
        if '-->' in line or line.startswith('WEBVTT') or not line.strip():
            new_lines.append(line)
        else:
            limit = 16
            wrapped = '\n'.join([line[i:i + limit] for i in range(0, len(line), limit)])
            new_lines.append(wrapped)
    return '\n'.join(new_lines)

def burn_subtitles_nvenc(video_path, vtt_content, mode, preset_key, base_font_size):
    cfg = SUBTITLE_PRESETS[preset_key]
    is_vertical = cfg.get("vertical", False)
    protected_vtt_content = enforce_line_breaks(vtt_content, is_vertical)

    output_video = os.path.splitext(video_path)[0] + "_已翻译.mp4"
    with tempfile.NamedTemporaryFile(suffix=".vtt", delete=False, mode='w', encoding='utf-8') as tmp_vtt:
        tmp_vtt.write(protected_vtt_content)
        tmp_vtt_path = tmp_vtt.name

    clean_vtt_path = tmp_vtt_path.replace("\\", "/").replace(":", "\\:")
    actual_font_size = base_font_size - 4 if mode == "双语对照" else base_font_size
    align = cfg.get("align", 2)

    safe_margin = cfg.get("margin_lr", 40)
    margin_l = safe_margin if align in [2, 4] else 0
    margin_r = safe_margin if align in [2, 6] else 0
    margin_v = cfg.get("margin_v", 40)

    font_name = "@Microsoft YaHei" if is_vertical else "Microsoft YaHei"
    angle = ",Angle=270" if is_vertical else ""

    style = f"Fontname={font_name},Fontsize={actual_font_size},PrimaryColour=&H00FFFFFF,OutlineColour={cfg['color']},BorderStyle={cfg['style']},Outline=1.2,Shadow=0.5,MarginV={margin_v},MarginL={margin_l},MarginR={margin_r},Alignment={align}{angle},WrapStyle=0"

    cmd = ["ffmpeg", "-y", "-hwaccel", "cuda", "-i", video_path, "-vf",
           f"subtitles='{clean_vtt_path}':force_style='{style}'", "-c:v", "h264_nvenc", "-b:v", "6M", "-preset", "p4",
           "-c:a", "copy", output_video]

    with st.spinner("正在硬件加速压制视频，请耐心等待"):
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return output_video
        finally:
            if os.path.exists(tmp_vtt_path):
                os.remove(tmp_vtt_path)

def translate_batch(engine, ja_lines, full_glossary, prev_context, sys_prompt):
    active_glossary = {k: v for k, v in full_glossary.items() if k in "".join(ja_lines)}
    glossary_str = json.dumps(active_glossary, ensure_ascii=False) if active_glossary else "无"
    input_data = [{"id": i, "ja": text} for i, text in enumerate(ja_lines)]

    prompt = f"""
    {sys_prompt}
    【前情提要】：{prev_context if prev_context else "这是视频开头。"}
    【当前激活术语】：{glossary_str}
    【要求】：只返回纯 JSON 数组！严禁代码块标记。格式：[{{\"id\":0, \"zh\":\"翻译内容\"}}]
    输入数据：{json.dumps(input_data, ensure_ascii=False)}
    """
    for _ in range(3):
        try:
            if engine == "DeepSeek Pro":
                res = sf_client.chat.completions.create(model="pro/deepseek-ai/deepseek-v3",
                                                        messages=[{"role": "user", "content": prompt}], temperature=0.1)
                content = res.choices[0].message.content.strip()
            else:
                content = gemini_client.models.generate_content(model="gemini-1.5-flash", contents=prompt).text.strip()
            json_match = re.search(r'\[\s*\{.*?\}\s*\]', content, re.DOTALL)
            if json_match:
                parsed_json = json.loads(json_match.group(0))
                translations = [""] * len(ja_lines)
                for item in parsed_json:
                    if 'id' in item and 'zh' in item and item['id'] < len(translations):
                        translations[item['id']] = item['zh']
                return translations
        except:
            time.sleep(2)
    return ["【翻译超时或错误】"] * len(ja_lines)

def run_full_pipeline(video_path, engine, out_type, is_test, active_prof, full_gloss, preset, font_size):
    prog, stat = st.progress(0.0), st.empty()
    ja_captions = []

    stat.info(f"正在进行语音识别... ({os.path.basename(video_path)})")
    model = init_whisper_model()
    segments, _ = model.transcribe(video_path, language="ja", beam_size=5, initial_prompt=active_prof["whisper_prompt"],
                                   condition_on_previous_text=True)
    for s in segments:
        if s.text.strip():
            ja_captions.append(
                {'start': format_time(s.start), 'end': format_time(s.end), 'text': s.text.strip()})

    if is_test:
        ja_captions = ja_captions[:20]

    stat.info("正在进行翻译处理...")
    final_vtt = "WEBVTT\n\n"
    prev_text = ""
    for i in range(0, len(ja_captions), 10):
        batch = ja_captions[i:i + 10]
        zh_texts = translate_batch(engine, [b['text'] for b in batch], full_gloss, prev_text, active_prof["llm_sys"])
        for idx, cap in enumerate(batch):
            zh = zh_texts[idx] if idx < len(zh_texts) else ""
            final_vtt += f"{cap['start']} --> {cap['end']}\n{zh}\n{cap['text'] if out_type == '双语对照' else ''}\n\n"
        if len(zh_texts) > 0:
            prev_text = " ".join([z for z in zh_texts[-3:] if z])
        prog.progress(min((i + 10) / len(ja_captions), 1.0))

    vtt_path = os.path.splitext(video_path)[0] + ".zh.vtt"
    with open(vtt_path, "w", encoding="utf-8") as f:
        f.write(final_vtt)

    prog.empty()
    stat.empty()

    out_vid = burn_subtitles_nvenc(video_path, final_vtt, out_type, preset, font_size)

    try:
        backup_dir = os.path.join(os.path.dirname(video_path), "生肉备份_Backup")
        os.makedirs(backup_dir, exist_ok=True)
        shutil.move(video_path, os.path.join(backup_dir, os.path.basename(video_path)))
        if os.path.exists(vtt_path):
            shutil.move(vtt_path, os.path.join(backup_dir, os.path.basename(vtt_path)))
    except:
        pass

    st.success(f"处理完成: {os.path.basename(out_vid)}")

with st.sidebar:
    st.header("配置")
    selected_domain = st.selectbox("视频类型", list(DOMAIN_PROFILES.keys()), index=0)
    active_profile = DOMAIN_PROFILES[selected_domain]

    st.divider()
    if st.button("清空系统状态并重置", type="secondary", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    st.divider()
    is_test_mode = st.toggle("急速测试模式 (仅处理前20句)")

    if "将棋" in selected_domain:
        with st.expander("局部术语注入面板 (将棋)"):
            if os.path.exists(GLOSSARY_FILE):
                with open(GLOSSARY_FILE, 'r', encoding='utf-8-sig') as f:
                    current_glossary = json.load(f)
            else:
                current_glossary = {"居飛車": "居飞车"}
            edited_df = st.data_editor([{"日文": k, "中文": v} for k, v in current_glossary.items()],
                                       num_rows="dynamic")
            full_glossary = {r["日文"]: r["中文"] for r in edited_df if r["日文"] and r["中文"]}
            if st.button("保存本地词库"):
                with open(GLOSSARY_FILE, 'w', encoding='utf-8') as f:
                    json.dump(full_glossary, f, ensure_ascii=False)
    else:
        full_glossary = {}

st.title("视频处理工作台")

tab_download, tab_translate, tab_pipeline = st.tabs(
    ["1. 独立下载终端", "2. 独立翻译压制", "3. 端到端流水线 (全自动)"])

def render_input_hub(key_prefix):
    st.markdown("##### 数据源输入 (支持单链接 / 多行批量 / 专栏 / 播放列表)")
    with st.container(border=True):
        txt_input = st.text_area("在下方粘贴链接：", height=100, key=f"{key_prefix}_text",
                                 placeholder="https://youtube.com/...\nhttps://youtube.com/playlist...")
        st.markdown("<div style='text-align: center; color: gray;'>--- 或者 ---</div>", unsafe_allow_html=True)
        file_input = st.file_uploader("将包含链接的 .txt 文件拖拽到此处：", type=['txt'], key=f"{key_prefix}_file")
    return txt_input, file_input

with tab_download:
    dl_txt, dl_file = render_input_hub("tab1")

    c1, c2 = st.columns(2)
    with c1:
        dl_mode = st.selectbox("下载配置", ["视频 + 日文字幕 (标准工作流)", "纯音频提取 (MP3 最高音质)"])
    if st.button("开始下载", use_container_width=True):
        urls = extract_urls(dl_txt, dl_file)
        if urls:
            paths = download_video(urls, dl_mode, "1080P", st.progress(0.0), st.empty())
            if paths and "视频" in dl_mode:
                st.session_state.selected_path = paths[0]
        else:
            st.warning("请输入有效链接或上传 txt 文件！")

with tab_translate:
    st.markdown("### 压制控制台")
    col_p1, col_p2 = st.columns([5, 1])
    with col_p1:
        local_path = st.text_input("视频绝对路径", value=st.session_state.selected_path)
    with col_p2:
        st.write("")
        st.write("")
        if st.button("浏览视频", use_container_width=True):
            root = tk.Tk()
            root.attributes('-topmost', True)
            root.withdraw()
            p = filedialog.askopenfilename(filetypes=[("视频", "*.mp4 *.mkv *.webm")])
            root.destroy()
            if p:
                st.session_state.selected_path = p.replace("/", "\\")
                st.rerun()

    st.divider()

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        tr_mode = st.selectbox("工作模式", ["自动识别 (听写翻译全流程)", "自由挂载/重压制 (读取外部字幕)"])
    with c2:
        tr_out = st.selectbox("最终格式", ["仅中文字幕", "双语对照"])
    with c3:
        engine = st.selectbox("翻译引擎", ["DeepSeek Pro", "Gemini 1.5 Flash"])

    c_p1, c_p2 = st.columns([3, 1])
    with c_p1:
        selected_preset = st.selectbox("字幕排版与滤镜", list(SUBTITLE_PRESETS.keys()))
    with c_p2:
        local_font_size = st.number_input("基准字号 (建议18-24)", min_value=12, max_value=40, value=22)

    st.divider()
    edited_df = None

    if tr_mode == "自由挂载/重压制 (读取外部字幕)":
        st.info("你可以在这里强制将任意字幕文件（.vtt）烧录到上方指定的视频中。")
        uploaded_sub = st.file_uploader("上传外部 .vtt 格式字幕文件", type=['vtt'])

        physical_vtt_path = None
        tmp_vtt_to_delete = None

        if uploaded_sub:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".vtt") as tmp:
                tmp.write(uploaded_sub.getvalue())
                physical_vtt_path = tmp.name
                tmp_vtt_to_delete = tmp.name
        elif local_path and os.path.exists(local_path):
            auto_vtt_path = os.path.splitext(local_path)[0] + ".zh.vtt"
            if os.path.exists(auto_vtt_path):
                physical_vtt_path = auto_vtt_path
                st.caption(f"已自动加载同名字幕：{os.path.basename(auto_vtt_path)}")

        if physical_vtt_path:
            st.caption("下方是解析出的字幕数据（双击修改内容，选中按 Delete 删除）")
            try:
                vtt = webvtt.read(physical_vtt_path)
                vtt_data = [{"时间轴": f"{c.start} --> {c.end}", "字幕内容": c.text} for c in vtt]
                df = pd.DataFrame(vtt_data)

                edited_df = st.data_editor(
                    df,
                    column_config={
                        "时间轴": st.column_config.TextColumn("时间轴 (防误触保护)", disabled=True, width="medium"),
                        "字幕内容": st.column_config.TextColumn("字幕内容 (双击编辑)", width="large")
                    },
                    use_container_width=True, height=450, hide_index=True, num_rows="dynamic"
                )
            except Exception as e:
                st.error(f"字幕解析失败: {e}")
            finally:
                if tmp_vtt_to_delete and os.path.exists(tmp_vtt_to_delete):
                    os.remove(tmp_vtt_to_delete)

    if tr_mode == "自由挂载/重压制 (读取外部字幕)":
        if st.button("确认烧录：执行硬件压制", type="primary", use_container_width=True):
            if local_path and os.path.exists(local_path) and edited_df is not None:
                new_vtt_content = "WEBVTT\n\n"
                for index, row in edited_df.iterrows():
                    if str(row['时间轴']).strip():
                        new_vtt_content += f"{row['时间轴']}\n{row['字幕内容']}\n\n"

                out_vid = burn_subtitles_nvenc(local_path, new_vtt_content, tr_out, selected_preset, local_font_size)

                if "生肉备份_Backup" in out_vid:
                    parent_dir = os.path.dirname(os.path.dirname(out_vid))
                    final_out_vid = os.path.join(parent_dir, os.path.basename(out_vid))
                    if os.path.exists(final_out_vid):
                        os.remove(final_out_vid)
                    shutil.move(out_vid, final_out_vid)
                    out_vid = final_out_vid

                st.success(f"重新压制完成！成品视频已更新：{os.path.basename(out_vid)}")
                st.balloons()
            else:
                st.error("请确认已指定视频路径，并且字幕数据加载成功。")
    else:
        if st.button("启动自动化处理流程", type="primary", use_container_width=True):
            if local_path and os.path.exists(local_path):
                run_full_pipeline(local_path, engine, tr_out, is_test_mode, active_profile, full_glossary,
                                  selected_preset, local_font_size)
            else:
                st.error("请输入有效的本地视频绝对路径！")

with tab_pipeline:
    st.markdown("### 自动化流水线")
    pipe_txt, pipe_file = render_input_hub("tab3")

    c_a, c_b, c_c, c_d = st.columns(4)
    with c_a:
        pipe_out = st.selectbox("最终格式", ["仅中文字幕", "双语对照"], key="pipe_out")
    with c_b:
        pipe_eng = st.selectbox("翻译引擎", ["DeepSeek Pro", "Gemini 1.5 Flash"])
    with c_c:
        pipe_preset = st.selectbox("字幕排版", list(SUBTITLE_PRESETS.keys()))
    with c_d:
        pipe_font_size = st.number_input("基准字号", min_value=12, max_value=40, value=22)

    if st.button("启动批量自动化流水线", type="primary", use_container_width=True):
        urls = extract_urls(pipe_txt, pipe_file)
        if urls:
            st.divider()
            st.markdown("#### 阶段 1：批量下载")
            prog_dl, stat_dl = st.progress(0.0), st.empty()

            downloaded_paths = download_video(urls, "视频 + 日文字幕 (标准工作流)", "1080P", prog_dl, stat_dl)

            if downloaded_paths:
                st.markdown(f"#### 阶段 2：处理队列 (共 {len(downloaded_paths)} 个视频)")
                for idx, path in enumerate(downloaded_paths):
                    st.write(f"正在处理 ({idx + 1}/{len(downloaded_paths)}): `{os.path.basename(path)}`")
                    run_full_pipeline(path, pipe_eng, pipe_out, is_test_mode, active_profile, full_glossary,
                                      pipe_preset, pipe_font_size)
                st.success("所有任务已执行完毕。")
            else:
                st.error("未能成功下载任何视频，请检查链接。")
        else:
            st.warning("请输入链接或上传 txt 文件。")
