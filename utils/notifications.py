import streamlit as st
from datetime import datetime, date

def check_reminders():
    """Check and display active reminders"""
    today = date.today()
    current_reminders = []
    
    for reminder in st.session_state.reminders:
        reminder_date = datetime.strptime(reminder['date'], '%Y-%m-%d').date()
        if reminder_date == today:
            current_reminders.append(reminder)
    
    return current_reminders

def display_notifications():
    """Display notification messages"""
    reminders = check_reminders()
    
    if reminders:
        with st.sidebar:
            st.markdown("### 📌 Today's Reminders")
            for reminder in reminders:
                st.info(reminder['description'])
