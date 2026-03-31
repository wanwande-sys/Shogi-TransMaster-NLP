# core_engine.py
import os
import re
import json
import time
import shutil
import tempfile
import subprocess
import yt_dlp
import httpx
import streamlit as st
from openai import OpenAI
from google import genai
from core.config import BASE_DOWNLOAD_DIR, SUBTITLE_PRESETS
from core.utils import get_video_duration, enforce_line_breaks, format_time


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


def download_video(urls, mode, quality, progress_ui, status_ui):
    outtmpl = os.path.join(BASE_DOWNLOAD_DIR, '%(uploader)s', '%(title)s', '%(title)s.%(ext)s')
    ydl_opts = {
        'proxy': 'http://127.0.0.1:7890', 'outtmpl': outtmpl,
        'sponsorblock_remove': ['sponsor', 'selfpromo', 'interaction'],
        'writethumbnail': True, 'quiet': True, 'no_warnings': True, 'ignoreerrors': True,
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
        p_index, p_count = info.get('playlist_index'), info.get('playlist_count')
        title = info.get('title', '未知视频')
        prefix = f"🗂️ [专栏进度: {p_index} / {p_count}]" if p_index and p_count else "🎬 [单集下载]"

        if d['status'] == 'downloading':
            try:
                pct_str = re.sub(r'\x1b\[[0-9;]*m', '', d.get('_percent_str', '0%').replace('%', '').strip())
                progress_ui.progress(float(pct_str) / 100.0)
            except:
                pass
            speed = re.sub(r'\x1b\[[0-9;]*m', '', d.get('_speed_str', 'N/A'))
            eta = re.sub(r'\x1b\[[0-9;]*m', '', d.get('_eta_str', 'N/A'))
            status_ui.markdown(f"### 📥 下载中...\n**{prefix}** `{title}`\n⚡ **速度**: `{speed}` | ⏳ **剩余**: `{eta}`")
        elif d['status'] == 'finished':
            progress_ui.progress(1.0)
            status_ui.success(f"✅ **{prefix}** `{title}` 下载完成，封装中...")

    ydl_opts['progress_hooks'] = [my_hook]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for url in urls:
                status_ui.info(f"🔍 解析容器: {url}")
                info = ydl.extract_info(url, download=True)
                if not info: continue
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            fp = ydl.prepare_filename(entry)
                            if 'merge_output_format' in ydl_opts and not fp.endswith('.mp4'): fp = fp.rsplit('.', 1)[
                                                                                                       0] + '.mp4'
                            final_paths.append(fp)
                else:
                    fp = ydl.prepare_filename(info)
                    if 'merge_output_format' in ydl_opts and not fp.endswith('.mp4'): fp = fp.rsplit('.', 1)[0] + '.mp4'
                    final_paths.append(fp)
        return final_paths
    except Exception as e:
        st.error(f"解析/下载异常: {e}")
        return []


def burn_subtitles_nvenc_with_progress(video_path, vtt_content, mode, preset_key, base_font_size, st_prog_bar,
                                       st_stat_text):
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
    margin_l = cfg.get("margin_lr", 40) if align in [2, 4] else 0
    margin_r = cfg.get("margin_lr", 40) if align in [2, 6] else 0
    margin_v = cfg.get("margin_v", 40)
    font_name = "@Microsoft YaHei" if is_vertical else "Microsoft YaHei"
    angle = ",Angle=270" if is_vertical else ""

    style = f"Fontname={font_name},Fontsize={actual_font_size},PrimaryColour=&H00FFFFFF,OutlineColour={cfg['color']},BorderStyle={cfg['style']},Outline=1.2,Shadow=0.5,MarginV={margin_v},MarginL={margin_l},MarginR={margin_r},Alignment={align}{angle},WrapStyle=0"

    cmd = ["ffmpeg", "-y", "-hwaccel", "cuda", "-i", video_path, "-vf",
           f"subtitles='{clean_vtt_path}':force_style='{style}'", "-c:v", "h264_nvenc", "-b:v", "6M", "-preset", "p4",
           "-c:a", "copy", output_video]

    total_duration = get_video_duration(video_path)
    st_stat_text.info("🔥 [4060 NVENC] 硬件加速压制引擎已启动，正在烧录...")

    try:
        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True, encoding='utf-8',
                                   errors='ignore')
        time_pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})")

        for line in process.stderr:
            match = time_pattern.search(line)
            if match and total_duration > 0:
                current_time = float(match.group(1)) * 3600 + float(match.group(2)) * 60 + float(match.group(3))
                st_prog_bar.progress(min(current_time / total_duration, 1.0))

        process.wait()
        if process.returncode != 0:
            st.error("❌ FFmpeg 压制出现错误，请检查控制台。")
            return None
        st_prog_bar.progress(1.0)
        return output_video
    finally:
        if os.path.exists(tmp_vtt_path): os.remove(tmp_vtt_path)


def translate_batch(engine, ja_lines, full_glossary, prev_context, sys_prompt):
    sf_client, gemini_client = init_translation_clients()
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
                    if 'id' in item and 'zh' in item and item['id'] < len(translations): translations[item['id']] = \
                    item['zh']
                return translations
        except:
            time.sleep(2)
    return ["【翻译超时或错误】"] * len(ja_lines)


def run_full_pipeline(video_path, engine, out_type, is_test, active_prof, full_gloss, preset, font_size):
    prog, stat = st.progress(0.0), st.empty()
    ja_captions = []

    stat.info(f"🎙️ [4060] Whisper 语音识别中... ({os.path.basename(video_path)})")
    model = init_whisper_model()
    segments, _ = model.transcribe(video_path, language="ja", beam_size=5, initial_prompt=active_prof["whisper_prompt"],
                                   condition_on_previous_text=True)
    for s in segments:
        if s.text.strip(): ja_captions.append(
            {'start': format_time(s.start), 'end': format_time(s.end), 'text': s.text.strip()})

    if is_test: ja_captions = ja_captions[:20]

    stat.info(f"🌐 [{engine}] 正在调用大模型进行上下文纠错翻译...")
    final_vtt = "WEBVTT\n\n"
    prev_text = ""
    for i in range(0, len(ja_captions), 10):
        batch = ja_captions[i:i + 10]
        zh_texts = translate_batch(engine, [b['text'] for b in batch], full_gloss, prev_text, active_prof["llm_sys"])
        for idx, cap in enumerate(batch):
            zh = zh_texts[idx] if idx < len(zh_texts) else ""
            final_vtt += f"{cap['start']} --> {cap['end']}\n{zh}\n{cap['text'] if out_type == '双语对照' else ''}\n\n"
        if len(zh_texts) > 0: prev_text = " ".join([z for z in zh_texts[-3:] if z])
        prog.progress(min((i + 10) / len(ja_captions), 1.0))

    vtt_path = os.path.splitext(video_path)[0] + ".zh.vtt"
    with open(vtt_path, "w", encoding="utf-8") as f:
        f.write(final_vtt)

    prog.empty()
    out_vid = burn_subtitles_nvenc_with_progress(video_path, final_vtt, out_type, preset, font_size, prog, stat)

    if out_vid:
        try:
            backup_dir = os.path.join(os.path.dirname(video_path), "生肉备份_Backup")
            os.makedirs(backup_dir, exist_ok=True)
            shutil.move(video_path, os.path.join(backup_dir, os.path.basename(video_path)))
            if os.path.exists(vtt_path):
                shutil.move(vtt_path, os.path.join(backup_dir, os.path.basename(vtt_path)))
        except:
            pass
        st.success(f"✅ 处理完成: {os.path.basename(out_vid)}")