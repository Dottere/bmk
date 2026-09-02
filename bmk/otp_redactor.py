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

import pymupdf

from dataclasses import dataclass
import re

from .redactor import Redactor, TextExtractKind
from .utils import rawdict as rd
from .utils import regex as reg

@dataclass
class OtpRedactor(Redactor):
    def __post_init__(self):
        self.extract_kind = TextExtractKind.RAWDICT
        self.redacted_initial_balance = False
        self.OTP_SPENDING_PATTERN = re.compile(r'\-\d+(?:\.\d+)?')
        self.OTP_DATE_PATTERN = re.compile(r'(\d{2}\.){2}\d{2}')


    def redact_account_number(self, page, page_text):
        account_details_block_idx = rd.block_idx_by_text(page_text, 'SZÁMLASZÁM')
        for line_idx, line in enumerate(page_text[account_details_block_idx]['lines']):
            for span_idx, span in enumerate(line['spans']):
                text = rd.extract_span_text(span)
                if 'SZÁMLASZÁM' in text or 'IBAN' in text or 'BIC(SWIFT)KÓD' in text:
                    page.add_redact_annot(line['spans'][span_idx + 1]['bbox'], fill=self.REDACTION_COLOR)

    def redact_spendings(self, page, page_text):
        new_transaction = False
        for block_idx, block in enumerate(page_text):
            for line_idx, line in enumerate(block['lines']):
                for span_idx, span in enumerate(line['spans']):
                    text = rd.extract_span_text(span)

                    if self.OTP_SPENDING_PATTERN.match(text):
                        chars_to_redact = span['chars'][1:]
                        page.add_redact_annot(rd.compute_substring_bounding_box(chars_to_redact), fill=self.REDACTION_COLOR)

                        new_transaction = True
                    elif new_transaction:
                        # a legközelebbi dátumig minden kitakarható
                        if self.OTP_DATE_PATTERN.fullmatch(text.strip()) or 'IDÕSZAK' in text:
                            new_transaction = False
                        else:
                            page.add_redact_annot(span['bbox'], fill=self.REDACTION_COLOR)


    def redact_total_spendings(self, page, page_text):
        total_spendings_idx = rd.block_idx_by_text(page_text, 'TERHELÉSEK ÖSSZESEN')
        if total_spendings_idx == -1:
            return

        chars = page_text[total_spendings_idx]['lines'][1]['spans'][0]['chars']
        minus_sign_idx = next((i for i, char in enumerate(chars) if
                              char['c'] == '-'), -1)
        page.add_redact_annot(rd.compute_substring_bounding_box(chars[minus_sign_idx+1:]), fill=self.REDACTION_COLOR)



    def process_page(self, page: pymupdf.Page, page_idx: int, extracted_text):
        page_text = [b for b in extracted_text['blocks'] if b['type'] == 0]

        self.redact_account_number(page, page_text)
        self.redact_spendings(page, page_text)


        if not self.redacted_initial_balance:
            initial_balance_block_idx = rd.block_idx_by_text(page_text, 'NYITÓ EGYENLEG')
            text_line_idx = rd.line_idx_by_text(page_text[initial_balance_block_idx], 'NYITÓ EGYENLEG')

            page.add_redact_annot(page_text[initial_balance_block_idx]['lines'][text_line_idx-1]['spans'][0]['bbox'], fill=self.REDACTION_COLOR)
            self.redacted_initial_balance = True

        final_balance_idx = rd.block_idx_by_text(page_text, 'ZÁRÓ EGYENLEG')
        if final_balance_idx != -1:
            page.add_redact_annot(page_text[final_balance_idx]['lines'][1]['spans'][0]['bbox'], fill=self.REDACTION_COLOR)
            self.redact_total_spendings(page, page_text)
