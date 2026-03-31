# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# --- 1. 全局与环境设置 ---
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"
BASE_DOWNLOAD_DIR = r"D:\YouTube下载器\已下载视频"
GLOSSARY_FILE = r"D:\YouTube下载器\将棋翻译\shogi_glossary.json"

# --- 2. 领域预设配置 ---
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

# --- 3. 滤镜与排版配置 ---
SUBTITLE_PRESETS = {
    "0️⃣ 原生纯净 (无背景/无厚重阴影)": {"margin_v": 40, "style": 1, "color": "&H00000000", "align": 2, "vertical": False, "margin_lr": 40},
    "1️⃣ 经典 B站风 (标准底部阴影)": {"margin_v": 40, "style": 1, "color": "&H99000000", "align": 2, "vertical": False, "margin_lr": 40},
    "2️⃣ 强力遮挡板 (带半透明黑底遮盖原文)": {"margin_v": 40, "style": 3, "color": "&H80000000", "align": 2, "vertical": False, "margin_lr": 40},
    "3️⃣ 高位防挡区 (强制抬高避开底部UI)": {"margin_v": 100, "style": 1, "color": "&H99000000", "align": 2, "vertical": False, "margin_lr": 40},
    "4️⃣ 真·竖排靠左 (垂直排版/自动分栏)": {"margin_v": 40, "style": 1, "color": "&H99000000", "align": 4, "vertical": True, "margin_lr": 40},
    "5️⃣ 真·竖排靠右 (垂直排版/自动分栏)": {"margin_v": 40, "style": 1, "color": "&H99000000", "align": 6, "vertical": True, "margin_lr": 40}
}