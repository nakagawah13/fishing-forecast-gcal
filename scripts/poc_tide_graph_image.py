#!/usr/bin/env python3
"""POC: タイドグラフ画像生成スクリプト

このスクリプトは、タイドグラフ画像（ダミー）を生成します。
Phase 1.9 POC用の検証スクリプトです。
"""

from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib_fontja
import numpy as np

# 日本語フォント適用（IPAexゴシック同梱、システムフォント不要）
matplotlib_fontja.japanize()


def generate_dummy_tide_graph(
    date: datetime,
    output_path: Path,
    location_name: str = "東京",
) -> None:
    """ダミーのタイドグラフ画像を生成

    Args:
        date: 対象日
        output_path: 出力ファイルパス
        location_name: 地点名
    """
    # 24時間分のタイムスタンプ
    hours = np.linspace(0, 24, 100)

    # ダミーの潮汐データ（正弦波で近似）
    # 実際は調和解析の結果を使用
    tide_height = 100 + 60 * np.sin(2 * np.pi * hours / 12.42)  # 半日周潮

    # グラフ生成
    _fig, ax = plt.subplots(figsize=(10, 4))

    # 潮位曲線
    ax.plot(hours, tide_height, linewidth=2, color="#1f77b4")
    ax.fill_between(hours, 0, tide_height, alpha=0.3, color="#1f77b4")

    # NOTE: 本番実装（TideGraphService）では以下の仕様を適用する:
    # - アスペクト比: 1:1 スクエア (6x6 インチ, 900x900px @150dpi)
    # - 配色: ダークモード基調 (背景 #0d1117, 曲線 #58a6ff)
    # - 満干潮アノテーション: ●マーカー + 時刻/潮位ラベル
    #   - 満潮: #f0883e (オレンジ), 干潮: #3fb950 (ティール)
    # - 時合い帯ハイライト: #d29922 (alpha=0.15)
    # - タイトル: {地名} {MM/DD} + 潮回り絵文字
    # - ファイル名: tide_graph_{location_id}_{YYYYMMDD}.png
    # - Drive フォルダ: fishing-forecast-tide-graphs（専用）

    # グリッド
    ax.grid(True, alpha=0.3, linestyle="--")

    # 軸ラベル
    ax.set_xlabel("時刻", fontsize=10)
    ax.set_ylabel("潮位 (cm)", fontsize=10)
    ax.set_title(
        f"{location_name} タイドグラフ - {date.strftime('%Y年%m月%d日')}",
        fontsize=12,
        fontweight="bold",
    )

    # X軸の範囲とラベル
    ax.set_xlim(0, 24)
    ax.set_xticks(range(0, 25, 3))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 25, 3)])

    # Y軸の範囲
    ax.set_ylim(0, 200)

    # レイアウト調整
    plt.tight_layout()

    # 保存
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"✅ タイドグラフ画像を生成しました: {output_path}")


def main() -> None:
    """メイン処理"""
    # 出力ディレクトリ
    output_dir = Path("output/poc_tide_graphs")

    # テスト用の日付
    test_date = datetime(2026, 2, 15)

    # 画像生成
    output_path = output_dir / f"tide_graph_{test_date.strftime('%Y%m%d')}.png"
    generate_dummy_tide_graph(test_date, output_path, location_name="東京")

    print("\n次のステップ:")
    print(f"1. 生成された画像を確認: {output_path}")
    print("2. Imgurへのアップロードテスト（scripts/poc_upload_imgur.py）")
    print("3. Google Calendarでの表示確認")


if __name__ == "__main__":
    main()
