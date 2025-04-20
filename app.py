import streamlit as st
import subprocess
import os
import shutil
from tools.ocr_script import perform_ocr
from tools.response_generator import auto_draft_response
from docx import Document  # Import Document
from io import BytesIO    # Import BytesIO

# Define key financial data points (assuming it's defined elsewhere or here)
DATA_POINTS = {
    "revenue": {"question": "What was your total revenue for the period?", "extracted": False, "value": 0},
    "expenses": {"question": "What were your total expenses for the period?", "extracted": False, "value": 0},
    "assets": {"question": "What were your total assets at the end of the period?", "extracted": False, "value": 0},
    "liabilities": {"question": "What were your total liabilities at the end of the period?", "extracted": False, "value": 0},
}

# Define tasks for the agent (assuming it's defined elsewhere or here)
TASKS = [
    "Gather all financial data points (revenue, expenses, assets, liabilities).",
    "Generate a Balance Sheet.",
    "Generate an Income Statement.",
    "Generate a Tax Calculation report."
]

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "data_points" not in st.session_state:
    st.session_state.data_points = DATA_POINTS
if "tasks" not in st.session_state:
    st.session_state.tasks = TASKS
if "current_task_index" not in st.session_state:
    st.session_state.current_task_index = 0

# Configure page
st.set_page_config(page_title="FinIQ", layout="wide")

# Add logo and title
col1, col2 = st.columns([1, 3])
with col1:
    if os.path.exists("FinIQ.svg"):
        st.image("FinIQ.svg", width=75)
    else:
        st.subheader("FinIQ") # Fallback if logo not found
with col2:
    st.title("FinIQ")

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Check if content is editable response structure
        if isinstance(message["content"], dict) and "original" in message["content"]:
             # For display purposes in history, show the original or last edited
             # You might want to refine how edited history is stored/shown
             st.markdown(message["content"]["original"]) # Or store/show edited version
        else:
            st.markdown(message["content"])


# Function to generate chain-of-thought prompt
def generate_cot_prompt(task, data_points):
    # --- (Keep your existing generate_cot_prompt function) ---
    prompt = f"""You are a financial expert. Your current task is: {task}

    You have the following data points to work with:
    {data_points}

    What is the next logical step to achieve this task?
    What information do you need to proceed?
    Ask a specific question to get that information.

    Your response should be in the following format:
    \"\"\"
    Next Step: [The next logical step]
    Information Needed: [The information you need]
    Question: [A specific question to get that information]
    \"\"\"
    """
    return prompt

# Function to get the next question
def get_next_question():
    # --- (Keep your existing get_next_question function) ---
    if st.session_state.current_task_index < len(st.session_state.tasks):
        task = st.session_state.tasks[st.session_state.current_task_index]
        data_points = st.session_state.data_points
        cot_prompt = generate_cot_prompt(task, data_points)

        try:
            # Make sure 'ollama' command is accessible in the system PATH
            # Handle potential encoding issues if needed
            result = subprocess.run(['ollama', 'run', 'mistral', cot_prompt],
                                    capture_output=True, text=True, check=True, encoding='utf-8')
            response = result.stdout.strip() # Strip leading/trailing whitespace

            # Parse the response to extract the question - improved parsing
            question_part = response.split("Question:")
            if len(question_part) > 1:
                 question = question_part[1].strip().replace("\"", "").replace("”", "").replace("“","") # Remove quotes
                 if not question: # Handle empty question after split
                     question = "Could you please provide more details or the next piece of information?"
            else: # Fallback if parsing fails
                 question = "What was your total revenue for the period?" # Or a more generic fallback
            return question

        except FileNotFoundError:
             st.error("Ollama command not found. Please ensure Ollama is installed and in your system's PATH.")
             return None # Indicate error
        except subprocess.CalledProcessError as e:
            st.error(f"Error running Ollama: {e}\nOutput: {e.stdout}\nError: {e.stderr}")
            return "An error occurred while generating the next question. Please try again." # Error message
        except Exception as e: # Catch other potential errors
            st.error(f"An unexpected error occurred: {e}")
            return "An unexpected error occurred. Please check the logs."

    else:
        return "All tasks completed. Would you like to generate the reports?"

