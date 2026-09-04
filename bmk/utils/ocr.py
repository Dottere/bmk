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
import cv2 as cv
import numpy as np


def scale_bbox_to_orig(bbox, scaling_matrix: pymupdf.Matrix) -> pymupdf.Rect:
    return pymupdf.Rect(bbox) * scaling_matrix


def preprocess_scanned_page(scanned: pymupdf.Page, dpi: int = 300, denoise_h: int = 20, threshold_value: int = 190) -> tuple[pymupdf.Matrix, pymupdf.Document]:
    '''
    Szkennelt dokumentumot zajmentesít és OCR-t futtat rajta.
    A végeredmény az oldal magasságának, szélességének skálázása,
    és egy 1 oldalas dokumentum
    '''
    pixmap = scanned.get_pixmap(dpi=dpi)
    #img = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.h, pixmap.w, pixmap.n)
    img = np.ndarray(
        shape=(pixmap.h, pixmap.w, pixmap.n),
        dtype=np.uint8,
        buffer=pixmap.samples,
        strides=(pixmap.stride, pixmap.n, 1)
    )

    gray = cv.cvtColor(img, cv.COLOR_RGB2GRAY)
    denoised = cv.fastNlMeansDenoising(gray, h=denoise_h)
    _, thresh = cv.threshold(denoised, threshold_value, 255, cv.THRESH_BINARY)
    rgb = cv.cvtColor(thresh, cv.COLOR_GRAY2RGB) # mupdf RGB-t vár el

    preprocessed_pixmap = pymupdf.Pixmap(pymupdf.csRGB, rgb.shape[1], rgb.shape[0], rgb.tobytes(), False)

    new_doc = pymupdf.open('pdf', preprocessed_pixmap.pdfocr_tobytes(language='hun'))
    # shoutout to A2 lineáris leképezések
    scaling_matrix = new_doc[0].rect.torect(scanned.rect)

    return scaling_matrix, new_doc
