---
applyTo: "**"
---

# Git Workflow: AI Commit Process (MUST)

このガイドラインは、**AIがコミットメッセージを作成する際の必須プロセス**を定義します。

## 関連ガイドライン

- **基本Gitワークフロー**: [git-workflow.instructions.md](./git-workflow.instructions.md)
- **PR作成**: [ai-pull-request.instructions.md](./ai-pull-request.instructions.md)

---

## AI向けコミット作成プロセス (MUST)

AIがコミットメッセージを作成する際は、以下のプロセスを**必ず遵守**してください。

### 必須ステップ

#### 1. 変更内容の詳細確認（必須）

コミットメッセージを作成する前に、**必ず以下のコマンドを実行**して変更内容を把握してください:

```bash
# ステージング前の変更を確認
git diff

# ステージング済みの変更を確認
git diff --cached

# 変更統計（ファイル数、追加/削除行数）
git diff --stat
# または
git diff --cached --stat

# 変更ファイルのリストのみ
git diff --name-only
# または
git diff --cached --name-only
```

**重要**: `git diff` の結果を確認せずにコミットメッセージを作成することは**禁止**です。

#### 2. 変更の複雑さに応じたメッセージ形式の選択

**最小限の変更の場合（一行メッセージ許可）**:

以下の条件を**すべて満たす**場合のみ、一行のコミットメッセージが許可されます:

- 変更ファイルが1-2個以内
- 変更内容が単純明快（typo修正、コメント追加、単一の小さな修正）
- 追加説明が不要なほど自明

```bash
# 許可される一行メッセージの例
git commit -m "fix: correct typo in README"
git commit -m "docs: add missing comma in docstring"
git commit -m "style: remove trailing whitespace"
```

**通常の変更（複数行メッセージ必須）**:

上記以外のすべての変更は、**必ず複数行のコミットメッセージ**を作成してください:

- 変更ファイルが3個以上
- 複数の機能追加・修正がある
- 変更の理由や背景の説明が必要
- リファクタリング、新機能、バグ修正など

```bash
# エディタを使用（推奨）
git commit

# または複数行文字列を使用
git commit -m "feat: add type hints and docstrings to trainer module

- Add Google Style docstrings to all public functions
- Add type hints for function arguments and return values
- Add module-level docstring explaining purpose
- Improve code readability with better variable names

This improves code maintainability and enables better IDE support
for type checking and autocompletion."
```

#### 3. コミットメッセージの構成

**概要行（1行目）**:
- `<type>[optional scope]: <description>` の形式
- 50文字以内
- 英語、小文字開始、命令形、ピリオドなし

**本文（3行目以降）**:
- 概要行から1行空ける
- 72文字で折り返す
- 以下を含める:
  - **何を変更したか**（箇条書き推奨）
  - **なぜ変更したか**（背景・理由）
  - **どのような影響があるか**（必要に応じて）

**フッター（最後）**:
- Issue参照: `Closes #123`, `Refs #456`
- 破壊的変更: `BREAKING CHANGE: 説明`

### コミット作成の判断フロー

```
変更を確認
  ↓
git diff / git diff --cached を実行
  ↓
変更内容を分析
  ↓
┌─────────────────────────────────────┐
│ 変更は最小限？                      │
│ - 1-2ファイル以内                   │
│ - 単純明快な変更                    │
│ - 説明不要なほど自明                │
└─────────────────────────────────────┘
  ↓               ↓
 YES             NO
  ↓               ↓
一行メッセージ    複数行メッセージ（必須）
  ↓               ↓
git commit -m   git commit (エディタ)
"type: desc"    または複数行文字列
```

### 悪い例と良い例

**❌ 悪い例: git diff なしで推測**

```bash
# 変更内容を確認せずにコミット
git add .
git commit -m "refactor: improve code"  # 曖昧で詳細不明
```

**❌ 悪い例: 複数の変更を一行で済ます**

```bash
# 5ファイルに変更があるのに一行メッセージ
git commit -m "feat: add features"  # 何を追加したか不明
```

**✅ 良い例: git diff で確認後、詳細なメッセージ**

```bash
# 1. 変更内容を確認
git diff --cached --stat
# python-trainer/src/trainer/data_loader.py     | 25 +++++++++++++++++
# python-trainer/src/trainer/preprocessor.py   | 18 ++++++++++--
# python-trainer/src/trainer/model_trainer.py  | 32 +++++++++++++++------
# 3 files changed, 65 insertions(+), 10 deletions(-)

git diff --cached
# (詳細な変更内容を確認)

# 2. 変更内容に基づいて複数行メッセージを作成
git commit -m "refactor: add type hints and docstrings to trainer module

- Add Google Style docstrings to DataLoader, Preprocessor, ModelTrainer
- Add type hints for all function arguments and return values
- Add module-level docstrings explaining each file's purpose
- Improve variable naming for better clarity

This improves code maintainability and enables better IDE support
for type checking and autocompletion. All existing functionality
remains unchanged."
```