# Function to save response text to a docx file in memory
def save_response_to_docx(response_text):
    """Creates a .docx file in memory containing the response text."""
    document = Document()
    document.add_paragraph(response_text)
    # Save document to a BytesIO object
    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)  # Rewind the buffer to the beginning
    return buffer

# --- Chat Input Logic ---
next_q = get_next_question()
if next_q: # Only show input if there's a valid next question or prompt
    prompt = st.chat_input(next_q)
else:
    # Handle the case where ollama might not be available or errored
    st.warning("Could not get the next question. Please ensure Ollama is running correctly.")
    prompt = None # Disable input if no question

if prompt:
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- Assistant Response Generation ---
    # (This part might be where you ask Mistral to *process* the user's input,
    # not just ask the next question. Let's assume for now the goal is
    # to just display *some* response and make it editable).

    # Placeholder: Simulate getting a response based on the user's prompt
    # In a real scenario, you'd feed the prompt AND context to Mistral
    # to get a relevant answer. Here, we'll just use a placeholder response
    # or re-run Mistral with the user's prompt for a direct answer.
    try:
        # Example: Run ollama again with the user's prompt for a direct response
        # You might want a more sophisticated logic here depending on your agent's design
        llm_process_prompt = f"Based on the previous context and the user's input '{prompt}', provide a relevant response or analysis."
        result = subprocess.run(['ollama', 'run', 'mistral', llm_process_prompt], # Use user's prompt
                                capture_output=True, text=True, check=True, encoding='utf-8')
        assistant_response_text = result.stdout.strip()

    except FileNotFoundError:
         assistant_response_text = "Error: Ollama command not found."
         st.error(assistant_response_text)
    except subprocess.CalledProcessError as e:
        assistant_response_text = f"Error running Ollama: {e.stderr or e.stdout or e}"
        st.error(assistant_response_text)
    except Exception as e:
        assistant_response_text = f"An unexpected error occurred: {e}"
        st.error(assistant_response_text)


    # --- Display Assistant Response with Editing and Download ---
    with st.chat_message("assistant"):
        # Use a unique key for the text_area based on message index or similar
        # This prevents issues if multiple editable areas exist.
        message_key = f"response_edit_{len(st.session_state.messages)}"

        # Display the editable response area
        edited_response = st.text_area(
            "Edit Response:",
            value=assistant_response_text, # Pre-fill with the generated response
            height=200,
            key=message_key # Unique key
        )

        # Save the edited response to a docx file in memory
        docx_buffer = save_response_to_docx(edited_response)

        # Add download button for the *edited* response
        st.download_button(
            label="Download Edited Response (.docx)",
            data=docx_buffer, # Use the buffer containing the docx data
            file_name=f"FinIQ_response_{len(st.session_state.messages)}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", # MIME type for docx
        )

        # Store original/edited content in history (optional, decide structure)
        # Simple approach: Store the original response text.
        # Complex: Store both original and last edited state.
        st.session_state.messages.append({
            "role": "assistant",
            "content": {"original": assistant_response_text, "edited": edited_response} # Store both if needed
            # Or just store the original: "content": assistant_response_text
        })


    # --- Update Data Points & Tasks (Your existing logic) ---
    # Placeholder: Extract data from 'prompt' or 'edited_response' if needed
    # This part needs actual logic to parse the user's input (prompt) or
    # maybe even the edited_response to find values for DATA_POINTS.
    # For now, it's just illustrative.
    extracted_data = {} # Replace with actual extraction logic based on 'prompt'

    # Update data points based on extracted information
    for key, value in extracted_data.items():
        if key in st.session_state.data_points:
            # Ensure 'value' key exists before assignment
            if "value" not in st.session_state.data_points[key]:
                 st.session_state.data_points[key]["value"] = None # Or 0, or appropriate default
            st.session_state.data_points[key]["extracted"] = True
            st.session_state.data_points[key]["value"] = value # Store the extracted value

    # Check if all data points are collected for the current task
    # This logic might need refinement based on which data points belong to which task
    task_data_points_keys = list(DATA_POINTS.keys()) # Assuming all points needed for *first* task initially
    all_required_points_collected = True
    for data_key in task_data_points_keys:
        if not st.session_state.data_points[data_key].get("extracted", False):
             all_required_points_collected = False
             break

    # If all data points are collected, move to the next task
    if all_required_points_collected and st.session_state.current_task_index < len(st.session_state.tasks):
        # Check if we are not already past the last task before incrementing
        st.session_state.current_task_index += 1
        st.info(f"Moving to next task: {st.session_state.tasks[st.session_state.current_task_index] if st.session_state.current_task_index < len(st.session_state.tasks) else 'Completion'}")
        # Reset the extracted status if needed for the next task (depends on your logic)
        # for key in st.session_state.data_points:
        #     st.session_state.data_points[key]["extracted"] = False
        st.rerun() # Rerun to get the next question immediately


    # Check if all tasks are completed
    all_tasks_completed = st.session_state.current_task_index >= len(st.session_state.tasks)

    # Generate reports if all tasks are completed (Placeholder)
    if all_tasks_completed:
        st.success("All tasks completed! Ready to generate reports.")
        # Add report generation button or logic here
        if st.button("Generate Final Reports"):
             st.write("Generating financial reports...")
             # Add actual report generation logic here
             # You might generate DOCX reports here as well


