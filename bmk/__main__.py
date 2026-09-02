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

import argparse
from sys import stderr

from .unicredit_redactor import UnicreditRedactor
from .otp_redactor import OtpRedactor
from .redactor import Redactor

ALL_REDACTORS: dict[str, type[Redactor]] = {
    'unicredit': UnicreditRedactor,
    'otp': OtpRedactor,
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
