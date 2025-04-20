import streamlit as st
import subprocess
import os
import shutil
from tools.ocr_script import perform_ocr
from tools.response_generator import auto_draft_response, save_response_to_docx
import database  # Import database functions
from docx import Document  # Import Document
from io import BytesIO    # Import BytesIO
from tools.metadata_extractor import extract_metadata # Import metadata extraction
import re # Import regex module
from datetime import datetime # Import datetime for reminders
import pandas as pd

# Initialize database
database.create_database()

# Initialize session state for chat
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How can I assist you with financial matters today?"}]
if "due_date" not in st.session_state:
    st.session_state.due_date = None # Initialize due_date in session state
if "selected_client_id" not in st.session_state:
    st.session_state.selected_client_id = None


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

# --- Core Financial Calculations ---
def parse_excel_data(file):
    """Parses the uploaded Excel file and extracts relevant data."""
    try:
        # Read the Excel file into a pandas DataFrame
        df = pd.read_excel(file)
        # Basic validation: Check if essential columns might exist (adjust column names as needed)
        # This is a very basic check; more robust validation might be needed.
        required_cols_check = ['Transaction Type', 'Amount']
        if not all(col in df.columns for col in required_cols_check):
             st.warning(f"Uploaded Excel might be missing expected columns like: {', '.join(required_cols_check)}. Calculations might be affected.")
        return df
    except Exception as e:
        st.error(f"Error reading or parsing Excel file: {e}")
        return None # Return None to indicate failure

def analyze_financials(df):
    """Calculates income, expenses, profit, and margin from the DataFrame."""
    if df is None or not all(col in df.columns for col in ['Transaction Type', 'Amount']):
        return 0, 0, 0, 0 # Return zeros or handle error appropriately
    try:
        income = df.loc[df['Transaction Type'] == 'Income', 'Amount'].sum()
        expenses = df.loc[df['Transaction Type'] == 'Expense', 'Amount'].sum()
        profit = income - expenses
        margin = profit / income if income else 0
        return income, expenses, profit, margin
    except Exception as e:
        st.error(f"Error analyzing financials: {e}")
        return 0, 0, 0, 0

def estimate_tax(df, rate=0.25):
    """Estimates tax liability based on income and sums TDS."""
    if df is None or not all(col in df.columns for col in ['Transaction Type', 'Amount']):
        return 0, 0
    try:
        income_total = df.loc[df['Transaction Type'] == 'Income', 'Amount'].sum()
        tax = income_total * rate
        # Safely get TDS, sum only numeric values, default to 0 if column missing or non-numeric
        tds = pd.to_numeric(df.get('TDS Deducted', pd.Series(dtype=float)), errors='coerce').fillna(0).sum()
        return tax, tds
    except Exception as e:
        st.error(f"Error estimating tax: {e}")
        return 0, 0

def summarize_gst(df, gst_rate=0.18):
    """Summarizes Input and Output GST based on 'GST Included' column."""
    input_gst = output_gst = 0.0
    if df is None or not all(col in df.columns for col in ['Transaction Type', 'Amount', 'GST Included']):
        st.warning("GST calculation requires 'Transaction Type', 'Amount', and 'GST Included' columns.")
        return 0, 0, 0
    try:
        for _, row in df.iterrows():
            # Ensure 'GST Included' is treated as boolean, handle potential non-boolean values
            gst_included_flag = False
            if isinstance(row['GST Included'], bool):
                gst_included_flag = row['GST Included']
            elif isinstance(row['GST Included'], str):
                 gst_included_flag = row['GST Included'].strip().upper() == 'TRUE' # Example handling for string 'TRUE'

            if gst_included_flag:
                amount = pd.to_numeric(row['Amount'], errors='coerce')
                if pd.isna(amount): continue # Skip if amount is not numeric

                base = amount / (1 + gst_rate)
                gst_amt = base * gst_rate
                if row['Transaction Type'] in ['Income', 'GST Sale']:
                    output_gst += gst_amt
                elif row['Transaction Type'] in ['Expense', 'Asset']: # Assuming Assets also have input GST
                    input_gst += gst_amt
        net_gst = output_gst - input_gst
        return input_gst, output_gst, net_gst
    except Exception as e:
        st.error(f"Error summarizing GST: {e}")
        return 0, 0, 0

