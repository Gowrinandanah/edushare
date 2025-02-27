import streamlit as st
import os
import json
import datetime
import calendar
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from io import BytesIO



# Path to your Google Drive service account JSON file
SERVICE_ACCOUNT_FILE = r"C:\Users\Gowri\OneDrive\Desktop\python\LearnShare\edusharewebsite-efa425f24047.json"
SCOPES = ['https://www.googleapis.com/auth/drive']

# Authenticate Google Drive
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

# Google Drive Folder ID
#NOTES_FOLDER_ID = "1gZ_18i_IO4l_hn1bJVTT3fMuazoIvCJr"
CALENDAR_FOLDER_ID = "1eXLPz-xz7bfOuQDHraNQJ1Gq0jd93wW5"
QA_FOLDER_ID = "1MBbMLp6iJh37DIADjPQ3w4tWfE2Nk3nu"
# Reminders file name
REMINDERS_FILE_NAME = "reminders.json"

QA_FILE_NAME = "qa_data.json"


def upload_to_drive(file, folder_id):
    """Uploads a file to the specified Google Drive folder."""
    file_metadata = {
        'name': file.name,
        'parents': [folder_id]  # Store in the correct folder
    }
    
    # Convert the uploaded file to a format that Google Drive API accepts
    media = MediaIoBaseUpload(file, mimetype=file.type, resumable=True)
    
    uploaded_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    
    return uploaded_file.get('id')


def list_drive_files(folder_id):
    """Lists files in a specific Google Drive folder."""
    query = f"'{folder_id}' in parents"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    return results.get('files', [])

# Google Drive Folder IDs for different subjects
SUBJECT_FOLDERS = {
    "Subject A": "1gZ_18i_IO4l_hn1bJVTT3fMuazoIvCJr",
    "Subject B": "1VPSgY4Bm0hNoavmmgfIcv0jq4W_R04zC",
    "Subject C": "1-OpbFpv13J9DV5pDtOQL7zwUohmnZp_0",
    "Subject D": "1LQ1IE452CbnGHeoWSmayu9h4vNRYwD-e",
}

def render_notes_section():
    st.header("📚 Notes Section")
    
    for subject, folder_id in SUBJECT_FOLDERS.items():
        with st.expander(f"📌 {subject}", expanded=False):
            st.markdown("### 📜 Uploaded Files")
            uploaded_files = list_drive_files(folder_id)  # Fetch files from the specific folder
            
            if uploaded_files:
                for file in uploaded_files:
                    file_link = f"https://drive.google.com/file/d/{file['id']}/view"
                    st.markdown(f"📥 [{file['name']}]({file_link})")
            else:
                st.info(f"No files uploaded yet for {subject}.")
            
            st.markdown("---")  # Separator for clarity
            
            st.markdown(f"**Upload your notes for {subject}**")
            file = st.file_uploader(f"Choose a file for {subject}", type=["pdf", "docx", "txt"], key=f"uploader_{subject}")
            if st.button("Upload", key=f"upload_{subject}") and file is not None:
                file_id = upload_to_drive(file, folder_id)  # Upload to the specific subject folder
                st.success(f"✅ File '{file.name}' uploaded successfully! ID: {file_id}")




def save_reminders_to_drive():
    """Saves reminders to Google Drive in the Calendar folder."""
    reminders_json = json.dumps(st.session_state.reminders, indent=4)
    file_stream = BytesIO(reminders_json.encode())

    query = f"name='{REMINDERS_FILE_NAME}' and '{CALENDAR_FOLDER_ID}' in parents"
    results = drive_service.files().list(q=query, fields="files(id)").execute()
    files = results.get('files', [])

    if files:
        file_id = files[0]['id']
        drive_service.files().update(
            fileId=file_id,
            media_body=MediaIoBaseUpload(file_stream, mimetype='application/json', resumable=True)
        ).execute()
    else:
        file_metadata = {'name': REMINDERS_FILE_NAME, 'parents': [CALENDAR_FOLDER_ID]}
        drive_service.files().create(
            body=file_metadata,
            media_body=MediaIoBaseUpload(file_stream, mimetype='application/json', resumable=True)
        ).execute()


def load_reminders_from_drive():
    """Loads reminders from the Calendar folder in Google Drive."""
    query = f"name='{REMINDERS_FILE_NAME}' and '{CALENDAR_FOLDER_ID}' in parents"
    results = drive_service.files().list(q=query, fields="files(id)").execute()
    files = results.get('files', [])

    if files:
        file_id = files[0]['id']
        request = drive_service.files().get_media(fileId=file_id)
        file_stream = BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        file_stream.seek(0)
        return json.load(file_stream)
    return []


