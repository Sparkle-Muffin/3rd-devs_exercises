import cv2


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