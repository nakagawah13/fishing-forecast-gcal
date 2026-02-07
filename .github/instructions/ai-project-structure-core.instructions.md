---
applyTo: "**"
---

# AIプロジェクト構造保護ガイドライン（コア）

## 概要

このファイルは、AIがプロジェクトでファイル・ディレクトリを作成する際の**最重要ルール**を定義します。一貫性のある高品質なプロジェクト構造を維持するための必須要件です。

## 関連ガイドライン

- [ai-project-structure-ml.instructions.md](./ai-project-structure-ml.instructions.md): ML/AI特有の構造ルール
- [ai-project-structure-maintenance.instructions.md](./ai-project-structure-maintenance.instructions.md): 保守・修正プロセス
- [ai-code-writing.instructions.md](./ai-code-writing.instructions.md): コード内容とスタイル

## 最重要ルール (MUST)

### 重複ディレクトリの作成禁止

以下のような重複パターンは **絶対に避ける** こと:

#### 1. 同一機能の重複

```
❌ 禁止: src/utils/ と src/utilities/ と src/helpers/
❌ 禁止: src/services/ と src/service/（単数形・複数形混在）
❌ 禁止: src/models/ と src/model/（単数形・複数形混在）
```

#### 2. 異なる命名の同一目的

```
❌ 禁止: src/components/ と src/widgets/
❌ 禁止: src/validators/ と src/validation/
❌ 禁止: tests/unit/ と tests/unittest/
```

#### 3. 階層の不整合

```
❌ 禁止: config/ と src/config/（ルート階層と重複）
❌ 禁止: docs/ と src/docs/（ルート階層と重複）
❌ 禁止: src/api/routes/ と src/routes/（api内と外で重複）
```

#### 4. 言語混在による重複

```
❌ 禁止: src/models/ と src/modelos/（英語とスペイン語）
❌ 禁止: src/models/ と src/modèles/（英語とフランス語）
```

#### 5. 略語と完全形の混在

```
❌ 禁止: src/config/ と src/configuration/
❌ 禁止: src/docs/ と src/documentation/
❌ 禁止: src/db/ と src/database/
```

#### 6. 技術スタック間の重複

```
❌ 禁止:
java-app/src/main/java/com/factory/ml/util/
python-trainer/src/util/
```

### 重複チェック手順 (MUST)

新しいディレクトリを作成する前に、**必ず以下を確認**:

1. **既存ディレクトリの確認**
   - `tree` コマンドで既存構造を視覚的に把握
   - `grep_search` で類似名称のディレクトリを検索

2. **名称の統一性チェック**
   - 単数形/複数形の統一
   - 略語/完全形の統一
   - 言語の統一（英語推奨）

3. **階層構造の整合性確認**
   - 同じ目的のディレクトリが異なる階層に存在しないか
   - 親子関係が適切か

## 必須事前確認プロセス (MUST)

### STOP-SEARCH-ANALYZE-CONFIRM-CREATE

新規ファイル・ディレクトリ作成時は、以下を**必ず遵守**:

#### 1. STOP（停止）

- 即座に作成せず、必要性と配置を再考する
- 「本当にこの場所に必要か？」を自問する
- 衝動的な作成を避ける

#### 2. SEARCH（既存構造検索）

**必須の検索**:
- `tree` コマンドでプロジェクト全体の構造を視覚的に把握
- `grep_search` で類似名称のディレクトリ・ファイルを検索
- `file_search` で既存の同目的ファイルを探索
- `semantic_search` で機能的に類似するコードを検出

#### 3. ANALYZE（分析）

**分析観点**:
- 既存ディレクトリと目的が重複していないか
- プロジェクトの命名規則に従っているか
- 配置する階層は論理的に正しいか
- ディレクトリの責任範囲は明確か

**判断基準**:
```
✅ 作成すべき: 既存で代替不可、明確な責任範囲、規約準拠
❌ 作成不可: 既存で代替可能、目的が曖昧、命名不統一
```

#### 4. CONFIRM（最終確認）

**確認項目**:
- [ ] 既存の類似ディレクトリを再利用できないか確認済み
- [ ] 命名規則に準拠しているか確認済み
- [ ] 配置する階層が論理的に正しいか確認済み
- [ ] 重複チェック手順を完了している

