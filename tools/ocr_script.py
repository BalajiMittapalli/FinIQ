import argparse
import os
import ocr_engine
import metadata_extractor
import response_generator

def main():
    parser = argparse.ArgumentParser(description="Extract metadata from a markdown file and auto-draft a response letter.")
    parser.add_argument("input_file", help="Path to the input markdown file")
    args = parser.parse_args()

    input_file = args.input_file

    # Determine if the input file is a markdown file or an image
    if input_file.lower().endswith(".md"):
        text = ocr_engine.extract_text_from_markdown(input_file)
    else:
        text = ocr_engine.extract_text_from_image(input_file)

    if not text:
        print("Could not extract text from the input file.")
        return

    metadata = metadata_extractor.extract_metadata(text)
    response_letter = response_generator.auto_draft_response(metadata)
    print(response_letter)
    response_generator.save_response_to_docx(response_letter)

if __name__ == "__main__":
    main()