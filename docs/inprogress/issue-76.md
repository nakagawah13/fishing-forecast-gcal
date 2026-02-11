# Issue #76: タイドグラフ画像のカレンダー表示方式POC

**ステータス**: In Progress  
**担当**: AI Assistant  
**作成日**: 2026-02-11  
**関連Issue**: #76  
**フェーズ**: Phase 1.9

---

## 概要

既存のブロック課題に干渉せず、タイドグラフ画像をカレンダーイベントに表示する方式を比較検証する。

- **方式A**: イベント本文に画像URLを挿入（外部画像ホスティング）
- **方式B**: Google Calendar のイベント添付（Drive）を利用

画像ホスティングは外部画像サービスを前提とし、具体サービスは本タスクで選定する。

---

## 現状分析

### 既存実装の確認

#### 1. GoogleCalendarClient（インフラ層）

**ファイル**: `src/fishing_forecast_gcal/infrastructure/clients/google_calendar_client.py`

**既存メソッド**:
- `create_event()`: イベント作成（extendedPropertiesサポート済み）
- `get_event()`: イベント取得
- `update_event()`: イベント更新

**現状の制限**:
- ❌ イベント添付（attachments）未対応
- ✅ イベント本文（description）のHTML/Markdown対応（Google Calendar側の仕様次第）

#### 2. SyncTideUseCase（アプリケーション層）

**ファイル**: `src/fishing_forecast_gcal/application/usecases/sync_tide_usecase.py`

**既存のイベント本文構造**:
```
🔴大潮 🟠中潮 🔵小潮 ⚪長潮 🟢若潮

[TIDE]
⭐ 中央日（大潮のみ）
- 満潮: 06:12 (162cm)
- 干潮: 12:34 (58cm)
- 時合い: 04:12-08:12

[FORECAST]
（フェーズ2で追加予定）

[NOTES]
（ユーザー手動追記欄）
```

**セクション更新ルール**:
- Sync-Tide は `[TIDE]` セクションを更新（予報・メモは保持）
- Sync-Weather (Phase 2) は `[FORECAST]` セクションのみ更新（他セクションは保持）
- ユーザー編集は `[NOTES]` のみを対象とし、セクション名は変更しない

---

## 方式比較

### 方式A: イベント本文に画像URLを挿入

#### 概要
- 外部画像ホスティングサービスを利用
- 画像URLをイベント本文に挿入（Markdown形式またはHTML形式）

#### メリット
- ✅ 既存のクライアント実装をほぼそのまま利用可能
- ✅ Google Calendar API の追加権限不要
- ✅ 実装が簡単（本文にURLを追加するだけ）

#### デメリット
- ❌ 外部依存（画像ホスティングサービスの安定性・料金）
- ❌ Google Calendar の本文表示仕様に依存（HTML/Markdownのレンダリング）
- ❌ 画像の生存期間管理（ホスティングサービスの保存期間制限）

#### 必要な実装
1. タイドグラフ画像生成（matplotlib等）
2. 画像ホスティングサービスへのアップロード
3. 画像URLの取得
4. イベント本文への画像URL挿入（新規セクション `[GRAPH]` の追加？）

#### 候補サービス
- **Imgur**: 無料、API利用可能、アップロード上限あり
- **GitHub Issues/Releases**: 無料、Markdown対応、リポジトリに紐付け
- **Cloudinary**: 無料枠あり、画像最適化機能
- **その他**: Google Drive（公開リンク生成）、AWS S3（有料）

---

### 方式B: Google Calendar のイベント添付（Drive）

#### 概要
- Google Drive に画像をアップロード
- Calendar API の `attachments` フィールドを使用してイベントに添付

#### メリット
- ✅ Google エコシステム内で完結（外部依存なし）
- ✅ Google Calendar の標準機能を利用（表示の安定性）
- ✅ Driveの保存容量内で管理（15GB無料枠）

#### デメリット
- ❌ 追加のOAuth2スコープが必要（`https://www.googleapis.com/auth/drive.file`）
- ❌ 既存のクライアント実装を拡張する必要あり
- ❌ Driveへのアップロード処理が必要（API呼び出し増加）
- ❌ 古い画像の削除管理が必要（Drive容量の逼迫）

#### 必要な実装
1. タイドグラフ画像生成（matplotlib等）
2. Google Drive API クライアントの実装
3. Driveへの画像アップロード
4. Calendar API の `attachments` フィールド対応
5. GoogleCalendarClient の拡張（`create_event`, `update_event` に `attachments` パラメータ追加）

#### 必要な権限
```python
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive.file",  # 新規追加
]
```

---

## 調査項目

### 1. Google Calendar のイベント本文仕様
- プレーンテキストのみか、HTML/Markdown対応か？
- 画像URLを挿入した場合、プレビュー表示されるか？

### 2. Google Calendar API の `attachments` 仕様
- 添付できるファイル形式の制限
- 添付ファイルの最大サイズ
- Drive以外のファイルソースのサポート有無

