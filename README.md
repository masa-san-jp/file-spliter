# ファイル分割プログラム

`分割前` フォルダに置いたファイルを指定サイズで分割し、`分割後` フォルダへ出力するデスクトップ向けアプリです。

## 機能

- **汎用ファイル**（テキスト・PDF・画像・ZIP など）をバイト単位で厳密に分割
- **音声・動画ファイル**（MP3・MP4・WAV・MOV など）を ffmpeg で再生可能な状態に分割
  - 高速モード: 再エンコードなし、処理が速い
  - 精度優先モード: 再エンコードあり、指定サイズへの精度が高い
- 分割サイズを KB / MB / GB 単位で指定（1 MB〜10 GB）
- 各断片の SHA-256 ハッシュと元ファイル情報を `metadata.json` として保存
- 処理ログを `logs/execution_YYYYMMDD_HHMMSS.log` へ出力
- 処理中の中断ボタン対応

## 動作環境

- Python 3.11 以上
- macOS / Linux / Windows（tkinter が利用可能な環境）
- 音声・動画の分割には ffmpeg が必要

## セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/<your-username>/file-spliter.git
cd file-spliter

# （任意）仮想環境を作成
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存パッケージをインストール（テスト用のみ）
pip install -r requirements.txt
```

### ffmpeg のインストール（音声・動画を分割する場合）

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Windows
# https://ffmpeg.org/download.html からダウンロードし PATH を通す
```

## 使い方

1. `分割前` フォルダに分割したいファイルを置く
2. アプリを起動する

```bash
python3 main.py
```

3. 分割サイズと単位を入力する（例: `500` + `MB`）
4. 音声・動画の分割モードを選ぶ（高速 or 精度優先）
5. **実行** ボタンを押す
6. 完了後、`分割後` フォルダに結果が出力される

### 出力フォルダ構成

```
分割後/
  sample/
    sample.part001
    sample.part002
    metadata.json
  music/
    music_001.mp3
    music_002.mp3
    metadata.json
```

### metadata.json の内容

```json
{
  "original_name": "sample.zip",
  "original_ext": ".zip",
  "original_size_bytes": 104857600,
  "original_sha256": "abc123...",
  "split_mode": "binary",
  "created_at": "2026-04-09T12:00:00+00:00",
  "part_count": 2,
  "parts": [
    { "index": 1, "filename": "sample.part001", "size_bytes": 52428800, "sha256": "..." },
    { "index": 2, "filename": "sample.part002", "size_bytes": 52428800, "sha256": "..." }
  ]
}
```

## テスト

```bash
python3 -m pytest tests/ -v
```

## プロジェクト構成

```
file-spliter/
├── main.py                          # エントリーポイント
├── requirements.txt
├── 分割前/                           # 入力フォルダ（ここにファイルを置く）
├── 分割後/                           # 出力フォルダ（自動生成）
├── logs/                            # 実行ログ（自動生成）
├── src/
│   ├── config/                      # 定数・設定
│   ├── core/                        # ファイル判定・ハッシュ・メタデータ
│   ├── services/                    # ffmpeg・ログ・オーケストレーション
│   ├── splitters/                   # 汎用分割・メディア分割
│   ├── gui/                         # tkinter GUI
│   └── utils/                       # エラー定義・パスユーティリティ
└── tests/                           # ユニット・統合テスト
```

## 対応ファイル形式

| 種別 | 拡張子 |
|------|--------|
| 音声 | `.mp3` `.wav` `.m4a` `.aac` `.flac` `.ogg` |
| 動画 | `.mp4` `.mov` `.mkv` `.avi` `.webm` |
| 汎用 | 上記以外すべて（テキスト・PDF・画像・ZIP など） |

## ライセンス

MIT
