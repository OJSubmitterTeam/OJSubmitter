from typing import List


def parse_ids(string: str) -> List[int]:
    parts = map(str.strip, string.split(","))
    ids: List[int] = []
    for part in parts:
        if "-" in part:
            start_str, end_str = map(str.strip, part.split("-", 1))
            if start_str.isdigit() and end_str.isdigit():
                l, r = int(start_str), int(end_str)
                if l <= r:
                    ids.extend(range(l, r + 1))
        elif part.isdigit():
            ids.append(int(part))
    return ids
