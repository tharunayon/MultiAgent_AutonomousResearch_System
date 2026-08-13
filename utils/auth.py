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
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user_role" not in st.session_state:
        st.session_state.user_role = ROLE_PATIENT
    if "current_view" not in st.session_state:
        st.session_state.current_view = "login"

def get_user_role() -> str:
    """Returns the current user role."""
    init_auth()
    return st.session_state.user_role

def set_user_role(role: str):
    """Sets the user role to the specified value."""
    if role in [ROLE_DOCTOR, ROLE_PATIENT]:
        st.session_state.user_role = role

def render_login_page():
    """Renders the secure split-layout login page for Patient and Practitioner."""
    init_auth()
    
    st.markdown("""
    <div class="login-header-logo" style="text-align: center; margin-top: 3rem; margin-bottom: 2rem;">
        <span style="font-family: 'Outfit'; font-weight: 850; font-size: 2.2rem; color: #1E293B; letter-spacing: -0.5px;">
            DHANVA TEACH <span style="color: #FF4B4B; font-weight: 500; font-size: 1.4rem;">Portal</span>
        </span>
    </div>
    """, unsafe_allow_html=True)

    login_col1, login_col2 = st.columns([1.1, 0.9])
    
    with login_col1:
        st.markdown("""
        <div class="login-promo-card">
            <div class="hero-pill" style="background-color: #E0F2FE; color: #0284C7; border-color: #BAE6FD; margin-bottom: 1rem;">SECURE MEDICAL SEARCH</div>
            <h2 style="font-size: 2.2rem; font-weight: 850; color: #1E293B; line-height: 1.2; margin-bottom: 1rem;">
                Empowering Practitioners & Supporting Patients
            </h2>
            <p style="color: #475569; font-size: 1.1rem; line-height: 1.6; margin-bottom: 2rem;">
                Dhanva Teach provides automated retrieval-augmented translation of restricted medical documents, 
                audited by automated fact-checking systems to guarantee medical grounding.
            </p>
            <div style="border-left: 3px solid #0052FF; padding-left: 1rem; margin-bottom: 2rem;">
                <span style="display: block; font-weight: 700; color: #1E293B; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 0.5px;">Security Boundary Isolation</span>
                <span style="color: #64748B; font-size: 0.9rem;">FAISS clinical database is mathematically isolated based on your credential level.</span>
            </div>
            <div style="border-left: 3px solid #10B981; padding-left: 1rem;">
                <span style="display: block; font-weight: 700; color: #1E293B; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 0.5px;">Integrity Audits</span>
                <span style="color: #64748B; font-size: 0.9rem;">Automated clinical router and auditor ensure zero-hallucination patient summaries.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with login_col2:
        st.markdown('<div class="login-form-card">', unsafe_allow_html=True)
        st.markdown("<div style='font-family: \"Outfit\"; font-weight: 700; font-size: 1.4rem; color: #1E293B; margin-bottom: 0.2rem;'>Secure Portal Sign-In</div>", unsafe_allow_html=True)
        st.markdown("<div style='color: #64748B; font-size: 0.9rem; margin-bottom: 1.5rem;'>Choose your profile level to access the workspace.</div>", unsafe_allow_html=True)
        
        # User role selection
        selected_role_label = st.radio(
            "Select Your Access Level:",
            options=["Normal Patient (Public Guidelines)", "Medical Practitioner (Restricted Database)"],
            index=0
        )
        
        is_doctor = "Medical Practitioner" in selected_role_label
        
        passkey = ""
        if is_doctor:
            passkey = st.text_input("Enter Practitioner Passkey:", type="password", help="Verify your practitioner credentials.")
            
        st.write("")
        if st.button("Sign In to Portal Workspace", use_container_width=True):
            if is_doctor:
                if passkey == "dhanva":
                    st.session_state.logged_in = True
                    st.session_state.user_role = ROLE_DOCTOR
                    st.session_state.current_view = "home"
                    st.success("Access Granted. Loading Portal Home...")
                    st.rerun()
                else:
                    st.error("Invalid Practitioner Passkey. Access Denied.")
            else:
                st.session_state.logged_in = True
                st.session_state.user_role = ROLE_PATIENT
                st.session_state.current_view = "home"
                st.success("Loading Patient Portal Home...")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

def render_auth_sidebar():
    """Renders the user profile status and secure logout controls in the sidebar."""
    init_auth()
    if not st.session_state.logged_in:
        return
        
    st.sidebar.markdown("<div class='sidebar-header'>Session Status</div>", unsafe_allow_html=True)
    
    role = st.session_state.user_role
    if role == ROLE_DOCTOR:
        st.sidebar.markdown("""
        <div style='background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 0.8rem; border-radius: 8px; margin-bottom: 1rem;'>
            <div style='font-size: 0.75rem; color: #64748B; font-weight: 700; text-transform: uppercase;'>Access Profile</div>
            <div style='font-size: 0.95rem; font-weight: 700; color: #0052FF;'>Practitioner</div>
            <div style='font-size: 0.7rem; color: #10B981; font-weight: 600; margin-top: 0.2rem;'>● SECURE SESSION</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.sidebar.markdown("""
        <div style='background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 0.8rem; border-radius: 8px; margin-bottom: 1rem;'>
            <div style='font-size: 0.75rem; color: #64748B; font-weight: 700; text-transform: uppercase;'>Access Profile</div>
            <div style='font-size: 0.95rem; font-weight: 700; color: #475569;'>Normal Patient</div>
            <div style='font-size: 0.7rem; color: #0284C7; font-weight: 600; margin-top: 0.2rem;'>● PUBLIC GUIDE LEVEL</div>
        </div>
        """, unsafe_allow_html=True)
        
    # Navigation controls in sidebar
    if st.session_state.current_view == "workspace":
        if st.sidebar.button("← Return to Home Page", use_container_width=True):
            st.session_state.current_view = "home"
            st.rerun()
    elif st.session_state.current_view == "home":
        if st.sidebar.button("Enter Workspace Portal", use_container_width=True):
            st.session_state.current_view = "workspace"
            st.rerun()
            
    if st.sidebar.button("Secure Log Out", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.current_view = "login"
        st.rerun()
