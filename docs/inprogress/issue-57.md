# Issue #57: 潮回り期間中央日のマーカー

**ステータス**: In Progress  
**担当**: AI Assistant  
**開始日**: 2026-02-10  
**Issue**: <https://github.com/nakagawah13/fishing-forecast-gcal/issues/57>

---

## 背景・目的

大潮/小潮などは幅を持たせて判定しているが、期間の中心日が分かりにくい。
カレンダー本文に中央日のマーカーを表示し、ユーザーが釣行計画を立てやすくする。

---

## 要件

### 機能要件

1. **連続期間の判定**
   - 同じ潮回りが連続する期間を特定する
   - 例: 大潮が2/7～2/9の3日間続く場合、2/8が中央日

2. **中央日の表示**
   - `[TIDE]` セクションに「⭐ 中央日」の表示を追加
   - 中央日のイベントのみに表示（他の日には表示しない）

3. **偶数日の扱い**
   - 連続期間が偶数日の場合、前半側の日を中央日とする
   - 例: 2/7～2/10の4日間 → 2/8を中央日とする（2日目）

### 非機能要件

- 既存の `[TIDE]` 表示を大きく崩さない（行数を最小限に）
- 記号は絵文字1文字で統一（⭐）

---

## 設計方針

### アーキテクチャ上の課題

現在の `SyncTideUseCase` は日次で独立してイベントを生成しているため、
連続期間の判定ができない。以下の設計変更を行う：

1. **ドメインサービスの追加**
   - `TidePeriodAnalyzer` クラスを新規作成
   - 複数日分の潮回りデータから連続期間を解析する責務を持つ

2. **UseCaseの拡張**
   - `execute()` で対象日付の前後数日分のデータを取得
   - `TidePeriodAnalyzer` で期間解析
   - 中央日判定結果を `_format_tide_section()` に渡す

### 実装詳細

#### 1. ドメインサービス: `TidePeriodAnalyzer`

**責務**: 潮回りの連続期間を解析し、中央日を特定する

**インターフェース**:
```python
class TidePeriodAnalyzer:
    @staticmethod
    def is_midpoint_day(
        target_date: date,
        tide_data_list: list[tuple[date, TideType]]
    ) -> bool:
        """指定日が潮回り期間の中央日かを判定
        
        Args:
            target_date: 判定対象の日付
            tide_data_list: 複数日分の潮回りデータ（日付昇順）
            
        Returns:
            True: 中央日である
            False: 中央日でない
        """
```

**アルゴリズム**:
1. `target_date` を含む連続期間を抽出
2. 期間の開始日と終了日を特定
3. 中央日を計算（期間日数が偶数の場合は前半側）
4. `target_date` が中央日と一致するかを返す

#### 2. UseCaseの変更: `SyncTideUseCase`

**変更点**:
```python
def execute(self, location: Location, target_date: date) -> None:
    # 1. 前後数日分の潮汐データを取得（例: ±3日）
    date_range = self._get_date_range(target_date, days_before=3, days_after=3)
    tide_data_list = [
        (d, self._tide_repo.get_tide_data(location, d))
        for d in date_range
    ]
    
    # 2. 中央日判定
    is_midpoint = TidePeriodAnalyzer.is_midpoint_day(
        target_date,
        [(d, tide.tide_type) for d, tide in tide_data_list]
    )
    
    # 3. 対象日のデータ取得
    tide = next(tide for d, tide in tide_data_list if d == target_date)
    
    # 4. イベント本文生成（中央日フラグを渡す）
    tide_section = self._format_tide_section(tide, is_midpoint=is_midpoint)
    ...
```

#### 3. フォーマッターの変更: `_format_tide_section()`

**変更点**:
```python
@staticmethod
def _format_tide_section(tide: Tide, is_midpoint: bool = False) -> str:
    lines = []
    
    # 中央日マーカーの追加（先頭行）
    if is_midpoint:
        lines.append("⭐ 中央日")
    
    # 満潮のリスト
    ...（既存ロジック）
```

---

## 実装計画

### Phase 1: ドメインサービス実装
- [ ] `domain/services/tide_period_analyzer.py` を新規作成
- [ ] `TidePeriodAnalyzer.is_midpoint_day()` を実装
- [ ] ユニットテスト（10ケース以上）

### Phase 2: UseCase拡張
- [ ] `SyncTideUseCase.execute()` に期間判定ロジックを追加
- [ ] `_format_tide_section()` に `is_midpoint` 引数を追加
- [ ] 既存のユニットテストを更新

### Phase 3: 統合テスト
- [ ] E2Eテストで実際のカレンダー表示を確認
- [ ] 複数の連続期間パターンをテスト

---

## テスト戦略

### ユニットテスト: `TidePeriodAnalyzer`

1. **単一期間のケース**
   - 3日間連続（大潮-大潮-大潮） → 2日目が中央日
   - 4日間連続（大潮×4） → 2日目が中央日

2. **複数期間のケース**
   - 大潮×3 → 中潮×2 → 小潮×3
   - 各期間の中央日が正しく判定される

3. **境界値のケース**
   - 1日のみ（単独） → 自身が中央日
   - 期間の開始日/終了日 → 中央日でない

4. **エッジケース**
   - データが不足（前後のデータがない） → False
   - target_dateがリストに存在しない → False

### 統合テスト: `SyncTideUseCase`

1. **前後データ取得**
   - 対象日±3日のデータが正しく取得される

2. **中央日判定の統合**
   - 中央日のイベントに「⭐ 中央日」が表示される
   - 非中央日のイベントには表示されない

3. **既存機能の非破壊**
   - [NOTES]セクションが保持される
   - イベントタイトル・絵文字が正しく生成される

### E2Eテスト

- 実際のカレンダーに登録して、中央日マーカーの表示を目視確認

---

## 影響範囲

### 新規ファイル
- `src/fishing_forecast_gcal/domain/services/tide_period_analyzer.py`
- `tests/unit/domain/services/test_tide_period_analyzer.py`

### 変更ファイル
- `src/fishing_forecast_gcal/application/usecases/sync_tide_usecase.py`
  - `execute()` メソッド
  - `_format_tide_section()` メソッド
- `tests/unit/application/usecases/test_sync_tide_usecase.py`
  - 既存テストの更新
  - 新規テストの追加

---

## リスク・懸念事項

### パフォーマンス
- 毎回前後数日分のデータを取得するため、API呼び出しが増える
- **対策**: キャッシュ機能は後続フェーズで検討（現段階では許容）

### データ不足時の挙動
- 期間の開始日・終了日では前後データが不足する可能性
- **対策**: データ不足時は `is_midpoint=False` を返す（安全側に倒す）

### 既存テストへの影響
- `_format_tide_section()` のシグネチャ変更により、既存テストが壊れる
- **対策**: デフォルト引数（`is_midpoint=False`）で後方互換性を維持

---

## 実装結果・変更点

（実装完了後に追記）

