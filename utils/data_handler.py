import pandas as pd
import streamlit as st
from datetime import datetime
import json

def init_session_state():
    """Initialize session state variables"""
    if 'notes' not in st.session_state:
        st.session_state.notes = []
    if 'questions' not in st.session_state:
        st.session_state.questions = []
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    if 'reminders' not in st.session_state:
        st.session_state.reminders = []
    if 'users' not in st.session_state:
        st.session_state.users = {}

def save_uploaded_file(uploaded_file, title, description):
    """Save uploaded file information"""
    if uploaded_file is not None:
        file_details = {
            'title': title,
            'description': description,
            'filename': uploaded_file.name,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'content': uploaded_file.getvalue()
        }
        st.session_state.notes.append(file_details)
        return True
    return False

def add_question(title, content, author):
    """Add a new question"""
    question = {
        'id': len(st.session_state.questions),
        'title': title,
        'content': content,
        'author': author,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'votes': 0
    }
    st.session_state.questions.append(question)
    return question['id']

def add_answer(question_id, content, author):
    """Add an answer to a question"""
    if question_id not in st.session_state.answers:
        st.session_state.answers[question_id] = []
    
    answer = {
        'id': len(st.session_state.answers[question_id]),
        'content': content,
        'author': author,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'votes': 0
    }
    st.session_state.answers[question_id].append(answer)

def vote(item_type, item_id, vote_type, answer_id=None):
    """Handle voting on questions and answers"""
    if item_type == 'question':
        if 0 <= item_id < len(st.session_state.questions):
            st.session_state.questions[item_id]['votes'] += (1 if vote_type == 'up' else -1)
    elif item_type == 'answer':
        if item_id in st.session_state.answers:
            if 0 <= answer_id < len(st.session_state.answers[item_id]):
                st.session_state.answers[item_id][answer_id]['votes'] += (1 if vote_type == 'up' else -1)

def add_reminder(date, description):
    """Add a new reminder"""
    reminder = {
        'date': date,
        'description': description,
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    st.session_state.reminders.append(reminder)
