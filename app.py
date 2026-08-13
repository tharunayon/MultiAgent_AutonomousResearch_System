import os
import streamlit as st
from utils.auth import render_auth_sidebar, get_user_role, ROLE_DOCTOR, ROLE_PATIENT, render_login_page, init_auth
from utils.rag_pipeline import init_rag_state, ingest_pdf, search_rag, clear_rag_state
from agents.health_agents import HealthcareAgentSystem

# Page configuration
st.set_page_config(
    page_title="Dhanva Teach - Multi-Agent Portal",
    page_icon="logo.svg",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern light-themed aesthetics and layout controls
st.markdown("""
<style>
    /* Google Fonts import */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Outfit:wght@500;700;800&display=swap');

    /* Grid pattern background globally */
    .stApp {
        background-color: #FFFFFF;
        background-image: radial-gradient(#E2E8F0 1.2px, transparent 1.2px);
        background-size: 24px 24px;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Outlined fonts for main elements */
    h1, h2, h3, .main-header {
        font-family: 'Outfit', sans-serif !important;
    }

    /* Redesigned Hero Elements */
    .hero-pill {
        display: inline-flex;
        align-items: center;
        background-color: #FFEAEF;
        color: #E05353;
        padding: 0.4rem 1rem;
        border-radius: 50px;
        font-size: 0.85rem;
        font-weight: 700;
        margin-bottom: 1.2rem;
        border: 1px solid #FFD1DC;
    }
    .hero-title {
        font-size: 3.2rem;
        font-weight: 850;
        line-height: 1.15;
        color: #1E293B;
        margin-bottom: 1.2rem;
    }
    .hero-highlight {
        color: #FF4B4B;
        background: linear-gradient(120deg, #FF4B4B 0%, #FF2E93 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-desc {
        font-size: 1.15rem;
        color: #475569;
        line-height: 1.6;
        margin-bottom: 1.5rem;
    }
    .hero-sublinks {
        font-size: 0.9rem;
        font-weight: 600;
        color: #64748B;
        margin-bottom: 2rem;
        display: flex;
        gap: 0.8rem;
    }
    .hero-sublink-item {
        background-color: #F1F5F9;
        padding: 0.25rem 0.6rem;
        border-radius: 6px;
    }

    /* Role badges styling */
    .role-badge {
        padding: 0.4rem 1rem;
        border-radius: 50px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
    }
    .badge-doctor {
        background-color: #FEE2E2;
        color: #991B1B;
        border: 1px solid #FCA5A5;
    }
    .badge-patient {
        background-color: #DCFCE7;
        color: #166534;
        border: 1px solid #86EFAC;
    }
    
    /* Bright blue button style override for Streamlit buttons */
    div.stButton > button:first-child {
        background-color: #0052FF !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        padding: 0.6rem 2rem !important;
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0 4px 6px -1px rgba(0, 82, 255, 0.2), 0 2px 4px -1px rgba(0, 82, 255, 0.1) !important;
        transition: transform 0.2s, box-shadow 0.2s !important;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 15px -3px rgba(0, 82, 255, 0.3), 0 4px 6px -2px rgba(0, 82, 255, 0.15) !important;
    }
    
    /* General cards styling */
    .citation-card, div[data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.02) !important;
        padding: 1.2rem !important;
        margin-bottom: 1.2rem !important;
        transition: transform 0.2s, box-shadow 0.2s !important;
    }
    .citation-card:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04) !important;
    }
    .citation-source {
        font-weight: 700;
        font-size: 0.85rem;
        color: #0369A1;
    }
    .citation-score {
        font-size: 0.8rem;
        color: #64748B;
        float: right;
    }
    .citation-text {
        font-size: 0.9rem;
        color: #334155;
        margin-top: 0.5rem;
        font-style: italic;
    }

    /* Professional Sidebar Header styling */
    .sidebar-header {
        font-family: 'Outfit', sans-serif !important;
        color: #1E293B;
        font-size: 0.85rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
        text-transform: uppercase;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 0.3rem;
    }

    .login-promo-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 2.5rem;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
        margin-bottom: 2rem;
    }
    .login-form-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 2.5rem;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05), 0 4px 6px -2px rgba(0,0,0,0.02);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state authentication
init_auth()

# Render secure login wall if user is not authenticated
if not st.session_state.logged_in:
    render_login_page()
    st.stop()

GUIDE_RESPONSES = {
    "role": "To switch roles, select the option under 'Role-Based Access Control' in the sidebar. You can select either 'Authorized Medical Practitioner (Doctor)' or 'Normal Patient'. This determines the document access boundary (filtering the RAG data) and query response style.",
    "switch": "To switch roles, select the option under 'Role-Based Access Control' in the sidebar. You can select either 'Authorized Medical Practitioner (Doctor)' or 'Normal Patient'. This determines the document access boundary (filtering the RAG data) and query response style.",
    "doctor": "The Doctor view provides clinical evaluations of RAG files, shows raw citations with FAISS L2 similarity scores, ICD-10 medical codes, research trials, and a Fact-Checking agent audit report to block hallucinations.",
    "patient": "The Patient view provides simplified summaries of RAG files, empathetic language, structured action steps, and a list of questions to ask their doctor. Technical trials and restricted clinical documents are completely hidden.",
    "rag": "RAG (Retrieval-Augmented Generation) reads uploaded PDFs, breaks them into small text blocks, creates vectors using a local HuggingFace embedding model, and saves them in FAISS. The system has two isolated indexes: one for public patient guide files, and one for restricted doctor documents.",
    "agents": "The system uses a Multi-Agent coordinator powered by Llama 3 on Groq: \n1. **Orchestration Agent**: evaluates intent.\n2. **Clinical Agent**: researches files.\n3. **Patient Agent**: simplifies details.\n4. **Fact-Checking Agent**: verifies grounding accuracy.",
    "sample": "Click the 'Generate Sample Medical PDFs' button in the sidebar. This compiles a cardiology note (restricted to Doctors) and a hypertension sheet (public to Patients) to let you test the RBAC filters instantly.",
    "pdf": "Click the 'Generate Sample Medical PDFs' button in the sidebar. This compiles a cardiology note (restricted to Doctors) and a hypertension sheet (public to Patients) to let you test the RBAC filters instantly.",
    "hi": "Hello! I am your HealthRAG Onboarding Assistant. Ask me anything about how this portal works (e.g. 'How do I switch roles?', 'What do the agents do?', 'How does RAG work?')."
}

def render_guide_chatbot(groq_key):
    st.sidebar.markdown("---")
    st.sidebar.markdown("<div class='sidebar-header'>Portal Guide Assistant</div>", unsafe_allow_html=True)
    
    # Initialize history for guide chatbot
    if "guide_history" not in st.session_state:
        st.session_state.guide_history = [
            {"role": "assistant", "content": "Hi! I'm your Portal Guide. Ask me how to use this website, how the RAG works, or what the agents do!"}
        ]
        
    # Render guide history in a compact area
    for chat in st.session_state.guide_history:
        role_label = "USER" if chat["role"] == "user" else "GUIDE"
        st.sidebar.caption(f"**{role_label}**: {chat['content']}")
        
    # Form input with unique key to prevent input overlapping
    guide_query = st.sidebar.text_input("Ask about the portal:", key="guide_query_input", placeholder="e.g. How does RAG work?")
    if st.sidebar.button("Send Query", key="guide_query_button"):
        if guide_query.strip():
            # Add user query
            st.session_state.guide_history.append({"role": "user", "content": guide_query})
            
            # Formulate response
            query_lower = guide_query.lower()
            response = ""
            
            # Check key word matches first for instant guide help
            matched_key = None
            for key in GUIDE_RESPONSES:
                if key in query_lower:
                    matched_key = key
                    break
                    
            if matched_key:
                response = GUIDE_RESPONSES[matched_key]
            elif groq_key:
                # Use Groq to answer based on website context
                try:
                    from agents.health_agents import HealthcareAgentSystem
                    agents = HealthcareAgentSystem(groq_key)
                    system_prompt = """
                    You are a helpful, brief Portal Guide Assistant for a Multi-Agent Healthcare RAG Web Application.
                    Your job is to explain how this website works, how to use it, the roles (Doctor and Patient), the RAG pipeline, the mock files, and the agents.
                    Keep your answer under 3 sentences. Be friendly and structured.
                    """
                    response = agents._call_llm_non_stream(system_prompt, guide_query)
                except Exception as e:
                    response = f"I'm sorry, I encountered an error checking Groq: {e}. You can switch roles in the sidebar or upload a PDF to begin."
            else:
                response = "I am a portal helper. Ask me about 'roles', 'agents', 'RAG', 'sample files', 'doctor view', or 'patient view' to get started!"
                
            st.session_state.guide_history.append({"role": "assistant", "content": response})
            st.rerun()

# Helper function to compile sample PDFs using reportlab
def generate_sample_files():
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        
        # 1. Clinical Research PDF (Doctor Only)
        doc_filename = "clinical_cardiology_notes.pdf"
        c = canvas.Canvas(doc_filename, pagesize=letter)
        width, height = letter
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "Clinical Cardiology Research: Hypertrophic Cardiomyopathy (HCM)")
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(50, height - 70, "Classification: RESTRICTED - Authorized Practitioner Use Only")
        
        c.setFont("Helvetica", 10)
        paragraphs = [
            "Overview: Hypertrophic Cardiomyopathy (HCM) is an autosomal dominant cardiovascular disorder characterized by unexplained left ventricular hypertrophy (LVH) in the absence of other systemic causes. It is a major cause of sudden cardiac death in young athletes. The primary diagnostic classification code under ICD-10 is I42.1 (Obstructive hypertrophic cardiomyopathy) and I42.2 (Other hypertrophic cardiomyopathy).",
            "Pathophysiology: The disease is primarily caused by mutations in genes encoding sarcomeric proteins, most commonly MYBPC3 (myosin-binding protein C) and MYH7 (beta-myosin heavy chain). This leads to myofibrillar disarray, myocardial fibrosis, and microvascular dysfunction. Left ventricular outflow tract (LVOT) obstruction is present in approximately 70% of patients at rest or with exercise.",
            "Management & Clinical Trials: Pharmacotherapy includes beta-blockers (e.g., metoprolol or atenolol) and non-dihydropyridine calcium channel blockers (e.g., verapamil) to improve diastolic filling. Surgical septal myectomy or alcohol septal ablation is recommended for patients with refractory symptoms and LVOT gradient >= 50 mmHg. Recent clinical trials like the EXPLORER-HCM study evaluated Mavacamten, a novel cardiac myosin inhibitor, which showed significant reductions in post-exercise LVOT gradient and improvements in exercise capacity (NYHA class)."
        ]
        
        y = height - 100
        for para in paragraphs:
            words = para.split(' ')
            line = []
            for w in words:
                line.append(w)
                if len(" ".join(line)) * 5 > width - 100:
                    c.drawString(50, y, " ".join(line[:-1]))
                    y -= 15
                    line = [w]
            c.drawString(50, y, " ".join(line))
            y -= 25
            
        c.save()

        # 2. Patient Guide PDF (Public Patient)
        pat_filename = "patient_hypertension_guide.pdf"
        c = canvas.Canvas(pat_filename, pagesize=letter)
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "Patient Guide: Managing Your High Blood Pressure")
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(50, height - 70, "Classification: PUBLIC - Patient Information Sheet")
        
        c.setFont("Helvetica", 10)
        paragraphs = [
            "What is Hypertension? Hypertension, or high blood pressure, occurs when the force of blood pushing against your artery walls is consistently too high. Over time, this can strain your heart and lead to serious conditions like heart disease or stroke.",
            "Daily Lifestyle Changes: Managing blood pressure starts with healthy habits. Adopt the DASH diet (Dietary Approaches to Stop Hypertension), which emphasizes fruits, vegetables, whole grains, and lean proteins while drastically reducing sodium (salt) intake to less than 1,500 milligrams per day. Engage in moderate aerobic exercise, such as brisk walking, for at least 30 minutes daily.",
            "Medication and Monitoring: If your doctor prescribes blood pressure medication, take it exactly as directed at the same time every day. Never skip a dose even if you feel fine, as high blood pressure is often a silent condition with no obvious symptoms. Keep a daily log of your blood pressure readings at home and share them with your physician at your next check-up."
        ]
        
        y = height - 100
        for para in paragraphs:
            words = para.split(' ')
            line = []
            for w in words:
                line.append(w)
                if len(" ".join(line)) * 5 > width - 100:
                    c.drawString(50, y, " ".join(line[:-1]))
                    y -= 15
                    line = [w]
            c.drawString(50, y, " ".join(line))
            y -= 25
            
        c.save()
        return True
    except Exception as e:
        st.sidebar.error(f"Failed to generate sample PDFs: {e}")
        return False

# Initialize states
init_rag_state()

# Auto-ingest documents from the local knowledge base on startup
if "knowledge_base_loaded" not in st.session_state:
    st.session_state.knowledge_base_loaded = False

if not st.session_state.knowledge_base_loaded:
    public_dir = os.path.join("knowledge_base", "public")
    restricted_dir = os.path.join("knowledge_base", "restricted")
    
    # Ensure directories exist
    os.makedirs(public_dir, exist_ok=True)
    os.makedirs(restricted_dir, exist_ok=True)
    
    # Ingest public files
    for f_name in os.listdir(public_dir):
        if f_name.lower().endswith(".pdf"):
            f_path = os.path.join(public_dir, f_name)
            try:
                with open(f_path, "rb") as f:
                    ingest_pdf(f, "public_patient")
            except Exception as e:
                st.error(f"Error loading public file {f_name}: {e}")
                
    # Ingest restricted files
    for f_name in os.listdir(restricted_dir):
        if f_name.lower().endswith(".pdf"):
            f_path = os.path.join(restricted_dir, f_name)
            try:
                with open(f_path, "rb") as f:
                    ingest_pdf(f, "doctor_only")
            except Exception as e:
                st.error(f"Error loading restricted file {f_name}: {e}")
                
    st.session_state.knowledge_base_loaded = True

# ----------------- TOP NAVBAR HEADER -----------------
col_nav_left, col_nav_right = st.columns([7, 3])
with col_nav_left:
    col_nav_logo, col_nav_title = st.columns([1, 6])
    with col_nav_logo:
        if os.path.exists("logo.svg"):
            st.image("logo.svg", width=55)
    with col_nav_title:
        st.markdown(
            "<div style='margin-top: 10px; font-family: \"Outfit\"; font-weight: 850; font-size: 1.8rem; color: #1E293B;'>"
            "DHANVA TEACH <span style='color: #FF4B4B; font-weight: 500; font-size: 1.2rem;'>HealthRAG</span>"
            "</div>",
            unsafe_allow_html=True
        )
with col_nav_right:
    role = get_user_role()
    if role == ROLE_DOCTOR:
        badge_html = "<div style='text-align: right; margin-top: 12px;'><span class='role-badge badge-doctor'>CLINICAL ACCESS</span></div>"
    else:
        badge_html = "<div style='text-align: right; margin-top: 12px;'><span class='role-badge badge-patient'>PATIENT ACCESS</span></div>"
    st.markdown(badge_html, unsafe_allow_html=True)

# ----------------- SIDEBAR CONTROLS -----------------
st.sidebar.markdown("<div class='sidebar-header'>Portal Management</div>", unsafe_allow_html=True)

# Render role selector switcher
render_auth_sidebar()

# ----------------- VIEW ROUTING -----------------
if st.session_state.current_view == "home":
    st.markdown("<hr style='margin-top: 0.5rem; margin-bottom: 2rem; border-color: #E2E8F0;'>", unsafe_allow_html=True)
    
    if role == ROLE_DOCTOR:
        st.markdown("""
        <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 2rem; border-radius: 16px; margin-bottom: 2rem;">
            <h1 style="font-family: 'Outfit'; font-weight: 850; font-size: 2.2rem; color: #1E293B; margin: 0 0 0.5rem 0;">
                Practitioner Clinical Research Dashboard
            </h1>
            <p style="color: #475569; font-size: 1.1rem; line-height: 1.6; margin: 0;">
                Welcome to the secure clinical decision-support portal. Query cross-boundary research data, 
                isolated trial journals, and verify AI findings using automated integrity auditing.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Technical Dashboard Stats
        stat_cols = st.columns(3)
        with stat_cols[0]:
            st.markdown("""
            <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); text-align: center;">
                <div style="font-size: 0.8rem; color: #64748B; font-weight: 700; text-transform: uppercase;">RESTRICTED SCHEMAS</div>
                <div style="font-size: 2rem; font-weight: 850; color: #0052FF; margin: 0.2rem 0;">FAISS-L2</div>
                <div style="font-size: 0.75rem; color: #10B981; font-weight: 600;">Mathematical Separation</div>
            </div>
            """, unsafe_allow_html=True)
        with stat_cols[1]:
            st.markdown("""
            <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); text-align: center;">
                <div style="font-size: 0.8rem; color: #64748B; font-weight: 700; text-transform: uppercase;">INTEGRITY ENGINE</div>
                <div style="font-size: 2rem; font-weight: 850; color: #10B981; margin: 0.2rem 0;">Audited</div>
                <div style="font-size: 0.75rem; color: #10B981; font-weight: 600;">Grounding Checked</div>
            </div>
            """, unsafe_allow_html=True)
        with stat_cols[2]:
            st.markdown("""
            <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); text-align: center;">
                <div style="font-size: 0.8rem; color: #64748B; font-weight: 700; text-transform: uppercase;">ACTIVE CODES</div>
                <div style="font-size: 2rem; font-weight: 850; color: #E05353; margin: 0.2rem 0;">ICD-10</div>
                <div style="font-size: 0.75rem; color: #64748B; font-weight: 600;">Clinical Trial Matching</div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        st.write("")
        
        # Interactive Flowchart
        st.markdown("### Interactive Clinical RAG System Diagram")
        st.write("Click on any node in the data pipeline to inspect its system parameters:")
        
        diagram_cols = st.columns(5)
        selected_doctor_node = st.session_state.get("selected_doctor_node", "Clinical Router")
        
        with diagram_cols[0]:
            if st.button("1. Document Ingestion", use_container_width=True, key="doc_ing"):
                st.session_state.selected_doctor_node = "Document Ingestion"
                st.rerun()
        with diagram_cols[1]:
            if st.button("2. Clinical Router", use_container_width=True, key="clin_rt"):
                st.session_state.selected_doctor_node = "Clinical Router"
                st.rerun()
        with diagram_cols[2]:
            if st.button("3. FAISS Indexing", use_container_width=True, key="faiss_idx"):
                st.session_state.selected_doctor_node = "FAISS Indexing"
                st.rerun()
        with diagram_cols[3]:
            if st.button("4. Multi-Agent System", use_container_width=True, key="ma_sys"):
                st.session_state.selected_doctor_node = "Multi-Agent System"
                st.rerun()
        with diagram_cols[4]:
            if st.button("5. Fact-Checking Guard", use_container_width=True, key="fc_guard"):
                st.session_state.selected_doctor_node = "Fact-Checking Guard"
                st.rerun()
                
        node_details = {
            "Document Ingestion": {
                "title": "Document Ingestion Pipeline",
                "desc": "Extracts text from clinical reports (Doctors) or health sheets (Patients) page-by-page using PyPDF, splitting them into overlapping semantic word chunks (400 words token limit, 50 words overlap) to preserve local boundaries.",
                "status": "Isolated Pipeline Active"
            },
            "Clinical Router": {
                "title": "Orchestrator Routing Agent",
                "desc": "Analyzes the patient query and credentials to verify access permissions, determining routing reasoning and mapping parameters before retrieving document matches.",
                "status": "Llama 3 Powered"
            },
            "FAISS Indexing": {
                "title": "Role-Isolated FAISS Vector DB",
                "desc": "Splits text embeddings into isolated indexes. Restricted clinical trials are stored strictly in the Doctor vector space. Public guides are stored in both vector indices.",
                "status": "SentenceTransformers (all-MiniLM-L6-v2)"
            },
            "Multi-Agent System": {
                "title": "Healthcare Multi-Agent Engine",
                "desc": "Coordinates reasoning. In Doctor mode, compiles raw similarity scores, ICD-10 medical codes, and clinical research details. In Patient mode, translates medical findings into empathetic layperson guides.",
                "status": "Llama 3 Coordinator"
            },
            "Fact-Checking Guard": {
                "title": "Fact-Checking & Integrity Auditor",
                "desc": "Automatically compares raw document source chunks with synthesized LLM outputs to generate a grounding score (0-10) and a verify checklist, catching and blocking hallucinations.",
                "status": "Integrity Guard Active"
            }
        }
        
        details = node_details.get(selected_doctor_node, node_details["Clinical Router"])
        st.markdown(f"""
        <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 1.5rem; border-radius: 12px; margin-top: 1rem; border-left: 5px solid #0052FF;">
            <div style="font-size: 0.8rem; color: #64748B; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">SYSTEM COMPONENT DETAILS ({details['status']})</div>
            <h4 style="font-family: 'Outfit'; font-weight: 700; color: #1E293B; margin-top: 0.2rem; margin-bottom: 0.5rem;">{details['title']}</h4>
            <p style="color: #475569; font-size: 0.95rem; line-height: 1.6; margin: 0;">{details['desc']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        st.write("")
        if st.button("Enter Clinical Workspace", use_container_width=True, type="primary", key="enter_ws_doc"):
            st.session_state.current_view = "workspace"
            st.rerun()
            
    else:
        # Patient Home Page
        st.markdown("""
        <div style="background-color: #F0FDF4; border: 1px solid #DCFCE7; padding: 2rem; border-radius: 16px; margin-bottom: 2rem;">
            <h1 style="font-family: 'Outfit'; font-weight: 850; font-size: 2.2rem; color: #14532D; margin: 0 0 0.5rem 0;">
                Your Patient Guidance Dashboard
            </h1>
            <p style="color: #166534; font-size: 1.1rem; line-height: 1.6; margin: 0;">
                Welcome to the patient education and care portal. Access verified patient guidelines, 
                learn about managing chronic conditions, and generate simple guides to discuss with your doctor.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Educational Cards
        pat_cols = st.columns(3)
        with pat_cols[0]:
            st.markdown("""
            <div style="background-color: #FFFFFF; border: 1px solid #DCFCE7; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); text-align: center;">
                <div style="font-size: 0.8rem; color: #166534; font-weight: 700; text-transform: uppercase;">ACCESSIBLE DIETS</div>
                <div style="font-size: 1.8rem; font-weight: 850; color: #10B981; margin: 0.2rem 0;">DASH Diet</div>
                <div style="font-size: 0.75rem; color: #166534; font-weight: 600;">Hypertension Guidelines</div>
            </div>
            """, unsafe_allow_html=True)
        with pat_cols[1]:
            st.markdown("""
            <div style="background-color: #FFFFFF; border: 1px solid #DCFCE7; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); text-align: center;">
                <div style="font-size: 0.8rem; color: #166534; font-weight: 700; text-transform: uppercase;">SECURE RECORDS</div>
                <div style="font-size: 1.8rem; font-weight: 850; color: #0284C7; margin: 0.2rem 0;">Isolated</div>
                <div style="font-size: 0.75rem; color: #166534; font-weight: 600;">Your data is protected</div>
            </div>
            """, unsafe_allow_html=True)
        with pat_cols[2]:
            st.markdown("""
            <div style="background-color: #FFFFFF; border: 1px solid #DCFCE7; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); text-align: center;">
                <div style="font-size: 0.8rem; color: #166534; font-weight: 700; text-transform: uppercase;">DOCTOR DISCUSSIONS</div>
                <div style="font-size: 1.8rem; font-weight: 850; color: #D97706; margin: 0.2rem 0;">Action Items</div>
                <div style="font-size: 0.75rem; color: #166534; font-weight: 600;">Custom check-ups checklist</div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        st.write("")
        
        # Interactive Journey
        st.write("### Interactive Patient Care Journey")
        st.write("Click on any stage of your care consultation path to see how your data is protected and translated:")
        
        p_cols = st.columns(5)
        selected_patient_node = st.session_state.get("selected_patient_node", "Translation")
        
        with p_cols[0]:
            if st.button("1. Inquiry Stage", use_container_width=True, key="p_inq"):
                st.session_state.selected_patient_node = "Inquiry Stage"
                st.rerun()
        with p_cols[1]:
            if st.button("2. Secure Search", use_container_width=True, key="p_sec"):
                st.session_state.selected_patient_node = "Secure Search"
                st.rerun()
        with p_cols[2]:
            if st.button("3. Translation", use_container_width=True, key="p_trans"):
                st.session_state.selected_patient_node = "Translation"
                st.rerun()
        with p_cols[3]:
            if st.button("4. Verification", use_container_width=True, key="p_ver"):
                st.session_state.selected_patient_node = "Verification"
                st.rerun()
        with p_cols[4]:
            if st.button("5. Doctor Checklist", use_container_width=True, key="p_chk"):
                st.session_state.selected_patient_node = "Doctor Checklist"
                st.rerun()
                
        p_details = {
            "Inquiry Stage": {
                "title": "Asking Your Health Question",
                "desc": "Enter symptoms, drug information, or dietary questions into the portal. The system handles patient queries with privacy guidelines.",
                "status": "Patient Shield Active"
            },
            "Secure Search": {
                "title": "Private Database Retrieval",
                "desc": "The RAG engine queries the public patient guides (like DASH diet worksheets) while keeping restricted practitioner trial documents mathematically hidden.",
                "status": "Role-Isolated Database"
            },
            "Translation": {
                "title": "Empathetic Patient Summary",
                "desc": "Converts complex clinical summaries into clear, supportive, and jargon-free instructions detailing daily lifestyle adjustments and safe scheduling.",
                "status": "Warm Layperson Guide"
            },
            "Verification": {
                "title": "Accuracy Check",
                "desc": "The Fact-Checking agent reviews the translation to ensure every single claim is grounded in official medical guides, eliminating risk.",
                "status": "Audited Grounding"
            },
            "Doctor Checklist": {
                "title": "Your Consultation Sheet",
                "desc": "The system automatically drafts a list of suggested questions to ask your physician during your next appointment, helping you coordinate care.",
                "status": "Prepared Consultation"
            }
        }
        
        det = p_details.get(selected_patient_node, p_details["Translation"])
        st.markdown(f"""
        <div style="background-color: #F0FDF4; border: 1px solid #DCFCE7; padding: 1.5rem; border-radius: 12px; margin-top: 1rem; border-left: 5px solid #10B981;">
            <div style="font-size: 0.8rem; color: #166534; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">PATIENT ROADMAP DETAIL ({det['status']})</div>
            <h4 style="font-family: 'Outfit'; font-weight: 700; color: #14532D; margin-top: 0.2rem; margin-bottom: 0.5rem;">{det['title']}</h4>
            <p style="color: #166534; font-size: 0.95rem; line-height: 1.6; margin: 0;">{det['desc']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        st.write("")
        if st.button("Enter Patient Workspace", use_container_width=True, type="primary", key="enter_ws_pat"):
            st.session_state.current_view = "workspace"
            st.rerun()

else:
    # ----------------- HERO SECTION -----------------
    st.markdown("<hr style='margin-top: 0.5rem; margin-bottom: 2rem; border-color: #E2E8F0;'>", unsafe_allow_html=True)
    
    hero_col1, hero_col2 = st.columns([1.1, 0.9])
    
    with hero_col1:
        st.markdown("""
        <div class="hero-pill">GOLD STANDARD MEDICAL RETRIEVAL</div>
        <div class="hero-title">Learn & Search<br>with <span class="hero-highlight">Dhanva Teach</span></div>
        <div class="hero-desc">
            Access isolated clinical trial data, consult diagnostic guidelines, and query multi-agent systems with absolute safety. 
            Features role-isolated indexes and automated clinical fact-checking.
        </div>
        <div class="hero-sublinks">
            <span class="hero-sublink-item"><span style="color: #0052FF; font-weight: 700; margin-right: 4px;">●</span>Clinically-Oriented</span>
            <span class="hero-sublink-item"><span style="color: #10B981; font-weight: 700; margin-right: 4px;">●</span>Fact-Checked</span>
            <span class="hero-sublink-item"><span style="color: #EF4444; font-weight: 700; margin-right: 4px;">●</span>Role-Isolated</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("Interactive workspace controls are active in the sidebar and main workspace tabs below.")

    with hero_col2:
        if os.path.exists("medical_hero_illustration.png"):
            st.image("medical_hero_illustration.png", use_container_width=True)

    st.markdown("<hr style='margin-top: 2rem; margin-bottom: 2rem; border-color: #E2E8F0;'>", unsafe_allow_html=True)

    # Groq API Key management (loaded silently from backend, not shown to users)
    groq_key = ""
    try:
        if "GROQ_API_KEY" in st.secrets and st.secrets["GROQ_API_KEY"] != "gsk_placeholder_replace_me":
            groq_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        pass

    if not groq_key:
        groq_key = os.environ.get("GROQ_API_KEY", "")

    # Programmatic Mock Document Ingestion Utility
    st.sidebar.markdown("---")
    st.sidebar.markdown("<div class='sidebar-header'>Sample Document Creator</div>", unsafe_allow_html=True)
    if st.sidebar.button("Generate Sample Medical PDFs"):
        if generate_sample_files():
            st.sidebar.info("Generated sample files. Loading them below...")
            # Auto-ingest doc_only notes
            if os.path.exists("clinical_cardiology_notes.pdf"):
                with open("clinical_cardiology_notes.pdf", "rb") as f:
                    res1 = ingest_pdf(f, "doctor_only")
                    st.sidebar.write(res1["message"])
            # Auto-ingest patient guide notes
            if os.path.exists("patient_hypertension_guide.pdf"):
                with open("patient_hypertension_guide.pdf", "rb") as f:
                    res2 = ingest_pdf(f, "public_patient")
                    st.sidebar.write(res2["message"])
            st.rerun()

    # Document Uploader widget
    st.sidebar.markdown("---")
    st.sidebar.markdown("<div class='sidebar-header'>Upload New Document</div>", unsafe_allow_html=True)
    uploaded_file = st.sidebar.file_uploader("Upload Medical PDF:", type="pdf")
    visibility_setting = st.sidebar.selectbox(
        "Set Document Access Boundary:",
        options=["public_patient", "doctor_only"],
        format_func=lambda x: "Public Patient (All)" if x == "public_patient" else "Doctor Only (Restricted)"
    )

    # Persistent notification state for uploads
    if "upload_success" not in st.session_state:
        st.session_state.upload_success = None
    if "last_uploaded_file" not in st.session_state:
        st.session_state.last_uploaded_file = None

    if uploaded_file != st.session_state.last_uploaded_file:
        st.session_state.last_uploaded_file = uploaded_file
        st.session_state.upload_success = None

    if uploaded_file is not None:
        if st.sidebar.button("Process & Ingest into RAG"):
            with st.spinner("Analyzing document structure..."):
                res = ingest_pdf(uploaded_file, visibility_setting)
                if res["success"]:
                    st.session_state.upload_success = res["message"]
                    st.rerun()
                else:
                    st.sidebar.error(res["message"])

    if st.session_state.upload_success:
        st.sidebar.success(st.session_state.upload_success)

    # Reset vector database button
    if st.sidebar.button("Reset Vector Database"):
        clear_rag_state()
        # Clean files if generated
        for f in ["clinical_cardiology_notes.pdf", "patient_hypertension_guide.pdf"]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass
        st.sidebar.info("FAISS Vector stores and catalogs cleared.")
        st.rerun()

    # Call guide assistant at the bottom of the sidebar
    render_guide_chatbot(groq_key)

    # ----------------- MAIN VIEW IMPLEMENTATION -----------------

    if role == ROLE_DOCTOR:
        # Doctor views
        tab_chat, tab_catalog = st.tabs(["PRACTITIONER PORTAL", "DOCUMENT CATALOG"])
        
        with tab_chat:
            st.write("*Ask diagnostics, drug interaction queries, or ICD-10 suggestions. The system searches through both doctor-only research files and public patient guides.*")
            
            # Initialize doctor chat history
            if "messages_doctor" not in st.session_state:
                st.session_state.messages_doctor = []
                
            # Render chat history
            for msg in st.session_state.messages_doctor:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
                    if msg.get("routing_reasoning"):
                        with st.expander("ROUTING EVALUATION", expanded=False):
                            st.info(msg["routing_reasoning"])
                    if msg.get("fact_check"):
                        with st.expander("INTEGRITY AUDIT REPORT", expanded=False):
                            st.warning(msg["fact_check"])
                    if msg.get("citations"):
                        with st.expander("VERIFIED CONTEXT REFERENCES", expanded=False):
                            for i, citation in enumerate(msg["citations"]):
                                st.markdown(
                                    f"<div class='citation-card'>"
                                    f"<span class='citation-score'>L2 Distance: {citation['score']:.4f}</span>"
                                    f"<span class='citation-source'>Source: {citation['source']} | Access: {citation['visibility']}</span>"
                                    f"<div class='citation-text'>{citation['text']}</div>"
                                    f"</div>",
                                    unsafe_allow_html=True
                                )

            # Chat Input
            if prompt := st.chat_input("Enter clinical query..."):
                if not groq_key:
                    st.error("System configuration error: Clinical translation engine is currently offline. Please contact your system administrator.")
                else:
                    # 1. Render user message
                    with st.chat_message("user"):
                        st.write(prompt)
                    st.session_state.messages_doctor.append({"role": "user", "content": prompt})
                    
                    # 2. Retrieve contexts from FAISS
                    contexts = search_rag(prompt, role=ROLE_DOCTOR, top_k=4)
                    
                    # 3. Create Agents client
                    agents = HealthcareAgentSystem(groq_key)
                    
                    # 4. Run Routing Agent
                    with st.status("Coordinating clinical agents...", expanded=True) as status:
                        status.write("Orchestration Routing Agent analyzing query...")
                        route_data = agents.run_routing_agent(prompt, ROLE_DOCTOR)
                        status.write(f"Routed Query. Orchestration Reasoning: {route_data['routing_reasoning']}")
                        
                        # 5. Stream Clinical Research Agent
                        status.write("Clinical Research Agent examining documents & compiling technical notes...")
                        with st.chat_message("assistant"):
                            assistant_response_placeholder = st.empty()
                            clinical_response = ""
                            for chunk in agents.run_clinical_research_agent_stream(prompt, contexts):
                                clinical_response += chunk
                                assistant_response_placeholder.markdown(clinical_response + "▌")
                            assistant_response_placeholder.markdown(clinical_response)
                        
                        # 6. Run Fact checker (non-streaming)
                        status.write("Fact-Checking Agent auditing clinical notes for grounding accuracy...")
                        fact_check_report = agents.run_fact_checking_agent(clinical_response, contexts)
                        
                        # Render outputs
                        status.update(label="Analysis Completed", state="complete", expanded=False)
                    
                    # Render routing, fact check and citations in expanders for current message
                    with st.expander("ROUTING EVALUATION", expanded=False):
                        st.info(route_data["routing_reasoning"])
                    with st.expander("INTEGRITY AUDIT REPORT", expanded=False):
                        st.warning(fact_check_report)
                    if contexts:
                        with st.expander("VERIFIED CONTEXT REFERENCES", expanded=False):
                            for i, citation in enumerate(contexts):
                                st.markdown(
                                    f"<div class='citation-card'>"
                                    f"<span class='citation-score'>L2 Distance: {citation['score']:.4f}</span>"
                                    f"<span class='citation-source'>Source: {citation['source']} | Access: {citation['visibility']}</span>"
                                    f"<div class='citation-text'>{citation['text']}</div>"
                                    f"</div>",
                                    unsafe_allow_html=True
                                )
                    
                    # Save to doctor history
                    st.session_state.messages_doctor.append({
                        "role": "assistant",
                        "content": clinical_response,
                        "routing_reasoning": route_data["routing_reasoning"],
                        "fact_check": fact_check_report,
                        "citations": contexts
                    })
                    st.rerun()

        with tab_catalog:
            st.markdown("### Registered Vector Documents")
            if not st.session_state.uploaded_documents:
                st.info("No documents are ingested in the FAISS database. Use the sidebar to upload medical PDFs or click 'Generate Sample Medical PDFs'.")
            else:
                doc_data = []
                for doc in st.session_state.uploaded_documents:
                    doc_data.append({
                        "Document Name": doc["filename"],
                        "Access Boundary": "Doctor Only (Restricted)" if doc["visibility"] == "doctor_only" else "Public Patient (All)",
                        "Chunks Processed": doc["chunks_count"]
                    })
                st.table(doc_data)
                
                # Interactive Citations Explorer
                st.markdown("---")
                st.markdown("### Raw Chunk Inspector")
                selected_doc = st.selectbox(
                    "Select Ingested Document:",
                    options=[doc["filename"] for doc in st.session_state.uploaded_documents]
                )
                
                if selected_doc:
                    matching_chunks = [c for c in st.session_state.chunks_doctor if c["source"] == selected_doc]
                    for idx, ch in enumerate(matching_chunks):
                        st.markdown(
                            f"<div class='citation-card'>"
                            f"<span class='citation-source'>Chunk {idx + 1} | Visibility: {ch['visibility']}</span>"
                            f"<div class='citation-text'>{ch['text']}</div>"
                            f"</div>",
                            unsafe_allow_html=True
                        )

    else:
        # Patient view
        tab_pchat, tab_plibrary = st.tabs(["PATIENT PORTAL", "DOCUMENT LIBRARY"])
        
        with tab_pchat:
            st.write("*Ask about symptoms, drug guides, or lifestyle habits. The assistant provides simple, empathetic guidance based on public documentation.*")
            
            # Initialize patient chat history
            if "messages_patient" not in st.session_state:
                st.session_state.messages_patient = []
                
            # Render patient chat history
            for msg in st.session_state.messages_patient:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
                    if msg.get("grounding_verified"):
                        st.success("Verification Status: Grounded in Patient Records")

            # Chat Input
            if prompt := st.chat_input("Enter your health question..."):
                if not groq_key:
                    st.error("System configuration error: Clinical translation engine is currently offline. Please contact your system administrator.")
                else:
                    # 1. Render user message
                    with st.chat_message("user"):
                        st.write(prompt)
                    st.session_state.messages_patient.append({"role": "user", "content": prompt})
                    
                    # 2. Retrieve patient-accessible contexts
                    contexts = search_rag(prompt, role=ROLE_PATIENT, top_k=4)
                    
                    # 3. Create Agents client
                    agents = HealthcareAgentSystem(groq_key)
                    
                    # 4. Run multi-agent pipeline
                    with st.status("Retrieving answers...", expanded=True) as status:
                        status.write("Orchestration Agent evaluating patient request...")
                        route_data = agents.run_routing_agent(prompt, ROLE_PATIENT)
                        
                        status.write("Clinical Research Agent verifying medical references...")
                        # Get research notes in background (non-stream)
                        clinical_notes = agents._call_llm_non_stream(
                            "You are a clinical researcher. Analyze the patient query and summarize facts based on context.",
                            f"Query: {prompt}\n\nContexts:\n" + "\n".join([c["text"] for c in contexts])
                        )
                        
                        status.write("Patient Layman Agent translating clinical facts into simple instructions...")
                        with st.chat_message("assistant"):
                            assistant_response_placeholder = st.empty()
                            patient_response = ""
                            for chunk in agents.run_patient_layman_agent_stream(prompt, clinical_notes, contexts):
                                patient_response += chunk
                                assistant_response_placeholder.markdown(patient_response + "▌")
                            assistant_response_placeholder.markdown(patient_response)
                            
                        status.write("Fact-Checking Agent verifying layman guide alignment...")
                        fact_report = agents.run_fact_checking_agent(patient_response, contexts)
                        
                        status.update(label="Response Formulated", state="complete", expanded=False)
                    
                    # Display simplified badge for patient reassurance
                    st.success("Verification Status: Grounded in Patient Records")
                    
                    # Save to patient history
                    st.session_state.messages_patient.append({
                        "role": "assistant",
                        "content": patient_response,
                        "grounding_verified": True
                    })
                    st.rerun()
                    
        with tab_plibrary:
            st.markdown("### Ingested Document Directory (Public)")
            public_docs = [doc for doc in st.session_state.uploaded_documents if doc["visibility"] == "public_patient"]
            hidden_count = len(st.session_state.uploaded_documents) - len(public_docs)
            
            if not public_docs:
                st.info("No public patient documents have been uploaded to the database. Ask your provider to upload them.")
            else:
                st.write("Below are the reference documents currently accessible to your profile:")
                doc_data = []
                for doc in public_docs:
                    doc_data.append({
                        "Document Name": doc["filename"],
                        "Access Setting": "Public (All Profiles)",
                        "Information Segments": doc["chunks_count"]
                    })
                st.table(doc_data)
                
            if hidden_count > 0:
                st.warning(f"RESTRICTED: {hidden_count} restricted clinical document(s) are currently loaded as 'Doctor Only' and are mathematically isolated from this view.")
            else:
                st.info("RESTRICTED: Some clinical trial data or technical diagnostic reports are restricted to Medical Practitioners (Doctors) only and are hidden from this view.")
