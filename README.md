<img width="2467" height="1266" alt="image" src="https://github.com/user-attachments/assets/493f8e31-54c2-45b2-b56c-4dc2e22cbf02" />
> ▲Shogi-TransMaster: 将棋動画の自動翻訳・字幕ハードコーディングツール


🎥 実際のシステムによる翻訳・ハードコーディング成果物（Bilibili）:
【【精校中字】山口惠梨子将棋讲座 01：形势判断基础】https://www.bilibili.com/video/BV1f2AtzvEHN?vd_source=8d4b25cf23468b18326df7305d9f7672
(Human-in-the-Loop (HITL) による機械翻訳ポストエディット (MTPE)
完全な自動化（ASR + LLM）を経た後、最終的な字幕のハードコーディング（焼き込み）を行う前に、GUI（Streamlit）上で人間がレビューおよび微修正（Post-editing）を行えるワークフローを設計しました。
これにより、AIの不確実性（幻覚や文脈エラー）を最終段階で排除し、実用レベルのプロフェッショナルな翻訳品質を担保しています。)


## 📸 デモ画面 (Demo)
<img width="2472" height="731" alt="image" src="https://github.com/user-attachments/assets/ffb6a585-3334-424f-802d-14717288038a" />

> ▲ Streamlitを活用したMTPE（ポストエディット）用GUIインタフェース。人間（ドメインエキスパート）による最終確認と修正が容易に行えるHITL（Human-in-the-Loop）設計。


## 📌 プロジェクトの背景 (Motivation)
将棋の解説動画（YouTubeなど）を翻訳・視聴する際、汎用的な音声認識（Whisper）や翻訳モデルでは、将棋特有の専門用語が正しく処理されないという問題に直面しました。
例えば、「1四歩」という座標が単なる「14歩」になったり、「成銀」や「打つ」といった表現が文脈を無視して直訳されたりします。
この課題を解決するため、特定ドメイン（将棋）の翻訳精度を向上させる個人的なツールとして、本システムを開発しました。

## 💡 解決へのアプローチ (Approach)
汎用モデルを専門領域に適応（Domain Adaptation）させるため、以下の実装を行いました。

1. **プロンプトによる出力フォーマットの制限**
   DeepSeek や Gemini などの LLM に対し、出力形式を「[アラビア数字][漢数字][駒の名前]」のフォーマット（例：7七金）に強制するシステムプロンプトを設計しました。
2. **外部辞書 (Glossary) の動的適用**
   汎用AIが知らない専門用語の誤訳を防ぐため、自作の用語辞書 (`shogi_glossary.json`) を翻訳時に動的に読み込ませる仕組みを実装しました。
3. **ローカル環境での処理高速化**
   ローカルの RTX 4060 の計算リソースを活かすため、`faster-whisper` による音声認識と、FFmpeg (NVENC) を用いた字幕焼き込み（ハードコーディング）を統合し、処理時間を短縮しています。

## 🎓 本プロジェクトでの学び (What I Learned)
私は日本語専攻（日本語能力試験N1）のバックグラウンドを持っています。このツールの開発を通じて、自然言語処理（NLP）において、汎用モデルを低資源ドメイン（特定分野の専門用語など）に適応させる際の実践的な手法を学びました。また、AIの出力を人間の専門知識で補正する「Human-in-the-loop」の重要性を実感しました。

## 🛠️ 技術スタック (Tech Stack)
* **ASR**: Faster-Whisper (large-v3, float16 on CUDA)
* **LLM**: DeepSeek-V3, Gemini 1.5 Flash
* **Media Processing**: yt-dlp, FFmpeg (h264_nvenc)
* **UI**: Streamlit

## 🚀 使い方 (Usage)

```bash
# 依存関係のインストール
pip install -r requirements.txt

# 起動
streamlit run app.py
<img width="2547" height="1277" alt="image" src="https://github.com/user-attachments/assets/f89172f0-969a-418c-9f9b-e758328de383" />

