#!/usr/bin/env python3

import pymupdf
from sys import argv, stderr
import re

REDACTION_COLOR = (0, 0, 0)
SPENDING_PATTERN = re.compile(r'-[0-9]{1,3}(?:\.[0-9]{3})*,\d{2}') # TODO jobb regex

if len(argv) < 2:
    print('Kell egy PDF file', file=stderr)
    exit()


def block_idx_by_text(page_text, substr):
    return next(
        (i for i, e in enumerate(page_text) if any(
            substr in span['text']
            for line in e['lines']
            for span in line['spans'])
        ), -1
    )


def block_idx_by_regex(page_text, regex):
    return next(
        (i for i, e in enumerate(page_text) if any(
            regex.search(span['text'])
            for line in e['lines']
            for span in line['spans'])
        ), -1
    )


def footer_redact_sensitive_value(page, page_text, substr):

    text_idx = block_idx_by_text(page_text, substr)
    if text_idx is -1:
        return False

    # következő blokkban van az érték
    value_idx = text_idx + 1
    if value_idx > len(page_text):
        return False

    rect_to_redact = pymupdf.Rect(page_text[value_idx]['lines'][0]['spans'][0]['bbox'])
    page.add_redact_annot(rect_to_redact, fill=REDACTION_COLOR)

    return True


def redact_iban_and_account_numbers(page, page_text):
    iban_and_account_idx = block_idx_by_text(page_text, 'IBAN')
    if iban_and_account_idx is -1:
        return False

    values_idx = iban_and_account_idx + 1

    account_rect = pymupdf.Rect(page_text[values_idx]['lines'][0]['spans'][0]['bbox'])
    iban_rect = pymupdf.Rect(page_text[values_idx]['lines'][1]['spans'][0]['bbox'])

    page.add_redact_annot(account_rect, fill=REDACTION_COLOR)
    page.add_redact_annot(iban_rect, fill=REDACTION_COLOR)

    return True


def redact_initial_balance(page, page_text):
    initial_balance_text_idx = block_idx_by_text(page_text, 'Nyitó egyenleg')
    if initial_balance_text_idx is -1:
        return False

    initial_balance_idx = initial_balance_text_idx + 1

    rect_to_redact = pymupdf.Rect(page_text[initial_balance_idx]['lines'][3]['spans'][0]['bbox'])
    page.add_redact_annot(rect_to_redact, fill=REDACTION_COLOR)

    return True


def has_spendings(page_text):
    idx = block_idx_by_text(page_text, 'Terhelések')
    return idx != -1


def redact_spendings(page, page_text):
    account_activity_idx = block_idx_by_regex(page_text, SPENDING_PATTERN)
    for line in page_text[account_activity_idx]['lines']:
        for span in line['spans']:
            text = span['text']
            print(f'matchin {text}')
            if SPENDING_PATTERN.match(text):
                # Mivel a '-' jelnek látszania kell, így az első karaktert nem takarjuk ki
                sub_text = text[1:]
                print(f'TALALT keressuk {sub_text}')
                rects_to_redact = page.search_for(sub_text, clip=span['bbox'])
                print(rects_to_redact)
                if len(rects_to_redact) >= 1:
                    page.add_redact_annot(rects_to_redact[0], fill=REDACTION_COLOR)
            else:
                print('NEM TALALT')

        #print(line)
        #print('\n')
    #for txt in page_text:
    #    print(txt)
    #    print('\n')


with pymupdf.open(argv[1]) as doc:
    found_spendings = False

    for page in doc.pages():
        page_text = [b for b in page.get_text(option='dict')['blocks'] if b['type'] == 0]

        if not found_spendings:
            found_spendings = has_spendings(page_text)

        footer_redact_sensitive_value(page, page_text, 'Terhelések összesen')
        footer_redact_sensitive_value(page, page_text, 'Záró egyenleg')
        redact_iban_and_account_numbers(page, page_text)
        redact_initial_balance(page, page_text)

        if found_spendings:
            print('MEGTALALTUK')
            redact_spendings(page, page_text)

        page.apply_redactions()
    doc.save('lassuk.pdf')
