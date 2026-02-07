---
applyTo: "**"
---

# Git Workflow Instructions (Core)

このガイドラインは、**Gitワークフローの基本操作**に特化したAI向けインストラクションです。

## このファイルの役割と対象範囲

### 対象範囲

このインストラクションは以下の内容を含みます:

- **Git基本操作**: ブランチ作成、切り替え、ファイル操作
- **ブランチ戦略**: ブランチタイプと命名規則
- **コミットメッセージ規約**: Conventional Commits準拠

### 関連ガイドライン

- **コミットプロセス**: [git-workflow-commit-process.instructions.md](./git-workflow-commit-process.instructions.md) - AI向けコミット作成の必須プロセス
- **PR作成**: [git-workflow-pr.instructions.md](./git-workflow-pr.instructions.md) - プルリクエストとレビュープロセス
- **トラブルシューティング**: [git-workflow-troubleshooting.instructions.md](./git-workflow-troubleshooting.instructions.md) - コンフリクト解決と問題対処
- **ML/AI実験管理**: [git-workflow-ml-experiments.instructions.md](./git-workflow-ml-experiments.instructions.md) - 実験管理とバージョニング
- **PR詳細**: [ai-pull-request.instructions.md](./ai-pull-request.instructions.md) - PR本文フォーマット
- **プロジェクト構造**: [ai-project-structure-core.instructions.md](./ai-project-structure-core.instructions.md) - ディレクトリ構造保護ルール
- **コード品質**: [ai-code-writing.instructions.md](./ai-code-writing.instructions.md) - コーディング規約

---

## ブランチ戦略

### ブランチタイプと命名規則

プロジェクトでは以下のブランチタイプを使用します。

#### 主要ブランチ

| ブランチ名 | 説明 | 保護設定 |
|-----------|------|----------|
| `main` | 本番環境のコード | 直接コミット禁止、PRのみ |
| `develop` | 開発統合ブランチ（使用する場合） | PRのみ |

#### 作業ブランチ

作業ブランチは以下の命名規則に従います:

```
<type>/<description>
```

**`<type>`の種類**:

| タイプ | 用途 | 例 |
|--------|------|-----|
| `feature` | 新機能の開発 | `feature/add-user-authentication` |
| `bugfix` | バグ修正 | `bugfix/correct-data-validation` |
| `experiment` | 実験的な実装・検証 | `experiment/test-new-algorithm` |
| `model` | モデル開発・改善 | `model/implement-lightgbm` |
| `train` | 訓練パイプライン | `train/add-cross-validation` |
| `eval` | 評価・検証 | `eval/add-metrics-calculation` |
| `data` | データ処理・前処理 | `data/add-feature-engineering` |
| `refactor` | リファクタリング | `refactor/optimize-query-performance` |
| `docs` | ドキュメント更新 | `docs/update-api-specification` |
| `test` | テスト追加・修正 | `test/add-unit-tests-for-validator` |
| `chore` | ビルド・ツール設定 | `chore/update-dependencies` |
| `config` | 設定ファイル変更 | `config/update-app-settings` |
| `perf` | パフォーマンス改善 | `perf/optimize-model-inference` |
| `style` | コードスタイル修正 | `style/format-python-files` |
| `infra` | インフラ整備 | `infra/setup-docker-environment` |

**`<description>`のルール**:

- 小文字のケバブケース（kebab-case）を使用
- 英語で簡潔に記述（3-5単語が目安）
- 変更の目的が明確にわかること
- 例: `add-defect-detection`, `correct-csv-parser`, `update-model-config`

#### 設定ファイル変更ブランチの詳細

`config/` タイプのブランチは、以下のような設定ファイル変更に使用します:

**開発環境設定**:
- `.vscode/settings.json`, `pyrightconfig.json`, `.editorconfig`
- 例: `config/update-vscode-settings`

**GitHub関連設定**:
- `.github/workflows/`, `.github/instructions/`
- 例: `config/add-ci-workflow`

