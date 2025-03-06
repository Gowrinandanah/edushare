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

    st.markdown(
        """
        <style>
            /* Change background color of the dropdown button */
            [data-testid="stExpander"] summary {
                background-color: #FFFFFF !important;  /* Orange */
                color: black !important;
                font-weight: bold;
                font-size: 18px;
                padding: 10px;
                border-radius: 10px;
                border: 2px solid #D84315; /* Darker border */
            }
            
            /* Optional: Change the hover effect */
            [data-testid="stExpander"] summary:hover {
                background-color: #F5FFFA !important; /* Darker orange */
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.header("📖 Notes Section")
    
    for subject, folder_id in SUBJECT_FOLDERS.items():
        with st.expander(f"**⚫{subject}**", expanded=False):
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
        
        if "reminders" not in st.session_state:
            st.session_state.reminders = load_reminders_from_drive()

        st.markdown("### 📋 Upcoming Reminders")
        if st.session_state.reminders:
            for reminder in sorted(st.session_state.reminders, key=lambda x: x["date"]):
                st.markdown(f"**📅 {reminder['date']}**")
                st.info(reminder["description"])

        # Use a unique identifier instead of `i`
                delete_key = f"del_{reminder['date']}_{reminder['description']}"
                if st.button(f"❌ Delete", key=delete_key):
                    st.session_state.reminders.remove(reminder)  # Remove by object reference
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



import time  # For smooth animations

def render_intro_page():
    """Displays the animated introduction page for EduShare."""
    st.markdown(
        """
        <style>
            .intro-title {
                font-size: 36px;
                font-weight: bold;
                text-align: center;
                margin-top: 50px;
            }
            .feature-box {
                background-color: rgba(255, 255, 255, 0.1);
                padding: 20px;
                margin: 20px auto;
                border-radius: 15px;
                text-align: center;
                box-shadow: 2px 2px 15px rgba(255, 255, 255, 0.2);
                transition: all 0.5s ease-in-out;
            }
            .feature-box:hover {
                transform: scale(1.05);
                background-color: rgba(255, 255, 255, 0.2);
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class='intro-title'>🚀 Welcome to EduShare</div>
    <p class='intro-text'>EduShare is your go-to platform for collaborative learning. Share notes, ask questions, stay organized, and personalize your learning experience—all in one place.</p>
    
    <h2 class='features-heading'>🌟 Features</h2>
     """, unsafe_allow_html=True)

    # Animated feature reveal
    features = [
        "📖 Notes Sharing - Upload & Download Subject Notes",
        "❓ Q&A Section - Ask & Answer Questions",
        "📅 Calendar & Reminders - Keep Track of Your Tasks",
        "👤 User Profiles - Customize Your Learning Experience"
    ]


    for feature in features:
        with st.container():
            time.sleep(0.5)  # Delay for smooth animation
            st.markdown(f"<div class='feature-box'>{feature}</div>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Button to navigate to the main sections
    if st.button("🚀 Get Started", key="home_start", use_container_width=True):
            st.session_state.current_page = "Notes"  # Navigate to Notes section
            st.rerun()




def add_sidebar_background(image_path="background.jpg"):
    """Applies a background PNG image to the sidebar and ensures it is not transparent."""
    with open(image_path, "rb") as f:
        encoded_string = base64.b64encode(f.read()).decode()

    sidebar_style = f"""
        <style>
            [data-testid="stSidebar"] {{
                background: url("data:image/png;base64,{encoded_string}") no-repeat center center !important;
                background-size: cover !important;
                background-color: rgba(0, 0, 0, 1) !important; /* Ensures full opacity */
                opacity: 1 !important;
            }}
            [data-testid="stSidebarContent"] {{
                background: none !important; /* Prevents inner transparency */
            }}
             
            
        

        </style>
    """
    st.markdown(sidebar_style, unsafe_allow_html=True)




import base64

def set_bg_and_theme():
    """Sets Squid Game theme in Streamlit using CSS."""
    
    # Background Image
    bg_image = "image.jpg"  # Ensure this file is in the same directory
    with open(bg_image, "rb") as img_file:
        img_data = img_file.read()
    
    encoded_img = base64.b64encode(img_data).decode()
    
    # CSS Theme
    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Moon+Dance&display=swap');

    
    .stApp {{
        background: url("data:image/jpg;base64,{encoded_img}") no-repeat center center fixed;
        background-size: cover;
        color: white;
        font-family: 'Press Start 2P', cursive;
    }}

    .stMarkdown, .stTitle {{
        color: #FFFFFF; /* Squid Game pink */
    }}

    .stButton>button {{
        background-color: #000000;
        color: white;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: bold;
        border: none;
    }}

    .stButton>button:hover {{
        background-color: white;
        color: #FFFFFF ;
    }}

    /* Make the calendar input text bigger and bolder */
    div[data-baseweb="input"] input {{
        font-size: 20px !important; /* Bigger size */
        font-weight: 900 !important; /* Thicker text */
        color: #FFFFFF !important; /* Squid Game pink */
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)









def apply_ui_template():
    st.markdown("""
    <style>
    /* Sidebar Background & Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(to bottom, #FFFFFF , #FFFFFF); /* ORANGE gradient */
        color: black;
    }
      /* Fix for calendar date input text */
    
    div[data-baseweb="input"] input {
        background-color: #333333 !important; /* Light gray background */
        border: 1px solid #d1d1d1 !important; /* Subtle gray border */
        color: black !important; /* Ensures text is visible */
        font-size: 18px !important; /* Bigger text */
        font-weight: bold !important; /* Thicker text */
        border-radius: 5px; /* Rounded edges */
        padding: 8px; /* Adds spacing inside the input */
    }
    
                
    [data-testid="stSidebarNav"] button, 
    [data-testid="stSidebarNav"] button * {
        color: black !important;  /* Ensures all text inside is black */
    }
                

    [data-testid="stSidebarContent"]  {
        margin-top: -75px  !important;
        padding-top: -10px  !important;      
    }
    [data-testid="stSidebarNav"] button {
        background-color: black !important;
        color: black !important;
        border: none !important;
        text-align: left;
        font-size: 16px;
        padding: 10px;
        width: 100%;
    }
    [data-testid="stSidebarNav"] button:hover {
        background-color: rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px;
    }

    /* Main Page Background */
    body {
        background-color: #f0f0f0 !important;
        color: #333 !important;
    }

    /* Headers */
    h2, h3 {
        color: #FFFFFF !important;  /* Dark Blue */
    }
    [data-testid="stSidebarNav"], 
    [data-testid="stSidebarNav"] * {
    color: black !important;  /* Ensures all text inside the sidebar nav is black */
    }
     
      /* Ensure settings menu text is visible */
    [data-testid="stSidebarUserMenu"] * {
        color: black !important; /* Default to black for light mode */
    }

    


    /* Cards for Sections */
    .card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }

    /* Buttons */
    .stButton>button {
        background-color:  #808080 !important;
        color: black !important;
        border-radius: 8px;
        font-size: 16px;
        padding: 10px 20px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #C0C0C0 !important;
    }
    
           
    

    /* Inputs */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea {
        background-color: #555555 !important;
        border: 1px solid #FFFFFF !important;
        color: black !important;
        border-radius: 8px;
        padding: 10px;
    }
    
    </style>
    """, unsafe_allow_html=True)


def main():
    
    st.set_page_config(page_title="EduShare", page_icon=" ", layout="wide")

    st.markdown(
        """
        <style>
            .nav-button {
                display: block;
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                font-size: 18px;
                font-weight: bold;
                color: black;
                background-color: white;
                text-align: center;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                transition: background 0.3s ease;
            }

            .nav-button:hover {
                background-color: #f0f0f0;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    apply_ui_template()
    set_bg_and_theme()
    add_sidebar_background("background.jpg")
   

    if "reminders" not in st.session_state:
        st.session_state.reminders = load_reminders_from_drive() or []

    if "entered_platform" not in st.session_state:
        st.session_state.entered_platform = False

    if "current_page" not in st.session_state:
        st.session_state.current_page = "Home"

    if not st.session_state.entered_platform:
        st.markdown("""
        <div style="text-align: center;">
            <h1>  EduShare </h1>
            <p>A Collaborative Learning Experience</p>
        </div>
        """, unsafe_allow_html=True)
        st.image("icon.png", use_container_width=True)
        

        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])  # Create 3 columns
        with col2:  # The middle column
            # Custom button with background color and padding
            if st.button("🚀 ENTER PLATFORM", key="enter_platform", help="Click to enter the platform", use_container_width=True):
                st.session_state.entered_platform = "Home"
                st.rerun()  

    else:
        st.sidebar.title("  EduShare Platform")
        #nav_selection = st.sidebar.radio("Navigation", ["Home","Notes", "Calendar", "Q&A", "Profile"], 
         #   index=["Home", "Notes", "Calendar", "Q&A", "Profile"].index(st.session_state.current_page)
        #)
        
        #if nav_selection != st.session_state.current_page:
         #   st.session_state.current_page = nav_selection
          #  st.rerun()
        
        if st.sidebar.button("🏠 Home", use_container_width=True):
            st.session_state.current_page = "Home"
            st.rerun()

        if st.sidebar.button("📖 Notes", use_container_width=True):
            st.session_state.current_page = "Notes"
            st.rerun()

        if st.sidebar.button("📅 Calendar", use_container_width=True):
            st.session_state.current_page = "Calendar"
            st.rerun()

        if st.sidebar.button("❓ Q&A", use_container_width=True):
            st.session_state.current_page = "Q&A"
            st.rerun()

        if st.sidebar.button("👤 Profile", use_container_width=True):
            st.session_state.current_page = "Profile"
            st.rerun()



        if st.session_state.current_page == "Home":
            render_intro_page()
        elif st.session_state.current_page == "Notes":
            render_notes_section()
        elif st.session_state.current_page == "Calendar":
            render_calendar_section()
        elif st.session_state.current_page == "Q&A":
            render_qa_section()
        elif st.session_state.current_page == "Profile":
            render_user_profile()
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center'>
        <p>EduShare Platform - Making Learning Collaborative</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
