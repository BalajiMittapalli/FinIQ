from PIL import Image
import pytesseract
import markdown
import re

def extract_text_from_markdown(markdown_file):
    with open(markdown_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    html_content = markdown.markdown(md_content)
    text = ''.join(re.findall(r'\>([^<]+)\<', html_content))
    return text

def extract_text_from_image(image_path):
    try:
        text = pytesseract.image_to_string(Image.open(image_path))
        return text
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return None