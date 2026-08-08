#!/usr/bin/env python3
"""
prep_photo.py — turn a raw headshot into a clean grayscale PNG ready for
ASCII conversion.

Steps:
  1. Remove the background (rembg) so only the subject remains.
  2. Boost local contrast with CLAHE so a flatly-lit face gets real
     highlights and shadows.
  3. Composite onto pure white so the background maps to the blank end
     of the ASCII density ramp.

Usage:
  python scripts/prep_photo.py source-photo.png
Output:
  source-prepped.png
"""
import sys
import numpy as np
import cv2
from PIL import Image
from rembg import remove


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/prep_photo.py <input-photo>")
        sys.exit(1)

    in_path = sys.argv[1]
    out_path = "source-prepped.png"

    print(f"[1/3] Removing background from {in_path} ...")
    with open(in_path, "rb") as f:
        input_bytes = f.read()
    result_bytes = remove(input_bytes)

    # Load RGBA result
    rgba = Image.open(__import__("io").BytesIO(result_bytes)).convert("RGBA")

    print("[2/3] Boosting local contrast (CLAHE) ...")
    rgb = np.array(rgba.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray_eq = clahe.apply(gray)

    print("[3/3] Compositing onto pure white ...")
    alpha = np.array(rgba)[:, :, 3]  # alpha channel from bg removal
    white_bg = np.full_like(gray_eq, 255)
    alpha_f = alpha.astype(np.float32) / 255.0
    composited = (gray_eq.astype(np.float32) * alpha_f +
                  white_bg.astype(np.float32) * (1 - alpha_f)).astype(np.uint8)

    Image.fromarray(composited, mode="L").save(out_path)
    print(f"Done -> {out_path}")


if __name__ == "__main__":
    main()
