"""
app.py  ← Entry point. Run with: streamlit run app.py
────────────────────────────────────────────────
Trainer-Client Sync — Streamlit Web App
  • Role-based routing: Trainer → trainer dashboard, Client → client dashboard
  • Session state holds the logged-in user
  • No file/media permissions required anywhere
"""

import streamlit as st

# Must be the very first Streamlit call
st.set_page_config(
    page_title  = "Trainer-Client Sync",
    page_icon   = "💪",
    layout      = "wide",
    initial_sidebar_state = "collapsed",
)

# Minimal global style tweaks
st.markdown("""
<style>
  /* Tighten the top padding */
  .block-container { padding-top: 2rem; }

  /* Make primary buttons pop */
  .stButton > button[kind="primary"] {
      font-weight: 600;
      letter-spacing: 0.3px;
  }

  /* Metric cards */
  div[data-testid="metric-container"] {
      background-color: var(--secondary-background-color);
      border-radius: 8px;
      padding: 1rem;
  }
</style>
""", unsafe_allow_html=True)

# Lazy imports (after page config)
from auth         import show_login_page
from trainer_view import show_trainer_dashboard
from client_view  import show_client_dashboard


def main():
    # Initialise session if first visit
    if "user" not in st.session_state:
        st.session_state.user = None

    user = st.session_state.user

    if user is None:
        show_login_page()
        return

    role = user.get("role", "client")
    if role == "trainer":
        show_trainer_dashboard()
    else:
        show_client_dashboard()


if __name__ == "__main__":
    main()
