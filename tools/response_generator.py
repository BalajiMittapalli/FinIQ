import subprocess
from docx import Document
from docx.shared import Inches
import os

def auto_draft_response(metadata):
    # Use Ollama to draft the response
    prompt = f"""You are an AI assistant that specializes in drafting formal business letters.
    Based on the following metadata, draft a professional and understandable response letter in the first person.
    Include all available information in the letter. If a piece of information is not available, do not include it.
    The letter should be well-written and easy to understand.
    The letter should be addressed to the client.
    The letter should include the full issue date.
    The letter should be signed by Adilya Traders.
    The sender's contact information is Praveen N - 9876543210, Braven N - 9876543210, buildersconcrete@mail.com.
    Metadata: {metadata}
    """
    try:
        result = subprocess.run(['ollama', 'run', 'mistral', prompt], capture_output=True, text=True, check=True, encoding='utf-8')
        response_letter = result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running Ollama: {e}")
        response_letter = "Error generating response."
    return response_letter

def save_response_to_docx(response_letter, output_path="response.docx"):
    if os.path.exists(output_path):
        os.remove(output_path)
    document = Document()
    document.add_heading('Response Letter', 0)
    document.add_paragraph(response_letter)
    document.save(output_path)
    print(f"Response letter saved to {output_path}")