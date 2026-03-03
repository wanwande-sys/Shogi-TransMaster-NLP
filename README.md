<img width="2467" height="1266" alt="image" src="https://github.com/user-attachments/assets/493f8e31-54c2-45b2-b56c-4dc2e22cbf02" />

## 📸 デモ画面 (Demo)
<img width="2472" height="731" alt="image" src="https://github.com/user-attachments/assets/ffb6a585-3334-424f-802d-14717288038a" />

> ▲ Streamlitを活用したMTPE（ポストエディット）用GUIインタフェース。人間（ドメインエキスパート）による最終確認と修正が容易に行えるHITL（Human-in-the-Loop）設計。



🎥 実際のシステムによる翻訳・ハードコーディング成果物（Bilibili）:
【【精校中字】山口惠梨子将棋讲座 01：形势判断基础】https://www.bilibili.com/video/BV1f2AtzvEHN?vd_source=8d4b25cf23468b18326df7305d9f7672
(Human-in-the-Loop (HITL) による機械翻訳ポストエディット (MTPE)
完全な自動化（ASR + LLM）を経た後、最終的な字幕のハードコーディング（焼き込み）を行う前に、GUI（Streamlit）上で人間がレビューおよび微修正（Post-editing）を行えるワークフローを設計しました。
これにより、AIの不確実性（幻覚や文脈エラー）を最終段階で排除し、実用レベルのプロフェッショナルな翻訳品質を担保しています。)




# Shogi-TransMaster: 将棋特化型・ビデオ翻訳ツール

## 🎥 実機デモ / 成果物 (Demo & Output)
本システムを用いて作成した、実際の将棋解説動画の翻訳成果物です。
* **Bilibili**: [【精校中字】山口恵梨子将棋講座 01](https://www.bilibili.com/video/BV1f2AtzvEHN)
  * ※本システムで自動生成後、GUI上で微修正（HITL）を行った成果物です。

## 📌 開発の動機 (Motivation)
YouTubeなどの将棋解説動画を視聴する際、汎用的な音声認識（Whisper）や翻訳モデルでは、将棋特有の専門用語が正しく処理されないという問題に直面しました。
例えば、「1四歩」という座標が単なる「14歩」になったり、「成銀」や「打つ」といった表現が文脉を無視して直訳されたりします。
この課題を解決するため、特定ドメイン（将棋）の翻訳精度を向上させる個人的なツールとして、本システムを開発しました。

## 💡 解決へのアプローチ (Approach)
汎用モデルを専門領域に適応（Domain Adaptation）させるため、以下の実装を行いました。

1. **プロンプトによる出力フォーマットの制限**
   LLMに対し、出力形式を将棋の標準的な記譜法（例：7七金）に強制するシステムプロンプトを設計しました。
2. **外部辞書 (Glossary) の動的適用**
   自作の用語辞書 (`shogi_glossary.json`) を翻訳時に注入し、未登録語 (OOV) の誤訳を抑制しています。
3. **Human-in-the-Loop (HITL) の導入**
   完全自動化の限界を補うため、StreamlitベースのGUIで人間がレビューおよび微修正（Post-editing）を行えるワークフローを構築しました。

## 📊 翻訳精度の評価 (Evaluation)
システムの効果を確認するため、`samples/` フォルダに実際の字幕ファイルを配置しています。
* `raw_whisper.vtt`: 汎用ASRによる未処理の結果。
* `adapted_shogi.vtt`: 本システムによる修正後の結果。

## ⚠️ 現状の課題と限界 (Limitations)
* **ASRの精度不足**: 現時点では `faster-whisper` を使用していますが、解説者の早口や対局中の雑音により、音声認識自体のエラーが発生することがあります。
* **今後の展望**: 将棋解説に特化した音声データでのファインチューニングや、盤面認識（OCR）との連携による補正ロジックの実装を計画しています。

## 🛠️ 技術スタック (Tech Stack)
* **ASR**: Faster-Whisper (large-v3, float16 on CUDA)
* **LLM**: DeepSeek-V3, Gemini 1.5 Flash
* **Processing**: yt-dlp, FFmpeg (h264_nvenc加速)
* **UI**: Streamlit

## 🚀 使い方 (Usage)

### 1. 環境構築 (Setup)
プロジェクトを実行するために、まず依存関係をインストールしてください。

```bash
# 依存関係のインストール
pip install -r requirements.txt

### 2. 実行 (Execution)
Windows環境では、以下のバッチファイルを使用してプログラムを起動できます。

```bash
# 起動
run.bat
