# Issue #76: タイドグラフ画像のカレンダー表示方式POC

**ステータス**: ✅ Completed
**担当**: AI Assistant
**作成日**: 2026-02-11
**更新日**: 2026-02-11
**関連Issue**: #76
**フェーズ**: Phase 1.9

**後続 Issue（実装フェーズ）**:
- [#78](https://github.com/nakagawah13/fishing-forecast-gcal/issues/78): Google Drive/Calendar API 添付機能の実装（ST-1 + ST-2）
- [#79](https://github.com/nakagawah13/fishing-forecast-gcal/issues/79): タイドグラフ画像生成サービスの実装（ST-3）
- [#80](https://github.com/nakagawah13/fishing-forecast-gcal/issues/80): SyncTideUseCase への画像添付統合（ST-4）
- [#81](https://github.com/nakagawah13/fishing-forecast-gcal/issues/81): 古い Drive 画像の定期削除コマンド（ST-5）

---

## 概要

タイドグラフ画像を Google Calendar イベントに表示する方式を比較検証し、**方式B（Google Drive 添付）** を採用して実装する。

### 方式決定

| 方式 | 概要 | 結論 |
|------|------|------|
| 方式A | イベント本文に画像URL挿入（Imgur等） | ❌ 不採用 |
| **方式B** | **Google Drive + Calendar attachments** | **✅ 採用** |

**選定理由**: Google アカウントのみで完結し、外部サービスのアカウント作成が不要

---

## API 仕様調査結果

### Google Calendar API - attachments フィールド

**リファレンス**: https://developers.google.com/calendar/api/v3/reference/events

| 項目 | 仕様 |
|------|------|
| `attachments[]` | イベントのファイル添付リスト |
| `attachments[].fileUrl` | 添付ファイルの URL リンク（**書き込み可能、追加時必須**） |
| `attachments[].title` | 添付ファイルのタイトル |
| `attachments[].mimeType` | MIME タイプ |
| `attachments[].iconLink` | アイコン URL（サードパーティのみ変更可） |
| `attachments[].fileId` | Drive ファイル ID（**読み取り専用**） |
| 最大添付数 | **25 個/イベント** |
| 必須パラメータ | `supportsAttachments=true` をクエリパラメータに設定 |

**`fileUrl` の形式**: Drive API の `Files` リソースの `alternateLink` プロパティと同じ形式
- 例: `https://drive.google.com/file/d/{fileId}/view?usp=drivesdk`

**認可スコープ**: `https://www.googleapis.com/auth/calendar` （既存スコープで十分）

### Google Drive API - files.create

**リファレンス**: https://developers.google.com/drive/api/v3/reference/files/create

| 項目 | 仕様 |
|------|------|
| アップロード URI | `POST https://www.googleapis.com/upload/drive/v3/files` |
| 最大ファイルサイズ | 5,120 GB |
| アップロード方式 | `media`（シンプル）/ `multipart`（メタデータ+メディア）/ `resumable` |
| 認可スコープ | `drive` / `drive.appdata` / **`drive.file`**（最小権限） |

**`drive.file` スコープ**: アプリが作成したファイルのみアクセス可能（最小権限の原則に適合）

### Google Drive API - permissions.create

画像をカレンダー添付として使用するには、ファイルを閲覧可能にする必要がある:

```json
{
  "role": "reader",
  "type": "anyone"
}
```

### 必要な OAuth2 スコープ（変更箇所）

```python
SCOPES = [
    "https://www.googleapis.com/auth/calendar",      # 既存
    "https://www.googleapis.com/auth/drive.file",     # 新規追加
]
```

**注意**: スコープ追加時は既存の `token.json` を削除して再認証が必要

---

## 既存実装の確認

### 1. GoogleCalendarClient（インフラ層）

**ファイル**: `src/fishing_forecast_gcal/infrastructure/clients/google_calendar_client.py`

**既存メソッド**:
- `create_event()`: イベント作成（extendedProperties サポート済み）
- `get_event()`: イベント取得
- `update_event()`: イベント更新

**現状の制限**:
- ❌ イベント添付（`attachments`）未対応
- ❌ `supportsAttachments=true` パラメータ未設定
- ❌ Drive API 未統合

### 2. SyncTideUseCase（アプリケーション層）

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

## 実装計画

### アーキテクチャ配置

レイヤードアーキテクチャに基づく配置:

```
Infrastructure Layer:
  clients/
    google_calendar_client.py  ← attachments 対応拡張
    google_drive_client.py     ← 新規: Drive API クライアント
  repositories/
    calendar_repository.py     ← attachments パラメータ伝搬

Domain Layer:
  services/
    tide_graph_service.py      ← 新規: タイドグラフ画像生成サービス
  repositories/
    image_repository.py        ← 新規: 画像リポジトリインターフェース

Application Layer:
  usecases/
    sync_tide_usecase.py       ← 画像生成+添付の統合
```

### サブタスク分割

#### ST-1: Google Drive API クライアント実装
**新規ファイル**: `src/fishing_forecast_gcal/infrastructure/clients/google_drive_client.py`

**責務**:
- OAuth2 認証（既存の credentials/token を共有）
- ファイルアップロード（`files.create` / multipart upload）
- 公開リンク生成（`permissions.create` → `role: reader, type: anyone`）
- ファイル削除（`files.delete`）
- ファイル一覧取得（`files.list` + クエリフィルタ）

**メソッド設計**:
```python
class GoogleDriveClient:
    def authenticate(self) -> None: ...
    def upload_file(self, file_path: Path, folder_id: str | None = None) -> str:
        """ファイルをアップロードし、公開URLを返す"""
    def delete_file(self, file_id: str) -> None: ...
    def list_files(self, folder_id: str | None = None, query: str | None = None) -> list[dict]: ...
    def get_or_create_folder(self, folder_name: str) -> str:
        """指定名のフォルダを取得または作成し、folder_id を返す"""
```

**フォルダ管理**:
- 専用フォルダ（デフォルト名: `fishing-forecast-tide-graphs`）にアップロード
- ユーザーの他のファイルと混在しない
- フォルダが存在しない場合は初回アップロード時に自動作成
- `get_or_create_folder()` でフォルダ ID を取得し、`upload_file()` の `folder_id` に渡す
- ST-5 クリーンアップは同フォルダ内のみを対象とする（安全性）

**テスト要件**:
- Upload のモック API テスト
- Permission 設定のモック API テスト
- Delete のモック API テスト
- フォルダ作成・取得のモック API テスト
- 認証失敗時のエラーハンドリング

---

#### ST-2: GoogleCalendarClient の attachments 対応拡張
**変更ファイル**: `src/fishing_forecast_gcal/infrastructure/clients/google_calendar_client.py`

**変更内容**:
1. `create_event()` に `attachments` パラメータを追加
2. `update_event()` に `attachments` パラメータを追加
3. API 呼び出し時に `supportsAttachments=true` を設定
4. OAuth2 スコープに `drive.file` を追加

**API 呼び出し変更例**:
```python
# Before
self.service.events().insert(calendarId=calendar_id, body=event_body).execute()

# After
self.service.events().insert(
    calendarId=calendar_id,
    body=event_body,
    supportsAttachments=True,
).execute()
```

**attachments 形式**:
```python
event_body["attachments"] = [
    {
        "fileUrl": "https://drive.google.com/file/d/{fileId}/view?usp=drivesdk",
        "title": "tide_graph_20260215.png",
        "mimeType": "image/png",
    }
]
```

**テスト要件**:
- attachments 付きイベント作成のモックテスト
- attachments 付きイベント更新のモックテスト
- `supportsAttachments=true` パラメータの確認
- attachments なしの後方互換性テスト

---

#### ST-3: タイドグラフ画像生成サービス
**新規ファイル**: `src/fishing_forecast_gcal/domain/services/tide_graph_service.py`

**責務**:
- 潮汐データからタイドグラフ画像を生成
- matplotlib + seaborn + matplotlib-fontja によるプロット
- 一時ファイルとして PNG 出力

**日本語フォント対応**:
- `matplotlib-fontja`（IPAexゴシック同梱）でシステムフォント不要で日本語表示
- seaborn の `set_theme()` 後に `matplotlib_fontja.japanize()` を呼ぶ必要がある
  （seaborn がデフォルトフォントで上書きするため）
- リンターの F401 警告回避: `matplotlib_fontja.japanize()` を明示的に呼ぶ

```python
import matplotlib_fontja
import seaborn as sns

sns.set_theme()
matplotlib_fontja.japanize()  # seaborn のフォント上書き後に再適用
```

**メソッド設計**:
```python
class TideGraphService:
    def generate_graph(
        self,
        date: date,
        tide_events: list[TideEvent],
        hourly_heights: list[float],
        location_name: str,
        tide_type: TideType,
    ) -> Path:
        """タイドグラフ画像を生成し、一時ファイルパスを返す"""
```

**画像仕様**:

| 項目 | 仕様 | 備考 |
|------|------|------|
| アスペクト比 | **1:1（スクエア）** | スマホ表示に最適化 |
| サイズ | 6×6 インチ | 150dpi → 900×900px |
| 解像度 | 150 dpi | モバイル表示に十分、ファイルサイズを抑制 |
| ファイルサイズ | **100KB 以下**目標 | Drive 転送・表示の効率化 |
| フォーマット | PNG | 透過不要だが可逆圧縮で品質維持 |
| 配色 | **ダークモード基調** | 早朝・夕方の確認を想定 |

**カラーパレット（ダークモード）**:

| 要素 | 色 | カラーコード |
|------|-----|-------------|
| 背景 | ダークネイビー | `#0d1117` |
| 潮位曲線 | シアン | `#58a6ff` |
| 海面フィル | シアン半透明 | `#58a6ff` (alpha=0.15) |
| 満潮マーカー | オレンジ | `#f0883e` |
| 干潮マーカー | ティール | `#3fb950` |
| 時合い帯 | ゴールド半透明 | `#d29922` (alpha=0.15) |
| グリッド線 | グレー | `#30363d` |
| テキスト（軸・ラベル） | ライトグレー | `#c9d1d9` |
| タイトル | ホワイト | `#f0f6fc` |

**描画要素**:
1. **潮位曲線**: 24 時間分の潮位を滑らかにプロット
2. **海面フィル**: 曲線から下を半透明で塗りつぶし（満ち引きの直感的表現）
3. **満干潮マーカー**: ● ドット + テキストラベル（時刻 + 潮位）
   - 例: `06:12` / `162cm` を 2 行で表示
4. **時合い帯ハイライト**: 満潮前後の時合い帯を半透明の縦帯で可視化
5. **グリッド**: 低コントラストのグレーで 24h 軸に沿って表示
6. **タイトル（画像内）**: `{地名} {YYYY年MM月DD日}` + 潮回り絵文字（例: `🔴大潮`）
7. **X 軸**: 0〜24 時（3 時間刻み）
8. **Y 軸**: 潮位 (cm)

**ファイル命名規則**:
```
tide_graph_{location_id}_{YYYYMMDD}.png
```
- 例: `tide_graph_tk_20260215.png`
- `location_id` で地点を識別、Drive 上でソート時にグルーピングされる

**テスト要件**:
- 画像ファイルが正常に生成されること
- ファイルサイズが 100KB 以下であること
- ダークモード配色が正しく適用されていること
- 満干潮アノテーション（時刻・潮位）が含まれていること
- 地名がタイトルに含まれていること
- 時合い帯ハイライトが正しい時間帯に表示されること
- 異常データ（空リスト等）でのエラーハンドリング

---

#### ST-4: SyncTideUseCase への統合
**変更ファイル**: `src/fishing_forecast_gcal/application/usecases/sync_tide_usecase.py`

**変更内容**:
1. `TideGraphService` と `GoogleDriveClient` を DI で注入
2. `execute()` メソッド内で画像生成 → Drive アップロード → Calendar 添付
3. 画像生成・アップロードが失敗してもイベント同期は継続（graceful degradation）
4. 設定で画像添付の ON/OFF を制御可能

**処理フロー**:
```
1. 潮汐データ取得（既存）
2. イベント本文生成（既存）
3. タイドグラフ画像生成（新規）
4. Google Drive にアップロード（新規）
5. attachments 付きでイベント作成/更新（拡張）
6. 一時ファイル削除（新規）
```

**テスト要件**:
- 画像添付有効時のフロー正常動作テスト
- 画像添付無効時の後方互換性テスト
- 画像生成失敗時の graceful degradation テスト
- Drive アップロード失敗時の graceful degradation テスト

---

#### ST-5: 古い画像の定期削除
**新規ファイル**: `src/fishing_forecast_gcal/application/usecases/cleanup_drive_images_usecase.py`

**責務**:
- Google Drive 上の古いタイドグラフ画像を定期的に削除
- 保持期間を設定で制御可能（デフォルト: 30 日）
- CLI コマンドとして実行可能

**メソッド設計**:
```python
class CleanupDriveImagesUseCase:
    def execute(self, retention_days: int = 30) -> int:
        """保持期間を超えた画像を削除し、削除件数を返す"""
```

**削除ロジック**:
1. Drive API の `files.list` で対象フォルダ内のファイルを取得
2. `createdTime` が保持期間を超えたファイルをフィルタ
3. `files.delete` で一括削除
4. 削除件数をログ出力

**テスト要件**:
- 保持期間内のファイルが削除されないこと
- 保持期間を超えたファイルが削除されること
- Drive にファイルがない場合のハンドリング

---

## 設定ファイル変更

### config.yaml への追加項目

```yaml
tide_graph:
  enabled: true                                        # タイドグラフ画像の生成・添付を有効化
  drive_folder_name: "fishing-forecast-tide-graphs"     # Drive 上の専用フォルダ名
  retention_days: 30                                    # 古い画像の保持期間（日）
  dpi: 150                                              # 画像解像度
  figsize: [6, 6]                                       # 画像サイズ [幅, 高さ] インチ（スクエア）
  dark_mode: true                                       # ダークモード配色
```

---

## 受け入れ条件（POC スコープ）

- [x] 方式A/方式B の比較メモ
- [x] 方式選定の結論と理由（方式B採用）
- [x] API 仕様調査（Calendar attachments, Drive files.create, permissions.create）
- [x] POC スクリプトによるタイドグラフ画像生成検証
- [x] 画像仕様の確定（スクエア 6×6, ダークモード, アノテーション）
- [x] 日本語フォント対応の検証（matplotlib-fontja）
- [x] 実装計画の策定（ST-1〜ST-5 サブタスク分割）
- [x] 後続 Issue の起票（#78, #79, #80, #81）

**注**: 実装タスク（ST-1〜ST-5）は後続 Issue #78〜#81 で追跡

---

## スコープ

### スコープ内
- タイドグラフ画像の生成（matplotlib + seaborn）
- Google Drive API クライアント実装
- Calendar API の attachments 対応
- SyncTideUseCase への統合
- 古い画像の定期削除
- 設定ファイルでの ON/OFF 制御

### スコープ外
- 本番運用のスケール設計（画像生成の最適化、キャッシュ）
- 気象予報機能の変更（Phase 2 タスク）
- ライト/ダークモードの動的切替（初版はダークモード固定）

---

## 実装予定ファイル

### 新規作成
- `src/fishing_forecast_gcal/infrastructure/clients/google_drive_client.py`
- `src/fishing_forecast_gcal/domain/services/tide_graph_service.py`
- `src/fishing_forecast_gcal/domain/repositories/image_repository.py`
- `src/fishing_forecast_gcal/application/usecases/cleanup_drive_images_usecase.py`
- `tests/infrastructure/clients/test_google_drive_client.py`
- `tests/domain/services/test_tide_graph_service.py`
- `tests/application/usecases/test_cleanup_drive_images_usecase.py`

### 変更
- `src/fishing_forecast_gcal/infrastructure/clients/google_calendar_client.py`
  - `create_event`, `update_event` に `attachments` パラメータ追加
  - `supportsAttachments=true` を API 呼び出しに追加
  - OAuth2 スコープに `drive.file` を追加
- `src/fishing_forecast_gcal/application/usecases/sync_tide_usecase.py`
  - 画像生成 → Drive アップロード → 添付の統合
- `config/config.yaml.template`
  - `tide_graph` セクション追加
- `pyproject.toml`
  - `matplotlib-fontja` を依存追加（日本語フォント対応）
  - `google-api-python-client` は既存（Drive API 含む）

### POC 用（完了済み）
- `scripts/poc_tide_graph_image.py`: ダミータイドグラフ画像生成
- `scripts/poc_upload_imgur.py`: Imgur アップロードテスト（方式A検証用、不要に）
- `docs/tide_graph_image_poc.md`: 調査結果・比較メモ

---

## 備考

- 画像生成・アップロードが失敗してもイベント同期は継続（graceful degradation）
- 既存の `[TIDE]`/`[FORECAST]`/`[NOTES]` セクション更新ルールを維持
- ユーザーが手動で追記した `[NOTES]` セクションは絶対に破壊しない
- `google-api-python-client` は Calendar API と Drive API の両方をカバー（追加パッケージ不要）
- `matplotlib-fontja` で日本語フォント対応（IPAexゴシック同梱、システムフォント不要）
- seaborn 併用時は `set_theme()` 後に `matplotlib_fontja.japanize()` を呼ぶこと
- スコープ追加時は既存の `token.json` を削除して再認証が必要（README に手順追記）
