# FinIQ - Empowering MSMEs with Actionable Insights

FinIQ is a Streamlit application designed to help Micro, Small, and Medium Enterprises (MSMEs) manage their finances and documents more efficiently. It provides a unified interface for various financial and document processing tasks.

## Features

- **Chat/Tasks:** A chat interface powered by a financial expert assistant to answer financial queries.
- **Document Processing:** OCR (Optical Character Recognition) functionality to extract text from documents.
- **Client Management:** Tools to manage client information, including adding new clients and viewing existing client details.
- **Reminders:** A reminder system to set and track important deadlines and tasks.
- **Balance Sheet Analyzer:** Analyzes uploaded Excel (Tally/CSV) reports to provide financial summaries, tax estimations, and GST summaries.

## File Structure

- `.env`: Contains environment variables for the application.
- `.gitignore`: Specifies intentionally untracked files that Git should ignore.
- `app.py`: The main Streamlit application file that combines all the features.
- `celery_app.py`: Configures Celery, a task queue, for asynchronous tasks.
- `client_management.db`: SQLite database file to store client and reminder information.
- `completion_server.py`: Likely related to autocompletion or suggestion functionalities.
- `config.py`: Contains configuration settings for the application.
- `database.py`: Handles database creation, connection, and data retrieval/storage functions.
- `FinIQ\_logo\_instructions.docx`: Instructions for the FinIQ logo.
- `FinIQ.svg`: The FinIQ logo in SVG format.
- `mock\_income\_tax\_notice\_3\_response.docx`: Mock income tax notice response document.
- `mock\_income\_tax\_notice\_3.pdf`: Mock income tax notice PDF file.
- `nohup.out`: Output file for nohup command (likely used to run the application in the background).
- `ocr\_script.py`: Contains the OCR script to extract text from images and PDFs.
- `README.md`: This file, providing an overview of the project.
- `tasks.py`: Defines the Celery tasks for asynchronous operations.
- `data/`: Directory to store uploaded files and other data.
  - `uploads/`: Directory to store uploaded documents for processing.
- `myenv/`: Virtual environment directory (may not be present in the repository).
- `tools/`: Directory containing helper scripts and modules.
  - `\_\_init\_\_.py`: Initializes the tools directory as a Python package.
  - `metadata\_extractor.py`: Extracts metadata from documents.
  - `ocr\_engine.py`: Contains the OCR engine implementation.
  - `ocr\_script.py`: Script to perform OCR on documents.
  - `response\_generator.py`: Generates automated responses based on extracted text.

## Dependencies

The application uses the following Python libraries:

- streamlit
- subprocess
- os
- shutil
- docx
- io
- re
- datetime
- pandas
- sqlite3
- celery
- torch

## Setup

1.  Clone the repository:

    `git clone <repository\_url>`

2.  Create a virtual environment:

    `python3 -m venv myenv`

3.  Activate the virtual environment:

    `source myenv/bin/activate`

4.  Install the dependencies:

    `pip install -r requirements.txt`

5.  Configure the environment variables:

    Create a `.env` file based on the `.env.example` and set the necessary variables.

6.  Run the Streamlit application:

    `streamlit run app.py`

## Usage

1.  Open the Streamlit application in your browser.
2.  Navigate through the tabs to use the different features:
    - **Chat/Tasks:** Interact with the financial expert assistant.
    - **Document Processing:** Upload and process documents using OCR.
    - **Client Management:** Add and manage client information.
    - **Reminders:** Set and track reminders.
    - **Balance Sheet Analyzer:** Upload and analyze Excel reports.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

all the rights are reserved by TEAM AKATSUKI
