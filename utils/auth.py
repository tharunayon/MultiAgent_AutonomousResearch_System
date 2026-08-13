import streamlit as st

# Define role constants
ROLE_DOCTOR = "doctor"
ROLE_PATIENT = "patient"

ROLE_LABELS = {
    ROLE_DOCTOR: "Authorized Medical Practitioner (Doctor)",
    ROLE_PATIENT: "Normal Patient"
}

def init_auth():
    """Initializes authentication variables in streamlit session state."""
    if "user_role" not in st.session_state:
        st.session_state.user_role = ROLE_PATIENT

def get_user_role() -> str:
    """Returns the current user role."""
    init_auth()
    return st.session_state.user_role

def set_user_role(role: str):
    """Sets the user role to the specified value."""
    if role in [ROLE_DOCTOR, ROLE_PATIENT]:
        st.session_state.user_role = role

def render_auth_sidebar():
    """Renders the authentication/role selection widget in the Streamlit sidebar."""
    init_auth()
    
    st.sidebar.markdown("<div class='sidebar-header'>Role-Based Access Control</div>", unsafe_allow_html=True)
    
    # Map raw role string to user-friendly label
    current_label = ROLE_LABELS[st.session_state.user_role]
    options = list(ROLE_LABELS.values())
    default_index = options.index(current_label)
    
    selected_label = st.sidebar.selectbox(
        "Select User Role:",
        options=options,
        index=default_index,
        key="role_selectbox_nav"
    )
    
    # Reverse lookup key from label
    new_role = next(key for key, val in ROLE_LABELS.items() if val == selected_label)
    
    if new_role != st.session_state.user_role:
        st.session_state.user_role = new_role
        st.rerun()
