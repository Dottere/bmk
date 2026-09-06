'''
 This file is part of bmk.

bmk is free software: you can redistribute it and/or modify it under the terms
of the GNU General Public License as published by the Free Software Foundation,
either version 3 of the License, or (at your option) any later version.

bmk is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with bmk.
If not, see <https://www.gnu.org/licenses/>.
'''

import re
from typing import Any


def extract_span_text(span: dict[str, Any]) -> str:
    return ''.join(char['c'] for char in span['chars'])

def compute_substring_bounding_box(span_chars: list[dict[str, Any]]) -> tuple[float, float, float, float]:
    x0: float = min(c['bbox'][0] for c in span_chars)
    y0: float = min(c['bbox'][1] for c in span_chars)
    x1: float = max(c['bbox'][2] for c in span_chars)
    y1: float = max(c['bbox'][3] for c in span_chars)

    return (x0, y0, x1, y1)

def block_idx_by_text(page_text: list[dict[str, Any]], substr: str) -> int:
    return next(
        (i for i, e in enumerate(page_text) if any(
            substr in extract_span_text(span)
            for line in e['lines']
            for span in line['spans'])
        ), -1
    )

def line_idx_by_text(block: dict[str, Any], substr: str) -> int:
    return next(
        (i for i, line in enumerate(block['lines']) if any(
            substr in extract_span_text(span)
            for span in line['spans']
        )), -1
    )


def block_idx_by_regex(page_text: list[dict[str, Any]], regex: re.Pattern) -> int:
    return next(
        (i for i, e in enumerate(page_text) if any(
            regex.search(extract_span_text(span))
            for line in e['lines']
            for span in line['spans'])
        ), -1
    )
