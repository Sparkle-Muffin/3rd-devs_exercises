from __future__ import annotations

from pathlib import Path

import cv2
import pytesseract


def image_to_text(image_path: str | Path, use_opencv_preprocessing: bool = False) -> str:
    """
    Extract text content from an image using OpenCV pre-processing and pytesseract OCR.

    Args:
        image_path: Path to the image file to parse.

    Returns:
        Recognised text as a string (empty string when nothing is detected).

    Raises:
        FileNotFoundError: If the image path does not exist.
        ValueError: If OpenCV cannot load the image.
    """

    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Unable to load image: {image_path}")

    if use_opencv_preprocessing:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Apply adaptive thresholding to enhance contrast before OCR.
        processed = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            3,
        )

        # A light blur can remove speckles without harming sharp edges.
        processed = cv2.medianBlur(processed, 3)

        # pytesseract expects RGB images; convert the binary image back to RGB.
        rgb = cv2.cvtColor(processed, cv2.COLOR_GRAY2RGB)

        text = pytesseract.image_to_string(rgb, lang='pol')
    else:
        text = pytesseract.image_to_string(image, lang='pol')

    return text.strip()


def split_text_blocks(input_file_path, output_prefix, kernel_size=(30, 10), iterations=2, contour_min_width=200, contour_min_height=100):
    # Load the image
    image = cv2.imread(input_file_path)
    if image is None:
        raise ValueError(f"Unable to load image: {input_file_path}")

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply thresholding to binarize the image
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    # Use morphological operations to group text areas
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)  # Adjust kernel size as needed
    dilated = cv2.dilate(binary, kernel, iterations=iterations)

    # Find contours on the processed image
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter and save meaningful contours
    fragment_count = 0
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)

        # Filter out small or irrelevant contours
        if w < contour_min_width or h < contour_min_height:  # Adjust minimum width and height as needed
            continue

        # Extract region of interest (ROI)
        roi = image[y:y+h, x:x+w]

        # Save the fragment
        fragment_count += 1
        output_file = f"{output_prefix}_{fragment_count}.png"
        cv2.imwrite(output_file, roi)

    return fragment_count