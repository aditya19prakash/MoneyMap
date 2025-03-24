import streamlit as st
from Home import home
from database import users_collection

if "authenticate" not in st.session_state:
    st.session_state["authenticate"] = False

if "username" not in st.session_state:
    st.session_state["username"] = None

def login():
    if not st.session_state["authenticate"]:
        col1, col2, col3 = st.columns([0.5, 2, 0.5])
        with col2:
            tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
            
           
            with tab1:
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.button("Login", use_container_width=True):
                    if check_credentials(username, password):
                        st.session_state["authenticate"] = True 
                        st.session_state["username"] = username
                        st.success("Login Success")
                    else:
                        st.error("Invalid username or password")

           
            with tab2:
                new_username = st.text_input("New Username")
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                if st.button("Create Account", use_container_width=True):
                    if new_password != confirm_password:
                        st.warning("Passwords do not match")
                    else:
                        create_user(new_username, new_password)

    else:
        home()  

def create_user(username, password):
    if users_collection.find_one({"username": username}):
        st.warning("Username already exists!")
    else:
        users_data = {"username": username, "password": password}
        users_collection.insert_one(users_data)
        st.success("Account created successfully!")

def check_credentials(username, password) -> bool:
    user = users_collection.find_one({"username": username, "password": password})
    return bool(user)