#### 5. CREATE（作成）

上記すべてのステップ完了後のみ作成可能。

**作成時の注意**:
- `create_file` または `create_directory` を使用
- 作成後は git status で変更を確認
- 作成理由をユーザーに報告

### プロセス適用例

**良い例:**
```
要求: 「バリデーション用のディレクトリを作りたい」

1. STOP: 即座に作成せず立ち止まる
2. SEARCH: tree コマンドで確認 → src/validators/ が既存
3. ANALYZE: validators/ は同じ目的 → 重複になる
4. CONFIRM: 既存で十分 → 新規作成不要
5. CREATE: 作成せず、既存ディレクトリを使用

結果: ✅ 重複回避、構造の一貫性維持
```

**悪い例:**
```
要求: 「バリデーション用のディレクトリを作りたい」

1. STOP: スキップ（即座に作成判断）
2. SEARCH: スキップ（既存構造を調査せず）
3. ANALYZE: スキップ（重複チェックなし）
4. CONFIRM: スキップ（妥当性確認なし）
5. CREATE: src/validation/ を作成

結果: ❌ src/validators/ と重複、構造破綻
```

### プロセス遵守の重要性

このプロセスを遵守することで:
- **重複ディレクトリの防止**: 構造の一貫性を維持
- **保守性の向上**: 将来的な混乱を回避
- **チーム協調**: 他の開発者が理解しやすい構造
- **品質の担保**: 高品質なプロジェクト構造を保証

**警告**: このプロセスをスキップすると、プロジェクト構造が破綻し、長期的な保守コストが増大します。必ず遵守してください。

## 作成禁止ディレクトリ（MUST）

### 1. 一時的・実験的ディレクトリ

```
❌ 絶対禁止
temp/, tmp/, test_folder/, experiment/, sandbox/
scratch/, draft/, backup/, old/, archive_temp/
```

**代替案**: システムの`/tmp`を使用、`.gitignore`で除外

### 2. 曖昧な目的のディレクトリ

```
❌ 絶対禁止
misc/, other/, stuff/, things/, various/, random/, general/
```

**代替案**: 明確な責任範囲を持つディレクトリ名を使用

### 3. 個人名・チーム名のディレクトリ

```
❌ 絶対禁止
nakagawa/, tanaka_san/, team_a/, my_code/, johns_stuff/
```

**代替案**: 機能や責任範囲に基づいたディレクトリ名

### 4. 非標準的な命名のディレクトリ

```
❌ 絶対禁止
new_feature/, v2/, feature-branch/, 試験/, テスト用/
```

**代替案**: プロジェクトの命名規則に従った英語名

## クイックチェックリスト

### 新規ディレクトリ作成前チェックリスト

- [ ] **STOP**: 立ち止まって必要性を再考した
- [ ] **SEARCH**: `tree` コマンドで既存構造を視覚的に確認した
- [ ] **SEARCH**: `grep_search` で類似名称を検索した
- [ ] **ANALYZE**: 既存ディレクトリで代替できないか検討した
- [ ] **CONFIRM**: 階層配置が論理的に正しいか確認した
- [ ] **CONFIRM**: 作成禁止ディレクトリに該当しないか確認した

**すべて ✓ の場合のみ作成可能**

### 重複パターンクイックチェック

以下に該当する場合は作成禁止:

- [ ] 単数形/複数形の混在（`model/` と `models/`）
- [ ] 略語/完全形の混在（`config/` と `configuration/`）
- [ ] 同一目的の異名（`utils/` と `helpers/`）
- [ ] 階層の不整合（`config/` と `src/config/`）
- [ ] 言語の混在（`models/` と `modelos/`）

### 作成禁止ディレクトリクイックチェック

- [ ] `temp/`, `tmp/`, `test_folder/`（一時的）
- [ ] `misc/`, `other/`, `stuff/`（曖昧）
- [ ] 個人名・チーム名
- [ ] 非英語名

**1つでも該当する場合は作成不可**

## 重要な警告

このプロセスをスキップすると、プロジェクト構造が破綻し、長期的な保守コストが増大します。**必ず遵守**してください。
