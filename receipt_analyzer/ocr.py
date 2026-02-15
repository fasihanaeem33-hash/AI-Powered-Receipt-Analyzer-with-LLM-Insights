import io
from typing import Tuple
from PIL import Image, ImageFilter, ImageOps
import pytesseract
import os
import shutil

try:
    import easyocr
    HAS_EASYOCR = True
except Exception:
    HAS_EASYOCR = False


def _configure_tesseract():
    """Try to locate tesseract executable and configure pytesseract and env vars."""
    # if already configured, skip
    try:
        cur = getattr(pytesseract, 'pytesseract').tesseract_cmd
    except Exception:
        cur = None
    if cur:
        return

    # possible candidates
    candidates = []
    # environment variables
    for k in ('TESSERACT_CMD', 'TESSERACT_PATH', 'TESSDATA_PREFIX'):
        v = os.environ.get(k)
        if v:
            candidates.append(v)

    # common install locations on Windows
    candidates += [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]

    # check PATH
    which_t = shutil.which('tesseract')
    if which_t:
        candidates.insert(0, which_t)

    for c in candidates:
        if not c:
            continue
        # if path points to tessdata, skip
        if os.path.isdir(c) and os.path.isdir(os.path.join(c, 'tessdata')):
            os.environ['TESSDATA_PREFIX'] = c
            continue
        if os.path.isfile(c):
            try:
                pytesseract.pytesseract.tesseract_cmd = c
                os.environ['TESSERACT_CMD'] = c
                base = os.path.dirname(c)
                td = os.path.join(base, 'tessdata')
                if os.path.isdir(td):
                    os.environ['TESSDATA_PREFIX'] = td
                return
            except Exception:
                continue


# configure at import time
_configure_tesseract()

try:
    import numpy as np
    import cv2
    HAS_CV2 = True
except Exception:
    HAS_CV2 = False


def preprocess_image_bytes(image_bytes: bytes):
    """Preprocess image bytes. Returns either a PIL.Image or a numpy array depending on available libs."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    if HAS_CV2:
        arr = np.array(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        denoised = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)
        # adaptive threshold helps with varied lighting
        th = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        # morphological opening to reduce small noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
        opened = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel)
        return opened
    else:
        # PIL-only fallback: enhance contrast, reduce noise, then threshold
        img = ImageOps.autocontrast(img)
        img = img.filter(ImageFilter.MedianFilter(size=3))
        # simple threshold
        img_l = img.convert("L")
        img_t = img_l.point(lambda p: 255 if p > 160 else 0)
        return img_t


# global OCR reader for EasyOCR (lazy-loaded)
_reader = None

def _get_easyocr_reader():
    global _reader
    if _reader is None and HAS_EASYOCR:
        _reader = easyocr.Reader(['en'], gpu=False)
    return _reader


def ocr_image_bytes(image_bytes: bytes) -> Tuple[str, dict]:
    """Run OCR on image bytes and return raw text and optional detailed data.
    
    Tries EasyOCR first (pure Python, no system binaries), then Tesseract.
    Returns fallback message if both fail.
    """
    processed = preprocess_image_bytes(image_bytes)
    # Convert to PIL Image
    if HAS_CV2 and isinstance(processed, (np.ndarray,)):
        pil = Image.fromarray(processed)
    else:
        pil = processed
    
    text = None
    data = {}
    
    # Try EasyOCR first
    if HAS_EASYOCR:
        try:
            reader = _get_easyocr_reader()
            if reader:
                # EasyOCR expects numpy array
                img_array = np.array(pil)
                results = reader.readtext(img_array)
                # extract text from results (list of tuples: ([bbox], text, confidence))
                text_lines = [result[1] for result in results]
                text = '\n'.join(text_lines)
        except Exception as e:
            import sys
            print(f"EasyOCR failed: {e}", file=sys.stderr)
    
    # Try Tesseract as fallback
    if not text:
        try:
            if not pytesseract.pytesseract.tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            text = pytesseract.image_to_string(pil)
        except Exception as e:
            import sys
            print(f"Tesseract failed: {e}", file=sys.stderr)
    
    # Final fallback message
    if not text:
        text = "(OCR unavailable — install EasyOCR or Tesseract)"
    
    try:
        data = pytesseract.image_to_data(pil, output_type=pytesseract.Output.DICT)
    except Exception:
        data = {}
    return text, data
