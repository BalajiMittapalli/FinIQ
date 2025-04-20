import subprocess
import re

def extract_metadata(text):
    # Use Ollama to extract metadata
    prompt = f"""Extract the following metadata from this text. If a piece of information is not present, return "Not Found":
    - Client name: The name of the client.
    - Issue date: The date the invoice was issued.
    - Response deadline: The date a response is due.
    - Applicable sections: Any applicable sections or HSN/SAC codes.
    - Penalty amounts: Any penalty amounts mentioned.
    - Invoice number: The invoice number.
    - Application number: The application number, if present.
    - Due amount: The amount due.
    - GST number: The GST number.
    Text: {text}"""
    try:
        result = subprocess.run(['ollama', 'run', 'mistral', prompt], capture_output=True, text=True, check=True, encoding='utf-8')
        output = result.stdout
        print("Ollama Output:")
        print(output)

        # Parse the Ollama output (this will likely need adjustment based on Ollama's response format)
        client_name = re.search(r"Client Name:\s*([A-Za-z\s]*)", output, re.IGNORECASE)
        client_name = client_name.group(1).strip() if client_name else "Not Found"

        issue_date = re.search(r"Issue Date:\s*([0-9\/\-]*)", output, re.IGNORECASE)
        issue_date = issue_date.group(1).strip() if issue_date else "Not Found"

        response_deadline = re.search(r"Response Deadline:\s*([0-9\/\-]*)", output, re.IGNORECASE)
        response_deadline = response_deadline.group(1).strip() if response_deadline else "Not Found"

        applicable_sections = re.search(r"Applicable Sections:\s*([A-Za-z0-9\s,]*)", output, re.IGNORECASE)
        applicable_sections = applicable_sections.group(1).strip() if applicable_sections else "Not Found"

        penalty_amounts = re.search(r"Penalty Amounts:\s*([0-9\.]*)", output, re.IGNORECASE)
        penalty_amounts = penalty_amounts.group(1).strip() if penalty_amounts else "Not Found"

        invoice_number = re.search(r"Invoice Number:\s*([A-Za-z0-9\s\-]*)", output, re.IGNORECASE)
        invoice_number = invoice_number.group(1).strip() if invoice_number else "Not Found"

        application_number = re.search(r"Application Number:\s*([A-Za-z0-9\s\-]*)", output, re.IGNORECASE)
        application_number = application_number.group(1).strip() if application_number else "Not Found"

        due_amount = re.search(r"Due Amount:\s*([0-9\.]*)", output, re.IGNORECASE)
        due_amount = due_amount.group(1).strip() if due_amount else "Not Found"

        gst_number = re.search(r"GST Number:\s*([A-Za-z0-9\s]*)", output, re.IGNORECASE)
        gst_number = gst_number.group(1).strip() if gst_number else "Not Found"

    except subprocess.CalledProcessError as e:
        print(f"Error running Ollama: {e}")
        return {
            "client_name": "Error",
            "issue_date": "Error",
            "response_deadline": "Error",
            "applicable_sections": "Error",
            "penalty_amounts": "Error",
            "invoice_number": "Error",
            "application_number": "Error",
            "due_amount": "Error",
            "gst_number": "Error",
        }

    return {
        "client_name": client_name,
        "issue_date": issue_date,
        "response_deadline": response_deadline,
        "applicable_sections": applicable_sections,
        "penalty_amounts": penalty_amounts,
        "invoice_number": invoice_number,
        "application_number": application_number,
        "due_amount": due_amount,
        "gst_number": gst_number,
    }