def render_calendar_section():
    st.header("📅 Calendar & Reminders")

    col1, col2 = st.columns([2, 1])

    with col1:
        current_date = datetime.datetime.now()
        year, month = current_date.year, current_date.month
        cal = calendar.monthcalendar(year, month)

        st.subheader(f"📆 {current_date.strftime('%B %Y')}")
        
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        cols = st.columns(7)
        for col, day in zip(cols, days):
            col.markdown(f"**{day}**")

        for week in cal:
            cols = st.columns(7)
            for col, day in zip(cols, week):
                if day == 0:
                    col.markdown(" ")
                elif day == current_date.day:
                    col.markdown(f"🎯 **{day}**")
                else:
                    col.markdown(f"**{day}**")

        st.markdown("---")

    with col2:
        st.subheader("➕ Add Reminder")
        reminder_date = st.date_input("📅 Select Date", min_value=datetime.date.today())  
        reminder_desc = st.text_area("📝 Description", height=100)

        if st.button("💾 Save Reminder"):
            if reminder_desc:
                new_reminder = {"date": reminder_date.strftime("%Y-%m-%d"), "description": reminder_desc}
                st.session_state.reminders.append(new_reminder)
                save_reminders_to_drive()
                st.success("✅ Reminder added successfully!")
                st.rerun()
            else:
                st.error("❌ Please enter a description.")

        st.markdown("### 📋 Upcoming Reminders")
        if st.session_state.reminders:
            for i, reminder in enumerate(sorted(st.session_state.reminders, key=lambda x: x["date"])):
                st.markdown(f"**📅 {reminder['date']}**")
                st.info(reminder["description"])
                if st.button(f"❌ Delete", key=f"del_{i}"):
                    del st.session_state.reminders[i]
                    save_reminders_to_drive()
                    st.rerun()
        else:
            st.info("No reminders added yet.")







# Google Drive Configuration
SCOPES = ['https://www.googleapis.com/auth/drive']
FOLDER_ID = QA_FOLDER_ID  # Use the same folder for both questions and answers

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

# Filenames for storing questions and answers
QUESTIONS_FILE = "questions.json"
ANSWERS_FILE = "answers.json"

def save_data(file_name, data):
    json_data = json.dumps(data, indent=4)
    file_stream = BytesIO(json_data.encode())
    
    query = f"name='{file_name}' and '{FOLDER_ID}' in parents"
    results = drive_service.files().list(q=query, fields="files(id)").execute()
    files = results.get('files', [])
    
    if files:
        file_id = files[0]['id']
        drive_service.files().update(
            fileId=file_id,
            media_body=MediaIoBaseUpload(file_stream, mimetype='application/json', resumable=True)
        ).execute()
    else:
        file_metadata = {'name': file_name, 'parents': [FOLDER_ID]}
        drive_service.files().create(
            body=file_metadata,
            media_body=MediaIoBaseUpload(file_stream, mimetype='application/json', resumable=True)
        ).execute()

def load_data(file_name):
    query = f"name='{file_name}' and '{FOLDER_ID}' in parents"
    results = drive_service.files().list(q=query, fields="files(id)").execute()
    files = results.get('files', [])
    
    if files:
        file_id = files[0]['id']
        request = drive_service.files().get_media(fileId=file_id)
        file_stream = BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        file_stream.seek(0)
        return json.load(file_stream)
    return []

