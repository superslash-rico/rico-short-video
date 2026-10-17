#!/usr/bin/env python3
"""Read a UTF-8 spoken script and estimate Chinese finished-video density.

No network, subprocesses, source-corpus access, or file writes. Use --help.
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path

LOW_RATE = 300.0
HIGH_RATE = 330.0
REFERENCE_RATE = 316.2138099842073
START = "<!-- SPOKEN_START -->"
END = "<!-- SPOKEN_END -->"


def nonnegative_minutes(value):
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("时长必须是数字") from exc
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError("时长必须是有限的非负分钟数")
    return number


def positive_minutes(value):
    number = nonnegative_minutes(value)
    if number == 0:
        raise argparse.ArgumentTypeError("目标时长必须大于0")
    return number


def extract_spoken_text(text):
    """Keep spoken content; remove only documented, unambiguous metadata."""
    text = text.lstrip("\ufeff")
    if START in text or END in text:
        if text.count(START) != 1 or text.count(END) != 1:
            raise ValueError("正文标记必须各有一个：SPOKEN_START 和 SPOKEN_END")
        a = text.index(START) + len(START)
        b = text.index(END)
        if b < a:
            raise ValueError("SPOKEN_END 必须在 SPOKEN_START 后面")
        text = text[a:b]

    text = re.sub(r"<!--[\s\S]*?-->", "", text)
    text = re.sub(r"【非口播[：:][^】]*】", "", text)
    kept = []
    fence_char = None
    fence_length = 0
    for line in text.splitlines():
        fence = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            marker, tail = fence.groups()
            if fence_char is None:
                fence_char, fence_length = marker[0], len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_length and not tail.strip():
                fence_char = None
                fence_length = 0
            continue
        if fence_char is not None:
            continue
        if re.match(r"^\s{0,3}#{1,6}\s+", line):
            continue
        line = re.sub(r"^\s*(?:[-+*]|\d+[.)])\s+", "", line)
        line = re.sub(r"!\[[^\]]*\]\([^\n)]*\)", "", line)
        line = re.sub(r"\[([^\]]*)\]\([^\n)]*\)", r"\1", line)
        kept.append(line)
    if fence_char is not None:
        raise ValueError("存在未闭合代码块；请先整理为纯口播正文")
    return "\n".join(kept)


def measure(text, target_minutes=None, extra_silent_minutes=0.0):
    if not math.isfinite(extra_silent_minutes) or extra_silent_minutes < 0:
        raise ValueError("额外静默时长必须是有限非负数")
    if target_minutes is not None:
        if not math.isfinite(target_minutes) or target_minutes <= 0:
            raise ValueError("目标时长必须是有限正数")
        if extra_silent_minutes >= target_minutes:
            raise ValueError("额外静默时长必须小于目标总时长")
    spoken = extract_spoken_text(text)
    hanzi = len(re.findall(r"[\u4e00-\u9fff]", spoken))
    english = re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*", spoken)
    numeric = re.findall(r"[0-9]+(?:[.,][0-9]+)*", spoken)
    result = {
        "spoken_hanzi": hanzi,
        "english_word_tokens": len(english),
        "numeric_tokens": len(numeric),
        "alphanumeric_characters": len(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]", spoken)),
        "planning_hanzi_per_finished_minute": {"low": LOW_RATE, "high": HIGH_RATE, "reference": round(REFERENCE_RATE, 3)},
        "extra_silent_minutes": extra_silent_minutes,
        "estimated_finished_minutes": None,
        "target_budget": None,
        "notes": ["按历史中文课程成片有效密度估算，已包含样本通常停顿与操作；不是净发声语速或精确计时。"],
    }
    if hanzi:
        result["estimated_finished_minutes"] = {
            "low": round(hanzi / HIGH_RATE + extra_silent_minutes, 3),
            "high": round(hanzi / LOW_RATE + extra_silent_minutes, 3),
            "reference": round(hanzi / REFERENCE_RATE + extra_silent_minutes, 3),
        }
    else:
        result["notes"].append("没有可计数汉字，无法用中文模型估算朗读时长。")
    if english or numeric:
        result["notes"].append("英语词与阿拉伯数字已单列，未折算为汉字；密集出现时需实际试读校准。")
    if target_minutes is not None:
        available = target_minutes - extra_silent_minutes
        low = math.floor(available * LOW_RATE)
        high = math.ceil(available * HIGH_RATE)
        status = "within_range" if low <= hanzi <= high else ("below_range" if hanzi < low else "above_range")
        result["target_budget"] = {
            "target_total_minutes": target_minutes,
            "density_model_minutes": round(available, 3),
            "planned_hanzi_low": low,
            "planned_hanzi_high": high,
            "planned_hanzi_reference": round(available * REFERENCE_RATE),
            "hanzi_budget_status": status,
        }
    return result


def main():
    parser = argparse.ArgumentParser(description="统计口播正文汉字、英语词与数字，按Rico历史中文成片密度估算字数与时长。")
    parser.add_argument("script", nargs="?", default="-", help="UTF-8正文文件；- 为标准输入（默认）")
    parser.add_argument("--minutes", type=positive_minutes, help="目标总时长，单位分钟")
    parser.add_argument("--extra-silent-minutes", type=nonnegative_minutes, default=0.0, help="额外明确留出的静默区间；不要填通常停顿或边操作边说的时间")
    parser.add_argument("--json", action="store_true", help="输出JSON统计")
    args = parser.parse_args()
    try:
        raw = sys.stdin.read() if args.script == "-" else Path(args.script).read_text(encoding="utf-8-sig")
        result = measure(raw, args.minutes, args.extra_silent_minutes)
    except (OSError, UnicodeError, ValueError) as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print(f"口播正文：{result['spoken_hanzi']}汉字；英语词{result['english_word_tokens']}个；数字片段{result['numeric_tokens']}个。")
    estimated = result["estimated_finished_minutes"]
    if estimated:
        print(f"参考成片时长：{estimated['low']:.2f}—{estimated['high']:.2f}分钟，中心约{estimated['reference']:.2f}分钟。")
    budget = result["target_budget"]
    if budget:
        print(f"目标{budget['target_total_minutes']:g}分钟：建议{budget['planned_hanzi_low']}—{budget['planned_hanzi_high']}汉字，中心约{budget['planned_hanzi_reference']}字。")
        status = {"within_range": "在参考范围内", "below_range": "低于参考范围", "above_range": "高于参考范围"}[budget["hanzi_budget_status"]]
        print(f"当前正文汉字数{status}；仍需结合内容与试读判断。")
    for note in result["notes"]:
        print(note)


if __name__ == "__main__":
    main()
