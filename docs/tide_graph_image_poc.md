# タイドグラフ画像 カレンダー表示方式 POC

**作成日**: 2026-02-11  
**Issue**: #76  
**ステータス**: 調査中

---

## 目的

タイドグラフ画像をGoogle Calendarイベントに表示する方式を比較検証し、最適な方式を選定する。

---

## 方式A: イベント本文に画像URLを挿入

### 概要
外部画像ホスティングサービス（Imgur等）を使用し、画像URLをイベント本文に挿入する方式。

### 実装状況
- ✅ タイドグラフ画像生成スクリプト作成（`scripts/poc_tide_graph_image.py`）
- ✅ Imgurアップロードスクリプト作成（`scripts/poc_upload_imgur.py`）
- ⏳ Google Calendarでの表示確認（手動テスト待ち）

### 検証ステップ

#### 1. 画像生成
```bash
uv run python scripts/poc_tide_graph_image.py
```
- **結果**: ✅ 成功
- **出力**: `output/poc_tide_graphs/tide_graph_20260215.png`
- **注意**: 日本語フォント警告あり（実装時に対応必要）

#### 2. Imgurアップロード
```bash
export IMGUR_CLIENT_ID="your_client_id"
uv run python scripts/poc_upload_imgur.py
```
- **状態**: 未実施（Client ID取得が必要）
- **取得方法**: https://api.imgur.com/oauth2/addclient

#### 3. Google Calendarでの表示確認
以下の形式でイベント本文に挿入して表示を確認:

**パターン1: プレーンテキストURL**
```
[TIDE]
...

[GRAPH]
https://i.imgur.com/XXXXX.png

[FORECAST]
...
```

**パターン2: Markdown形式**
```
[GRAPH]
![タイドグラフ](https://i.imgur.com/XXXXX.png)
```

**パターン3: HTML形式**
```
[GRAPH]
<img src="https://i.imgur.com/XXXXX.png" alt="タイドグラフ" width="100%">
```

### メリット
- ✅ 既存のクライアント実装をほぼそのまま利用可能
- ✅ Google Calendar API の追加権限不要
- ✅ 実装が簡単（本文にURLを追加するだけ）
- ✅ 画像生成とアップロードが分離されているため、デバッグしやすい

### デメリット
- ❌ 外部依存（画像ホスティングサービスの安定性・料金）
- ❌ Google Calendar の本文表示仕様に依存（HTML/Markdownのレンダリング）
- ❌ 画像の生存期間管理（ホスティングサービスの保存期間制限）
- ❌ プライバシー懸念（外部サービスに画像をアップロード）

---

## 方式B: Google Calendar のイベント添付（Drive）

### 概要
Google Driveに画像をアップロードし、Calendar APIの `attachments` フィールドを使用してイベントに添付する方式。

### 実装状況
- ⏳ 調査中（ドキュメント確認）

### 検証ステップ

#### 1. Calendar API の `attachments` 仕様確認
- **ドキュメント**: https://developers.google.com/calendar/api/v3/reference/events
- **確認事項**:
  - [ ] `attachments` フィールドのサポート有無
  - [ ] 添付できるファイル形式
  - [ ] 添付ファイルの最大サイズ
  - [ ] Drive以外のファイルソースのサポート

#### 2. 必要な権限スコープ
```python
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive.file",  # 新規追加
]
```

#### 3. Drive APIの利用方法
- Google Drive API クライアントの実装
- Driveへの画像アップロード
- 公開リンクの生成

### メリット
- ✅ Google エコシステム内で完結（外部依存なし）
- ✅ Google Calendar の標準機能を利用（表示の安定性）
- ✅ Driveの保存容量内で管理（15GB無料枠）
- ✅ プライバシー保護（外部サービスにアップロードしない）

### デメリット
- ❌ 追加のOAuth2スコープが必要
- ❌ 既存のクライアント実装を拡張する必要あり
- ❌ Driveへのアップロード処理が必要（API呼び出し増加）
- ❌ 古い画像の削除管理が必要（Drive容量の逼迫）
- ❌ 実装が複雑（Drive API + Calendar API の統合）

---

## イベント本文への画像セクション配置案

