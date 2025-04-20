from PIL import Image
import pytesseract
import markdown
import re
import cv2
import numpy as np

def extract_text_from_markdown(markdown_file):
    with open(markdown_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    html_content = markdown.markdown(md_content)
    text = ''.join(re.findall(r'\>([^<]+)\<', html_content))
    return text

def extract_text_from_image(image_path):
    try:
        # Read image with OpenCV
        img = cv2.imread(image_path)

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

        # Denoise the image
        denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)

        # Configuration for pytesseract
        config = ('-l eng --oem 1 --psm 3')

        # Extract text with Tesseract
        text = pytesseract.image_to_string(denoised, config=config)
        return text
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return None