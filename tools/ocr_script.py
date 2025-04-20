import os
# import cv2 # No longer needed for basic OCR with DocumentConverter
# Import the specific converter class
from docling.document_converter import DocumentConverter

# Instantiate the converter once outside the function for efficiency
converter = DocumentConverter()

def perform_ocr(image_path):
    """
    Performs OCR on the given image using docling.DocumentConverter.
    """
    try:
        # Use the converter to process the file directly
        result = converter.convert(image_path)

        # Check if conversion was successful and a document object exists
        if result and result.document:
            # Export the document content to Markdown format
            markdown_text = result.document.export_to_markdown()
            return markdown_text.strip()
        else:
            # Handle cases where conversion failed or no document was produced
            print(f"Warning: No document found in the result for {image_path}")
            return None
    
    # Catch potential exceptions during conversion
    except Exception as e:
        print(f"Error processing image {image_path} with DocumentConverter: {e}")
        return None

def extract_due_date(markdown_text):
    """
    Extracts due date from markdown text using regex.
    """
    import re
    date_patterns = [
        r"Due Date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",  # DD/MM/YYYY, DD-MM-YYYY, DD/MM/YY, DD-MM-YY
        r"Payment Date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"Date Due:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"Expiry Date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", # Added "Expiry Date" as a possible indicator
        r"Last Date to Pay:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})" # Added "Last Date to Pay"
        # Add more patterns as needed
    ]
    for pattern in date_patterns:
        match = re.search(pattern, markdown_text, re.IGNORECASE)
        if match:
            return match.group(1)  # Return the first captured group (the date)
    return None  # Return None if no date is found

def main():
    """
    Main function to iterate through images in the data folder and perform OCR.
    """
    data_folder = "data"
    image_files = [f for f in os.listdir(data_folder) if f.endswith(('.png', '.jpg', '.jpeg', '.pdf'))]

    if not image_files:
        print("No image files found in the data folder.")
        return

    for image_file in image_files:
        image_path = os.path.join(data_folder, image_file)
        print(f"Processing: {image_path}")
        extracted_text = perform_ocr(image_path)

        if extracted_text:
            print("Extracted Text:")
            print(extracted_text)
        else:
            print("No text extracted or error occurred.")
        print("-" * 30)

if __name__ == "__main__":
    main()

    # Call response generator
    from tools.response_generator import auto_draft_response
    import glob
    
    # Get the list of pdf files
    pdf_files = glob.glob("data/*.pdf")
    
    # Loop through each pdf file
    for pdf_file in pdf_files:
        # Extract the file name
        file_name = os.path.basename(pdf_file)
        # Perform OCR
        extracted_text = perform_ocr(pdf_file)
        # Generate the response letter
        response_letter = auto_draft_response(extracted_text)
        # Save the response letter to a file
        with open(f"{file_name.replace('.pdf', '')}_response.txt", "w") as f:
            f.write(response_letter)


# import os
# import re
# import json
# from docling.document_converter import DocumentConverter

# converter = DocumentConverter()

# def markdown_to_json(markdown_file):
#     """
#     Converts a markdown invoice file to a JSON object.
#     """
#     try:
#         with open(markdown_file, 'r') as f:
#             markdown_content = f.read()

#         invoice_data = {}

#         # Extract data using regex
#         company_match = re.search(r'## Concrete Builders\n(.*?)(?=\nPlace of Supply)', markdown_content, re.DOTALL)
#         invoice_data['company'] = company_match.group(1).strip() if company_match else None

#         place_of_supply_match = re.search(r'Place of Supply\n(.*?)(?=\nAdilya Traders)', markdown_content)
#         invoice_data['place_of_supply'] = place_of_supply_match.group(1).strip() if place_of_supply_match else None

#         customer_match = re.search(r'Adilya Traders\n(.*?)(?=\n\d{6})', markdown_content, re.DOTALL)
#         invoice_data['customer'] = customer_match.group(1).strip() if customer_match else None

#         gst_no_match = re.search(r'GST Nol(.*?)\n', markdown_content)
#         invoice_data['gst_no'] = gst_no_match.group(1).strip() if gst_no_match else None

#         invoice_no_match = re.search(r'Invoice No: (.*?)\n', markdown_content)
#         invoice_data['invoice_no'] = invoice_no_match.group(1).strip() if invoice_no_match else None

#         date_of_issue_match = re.search(r'Date of-ssue: (.*?)\n', markdown_content)
#         invoice_data['date_of_issue'] = date_of_issue_match.group(1).strip() if date_of_issue_match else None

