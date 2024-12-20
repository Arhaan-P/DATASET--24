import streamlit as st
import json
import os
from src.main import main

def load_credentials():
    if not os.path.exists("credentials.json"):
        with open("credentials.json", "w") as f:
            json.dump({}, f)
    
    with open("credentials.json", "r") as f:
        return json.load(f)

def save_credentials(credentials):
    with open("credentials.json", "w") as f:
        json.dump(credentials, f, indent=4)

def login_page():
    st.title("Welcome! 👋")
    
    # Initialize session state variables
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None

    # Create tabs for login and registration
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    # Login tab
    with tab1:
        st.header("Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            credentials = load_credentials()
            if username in credentials and credentials[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")
    
    # Registration tab
    with tab2:
        st.header("Register")
        new_username = st.text_input("Choose Username", key="reg_username")
        new_password = st.text_input("Choose Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        
        if st.button("Register"):
            if new_password != confirm_password:
                st.error("Passwords don't match!")
            else:
                credentials = load_credentials()
                if new_username in credentials:
                    st.error("Username already exists!")
                else:
                    credentials[new_username] = new_password
                    save_credentials(credentials)
                    st.success("Registration successful! Please login.")
    
# Main flow control
if __name__ == "__main__":
    if not st.session_state.get('logged_in', False):
        login_page()
    else:
        # Pass the logged-in username to the main function
        main(st.session_state.username)