# タイドグラフ画像 カレンダー表示方式 POC

**作成日**: 2026-02-11
**更新日**: 2026-02-12
**Issue**: #76
**ステータス**: 完了（方式B採用）

---

## 目的

タイドグラフ画像をGoogle Calendarイベントに表示する方式を比較検証し、最適な方式を選定する。

---

## 結論

**採用方式**: **方式B（Google Drive + Calendar attachments）**

**選定理由**:
1. Google アカウントのみで完結（外部サービスのアカウント作成不要）
2. Google Calendar の標準添付機能を利用（表示の安定性・将来互換性）
3. Google Drive の無料枠（15GB）で十分な容量を確保
4. `drive.file` スコープ（最小権限）でセキュリティリスクを最小化
5. 古い画像の定期削除で容量を管理可能

**方式A を不採用とした理由**:
- Imgur 等の外部サービスアカウントの追加管理が煩雑
- 外部サービスの SLA/保存期間に依存するリスク
- Google Calendar の本文は HTML/Markdown の画像レンダリングが不安定

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

## 調査結果

### Google Calendar API の attachments 仕様

**調査完了**: ✅

| 項目 | 仕様 |
|------|------|
| `attachments[].fileUrl` | Drive ファイルの alternateLink 形式 URL（**追加時必須**） |
| `attachments[].title` | 添付ファイルのタイトル |
| `attachments[].mimeType` | MIME タイプ |
| `attachments[].fileId` | Drive ファイル ID（**読み取り専用**） |
| 最大添付数 | 25 個/イベント |
| 必須パラメータ | `supportsAttachments=true` をクエリパラメータに設定 |
| 認可スコープ | `calendar`（既存スコープで OK） |

### Google Drive API の仕様

| 項目 | 仕様 |
|------|------|
| アップロード URI | `POST https://www.googleapis.com/upload/drive/v3/files` |
| 最大ファイルサイズ | 5,120 GB |
| アップロード方式 | `media` / `multipart` / `resumable` |
| 認可スコープ | `drive.file`（アプリ作成ファイルのみ、最小権限） |
| 公開設定 | `permissions.create` で `role: reader, type: anyone` |

### Google Calendar のイベント本文仕様

- Google Calendar は description フィールドに HTML を部分的にサポート
- `<img>` タグのレンダリングは不安定（Web/モバイルで挙動が異なる）
- Markdown 形式はサポートされていない
- **結論**: 本文への画像埋め込みは信頼性が低く、attachments の方が適切

### Imgur API（参考情報）
- 無料枠: 12,500 アップロード/日
- 認証: Client ID のみで匿名アップロード可能
- 保存期間: 無期限（ただし 6 ヶ月間アクセスがない場合は削除される可能性）
- **不採用理由**: 外部アカウント管理の煩雑さ

---

## 次のステップ

方式 B の実装に向けた詳細計画は [docs/inprogress/issue-76.md](inprogress/issue-76.md) を参照。

主要なサブタスク:
1. Google Drive API クライアント実装
2. GoogleCalendarClient の attachments 対応拡張
3. タイドグラフ画像生成サービス（matplotlib + seaborn）
4. SyncTideUseCase への統合
5. 古い画像の定期削除機能

---

## 技術的な注意事項

### 日本語フォント対応

**採用方式**: [`matplotlib-fontja`](https://github.com/ciffelia/matplotlib-fontja)

`import` するだけで matplotlib が日本語表示に対応する。IPAexゴシックフォントを同梱しているため、システムへの日本語フォントインストールが不要。

```python
import matplotlib.pyplot as plt
import matplotlib_fontja

# import だけで日本語フォントが適用される
plt.plot([1, 2, 3, 4])
plt.xlabel('簡単なグラフ')
plt.show()
```

**seaborn との併用時の注意**:
`sns.set_theme()` がフォントをデフォルトに上書きするため、その後に `japanize()` を呼ぶ必要がある:

```python
import matplotlib_fontja
import seaborn as sns

sns.set_theme()
matplotlib_fontja.japanize()  # set_theme() の後に再適用
```

または `sns.set_theme(font="IPAexGothic")` として明示的にフォントを指定することも可能。

**リンター警告回避**:
`import matplotlib_fontja` だけだと ruff の F401（未使用 import）警告が出るため、
`matplotlib_fontja.japanize()` を明示的に呼ぶことで回避する。

### 画像要件（スマホ表示最適化）

スマホでの閲覧を前提とし、以下の要件を採用:

| 項目 | 仕様 | 理由 |
|------|------|------|
| アスペクト比 | **1:1（スクエア）** | スマホ画面でピンチズーム不要 |
| サイズ | 6×6 インチ (900×900px @150dpi) | モバイルに十分な解像度 |
| 配色 | **ダークモード基調** | 早朝・夕方の確認を想定 |
| 背景色 | `#0d1117`（ダークネイビー） | ダークモードに調和 |
| 潮位曲線 | `#58a6ff`（シアン） | 暗背景で高コントラスト |
| 満潮マーカー | `#f0883e`（オレンジ）+ 時刻/潮位ラベル | グラフ内で時刻情報を直接確認可能 |
| 干潮マーカー | `#3fb950`（ティール）+ 時刻/潮位ラベル | 満潮と色で区別 |
| 時合い帯 | `#d29922` (alpha=0.15) | 釣りの最重要情報を可視化 |
| タイトル | `{地名} {MM/DD}` + 潮回り絵文字 | 地名・日付・潮回りを一目で確認 |
| ファイル名 | `tide_graph_{location_id}_{YYYYMMDD}.png` | Drive 上で地点別ソート可能 |
| Drive フォルダ | `fishing-forecast-tide-graphs`（専用） | 他のファイルと混在しない |
| ファイルサイズ | 100KB 以下目標 | Drive 転送・表示の効率化 |

---

## 参考リンク

- [Imgur API Documentation](https://apidocs.imgur.com/)
- [Google Calendar API - Events](https://developers.google.com/calendar/api/v3/reference/events)
- [Google Drive API - Files](https://developers.google.com/drive/api/v3/reference/files)
- [matplotlib - Japanese Font Support](https://matplotlib.org/stable/gallery/text_labels_and_annotations/font_family_rc_sgskip.html)