def generate_visual_dashboards(df):
    """Generates visual dashboards (placeholder)."""
    if df is None:
        return "No data available for dashboard."
    # Placeholder: Create a simple bar chart
    try:
        income, expenses, profit, _ = analyze_financials(df)
        chart_data = pd.DataFrame({
            'Metric': ['Income', 'Expenses', 'Profit'],
            'Amount': [income, expenses, profit]
        })
        st.bar_chart(chart_data.set_index('Metric'))
        return "Basic P&L Chart Displayed Above." # Return text confirmation
    except Exception as e:
        st.error(f"Could not generate dashboard chart: {e}")
        return "Error generating dashboard."


def to_docx(text):
    """Creates a .docx file in memory containing the response text."""
    doc = Document()
    doc.add_paragraph(text)
    buf = BytesIO(); doc.save(buf); buf.seek(0)
    return buf

# --- Main Content Tabs ---
tab_chat, tab_docs, tab_clients, tab_reminders, tab_balance_sheet = st.tabs(["Chat/Tasks", "Document Processing", "Client Management", "Reminders", "Balance Sheet Analyzer"])

with tab_balance_sheet:
    st.markdown("### Balance Sheet Analyzer & Tax Estimator")
    uploaded_excel = st.file_uploader("Upload Excel (Tally/CSV) Reports", type=["xlsx","xls","csv"], key="balance_sheet_analyzer_uploader_tab") # Unique key for tab

    if uploaded_excel is not None: # Check if parsing was successful
        st.write("Uploaded file:", uploaded_excel.name)
        
        df_financials = parse_excel_data(uploaded_excel) # Parse the data
        if df_financials is not None:
            st.dataframe(df_financials.head()) # Show head of dataframe

            # Perform calculations
            income, expenses, profit, margin = analyze_financials(df_financials)
            tax, tds = estimate_tax(df_financials)
            input_gst, output_gst, net_gst = summarize_gst(df_financials)

            # Display results
            st.subheader("Financial Summary")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Income", f"₹{income:,.2f}")
            c2.metric("Expenses", f"₹{expenses:,.2f}")
            c3.metric("Profit", f"₹{profit:,.2f}")
            c4.metric("Margin", f"{margin:.1%}")

            st.subheader("Tax & GST Summary")
            st.markdown(f"*Estimated Tax Liability (25% on Income):* ₹{tax:,.2f}")
            st.markdown(f"*TDS Deducted:* ₹{tds:,.2f}")
            st.markdown(f"*Total Output GST:* ₹{output_gst:,.2f}")
            st.markdown(f"*Total Input GST:* ₹{input_gst:,.2f}")
            st.markdown(f"*Net GST Payable:* ₹{net_gst:,.2f}")

            st.subheader("Visual Dashboard")
            dashboard_status = generate_visual_dashboards(df_financials) # Generate and display chart
            st.caption(dashboard_status) # Display status/confirmation

            # Download Report Button
            if st.button("Generate Executive Report (.docx)", key="download_report_button"):
                summary_text = (
                    f"Financial Report for: {uploaded_excel.name}\n\n"
                    f"Income: ₹{income:,.2f}\n"
                    f"Expenses: ₹{expenses:,.2f}\n"
                    f"Profit: ₹{profit:,.2f} (Margin: {margin:.1%})\n\n"
                    f"Estimated Tax Liability (25% on Income): ₹{tax:,.2f}\n"
                    f"TDS Deducted: ₹{tds:,.2f}\n\n"
                    f"Output GST: ₹{output_gst:,.2f}\n"
                    f"Input GST: ₹{input_gst:,.2f}\n"
                    f"Net GST Payable: ₹{net_gst:,.2f}\n"
                )
                report_buffer = to_docx(summary_text)
                st.download_button(
                    label="Download Report Now",
                    data=report_buffer,
                    file_name=f"FinIQ_Report_{uploaded_excel.name}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
        else:
            st.error("Could not process the uploaded Excel file. Please check the file format and content.")

with tab_chat:
    st.header("Chat with Financial Expert")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input and processing
    if prompt := st.chat_input("Ask the financial expert..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing your query..."):
                try:
                    # Create system prompt for financial focus
                    system_prompt = f"""You are a financial expert assistant.
                        Respond to the user's query about financial matters: {prompt}
                        Provide clear, professional advice with explanations.
                        If discussing numbers, format them clearly."""
                    
                    # Get response from Mistral via Ollama
                    result = subprocess.run(
                        ['ollama', 'run', 'mistral', system_prompt],
                        capture_output=True,
                        text=True,
                        check=True,
                        encoding='utf-8'
                    )
                    response = result.stdout.strip()
                    
                    # Display and store response
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

                except subprocess.CalledProcessError as e:
                    st.error(f"Error generating response: {e.stderr}")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {str(e)}")


with tab_docs:
    st.header("Document Processing")

    def extract_due_date(text):
        """
        Extracts a potential due date from the text based on keywords.
        Looks for the first date after "due date", "deadline", or "payment by".
        """
        keywords = ["due date", "deadline", "payment by"]
        # Regex to find common date formats (DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD, Month Day, Year)
        # This is a basic pattern and might need refinement for more complex cases
        date_pattern = r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}'

        text_lower = text.lower()

        for keyword in keywords:
            keyword_index = text_lower.find(keyword)
            if keyword_index != -1:
                # Search for a date pattern after the keyword
                search_start_index = keyword_index + len(keyword)
                match = re.search(date_pattern, text[search_start_index:])
                if match:
                    return match.group(0) # Return the first found date after the keyword

        return None # Return None if no date is found after any keyword


    def process_document(uploaded_file):
        """
        Performs OCR on the uploaded document, extracts due date, and generates a response.
        """
        if uploaded_file is not None:
            with st.spinner("Processing document..."):
                # Create temporary directory if it doesn't exist
                UPLOAD_DIR = "data/uploads"
                os.makedirs(UPLOAD_DIR, exist_ok=True)

                # Save uploaded file temporarily
                file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())

                # Perform OCR
                extracted_text = perform_ocr(file_path)
                due_date = extract_due_date(extracted_text) # Extract due date
                if extracted_text:
                    # Generate response
                    response_letter = auto_draft_response(extracted_text)

                    # Display results
                    with st.expander(f"Results for {uploaded_file.name}", expanded=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("Extracted Text")
                            st.code(extracted_text, language="markdown")
                        with col2:
                            st.subheader("Generated Response")
                            ocr_edited_response = st.text_area(f"Edit OCR Response ({uploaded_file.name}):", response_letter, height=150, key=f"ocr_edit_{uploaded_file.name}")
                            ocr_docx_buffer = save_response_to_docx(ocr_edited_response)
                            st.download_button(
                                label=f"Download OCR Response (.docx)",
                                data=ocr_docx_buffer,
                                file_name=f"FinIQ_OCR_{uploaded_file.name}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )

                    # Add reminder if due date is found
                    if due_date:
                        st.write("Extracted Due Date:", due_date) # Display due date
                        st.session_state.due_date = due_date # Store in session state
                        # Add reminder to database - associate with selected client if available
                        client_id_for_reminder = st.session_state.selected_client_id if st.session_state.selected_client_id else None
                        reminder_description = f"Due date from {uploaded_file.name}"
                        try:
                            database.add_reminder(client_id_for_reminder, due_date, reminder_description)
                            st.success(f"Reminder added for {due_date}")
                        except Exception as e:
                            st.error(f"Error adding reminder to database: {e}")

                    else:
                        st.write("Due Date: Not found")
                        st.session_state.due_date = None


                    st.success(f"Successfully processed {uploaded_file.name}")
                    # Optionally add document to database here, linking to client if selected
                    # if st.session_state.selected_client_id:
                    #     try:
                    #         database.add_document(st.session_state.selected_client_id, uploaded_file.name, file_path, "Unknown") # Document type could be extracted or selected
                    #         st.info(f"Document linked to client ID: {st.session_state.selected_client_id}")
                    #     except Exception as e:
                    #         st.error(f"Error linking document to client: {e}")


                else:
                    return "Error: Could not extract text from document.", None
        else:
            return "Please upload a document.", None


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
                process_document(file) # Process each uploaded file


    st.markdown("---")
    st.caption("Note: Uploaded files are temporarily stored for processing.")


with tab_clients:
    st.header("Client Management")

    # Add Client Form
    with st.form("add_client_form_tab"):
        st.subheader("Add New Client")
        client_name = st.text_input("Client Name*")
        client_email = st.text_input("Email (optional)")
        client_phone = st.text_input("Phone (optional)")
        
        # Email validation using regex
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if client_email and not re.match(email_regex, client_email):
            st.error("Invalid email format.")
            submit_button = st.form_submit_button("Add Client", disabled=True) # Disable submit button if email is invalid
        else:
            submit_button = st.form_submit_button("Add Client")
        if submit_button:
            if client_name:
                try:
                    client_id = database.add_client(client_name, client_email, client_phone)
                    st.success(f"Client '{client_name}' added successfully with ID: {client_id}")
                    st.session_state.selected_client_id = client_id # Select the newly added client
                    st.rerun() # Rerun to update the client list and potentially select the new client
                except Exception as e:
                    st.error(f"Error adding client: {e}")
            else:
                st.error("Client Name is required.")

    st.markdown("---")
    st.subheader("Existing Clients")

    # Display Existing Clients
    clients = database.get_all_clients()
    if clients:
        client_names = [client[1] for client in clients]
        selected_client_name = st.selectbox("Select a Client", ["-- Select Client --"] + client_names)

        if selected_client_name != "-- Select Client --":
            # Find the selected client's ID
            selected_client = next((client for client in clients if client[1] == selected_client_name), None)
            if selected_client:
                st.session_state.selected_client_id = selected_client[0]
                st.write(f"**Selected Client:** {selected_client[1]}")
                st.write(f"Email: {selected_client[2]}")
                st.write(f"Phone: {selected_client[3]}")
                st.write(f"Added On: {selected_client[4]}")

                # Display documents for the selected client (Optional)
                # st.subheader("Documents")
                # client_documents = database.get_documents_by_client(st.session_state.selected_client_id)
                # if client_documents:
                #     for doc in client_documents:
                #         st.write(f"- {doc[2]} (Uploaded: {doc[5]})")
                # else:
                #     st.info("No documents found for this client.")

                # Display reminders for the selected client
                st.subheader("Reminders for this Client")
                client_reminders = database.get_reminders(st.session_state.selected_client_id)
                if client_reminders:
                    for reminder in client_reminders:
                        st.write(f"- **Due Date:** {reminder[2]}, **Description:** {reminder[3]}")
                else:
                    st.info("No reminders found for this client.")


        else:
            st.session_state.selected_client_id = None # Deselect client if "-- Select Client --" is chosen

    else:
        st.info("No clients added yet.")


with tab_reminders:
    st.header("Reminders")

    # Add New Reminder Form
    with st.form("add_reminder_form"):
        st.subheader("Add New Reminder")
        # Optionally link to a client
        clients_for_reminder = database.get_all_clients()
        client_options = {client[1]: client[0] for client in clients_for_reminder}
        selected_client_name_reminder = st.selectbox("Link to Client (optional)", ["-- Select Client --"] + list(client_options.keys()))
        linked_client_id = client_options.get(selected_client_name_reminder) if selected_client_name_reminder != "-- Select Client --" else None

        reminder_date = st.date_input("Due Date")
        reminder_time = st.time_input("Reminder Time", value=datetime.now().time()) # Add time input with default value
        reminder_frequency = st.selectbox("Frequency", ["Once", "Daily", "Weekly", "Monthly"], index=0) # Frequency dropdown
        reminder_description = st.text_area("Description")
        add_reminder_button = st.form_submit_button("Add Reminder")

        if add_reminder_button:
            if reminder_date and reminder_description:
                # Check if a client is linked and if they have an email
                if linked_client_id:
                    client = database.get_client_by_id(linked_client_id)
                    # client[2] is the email field from the database query result
                    if client and (client[2] is None or client[2].strip() == ""):
                        st.error("Cannot add reminder: Selected client does not have an email address.")
                        # Stop here if client has no email

                try:
                    # Convert date and time objects to strings for storage
                    due_date_str = reminder_date.strftime("%Y-%m-%d")
                    reminder_time_str = reminder_time.strftime("%H:%M") # Format time
                    database.add_reminder(linked_client_id, due_date_str, reminder_time_str, reminder_frequency, reminder_description)
                    st.success("Reminder added successfully!")
                    st.rerun() # Rerun to update the reminders list
                except Exception as e:
                    st.error(f"Error adding reminder: {e}")
            else:
                st.error("Due Date and Description are required.")

    st.markdown("---")
    st.subheader("Upcoming Reminders")

    # Display Reminders
    all_reminders = database.get_reminders()
    if all_reminders:
        # Sort reminders by due date
        sorted_reminders = sorted(all_reminders, key=lambda x: x[2])
        for reminder in sorted_reminders:
            client_info = ""
            if reminder[1]: # If client_id is not None
                client = database.get_client_by_id(reminder[1])
                if client:
                    client_info = f" (Client: {client[1]})"
            st.write(f"- **Due Date:** {reminder[2]}, **Description:** {reminder[3]}{client_info}")
    else:
        st.info("No reminders added yet.")