### 3. 画像ホスティングサービスの比較
- 無料枠の上限
- API利用の容易さ
- 画像の保存期間
- アクセス制限（認証の有無）

### 4. 既存セクションとの整合性
- 画像をどのセクションに配置するか？
  - **案1**: 新規セクション `[GRAPH]` を追加（[TIDE]の直後？）
  - **案2**: `[TIDE]` セクション内に挿入
  - **案3**: イベント本文の最上部（各セクションの前）

---

## 実装方針（POC）

このPOCでは、以下の順序で検証を進めます:

### ステップ1: Google Calendar のイベント本文仕様調査
- 手動でイベントを作成し、本文に画像URLを挿入してプレビュー表示を確認
- HTML形式: `<img src="URL">` の動作確認
- Markdown形式: `![alt](URL)` の動作確認

### ステップ2: 方式Aの簡易実装（優先）
- matplotlib でダミーのタイドグラフを生成
- 画像ホスティングサービス（Imgur等）にアップロード
- 画像URLをイベント本文に挿入
- Google Calendar での表示確認

### ステップ3: 方式Bの調査
- Google Calendar API の `attachments` 仕様をドキュメントで確認
- 必要な権限スコープの確認
- Drive API の利用方法調査

### ステップ4: 比較と結論
- 使い勝手、リッチさ、権限、運用コストを比較
- 方式選定の結論と理由を記録
- 採用方式の最小POC計画を策定

---

## 受け入れ条件

- [ ] 方式A/方式B の比較メモ（使い勝手・リッチさ・権限・運用コスト）
- [ ] 方式選定の結論と理由
- [ ] 採用方式の最小POC計画
- [ ] フェーズ2のブロック課題に影響しないこと（既存のセクション更新ルールを維持）

---

## スコープ外

- 本番運用のスケール設計（画像生成の最適化、キャッシュ、バッチ処理）
- 気象予報機能の変更（Phase 2タスク）
- タイドグラフの詳細デザイン（このPOCでは簡易版で十分）

---

## 実装予定ファイル

### 新規作成（POC用）
- `scripts/poc_tide_graph_image.py`: タイドグラフ画像生成スクリプト（matplotlibを使用）
- `scripts/poc_upload_imgur.py`: Imgurへのアップロードテストスクリプト
- `docs/tide_graph_image_poc.md`: 調査結果と比較メモのドキュメント

### 変更予定（方式B採用の場合のみ）
- `src/fishing_forecast_gcal/infrastructure/clients/google_calendar_client.py`
  - `create_event`, `update_event` に `attachments` パラメータ追加
  - OAuth2スコープに `drive.file` を追加
- `src/fishing_forecast_gcal/application/usecases/sync_tide_usecase.py`
  - 画像生成・アップロード・URL取得のロジック追加
  - `_build_description` に画像セクション追加

---

## 検証計画

### 検証1: イベント本文での画像表示
- **目的**: Google Calendar がイベント本文内の画像URLをどう扱うか確認
- **手順**:
  1. テストカレンダーに手動でイベントを作成
  2. 本文にプレーンテキストのURL、HTML形式、Markdown形式を挿入
  3. Google Calendar（Web/モバイル）での表示を確認
- **期待結果**: URLがクリック可能、または画像がプレビュー表示される

### 検証2: 画像ホスティング（Imgur）
- **目的**: Imgurへのアップロードと公開URLの取得確認
- **手順**:
  1. ダミーのタイドグラフ画像を生成（matplotlib）
  2. Imgur API を使用してアップロード
  3. 公開URLを取得
  4. URLをブラウザで開いて画像が表示されることを確認
- **期待結果**: 画像が公開URLで表示される

### 検証3: Calendar API の attachments フィールド
- **目的**: Google Calendar API が attachments をどう扱うか確認
- **手順**:
  1. Google Calendar API のドキュメントで `attachments` の仕様を確認
  2. サンプルコードを参照
  3. 必要な権限スコープを確認
- **期待結果**: attachments の実装可能性が判明

---

## 次のステップ

POC完了後、採用方式に応じて以下のタスクに分割:

- **方式A採用の場合**:
  - タイドグラフ画像生成モジュールの実装（domain/services?）
  - 画像ホスティングクライアントの実装（infrastructure/clients）
  - SyncTideUseCaseへの統合
  
- **方式B採用の場合**:
  - Google Drive API クライアントの実装
  - GoogleCalendarClient の拡張
  - OAuth2スコープの更新
  - SyncTideUseCaseへの統合

---

## 備考

- このPOCは実装ではなく調査・検証が中心
- 画像生成ロジックの詳細は後続タスクで実装
- 既存の `[TIDE]`/`[FORECAST]`/`[NOTES]` セクション更新ルールを維持すること
- ユーザーが手動で追記した `[NOTES]` セクションは絶対に破壊しない