**プロジェクト設定**:
- `pyproject.toml`, `pom.xml`, `requirements.txt`
- 例: `config/add-python-dependencies`

**アプリケーション設定**:
- `config/app_settings.json`, `config/schema.json`
- 例: `config/update-inference-threshold`

**ML/AI特有の設定**:
- モデル設定、ハイパーパラメータ設定
- 例: `config/tune-model-hyperparameters`

**品質管理・テスト設定**:
- `.pylintrc`, `pytest.ini`, `ruff.toml`
- 例: `config/update-linter-rules`

### ブランチ作成のワークフロー

#### 1. 最新の状態を取得

```bash
# mainブランチの最新状態を取得
git switch main
git pull origin main
```

#### 2. 作業ブランチを作成

```bash
# 新しいブランチを作成して切り替え
git switch -c feature/your-feature-name

# または、特定のコミットから作成
git switch -c bugfix/bug-fix-name <commit-hash>
```

#### 3. 変更を論理的な単位でコミット

```bash
# ファイルをステージング
git add <files>

# コミット（後述のコミットメッセージ規約に従う）
git commit -m "feat: add new feature description"
```

#### 4. リモートにプッシュ

```bash
# 初回プッシュ（upstream設定）
git push -u origin feature/your-feature-name

# 2回目以降
git push
```

---

## Gitブランチ操作

### ブランチ切り替え操作

#### `git switch` と `git checkout` の使い分け

**原則**: `git switch` を優先的に使用してください。

| コマンド | 用途 | 推奨度 |
|---------|------|--------|
| `git switch` | ブランチ切り替え専用 | ⭐⭐⭐ 推奨 |
| `git checkout` | ブランチ切り替え + ファイル復元（多機能） | △ 特定用途のみ |

**`git switch` の使用例**:

```bash
# 既存ブランチに切り替え
git switch main
git switch feature/my-feature

# 新しいブランチを作成して切り替え
git switch -c feature/new-feature

# リモートブランチをトラッキングして切り替え
git switch -c feature/remote-feature origin/feature/remote-feature

# 直前のブランチに戻る
git switch -
```

**`git checkout` を使う場合（特定用途のみ）**:

```bash
# ファイルを最新のコミット状態に復元
git checkout -- <file>

# 特定のコミットのファイルを取得
git checkout <commit-hash> -- <file>

# 注意: ブランチ切り替えには git switch を使用
```

**なぜ `git switch` を推奨するか**:

- ブランチ操作とファイル復元が明確に分離
- より直感的で誤操作が少ない
- Git 2.23以降の新しい標準コマンド

### Git技術的なファイル操作

ファイルの移動、削除、名前変更を行う際は、**Gitの履歴追跡を維持する**ために、以下のコマンドを必ず使用してください。

**重要**: プロジェクト構造の保護やディレクトリ作成に関するルールは [ai-project-structure-core.instructions.md](./ai-project-structure-core.instructions.md) を参照してください。

#### ファイル移動・名前変更

**必須**: `git mv` コマンドを使用

```bash
# ファイルを移動（履歴を保持）
git mv old/path/file.py new/path/file.py

# ファイル名を変更（履歴を保持）
git mv old_name.py new_name.py

# ディレクトリごと移動
git mv src/old_module/ src/new_module/
```

**理由**:
- Git履歴が保持され、ファイルの変更履歴を追跡可能
- `git log --follow` でリネーム後もファイル履歴を参照可能
- コードレビューで変更内容が明確になる

#### ファイル削除

**必須**: `git rm` コマンドを使用

```bash
# ファイルを削除
git rm file.py

# ディレクトリを削除
git rm -r directory/

# ファイルをGit管理から外すが実ファイルは残す
git rm --cached file.py
```

**理由**:
- 削除履歴がGitに記録される
- 削除理由をコミットメッセージで説明可能
- 必要に応じてファイルを復元可能

#### 推奨されない操作（禁止）

以下のコマンドは**使用しないでください**:

