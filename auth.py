"""
auth.py
────────────────────────────────────────────────
Login and Registration screens.
"""

import streamlit as st
from firebase_service import sign_in, sign_up, create_user_doc, get_user_doc


def show_login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("## 💪 Trainer-Client Sync")
        st.markdown("Your personal fitness dashboard — built for trainers and clients.")
        st.markdown("---")

        tab_login, tab_register = st.tabs(["🔑 Login", "📝 Register"])

        with tab_login:
            _login_form()

        with tab_register:
            _register_form()


# ─── LOGIN ────────────────────────────────────────────────────────────────────

def _login_form():
    st.subheader("Login to your account")
    with st.form("login_form", clear_on_submit=False):
        email    = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Login", use_container_width=True, type="primary")

    if submitted:
        if not email or not password:
            st.error("Please fill in both fields.")
            return
        try:
            with st.spinner("Signing in…"):
                auth_data = sign_in(email, password)
            uid      = auth_data["localId"]
            user_doc = get_user_doc(uid)
            if not user_doc:
                st.error("Account found but profile is missing. Please re-register.")
                return
            # Store user in session
            st.session_state.user = {
                "uid":         uid,
                "email":       email,
                "role":        user_doc["role"],
                "displayName": user_doc["displayName"],
                "trainerUid":  user_doc.get("trainerUid"),
            }
            st.success("Logged in!")
            st.rerun()
        except Exception as e:
            err = str(e)
            if any(k in err for k in ("INVALID_PASSWORD", "EMAIL_NOT_FOUND",
                                       "INVALID_LOGIN_CREDENTIALS", "INVALID_EMAIL")):
                st.error("❌ Invalid email or password.")
            else:
                st.error(f"Login failed: {err}")


# ─── REGISTER ─────────────────────────────────────────────────────────────────

def _register_form():
    st.subheader("Create a new account")
    with st.form("register_form", clear_on_submit=False):
        display_name     = st.text_input("Full Name", placeholder="John Doe")
        email            = st.text_input("Email", placeholder="you@example.com")
        password         = st.text_input("Password", type="password",
                                          placeholder="Min 6 characters")
        confirm_password = st.text_input("Confirm Password", type="password")
        role             = st.selectbox("Register as", ["Client", "Trainer"])

        trainer_uid = None
        if role == "Client":
            st.info("💡 Ask your trainer to share their Trainer UID with you.")
            trainer_uid = st.text_input("Trainer UID",
                                         placeholder="Paste your trainer's UID here")

        submitted = st.form_submit_button("Create Account",
                                          use_container_width=True, type="primary")

    if submitted:
        # Validation
        if not all([display_name, email, password, confirm_password]):
            st.error("Please fill in all fields.")
            return
        if password != confirm_password:
            st.error("Passwords do not match.")
            return
        if len(password) < 6:
            st.error("Password must be at least 6 characters.")
            return
        if role == "Client" and not trainer_uid:
            st.error("Please enter your Trainer UID.")
            return

        try:
            with st.spinner("Creating account…"):
                auth_data = sign_up(email, password)
            uid = auth_data["localId"]
            create_user_doc(
                uid=uid,
                email=email,
                display_name=display_name,
                role=role.lower(),
                trainer_uid=trainer_uid if role == "Client" else None,
            )
            st.success("✅ Account created! Please switch to the Login tab.")
        except Exception as e:
            err = str(e)
            if "EMAIL_EXISTS" in err:
                st.error("This email is already registered. Please login instead.")
            else:
                st.error(f"Registration failed: {err}")
