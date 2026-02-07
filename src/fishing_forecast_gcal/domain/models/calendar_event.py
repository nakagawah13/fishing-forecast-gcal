"""カレンダーイベント関連のドメインモデル

このモジュールはGoogle カレンダーに登録するイベントを定義します。
- CalendarEvent: イベントID、タイトル、本文、日付などの情報
"""

import re
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class CalendarEvent:
    """Google カレンダーに登録するイベント

    潮汐情報と予報情報を統合したカレンダーイベントを表現します。

    Attributes:
        event_id: イベントID（calendar_id + location_id + date から生成されるハッシュ）
        title: イベントタイトル（例: "潮汐 東京湾 (大潮)"）
        description: イベント本文（Markdown形式、セクション分割）
        date: 対象日（終日イベント）
        location_id: 地点の不変ID

    Raises:
        ValueError: バリデーションエラー時

    Note:
        本文フォーマット例:
        ```
        [TIDE]
        - 満潮: 06:12 (162cm)
        - 干潮: 12:34 (58cm)
        - 時合い: 04:12-08:12

        [FORECAST]
        - 風速: 5m/s
        - 風向: 北
        - 気圧: 1012hPa

        [NOTES]
        （ユーザー手動追記欄）
        ```
    """

    event_id: str
    title: str
    description: str
    date: date
    location_id: str

    def __post_init__(self) -> None:
        """インスタンス化後のバリデーション"""
        # event_idの検証
        if not self.event_id or not self.event_id.strip():
            raise ValueError("event_id must not be empty")

        # titleの検証
        if not self.title or not self.title.strip():
            raise ValueError("title must not be empty")

        if len(self.title) > 50:
            raise ValueError(
                f"title must be 50 characters or less, got {len(self.title)}"
            )

        # location_idの検証
        if not self.location_id or not self.location_id.strip():
            raise ValueError("location_id must not be empty")

    def has_valid_sections(self) -> bool:
        """本文が推奨セクション形式であるかを確認

        Returns:
            True: [TIDE], [FORECAST], [NOTES] セクションが存在する
            False: セクションが欠落している、または形式が異なる

        Note:
            これは推奨チェックであり、必須ではありません。
            既存の手動作成イベントとの互換性のため、柔軟に対応します。
        """
        required_sections = ["[TIDE]", "[FORECAST]", "[NOTES]"]
        return all(section in self.description for section in required_sections)

    def extract_section(self, section_name: str) -> str | None:
        """指定されたセクションの内容を抽出

        Args:
            section_name: セクション名（例: "TIDE", "FORECAST", "NOTES"）

        Returns:
            セクションの内容（セクション名を除く）。セクションが存在しない場合は None。

        Example:
            >>> event.extract_section("TIDE")
            "- 満潮: 06:12 (162cm)\\n- 干潮: 12:34 (58cm)\\n- 時合い: 04:12-08:12"
        """
        pattern = rf"\[{section_name}\](.*?)(?=\n\[|$)"
        match = re.search(pattern, self.description, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def update_section(self, section_name: str, new_content: str) -> "CalendarEvent":
        """指定されたセクションの内容を更新した新しいインスタンスを返す

        Args:
            section_name: 更新するセクション名（例: "TIDE", "FORECAST"）
            new_content: 新しい内容（セクション名を除く）

        Returns:
            更新された新しい CalendarEvent インスタンス

        Raises:
            ValueError: セクションが存在しない場合

        Note:
            frozenなので新しいインスタンスを返します。
        """
        if not self.extract_section(section_name):
            raise ValueError(f"Section [{section_name}] does not exist in description")

        # セクションを更新
        pattern = rf"(\[{section_name}\])(.*?)(?=\n\[|$)"
        updated_description = re.sub(
            pattern,
            rf"\1\n{new_content}",
            self.description,
            flags=re.DOTALL
        )

        # 新しいインスタンスを返す（dataclassのreplaceを使用）
        from dataclasses import replace
        return replace(self, description=updated_description)
