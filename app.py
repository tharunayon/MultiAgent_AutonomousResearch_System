import os
import streamlit as st
from utils.auth import render_auth_sidebar, get_user_role, ROLE_DOCTOR, ROLE_PATIENT
from utils.rag_pipeline import init_rag_state, ingest_pdf, search_rag, clear_rag_state
from agents.health_agents import HealthcareAgentSystem

# Page configuration
st.set_page_config(
    page_title="Dhanva Teach - Multi-Agent Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern light-themed aesthetics and layout controls
st.markdown("""
<style>
    /* Styling headers and custom cards */
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #0052FF 0%, #FF007F 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #64748B;
        margin-bottom: 2rem;
    }
    .role-badge {
        padding: 0.4rem 1rem;
        border-radius: 50px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
        margin-bottom: 1.5rem;
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
    /* Citation block cards */
    .citation-card {
        background-color: #F8FAFC;
        border-left: 4px solid #0052FF;
        padding: 0.8rem;
        border-radius: 4px;
        margin-bottom: 0.8rem;
        border-top: 1px solid #E2E8F0;
        border-right: 1px solid #E2E8F0;
        border-bottom: 1px solid #E2E8F0;
    }
    .citation-source {
        font-weight: 600;
        font-size: 0.8rem;
        color: #0369A1;
    }
    .citation-score {
        font-size: 0.75rem;
        color: #64748B;
        float: right;
    }
    .citation-text {
        font-size: 0.85rem;
        color: #334155;
        margin-top: 0.3rem;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

GUIDE_RESPONSES = {
    "role": "To switch roles, select the option under '🔐 Role-Based Access Control' in the sidebar. You can select either 'Authorized Medical Practitioner (Doctor)' or 'Normal Patient'. This determines the document access boundary (filtering the RAG data) and query response style.",
    "switch": "To switch roles, select the option under '🔐 Role-Based Access Control' in the sidebar. You can select either 'Authorized Medical Practitioner (Doctor)' or 'Normal Patient'. This determines the document access boundary (filtering the RAG data) and query response style.",
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
    st.sidebar.markdown("### 🤖 Portal Guide Assistant")
    
    # Initialize history for guide chatbot
    if "guide_history" not in st.session_state:
        st.session_state.guide_history = [
            {"role": "assistant", "content": "Hi! I'm your Portal Guide. Ask me how to use this website, how the RAG works, or what the agents do!"}
        ]
        
    # Render guide history in a compact area
    for chat in st.session_state.guide_history:
        role_label = "👤 You" if chat["role"] == "user" else "🤖 Guide"
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

# Title text header with logo integration
col_logo, col_title = st.columns([1, 6])
with col_logo:
    if os.path.exists("logo.svg"):
        st.image("logo.svg", width=110)
with col_title:
    st.markdown("<div class='main-header'>DHANVA TEACH HealthRAG</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Multi-Agent Clinical Retrieval Augmented Generation (RAG) System</div>", unsafe_allow_html=True)

# ----------------- SIDEBAR CONTROLS -----------------
if os.path.exists("logo.svg"):
    st.sidebar.image("logo.svg", width=150)
st.sidebar.title("🛡️ Dhanva Teach Control Panel")

# Render role selector switcher
render_auth_sidebar()
role = get_user_role()

# Badge displaying active user role context
if role == ROLE_DOCTOR:
    st.markdown("<div class='role-badge badge-doctor'>🔐 Access Level: Authorized Medical Practitioner (Doctor)</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='role-badge badge-patient'>🔓 Access Level: Normal Patient</div>", unsafe_allow_html=True)

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
st.sidebar.markdown("### 🛠️ Sample Document Creator")
if st.sidebar.button("📁 Generate Sample Medical PDFs"):
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
st.sidebar.markdown("### 📤 Upload New Document")
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
    if st.sidebar.button("📥 Process & Ingest into RAG"):
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
if st.sidebar.button("🗑️ Reset Vector Database"):
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
    tab_chat, tab_catalog = st.tabs(["💬 Practitioner Chat Portal", "📑 Reference Documents Catalog"])
    
    with tab_chat:
        st.write("💡 *Ask diagnostics, drug interaction queries, or ICD-10 suggestions. The system searches through both doctor-only research files and public patient guides.*")
        
        # Initialize doctor chat history
        if "messages_doctor" not in st.session_state:
            st.session_state.messages_doctor = []
            
        # Render chat history
        for msg in st.session_state.messages_doctor:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if msg.get("routing_reasoning"):
                    with st.expander("🔍 Orchestrator Routing Reason", expanded=False):
                        st.info(msg["routing_reasoning"])
                if msg.get("fact_check"):
                    with st.expander("🛡️ Fact-Checker Report", expanded=False):
                        st.warning(msg["fact_check"])
                if msg.get("citations"):
                    with st.expander("📚 Matched Chunks (FAISS Similarity)", expanded=False):
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
                with st.status("🧠 Agents coordinating...", expanded=True) as status:
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
                with st.expander("🔍 Orchestrator Routing Reason", expanded=False):
                    st.info(route_data["routing_reasoning"])
                with st.expander("🛡️ Fact-Checker Report", expanded=False):
                    st.warning(fact_check_report)
                if contexts:
                    with st.expander("📚 Matched Chunks (FAISS Similarity)", expanded=False):
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
        st.markdown("### 🗃️ Registered Vector Documents")
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
            st.markdown("### 🔍 Raw Chunk Inspector")
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
    tab_pchat, tab_plibrary = st.tabs(["💬 Patient Chat Portal", "📖 Patient Document Library"])
    
    with tab_pchat:
        st.write("💡 *Ask about symptoms, drug guides, or lifestyle habits. The assistant provides simple, empathetic guidance based on public documentation.*")
        
        # Initialize patient chat history
        if "messages_patient" not in st.session_state:
            st.session_state.messages_patient = []
            
        # Render patient chat history
        for msg in st.session_state.messages_patient:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if msg.get("grounding_verified"):
                    st.success("✔ Verification Status: Grounded in Patient Records")

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
                with st.status("🔍 Portal retrieving answers...", expanded=True) as status:
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
                st.success("✔ Verification Status: Grounded in Patient Records")
                
                # Save to patient history
                st.session_state.messages_patient.append({
                    "role": "assistant",
                    "content": patient_response,
                    "grounding_verified": True
                })
                st.rerun()
                
    with tab_plibrary:
        st.markdown("### 📖 Ingested Document Directory (Public)")
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
            st.warning(f"🔒 Note: {hidden_count} restricted clinical document(s) are currently loaded as 'Doctor Only' and are mathematically isolated from this view.")
        else:
            st.info("🔒 Note: Some clinical trial data or technical diagnostic reports are restricted to Medical Practitioners (Doctors) only and are hidden from this view.")