# --- OCR Functionality (Keep your existing OCR section) ---
st.markdown("---")
st.markdown("### Document Processing")

# Create temporary directory
UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# File upload section
uploaded_files = st.file_uploader("Choose PDF files",
                                type="pdf",
                                accept_multiple_files=True,
                                help="Select one or more PDF files to process")

if uploaded_files:
    process_btn = st.button("Process Documents")

    if process_btn:
        # Clear previous uploads if desired
        # shutil.rmtree(UPLOAD_DIR)
        # os.makedirs(UPLOAD_DIR)

        for file in uploaded_files:
            with st.spinner(f"Processing {file.name}..."):
                try:
                    # Save uploaded file
                    save_path = os.path.join(UPLOAD_DIR, file.name)
                    with open(save_path, "wb") as f:
                        f.write(file.getbuffer())

                    # Perform OCR (Assuming these functions exist)
                    extracted_text = perform_ocr(save_path)

                    # Generate response (Assuming these functions exist)
                    response_text = auto_draft_response(extracted_text)

                    # Display results
                    with st.expander(f"Results for {file.name}", expanded=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("Extracted Text")
                            st.code(extracted_text, language="markdown")
                        with col2:
                            st.subheader("Generated Response")
                            # Make OCR response editable and downloadable too? (Optional)
                            ocr_edited_response = st.text_area(f"Edit OCR Response ({file.name}):", response_text, height=150, key=f"ocr_edit_{file.name}")
                            ocr_docx_buffer = save_response_to_docx(ocr_edited_response)
                            st.download_button(
                                label=f"Download OCR Response (.docx)",
                                data=ocr_docx_buffer,
                                file_name=f"FinIQ_OCR_{file.name}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )


                    st.success(f"Successfully processed {file.name}")

                except NameError as ne:
                     st.error(f"Error: A required function (like perform_ocr or auto_draft_response) is not defined: {ne}")
                except Exception as e:
                    st.error(f"Error processing {file.name}: {str(e)}")

st.markdown("---")
st.caption("Note: Uploaded files are temporarily stored for processing.")