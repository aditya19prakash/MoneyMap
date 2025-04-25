import streamlit as st
from Home import home
from database import users_collection
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None

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


try:
    st.set_page_config(page_title="Money Mapper", layout="wide")
except Exception as e:
    st.error(f"Error setting page config: {str(e)}")

st.markdown("<h1 style='text-align: center; color: white;'>Money Mapper</h1>", unsafe_allow_html=True)

if not st.session_state["authenticated"]:
    try:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
                <style>
                .login-box {
                    background-color: #333333;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    margin: 20px 0;
                    color: white;
                }
                </style>
                """, unsafe_allow_html=True)

            tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
            with tab1:
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.button("Login", use_container_width=True):
                    if check_credentials(username, password):
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = username
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
            with tab2:
                new_username = st.text_input("New Username")
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                if st.button("Sign Up", use_container_width=True):
                    if new_username and new_password:
                        if new_password != confirm_password:
                            st.error("Passwords don't match!")
                        elif create_user(new_username, new_password):
                            st.success("Account created successfully! Please sign in.")
                        else:
                            st.error("Username already exists!")
                    else:
                        st.error("Please fill all fields")
    except Exception as e:
        st.error(f"Error in login interface: {str(e)}")
else:
    try:
        col1, col2, col3 = st.columns([1, 8, 1])
        with col3:
            if st.button("Logout", key="logout"):
                st.session_state.clear()
                st.rerun()
        home()
    except Exception as e:
        st.error(f"Error in logout process: {str(e)}")
