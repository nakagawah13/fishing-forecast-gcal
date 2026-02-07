---
applyTo: "**"
---

# Git Workflow: Troubleshooting

このガイドラインは、**Gitのトラブルシューティングとコンフリクト解決**に関する手順を定義します。

## 関連ガイドライン

- **基本Gitワークフロー**: [git-workflow.instructions.md](./git-workflow.instructions.md)

---

## コンフリクト解決

### コンフリクトが発生する状況

```bash
# mainの最新を取得
git switch main
git pull origin main

# 作業ブランチをリベース
git switch feature/your-feature
git rebase main
# または
git merge main

# コンフリクトが発生
# Auto-merging file.py
# CONFLICT (content): Merge conflict in file.py
```

### コンフリクト解決手順

#### 1. コンフリクトの確認

```bash
# コンフリクトしているファイルを確認
git status

# コンフリクト箇所を確認
cat file.py
```

#### 2. コンフリクトマーカーの理解

```python
<<<<<<< HEAD (または現在のブランチ)
# あなたの変更
def calculate_rate(total, defect):
    return (defect / total) * 100
=======
# mainブランチの変更
def calculate_rate(total_count, defect_count):
    if total_count == 0:
        return 0.0
    return (defect_count / total_count) * 100
>>>>>>> main (またはマージ元のブランチ)
```

#### 3. コンフリクトの解決

```python
# マーカーを削除し、適切なコードを残す
# 両方の良い部分を統合
def calculate_rate(total_count, defect_count):
    """Calculate defect rate as percentage."""
    if total_count == 0:
        return 0.0
    return (defect_count / total_count) * 100
```

#### 4. 解決をマーク

```bash
# ファイルをステージング
git add file.py

# すべてのコンフリクトが解決されたら
git rebase --continue
# または（mergeの場合）
git commit
```

### 複雑なコンフリクトの対処

**取り消してやり直す**:

```bash
# リベース中止
git rebase --abort

# マージ中止
git merge --abort
```

**特定の変更を優先**:

```bash
# 自分の変更を優先（ours）
git checkout --ours file.py

# 相手の変更を優先（theirs）
git checkout --theirs file.py

# ステージング
git add file.py
```

---

## トラブルシューティング

### よくある問題と解決方法

#### 問題1: 間違ったブランチでコミットしてしまった

```bash
# コミットを取り消し（変更は保持）
git reset --soft HEAD~1

# 正しいブランチに切り替え
git switch correct-branch

# 再度コミット
git commit -m "feat: correct branch commit"
```

#### 問題2: プッシュ後にコミットメッセージを修正したい

```bash
# 最新コミットのメッセージを修正
git commit --amend -m "feat: corrected commit message"

# 強制プッシュ（注意: 共有ブランチでは避ける）
git push --force-with-lease
```

#### 問題3: 大きなファイルを誤ってコミットした

```bash
# 最新コミットから削除
git rm --cached large_file.dat
git commit --amend --no-edit

# .gitignoreに追加
echo "large_file.dat" >> .gitignore
git add .gitignore
git commit -m "chore: add large file to gitignore"
```

#### 問題4: リベース中に混乱した

```bash
# リベースを中止して最初からやり直す
git rebase --abort

# または、現在の状態を確認
git status
git log --oneline --graph --all
```

---

## クイックリファレンス

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
