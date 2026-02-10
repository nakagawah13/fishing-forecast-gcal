"""JMA tidal observation station data.

Provides the JMAStation dataclass and a complete dictionary of all 70
JMA tidal observation stations with official coordinates and reference levels.

気象庁の潮汐観測地点データを提供します。
全70地点の公式座標・基準面情報を定義しています。

Data Source:
    気象庁 潮汐観測地点一覧表 (2026年版)
    https://www.data.jma.go.jp/kaiyou/db/tide/genbo/station.php
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JMAStation:
    """JMA tidal observation station information.

    気象庁の潮汐観測地点情報。
    座標および基準面は気象庁公式の観測地点一覧表の値を使用。

    Attributes:
        id: Station code (2-character, e.g. 'TK').
            (地点記号、2文字)
        name: Station name in Japanese.
              (地点名、日本語)
        latitude: Station latitude in decimal degrees (north).
                  (緯度、度単位の10進数表記)
        longitude: Station longitude in decimal degrees (east).
                   (経度、度単位の10進数表記)
        ref_level_tp_cm: Observation reference level relative to T.P. in cm.
                         (観測基準面の標高、T.P.基準、cm単位)
                         Source: 気象庁観測地点一覧表「観測基準面の標高(cm)」列

    Reference:
        https://www.data.jma.go.jp/kaiyou/db/tide/genbo/station.php
    """

    id: str
    name: str
    latitude: float
    longitude: float
    ref_level_tp_cm: float


def _dms(degrees: int, minutes: int) -> float:
    """Convert degrees and minutes to decimal degrees.

    度分表記を10進数の度に変換する。
    気象庁一覧表の緯度・経度は度分表記のため統一的に変換する。

    Args:
        degrees: Degree part.
                 (度)
        minutes: Minute part.
                 (分)

    Returns:
        Decimal degrees rounded to 3 decimal places.
        (小数第3位で四捨五入した10進数の度)
    """
    return round(degrees + minutes / 60, 3)


# 全70地点 - 気象庁観測地点一覧表 (2026年版) に基づく
# https://www.data.jma.go.jp/kaiyou/db/tide/genbo/station.php
#
# 緯度・経度は公式の度分表記から _dms() で変換
# ref_level_tp_cm は「観測基準面の標高(cm)」列の値
# 地点番号順に配列
STATIONS: dict[str, JMAStation] = {
    # --- 北海道 ---
    # 1: 稚内
    "WN": JMAStation("WN", "稚内", _dms(45, 24), _dms(141, 41), -165.0),
    # 2: 網走
    "AS": JMAStation("AS", "網走", _dms(44, 1), _dms(144, 17), -150.5),
    # 3: 花咲
    "HN": JMAStation("HN", "花咲", _dms(43, 17), _dms(145, 34), -213.4),
    # 4: 釧路
    "KR": JMAStation("KR", "釧路", _dms(42, 59), _dms(144, 22), -189.6),
    # 5: 函館
    "HK": JMAStation("HK", "函館", _dms(41, 47), _dms(140, 43), -155.5),
    # 6: 小樽
    "B3": JMAStation("B3", "小樽", _dms(43, 11), _dms(141, 1), -210.2),
    # --- 東北 ---
    # 7: 下北
    "SH": JMAStation("SH", "下北", _dms(41, 22), _dms(141, 14), -265.4),
    # 8: 宮古
    "MY": JMAStation("MY", "宮古", _dms(39, 39), _dms(141, 59), -128.2),
    # 9: 大船渡
    "OF": JMAStation("OF", "大船渡", _dms(39, 1), _dms(141, 45), -255.7),
    # 10: 鮎川
    "AY": JMAStation("AY", "鮎川", _dms(38, 18), _dms(141, 30), -260.9),
    # 11: 小名浜
    "ON": JMAStation("ON", "小名浜", _dms(36, 56), _dms(140, 54), -171.4),
    # 70: 深浦 (※旧コード FK は「福岡」と誤記されていたが、公式は「深浦」)
    "FK": JMAStation("FK", "深浦", _dms(40, 39), _dms(139, 56), -129.8),
    # --- 関東 ---
    # 12: 布良
    "MR": JMAStation("MR", "布良", _dms(34, 55), _dms(139, 50), -138.1),
    # 13: 東京
    "TK": JMAStation("TK", "東京", _dms(35, 39), _dms(139, 46), -188.4),
    # 14: 岡田
    "OK": JMAStation("OK", "岡田", _dms(34, 47), _dms(139, 23), -154.2),
    # 15: 三宅島
    "MJ": JMAStation("MJ", "三宅島", _dms(34, 3), _dms(139, 33), -416.5),
    # 16: 父島
    "CC": JMAStation("CC", "父島", _dms(27, 6), _dms(142, 12), -186.0),
    # 17: 南鳥島
    "MC": JMAStation("MC", "南鳥島", _dms(24, 17), _dms(153, 59), -196.1),
    # 18: 小田原
    "OD": JMAStation("OD", "小田原", _dms(35, 14), _dms(139, 9), -344.9),
    # --- 東海 ---
    # 19: 石廊崎
    "G9": JMAStation("G9", "石廊崎", _dms(34, 38), _dms(138, 53), -375.6),
    # 20: 内浦
    "UC": JMAStation("UC", "内浦", _dms(35, 1), _dms(138, 53), -152.1),
    # 21: 清水港
    "SM": JMAStation("SM", "清水港", _dms(35, 1), _dms(138, 31), -158.3),
    # 22: 御前崎
    "OM": JMAStation("OM", "御前崎", _dms(34, 37), _dms(138, 13), -193.7),
    # 23: 舞阪
    "MI": JMAStation("MI", "舞阪", _dms(34, 41), _dms(137, 37), -235.4),
    # 24: 赤羽根
    "I4": JMAStation("I4", "赤羽根", _dms(34, 36), _dms(137, 11), -359.1),
    # 25: 名古屋
    "NG": JMAStation("NG", "名古屋", _dms(35, 5), _dms(136, 53), -201.0),
    # 26: 鳥羽
    "TB": JMAStation("TB", "鳥羽", _dms(34, 29), _dms(136, 49), -281.0),
    # 27: 尾鷲
    "OW": JMAStation("OW", "尾鷲", _dms(34, 5), _dms(136, 12), -147.3),
    # 28: 熊野
    "KN": JMAStation("KN", "熊野", _dms(33, 56), _dms(136, 10), -238.1),
    # --- 紀伊半島 ---
    # 29: 浦神
    "UR": JMAStation("UR", "浦神", _dms(33, 34), _dms(135, 54), -138.6),
    # 30: 串本
    "KS": JMAStation("KS", "串本", _dms(33, 29), _dms(135, 46), -161.1),
    # 31: 白浜
    "SR": JMAStation("SR", "白浜", _dms(33, 41), _dms(135, 23), -314.2),
    # 32: 御坊
    "GB": JMAStation("GB", "御坊", _dms(33, 51), _dms(135, 10), -266.0),
    # 33: 和歌山
    "WY": JMAStation("WY", "和歌山", _dms(34, 13), _dms(135, 9), -92.5),
    # --- 近畿 ---
    # 34: 淡輪
    "TN": JMAStation("TN", "淡輪", _dms(34, 20), _dms(135, 11), -185.1),
    # 35: 大阪
    "OS": JMAStation("OS", "大阪", _dms(34, 39), _dms(135, 26), -354.2),
    # 36: 神戸
    "KB": JMAStation("KB", "神戸", _dms(34, 41), _dms(135, 11), -168.2),
    # 37: 洲本
    "ST": JMAStation("ST", "洲本", _dms(34, 21), _dms(134, 54), -185.6),
    # --- 中国・四国 ---
    # 38: 宇野
    "UN": JMAStation("UN", "宇野", _dms(34, 29), _dms(133, 57), -176.1),
    # 39: 松山
    "MT": JMAStation("MT", "松山", _dms(33, 52), _dms(132, 43), -214.7),
    # 40: 高松
    "TA": JMAStation("TA", "高松", _dms(34, 21), _dms(134, 3), -189.8),
    # 41: 小松島
    "KM": JMAStation("KM", "小松島", _dms(34, 1), _dms(134, 35), -191.5),
    # 42: 阿波由岐
    "AW": JMAStation("AW", "阿波由岐", _dms(33, 46), _dms(134, 36), -264.7),
    # 43: 室戸岬
    "MU": JMAStation("MU", "室戸岬", _dms(33, 16), _dms(134, 10), -292.6),
    # 44: 高知
    "KC": JMAStation("KC", "高知", _dms(33, 30), _dms(133, 34), -95.9),
    # 45: 土佐清水
    "TS": JMAStation("TS", "土佐清水", _dms(32, 47), _dms(132, 58), -156.1),
    # 46: 宇和島
    "UW": JMAStation("UW", "宇和島", _dms(33, 14), _dms(132, 33), -207.8),
    # --- 九州 ---
    # 47: 佐伯
    "X5": JMAStation("X5", "佐伯", _dms(32, 57), _dms(131, 58), -452.9),
    # 48: 油津
    "AB": JMAStation("AB", "油津", _dms(31, 35), _dms(131, 25), -141.3),
    # 49: 鹿児島
    "KG": JMAStation("KG", "鹿児島", _dms(31, 36), _dms(130, 34), -201.5),
    # 50: 枕崎
    "MK": JMAStation("MK", "枕崎", _dms(31, 16), _dms(130, 18), -245.8),
    # 51: 種子島
    "TJ": JMAStation("TJ", "種子島", _dms(30, 28), _dms(130, 58), -378.4),
    # 52: 奄美
    "O9": JMAStation("O9", "奄美", _dms(28, 19), _dms(129, 32), -219.0),
    # --- 沖縄 ---
    # 53: 那覇
    "NH": JMAStation("NH", "那覇", _dms(26, 13), _dms(127, 40), -258.0),
    # 54: 南大東
    "DJ": JMAStation("DJ", "南大東", _dms(25, 52), _dms(131, 14), -557.6),
    # 55: 石垣
    "IS": JMAStation("IS", "石垣", _dms(24, 20), _dms(124, 10), -172.4),
    # 56: 与那国
    "YJ": JMAStation("YJ", "与那国", _dms(24, 27), _dms(122, 57), -374.0),
    # --- 九州(有明海・長崎) ---
    # 57: 苓北
    "RH": JMAStation("RH", "苓北", _dms(32, 28), _dms(130, 2), -412.1),
    # 58: 大浦
    "OU": JMAStation("OU", "大浦", _dms(32, 59), _dms(130, 13), -371.5),
    # 59: 口之津
    "KT": JMAStation("KT", "口之津", _dms(32, 36), _dms(130, 12), -339.6),
    # 60: 長崎
    "NS": JMAStation("NS", "長崎", _dms(32, 44), _dms(129, 52), -274.3),
    # 61: 福江
    "FE": JMAStation("FE", "福江", _dms(32, 42), _dms(128, 51), -263.8),
    # 62: 対馬比田勝
    "N5": JMAStation("N5", "対馬比田勝", _dms(34, 39), _dms(129, 29), -192.1),
    # --- 山陰・日本海 ---
    # 63: 浜田 (※旧コード HA は「博多」と誤記されていたが、公式は「浜田」)
    "HA": JMAStation("HA", "浜田", _dms(34, 54), _dms(132, 4), -91.3),
    # 64: 境
    "SK": JMAStation("SK", "境", _dms(35, 33), _dms(133, 15), -115.0),
    # 65: 西郷
    "SA": JMAStation("SA", "西郷", _dms(36, 12), _dms(133, 20), -106.6),
    # 66: 舞鶴
    "MZ": JMAStation("MZ", "舞鶴", _dms(35, 29), _dms(135, 23), -132.1),
    # 67: 能登
    "SZ": JMAStation("SZ", "能登", _dms(37, 30), _dms(137, 9), -121.8),
    # 68: 富山
    "TY": JMAStation("TY", "富山", _dms(36, 46), _dms(137, 13), -107.6),
    # 69: 佐渡
    "S0": JMAStation("S0", "佐渡", _dms(38, 19), _dms(138, 31), -151.7),
}