```bash
# ❌ 禁止: 通常のmvコマンド
mv old_file.py new_file.py
# 理由: Git履歴が途切れる

# ❌ 禁止: 通常のrmコマンド
rm file.py
# 理由: Git管理から削除されず不整合が発生

# ❌ 禁止: 直接ファイルシステム操作
mv src/utils/ src/utilities/
# 理由: Gitが変更を追跡できない
```

**例外**: `.gitignore` で除外されているファイル（一時ファイル、ビルド成果物など）は通常のコマンドで削除可能。

---

#### 大量ファイル操作時の注意

機械学習プロジェクトでは、大量のファイル移動・削除が発生することがあります。以下の点に注意してください。

- データファイルの整理時も`git mv` を使用
- 実験結果の移動時も`git mv` を使用し、履歴を保持
- 大量のファイルを一度に操作する場合、コミットを小分けにして履歴を明確に
- スクリプトで自動化する場合も、Gitコマンドを使用

---

## コミットメッセージの形式

### コミットメッセージ規約

このプロジェクトでは **Conventional Commits** 準拠のコミットメッセージを使用します。

#### 基本形式

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### `<type>` の種類

| タイプ | 説明 | 例 |
|--------|------|-----|
| `feat` | 新機能の追加 | `feat: add defect detection model` |
| `fix` | バグ修正 | `fix: correct CSV parsing error` |
| `model` | モデル開発・改善 | `model: implement lightgbm classifier` |
| `train` | 訓練パイプライン変更 | `train: add cross-validation` |
| `eval` | 評価・検証の追加・変更 | `eval: add confusion matrix calculation` |
| `data` | データ処理・前処理の変更 | `data: add feature scaling` |
| `docs` | ドキュメントのみの変更 | `docs: update API specification` |
| `style` | コードの動作に影響しないスタイル変更 | `style: format Python files with black` |
| `refactor` | バグ修正や機能追加を伴わないリファクタリング | `refactor: extract validation logic` |
| `perf` | パフォーマンス改善 | `perf: optimize model inference speed` |
| `test` | テストの追加・修正 | `test: add unit tests for DataValidator` |
| `build` | ビルドシステム・外部依存関係の変更 | `build: upgrade lightgbm to 4.0.0` |
| `ci` | CI設定ファイル・スクリプトの変更 | `ci: add GitHub Actions workflow` |
| `chore` | その他の変更（ビルドプロセス、補助ツールなど） | `chore: update .gitignore` |
| `revert` | 以前のコミットを取り消し | `revert: revert commit abc123` |

#### `<scope>` の指定（オプション）

スコープは変更の影響範囲を示します:

```
feat(trainer): add cross-validation support
fix(validator): handle missing column error
docs(api): update inference endpoint documentation
```

**スコープ例**:
- `trainer`: モデル訓練関連
- `validator`: データ検証関連
- `inference`: 推論関連
- `api`: API関連
- `config`: 設定ファイル
- `ui`: UIコンポーネント

#### `<description>` のルール

- **英語で記述**（プロジェクト標準）
- **小文字で開始**
- **命令形を使用**（"add" not "added", "fix" not "fixed"）
- **ピリオドで終わらない**
- **50文字以内を目標**
- **変更内容を簡潔に**

**良い例**:
```
feat: add ONNX model export functionality
fix: prevent null pointer in data loader
docs: clarify model training parameters
```

**悪い例**:
```
feat: Added new feature.  # 過去形、ピリオド付き
fix: Fix bug  # 曖昧
docs: update docs  # 不明瞭
```

#### `<body>` の記述（オプション）

複雑な変更の場合、本文で詳細を説明します:

```
feat: add automated model retraining pipeline

This commit introduces a scheduled retraining pipeline that:
- Monitors model performance metrics
- Triggers retraining when accuracy drops below threshold
- Automatically deploys improved models

Implementation uses APScheduler for scheduling and
includes comprehensive logging.
```

