from dataclasses import dataclass
from enum import StrEnum
from typing import final, ClassVar

import pymupdf

"""
mymupdf.Page.get_text() `option` paraméterét szabja meg,
a `process_page` `text_page` paramétere kapja a feldolgozott szöveget
"""
TextExtractKind = StrEnum('TextExtractKind', [('TEXT', 'text'), ('BLOCKS', 'blocks'), ('DICT', 'dict'), ('RAWDICT', 'rawdict')])

@dataclass
class Redactor:
    doc: pymupdf.Document
    output_filename: str
    extract_kind: TextExtractKind = TextExtractKind.TEXT

    REDACTION_COLOR: ClassVar[tuple[int, int, int]] = (0, 0, 0)

    def process_page(self, page: pymupdf.Page, page_idx: int, extracted_text):
        pass

    @final
    def process_pages(self):
        for page_idx, page in enumerate(self.doc.pages()):
            page_text = page.get_text(option=self.extract_kind)
            self.process_page(page, page_idx, page_text)
            self.finalize_page(page)

    @final
    def finalize_page(self, page: pymupdf.Page):
        page.apply_redactions()

    @final
    def __del__(self):
        self.doc.save(self.output_filename)
        self.doc.close()