### 案1: 新規セクション `[GRAPH]` を追加（推奨）
```
🔴大潮 🟠中潮 🔵小潮 ⚪長潮 🟢若潮

[TIDE]
⭐ 中央日
- 満潮: 06:12 (162cm)
- 干潮: 12:34 (58cm)
- 時合い: 04:12-08:12

[GRAPH]
![タイドグラフ](https://i.imgur.com/XXXXX.png)

[FORECAST]
（フェーズ2で追加予定）

[NOTES]
（ユーザー手動追記欄）
```

**理由**: 
- セクション分離の原則に従う
- 将来的に画像生成のON/OFF切り替えが容易
- 既存の `[TIDE]`/`[FORECAST]`/`[NOTES]` 更新ルールと整合

### 案2: `[TIDE]` セクション内に挿入
```
[TIDE]
⭐ 中央日
- 満潮: 06:12 (162cm)
- 干潮: 12:34 (58cm)
- 時合い: 04:12-08:12

![タイドグラフ](https://i.imgur.com/XXXXX.png)
```

**理由**: 
- タイドグラフは潮汐データの一部として扱う
- セクション数を増やさない

**懸念**: 
- `[TIDE]` セクションの更新時に画像URLも上書きされる可能性

### 案3: イベント本文の最上部
```
![タイドグラフ](https://i.imgur.com/XXXXX.png)

🔴大潮 🟠中潮 🔵小潮 ⚪長潮 🟢若潮

[TIDE]
...
```

**理由**: 
- 画像を最初に表示して視認性を向上

**懸念**: 
- セクション構造の一貫性が失われる

---

## 調査結果（未完）

### Google Calendarのイベント本文仕様
- **状態**: 未調査
- **確認事項**:
  - [ ] プレーンテキストのみか、HTML/Markdown対応か？
  - [ ] 画像URLを挿入した場合、プレビュー表示されるか？
  - [ ] モバイルアプリでの表示はどうなるか？

### Imgur API
- **無料枠**: 12,500アップロード/日、1,250,000リクエスト/月
- **認証**: Client IDのみで匿名アップロード可能
- **画像サイズ**: 最大10MB（PNG/JPG推奨）
- **保存期間**: 無期限（ただし、6ヶ月間アクセスがない場合は削除される可能性）

---

## 次のステップ

### 優先度1: 方式Aの手動検証
1. [ ] Imgur Client IDを取得
2. [ ] `poc_upload_imgur.py` を実行して画像をアップロード
3. [ ] 取得したURLを手動でGoogle Calendarイベント本文に挿入
4. [ ] Web版/モバイル版での表示を確認
5. [ ] 結果をこのドキュメントに記録

### 優先度2: 方式Bの調査
1. [ ] Google Calendar API の `attachments` 仕様をドキュメントで確認
2. [ ] Drive APIの利用方法を調査
3. [ ] 必要な実装範囲を見積もり

### 優先度3: 方式選定
1. [ ] 使い勝手、リッチさ、権限、運用コストを比較
2. [ ] 方式選定の結論と理由を記録
3. [ ] 採用方式の最小POC計画を策定

---

## 結論（未定）

**選定方式**: 未定

**理由**: データ収集中

**次のアクション**: 手動検証の実施

---

## 技術的な注意事項

### 日本語フォント対応
matplotlibで日本語を表示する場合、日本語フォントの設定が必要:

```python
import matplotlib.pyplot as plt

# 日本語フォント設定（Linux環境）
plt.rcParams['font.family'] = 'Noto Sans CJK JP'

# または、matplotlibrcで設定
```

**対応方法**:
- システムに日本語フォントをインストール
- matplotlibrcで明示的にフォントを指定
- フォントがない場合はローマ字表記にフォールバック

### 画像サイズの最適化
- 解像度: 150dpi（Web表示に十分）
- サイズ: 10x4インチ（横長）
- ファイルサイズ: 100KB以下を目標（Imgur/Drive転送の効率化）

---

## 参考リンク

- [Imgur API Documentation](https://apidocs.imgur.com/)
- [Google Calendar API - Events](https://developers.google.com/calendar/api/v3/reference/events)
- [Google Drive API - Files](https://developers.google.com/drive/api/v3/reference/files)
- [matplotlib - Japanese Font Support](https://matplotlib.org/stable/gallery/text_labels_and_annotations/font_family_rc_sgskip.html)