**✅ 良い例: 最小限の変更は一行**

```bash
# 1. 変更内容を確認
git diff --cached
# diff --git a/README.md b/README.md
# -This is a machien learning system.
# +This is a machine learning system.

# 2. 単純なtypo修正なので一行メッセージOK
git commit -m "docs: fix typo in README (machien -> machine)"
```

### チェックリスト

コミット前に以下を確認:

- [ ] `git diff` または `git diff --cached` を実行して変更内容を確認した
- [ ] 変更が最小限でない場合、複数行メッセージを作成した
- [ ] 概要行は Conventional Commits 形式に準拠している
- [ ] 本文に変更内容の詳細を箇条書きで記載した
- [ ] 本文に変更理由を説明した
- [ ] 関連するIssueがあれば参照を追加した

---

## Git管理対象

### バージョン管理すべきファイル

以下のファイルは必ず Git で管理します:

**ソースコード**:
- `*.py`, `*.java`, `*.js`, `*.ts` など
- すべてのアプリケーションコード

**設定ファイル**:
- `config/*.json` - アプリケーション設定
- `pyproject.toml`, `pom.xml` - プロジェクト設定
- `requirements.txt`, `setup.py` - Python依存関係
- `.github/workflows/*.yml` - CI/CD設定

**ドキュメント**:
- `README.md`, `docs/*.md` - すべてのドキュメント
- `docs/api_specification.md` - API仕様
- `docs/design_spec.md` - 設計仕様

**テストコード**:
- `*Test.java`, `test_*.py` - ユニットテスト
- `tests/` - テストディレクトリ

**インストラクションファイル**:
- `.github/instructions/*.instructions.md` - AI向けガイドライン

### Git管理対象外（`.gitignore`で除外）

以下のファイルは Git で管理しません:

**ビルド成果物**:
- `*.class`, `*.pyc`, `__pycache__/`
- `target/` (Java)
- `dist/`, `build/`

**機械学習モデル**:
- `models/current/*.onnx` - 学習済みモデル（大容量）
- `models/archive/*.onnx` - アーカイブモデル
- **理由**: サイズが大きく、Git LFSや専用ストレージで管理すべき

**実験結果・ログ**:
- `experiments/*/` - 実験ログ
- `mlruns/` - MLflow実験データ
- `*.log` - ログファイル

**データファイル**:
- `data/input/*.csv` - 入力データ
- `data/output/*.csv` - 出力データ
- **理由**: データは外部ストレージで管理し、READMEで取得方法を記載

**IDE・エディタ設定（個人設定）**:
- `.vscode/` (チーム共有する場合は例外)
- `.idea/`
- `*.swp`, `*.swo`

**OS生成ファイル**:
- `.DS_Store` (macOS)
- `Thumbs.db` (Windows)

**環境変数・機密情報**:
- `.env` - 環境変数ファイル
- `*.key`, `*.pem` - 秘密鍵
- **重要**: 絶対にコミットしない

---

## データとプライバシー

### 機密情報の取り扱い

**絶対にコミットしてはいけないもの**:

1. **認証情報**:
   - APIキー、トークン
   - データベースパスワード
   - 秘密鍵、証明書

2. **個人情報**:
   - 顧客データ
   - 従業員情報
   - 生産データ（実データ）

3. **機密設定**:
   - 本番環境の接続情報
   - 内部IPアドレス、ポート番号

4. **データファイル（機密性・サイズの観点）**:
   - **実データ**: 本番環境から取得した実際の生産データ
   - **サンプルデータ**: 実データから抽出したサンプル（個人情報含む場合）
   - **アノテーションデータ**: 手動でラベル付けした大容量データ
   - **理由**: プライバシー保護、リポジトリサイズ肥大化防止
   - **代替策**: データストレージ（S3、GCS等）で管理し、READMEにアクセス方法を記載

### 機密情報の管理方法

**環境変数を使用**:

```python
# ❌ 禁止: ハードコード
api_key = "sk-1234567890abcdef"

# ✅ 推奨: 環境変数
import os
api_key = os.environ.get("API_KEY")
```

**設定ファイルのテンプレート化**:

```bash
# テンプレートをバージョン管理
config/app_settings.template.json

# 実際の設定は.gitignoreで除外
config/app_settings.local.json
```

**万が一コミットしてしまった場合**:

```bash
# 1. 即座にキーを無効化
# 2. 履歴から削除（慎重に実行）
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch path/to/secret/file" \
  --prune-empty --tag-name-filter cat -- --all

# 3. チームに通知
```