**本文のルール**:
- 概要行から1行空ける
- 72文字で折り返す
- 何を変更したかだけでなく、**なぜ**変更したかを説明
- 複数の段落に分けて説明可能

#### `<footer>` の記述（オプション）

重大な変更やIssue参照を記載:

```
feat: migrate to new configuration format

BREAKING CHANGE: Configuration file format has changed from JSON to YAML.
Users must migrate existing config/app_settings.json to config/app_settings.yaml.

Closes #123
Refs #456
```

**footerの用途**:
- `BREAKING CHANGE:` - 破壊的変更の説明
- `Closes #123` - Issueのクローズ
- `Refs #456` - 関連Issueの参照
- `Co-authored-by:` - 共同作成者の記載

### 改行とエスケープ規約

ターミナルでコミットメッセージを作成する際の注意点:

#### シングルラインメッセージ

```bash
# 基本形式
git commit -m "feat: add new feature"

# スコープ付き
git commit -m "fix(validator): handle empty dataframe"
```

#### マルチラインメッセージ

**方法1**: エディタを使用（推奨）

```bash
# デフォルトエディタが開く
git commit

# 特定のエディタを使用
git commit -e
```

**方法2**: Here-Doc を使用

```bash
git commit -F - <<MSG
feat: add model retraining pipeline

This commit introduces automated retraining:
- Monitors performance metrics
- Triggers retraining on degradation

Closes #123
MSG
```

**方法3**: 改行を含む文字列（bashの場合）

```bash
git commit -m "feat: add model retraining pipeline

This commit introduces automated retraining:
- Monitors performance metrics
- Triggers retraining on degradation

Closes #123"
```

### コミットメッセージの例

#### 新機能追加

```
feat: add real-time anomaly detection

Implement sliding window approach for real-time detection:
- Use z-score method with configurable threshold
- Buffer last N data points for baseline calculation
- Emit alerts when anomaly is detected

Performance: Processes 1000 data points in <100ms
```

#### バグ修正

```
fix: prevent division by zero in defect rate calculation

Add validation to check if total_count is zero before calculation.
Returns 0.0 for defect rate when no products are counted.

Closes #234
```

#### ドキュメント更新

```
docs: add training pipeline setup guide

Include step-by-step instructions for:
- Environment setup
- Data preparation
- Model training execution
- ONNX export process
```

#### リファクタリング

```
refactor: extract data validation into separate class

Move validation logic from DataLoader to new DataValidator class:
- Improves separation of concerns
- Enables unit testing of validation independently
- Makes validation reusable across components
```

#### 破壊的変更

```
feat!: change API response format to JSON

BREAKING CHANGE: Inference API now returns JSON instead of CSV.

Before:
  timestamp,value,prediction
  2025-12-06T10:00:00,42.5,0

After:
  {"timestamp": "2025-12-06T10:00:00", "value": 42.5, "prediction": 0}

Clients must update their parsers to handle JSON format.

Refs #567
```

**注**: AI向けコミット作成の詳細プロセスについては [git-workflow-commit-process.instructions.md](./git-workflow-commit-process.instructions.md) を参照してください。

---

## まとめ

### 重要なポイントの再確認

1. **ブランチ命名**: `<type>/<description>` 形式を厳守
2. **コミットメッセージ**: Conventional Commits準拠
3. **ファイル操作**: `git mv`, `git rm` を使用（履歴保持）
4. **機密情報**: 絶対にコミットしない
5. **PR**: 小さく、明確に、テスト済み
6. **レビュー**: 建設的で具体的なコメント

### クイックリファレンス

```bash
# 新規ブランチ作成
git switch -c feature/new-feature

# コミット
git add .
git commit -m "feat: add new feature"

# プッシュ
git push -u origin feature/new-feature

# ファイル移動（履歴保持）
git mv old.py new.py

# 最新mainと同期
git switch main && git pull origin main
git switch - && git rebase main

# コンフリクト解決
git add <resolved-files>
git rebase --continue
```
