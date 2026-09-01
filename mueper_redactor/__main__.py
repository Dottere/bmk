import pymupdf

import argparse
from sys import stderr

from .unicredit_redactor import UnicreditRedactor
from .redactor import Redactor

ALL_REDACTORS: dict[str, type[Redactor]] = {
    'unicredit': UnicreditRedactor
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='mueper-redactor',
        description='Bankszámlakivonatok kitakarása egyetemi bürokráciához'
    )
    parser.add_argument('input_pdf')
    parser.add_argument('redactor')
    parser.add_argument('output_pdf')
    args = parser.parse_args()

    if args.redactor.lower() not in ALL_REDACTORS.keys():
        print('Rossz számlakivonat típus! Válassz a következők közül egyet:', file=stderr)
        for key in ALL_REDACTORS.keys():
            print(key, file=stderr)
        exit(1)

    doc = None
    try:
        doc = pymupdf.open(args.input_pdf)
    except FileNotFoundError:
        print(f'{args.input_pdf} Nem létezik!', file=stderr)
        exit(1)

    redactor_class = ALL_REDACTORS[args.redactor]
    redactor = redactor_class(doc, args.output_pdf)
    redactor.process_pages()