def render_qa_section():
    st.header("❓ Q&A Section")
    
    if "questions" not in st.session_state:
        st.session_state.questions = load_data(QUESTIONS_FILE) or []
    if "answers" not in st.session_state:
        st.session_state.answers = load_data(ANSWERS_FILE) or {}
    
    user_name = st.session_state.get("user_name", "Anonymous")
    
    with st.expander("📝 Ask a Question"):
        question_title = st.text_input("Question Title")
        if st.button("Post Question") and question_title:
            new_question = {
                "id": len(st.session_state.questions) + 1,
                "title": question_title,
                "asked_by": user_name,
                "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            st.session_state.questions.append(new_question)
            save_data(QUESTIONS_FILE, st.session_state.questions)
            st.success("✅ Question posted successfully!")
            st.rerun()
    
    for question in st.session_state.questions:
        with st.expander(f"📘 {question['title']} (Asked by {question['asked_by']})"):
            st.markdown(f"*Asked on {question['timestamp']}*")
            question_id = question['id']
            
            # Display existing answers
            if str(question_id) in st.session_state.answers:
                for answer in st.session_state.answers[str(question_id)]:
                    st.markdown(f"✅ **{answer['answered_by']}** *(Answered on {answer['timestamp']})*")
                    st.info(answer['answer_text'])
            
            # Check if user already answered
            user_already_answered = any(ans['answered_by'] == user_name for ans in st.session_state.answers.get(str(question_id), []))
            
            if not user_already_answered:
                user_answer = st.text_area("Your Answer", key=f"answer_{question_id}")
                if st.button("Post Answer", key=f"post_answer_{question_id}") and user_answer:
                    new_answer = {
                        "answered_by": user_name,
                        "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "answer_text": user_answer
                    }
                    if str(question_id) not in st.session_state.answers:
                        st.session_state.answers[str(question_id)] = []
                    st.session_state.answers[str(question_id)].append(new_answer)
                    save_data(ANSWERS_FILE, st.session_state.answers)
                    st.success("✅ Answer posted successfully!")
                    st.rerun()



def render_user_profile():
    st.header("👤 User Profile")
    user_name = st.text_input("Enter your name", value=st.session_state.get("user_name", "Anonymous"))
    user_profession = st.text_input("Enter your profession", value=st.session_state.get("user_profession", "Anonymous"))
    if st.button("Save Changes"):
        st.session_state["user_name"] = user_name
        st.session_state["user_profession"] = user_profession
        st.success("✅ Profile updated successfully!")
        st.rerun()

def main():
    st.set_page_config(page_title="EduShare Platform", page_icon="📚", layout="wide")
    st.markdown("""
    <style>
    /* Sidebar Background Color */
    .stSidebar[data-testid="stSidebar"] {
        background-color: #fd5d00 !important;  /* Forest Green background */
        color: #FFFFFF !important; /* White text */
    }

    /* Adjust Sidebar Text */
    .stSidebar[data-testid="stSidebar"] .st-radio label, 
    .stSidebar[data-testid="stSidebar"] .stSlider label,
    .stSidebar[data-testid="stSidebar"] .stTextInput label {
        color: #FFFFFF !important; /* White text for labels in sidebar */
    }

    /* Sidebar Menu Background */
    .stSidebar[data-testid="stSidebar"] .css-1d391kg {
        background-color: #ed0909 !important;  /* Forest Green Background */
    }

    /* Sidebar Button Style */
    .stSidebar[data-testid="stSidebar"] .stButton button {
        background-color: #d40846 !important; /* Medium Green for buttons */
        color: white !important;
    }

    /* Hover Effect on Sidebar Buttons */
    .stSidebar[data-testid="stSidebar"] .stButton button:hover {
        background-color: #3B8F57 !important; /* Darker Green on hover */
    }

    /* General Background Color for the Whole Page */
    body {
        background-color: #F1F8E6 !important; /* Light Greenish background */
        color: #2C6B2F !important; /* Dark Green text */
    }

    /* Text on Main Body */
    .stTextInput>div>div>input, 
    .stTextArea>div>div>textarea {
        background-color: #D9F0C7 !important; /* Pale Green background for inputs */
        color: #2C6B2F !important; /* Dark Green text */
        border: 1px solid #A5D08D !important; /* Light Green border */
    }

    /* Buttons */
    .stButton>button {
        background-color: #dd1515 !important; /* Medium Green buttons */
        color: #FFFFFF !important; /* White text */
        border-radius: 5px;
        padding: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        border: none;
        width: 100%;
        margin-bottom: 5px;
    }

    .stButton>button:hover {
        background-color: #3B8F57 !important; /* Darker Green */
    }

    /* Header */
    .css-1aumxhk {
        background-color: #4C9F70 !important; /* Medium Green header */
        color: #FFFFFF !important; /* White text */
    }

    /* Input labels */
    .stTextInput>label, .stTextArea>label, .stNumberInput>label {
        color: #c31414 !important; /* Dark Green */
    }

    </style>
    """, unsafe_allow_html=True)

    if "reminders" not in st.session_state:
        st.session_state.reminders = load_reminders_from_drive() or []

    if "entered_platform" not in st.session_state:
        st.session_state.entered_platform = False
    if not st.session_state.entered_platform:
        st.markdown("""
        <div style="text-align: center;">
            <h1>📚 EduShare Platform</h1>
            <p>A Collaborative Learning Experience</p>
        </div>
        """, unsafe_allow_html=True)
        st.image("generated-icon.png", use_container_width=True)
        

        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])  # Create 3 columns
        with col2:  # The middle column
            # Custom button with background color and padding
            if st.button("🚀 Enter Platform", key="enter_platform", help="Click to enter the platform", use_container_width=True):
                st.session_state.entered_platform = True
                st.rerun()  

    else:
        st.sidebar.title("📚 EduShare Platform")
        nav_selection = st.sidebar.radio("Navigation", ["Notes", "Calendar", "Q&A", "Profile"])
        if nav_selection == "Notes":
            render_notes_section()
        elif nav_selection == "Calendar":
            render_calendar_section()
        elif nav_selection == "Q&A":
            render_qa_section()
        elif nav_selection == "Profile":
            render_user_profile()
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center'>
        <p>EduShare Platform - Making Learning Collaborative</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