#         due_date_match = re.search(r'Due date. (.*?)\n', markdown_content)
#         invoice_data['due_date'] = due_date_match.group(1).strip() if due_date_match else None

#         terms_match = re.search(r'TERMS OR SPECIAL INSTRUCTIONS:\n(.*?)(?=\n\|)', markdown_content, re.DOTALL)
#         invoice_data['terms'] = terms_match.group(1).strip() if terms_match else None

#         # Extract line items
#         line_items = []
#         item_pattern = re.compile(r'\| (.*?) \| (.*?) \| (.*?) \| (.*?) \| (.*?) \| (.*?)(?=\n\|)', re.DOTALL)
#         items = item_pattern.findall(markdown_content)
#         for item in items:
#             if "SLNO" not in item[0]: # Skip header row
#                 line_items.append({
#                     'slno': item[0].strip(),
#                     'description': item[1].strip(),
#                     'hsnisac': item[2].strip(),
#                     'qty': item[3].strip(),
#                     'rate': item[4].strip(),
#                     'amount': item[5].replace(" |", "").strip()
#                 })
#         invoice_data['line_items'] = line_items

#         # Extract total amount
#         invoice_data['total_amount_words'] = re.search(r'AMOUNT \(IN WORDS\): (.*?)\n', markdown_content).group(1).strip()

#         return json.dumps(invoice_data, indent=4)

#     except Exception as e:
#         return f"Error: {e}"

# def perform_ocr(image_path):
#     """
#     Performs OCR on the given image using docling.DocumentConverter.
#     """
#     try:
#         result = converter.convert(image_path)
#         if result and result.document:
#             markdown_text = result.document.export_to_markdown()
#             return markdown_text.strip()
#         else:
#             print(f"Warning: No document found in the result for {image_path}")
#             return None
#     except Exception as e:
#         print(f"Error processing image {image_path} with DocumentConverter: {e}")
#         return None

# def main():
#     """
#     Main function to either convert markdown to JSON or perform OCR.
#     """
#     # Convert markdown to JSON
#     markdown_file = "image.md"
#     json_output = markdown_to_json(markdown_file)
#     if json_output:
#         print("JSON Output:")
#         print(json_output)
#         # Save to a JSON file
#         with open("invoice.json", "w") as outfile:
#             outfile.write(json_output)
#     else:
#         print("Could not convert markdown to JSON.")

#     # OCR functionality (commented out to avoid running it by default)
#     # data_folder = "data"
# #         invoice_data['line_items'] = line_items

# #         # Extract total amount
# #         invoice_data['total_amount_words'] = re.search(r'AMOUNT \(IN WORDS\): (.*?)\n', markdown_content).group(1).strip()

# #         return json.dumps(invoice_data, indent=4)

# #     except Exception as e:
# #         return f"Error: {e}"

# # def perform_ocr(image_path):
# #     """
# #     Performs OCR on the given image using docling.DocumentConverter.
# #     """
# #     try:
# #         result = converter.convert(image_path)
# #         if result and result.document:
# #             markdown_text = result.document.export_to_markdown()
# #             return markdown_text.strip()
# #         else:
# #             print(f"Warning: No document found in the result for {image_path}")
# #             return None
# #     except Exception as e:
# #         print(f"Error processing image {image_path} with DocumentConverter: {e}")
# #         return None

# # def main():
# #     """
# #     Main function to either convert markdown to JSON or perform OCR.
# #     """
# #     # Convert markdown to JSON
# #     markdown_file = "image.md"
# #     json_output = markdown_to_json(markdown_file)
# #     if json_output:
# #         print("JSON Output:")
# #         print(json_output)
# #         # Save to a JSON file
# #         with open("invoice.json", "w") as outfile:
# #             outfile.write(json_output)
# #     else:
# #         print("Could not convert markdown to JSON.")

# #     # OCR functionality (commented out to avoid running it by default)
# #     # data_folder = "data"
# #     # image_files = [f for f in os.listdir(data_folder) if f.endswith(('.png', '.jpg', '.jpeg'))]
# #     # if not image_files:
# #     #     print("No image files found in the data folder.")
# #     #     return
# #     # for image_file in image_files:
# #     #     image_path = os.path.join(data_folder, image_file)
# #     #     print(f"Processing: {image_path}")
# #     #     extracted_text = perform_ocr(image_path)
# #     #     if extracted_text:
# #     #         print("Extracted Text:")
# #     #         print(extracted_text)
# #     #     else:
# #     #         print("No text extracted or error occurred.")
# #     #     print("-" * 30)

# # if __name__ == "__main__":
# #     main()