import pymupdf

from dataclasses import dataclass, field
import re

from .redactor import Redactor, TextExtractKind
from .utils import rawdict as rd

@dataclass
class UnicreditRedactor(Redactor):
    def __post_init__(self):
        self.extract_kind = TextExtractKind.RAWDICT

        self.SPENDING_PATTERN = re.compile(r'-[0-9]{1,3}(?:\.[0-9]{3})*,\d{2}') # TODO jobb regex talan
        self.MONTH_DAY_PATTERN = re.compile(r'[0-9]{2}\/[0-9]{2}')
        self.DATE_PATTERN = re.compile(r'[0-9]{4}\.[0-9]{2}\.[0-9]{2}')

        self.spendings_start_page_idx = -1
        
    
    def footer_redact_sensitive_value(self, page, page_text, substr):
    
        text_idx = rd.block_idx_by_text(page_text, substr)
        if text_idx is -1:
            return False
    
        # következő blokkban van az érték
        value_idx = text_idx + 1
        if value_idx > len(page_text):
            return False
    
        rect_to_redact = pymupdf.Rect(page_text[value_idx]['lines'][0]['spans'][0]['bbox'])
        page.add_redact_annot(rect_to_redact, fill=self.REDACTION_COLOR)
    
        return True


    def redact_iban_and_account_numbers(self, page, page_text):
        iban_and_account_idx = rd.block_idx_by_text(page_text, 'IBAN')
        if iban_and_account_idx is -1:
            return False
    
        values_idx = iban_and_account_idx + 1
    
        account_rect = pymupdf.Rect(page_text[values_idx]['lines'][0]['spans'][0]['bbox'])
        iban_rect = pymupdf.Rect(page_text[values_idx]['lines'][1]['spans'][0]['bbox'])
    
        page.add_redact_annot(account_rect, fill=self.REDACTION_COLOR)
        page.add_redact_annot(iban_rect, fill=self.REDACTION_COLOR)
    
        return True
    
    
    def redact_initial_balance(self, page, page_text):
        initial_balance_text_idx = rd.block_idx_by_text(page_text, 'Nyitó egyenleg')
        if initial_balance_text_idx is -1:
            return False
    
        initial_balance_idx = initial_balance_text_idx + 1
    
        rect_to_redact = pymupdf.Rect(page_text[initial_balance_idx]['lines'][3]['spans'][0]['bbox'])
        page.add_redact_annot(rect_to_redact, fill=self.REDACTION_COLOR)
    
        return True
    
    
    def has_spendings(self, page_text):
        idx = rd.block_idx_by_text(page_text, 'Terhelések')
        return idx != -1
    
    
    def redact_spendings(self, page, page_text, page_idx):
        account_activity_idx = rd.block_idx_by_regex(page_text, self.SPENDING_PATTERN)
        found_spendings_marker = False
    
        # A dátumokat meghagyjuk, mert egyszer már így megfelelt
        should_keep = lambda text: self.MONTH_DAY_PATTERN.match(text) or self.DATE_PATTERN.match(text) or text.isspace()
    
        for line in page_text[account_activity_idx]['lines']:
            for span in line['spans']:
                text = rd.extract_span_text(span)
                if self.SPENDING_PATTERN.match(text):
                    # Mivel a '-' jelnek látszania kell, így az első karaktert nem takarjuk ki
                    chars_to_redact = span['chars'][1:]
    
                    page.add_redact_annot(rd.compute_substring_bounding_box(chars_to_redact), fill=self.REDACTION_COLOR)
                else:
                    # A 'Terhelések' szöveg után minden szöveget kitakarhatunk,
                    # de a dátumokat meghagyjuk, egyszer már így elfogadták
                    if (found_spendings_marker or page_idx > self.spendings_start_page_idx) and not should_keep(text):
                        page.add_redact_annot(span['bbox'], fill=self.REDACTION_COLOR)
                    elif 'Terhelések' in text:
                        found_spendings_marker = True


    def process_page(self, page: pymupdf.Page, page_idx: int, extracted_text):
        page_text = [b for b in extracted_text['blocks'] if b['type'] == 0]

        if self.spendings_start_page_idx == -1 and self.has_spendings(page_text):
            self.spendings_start_page_idx = page_idx

        self.footer_redact_sensitive_value(page, page_text, 'Terhelések összesen')
        self.footer_redact_sensitive_value(page, page_text, 'Záró egyenleg')
        self.redact_iban_and_account_numbers(page, page_text)
        self.redact_initial_balance(page, page_text)

        if self.spendings_start_page_idx != -1:
            self.redact_spendings(page, page_text, page_idx)
