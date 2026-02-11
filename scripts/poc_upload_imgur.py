#!/usr/bin/env python3
"""POC: Imgurアップロードテストスクリプト

このスクリプトは、Imgur APIを使用して画像をアップロードし、公開URLを取得します。
Phase 1.9 POC用の検証スクリプトです。

使用方法:
1. Imgur API Client ID を取得: https://api.imgur.com/oauth2/addclient
2. 環境変数を設定: export IMGUR_CLIENT_ID="your_client_id"
3. スクリプト実行: uv run python scripts/poc_upload_imgur.py
"""

import os
from pathlib import Path

import httpx


def upload_to_imgur(image_path: Path, client_id: str) -> str | None:
    """Imgurに画像をアップロード

    Args:
        image_path: 画像ファイルのパス
        client_id: Imgur API Client ID

    Returns:
        アップロードされた画像の公開URL（失敗時はNone）
    """
    if not image_path.exists():
        print(f"❌ 画像ファイルが見つかりません: {image_path}")
        return None

    # Imgur API エンドポイント
    url = "https://api.imgur.com/3/image"

    # ヘッダー
    headers = {
        "Authorization": f"Client-ID {client_id}",
    }

    # 画像ファイルを読み込み
    with open(image_path, "rb") as f:
        image_data = f.read()

    # リクエスト
    try:
        print(f"📤 Imgurにアップロード中: {image_path.name}...")
        response = httpx.post(
            url,
            headers=headers,
            files={"image": image_data},
            timeout=30.0,
        )
        response.raise_for_status()

        # レスポンス解析
        data = response.json()
        if data.get("success"):
            image_url = data["data"]["link"]
            print("✅ アップロード成功!")
            print(f"   公開URL: {image_url}")
            return image_url
        else:
            print(f"❌ アップロード失敗: {data}")
            return None

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTPエラー: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        print(f"❌ アップロードエラー: {e}")
        return None


def main() -> None:
    """メイン処理"""
    # Client IDを環境変数から取得
    client_id = os.environ.get("IMGUR_CLIENT_ID")
    if not client_id:
        print("❌ IMGUR_CLIENT_ID 環境変数が設定されていません。")
        print("\n設定方法:")
        print('  export IMGUR_CLIENT_ID="your_client_id"')
        print("\nImgur API Client IDの取得:")
        print("  https://api.imgur.com/oauth2/addclient")
        return

    # テスト用の画像パス
    image_path = Path("output/poc_tide_graphs/tide_graph_20260215.png")

    # アップロード
    url = upload_to_imgur(image_path, client_id)

    if url:
        print("\n次のステップ:")
        print(f"1. ブラウザで画像を確認: {url}")
        print("2. Google Calendarイベント本文にURLを挿入")
        print("3. プレビュー表示の確認")


if __name__ == "__main__":
    main()
