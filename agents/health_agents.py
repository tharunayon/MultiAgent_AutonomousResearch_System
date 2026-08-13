import os
import streamlit as st
from groq import Groq

class HealthcareAgentSystem:
    """Manages multi-agent interactions and routing using the Groq API."""
    def __init__(self, api_key: str):
        self.mock_mode = (not api_key or api_key == "mock_key" or api_key == "gsk_placeholder_replace_me")
        if not self.mock_mode:
            self.client = Groq(api_key=api_key)
            self.model = "llama-3.3-70b-versatile"
            self.fallback_model = "llama3-8b-8192"

    def _call_llm_stream(self, system_prompt: str, user_prompt: str):
        """Streams responses from the Groq API with fallback model redundancy."""
        if self.mock_mode:
            import time
            if "Clinical Research" in system_prompt or "Clinical Research Agent" in system_prompt:
                response = (
                    "**Clinical Evaluation & Sarcomeric Review (Simulated)**\n\n"
                    "1. **Therapeutic Recommendations**:\n"
                    "   - Continue monitoring patient left ventricular wall thickness and left ventricular outflow tract (LVOT) gradients.\n"
                    "   - Consider beta-blockers (e.g., Metoprolol) as first-line therapy to address symptomatic obstructive hypertrophy and improve diastolic filling parameters.\n"
                    "   - If refractory syncope or symptoms persist despite pharmacotherapy, evaluate for alcohol septal ablation or surgical septal myectomy.\n\n"
                    "2. **ICD-10 Classifications**:\n"
                    "   - **I42.1**: Obstructive hypertrophic cardiomyopathy\n"
                    "   - **I42.2**: Other hypertrophic cardiomyopathy\n\n"
                    "3. **Research Notes**:\n"
                    "   - EXPLORER-HCM clinical trial verified significant relief in LVOT gradients and exercise capacity using Mavacamten (cardiac myosin inhibitor)."
                )
            elif "layman" in system_prompt.lower() or "Family Physician" in system_prompt:
                response = (
                    "### Managing Your Heart Health (Simulated)\n\n"
                    "Based on verified medical guidelines, here is a simplified summary of the recommendations:\n\n"
                    "1. **Daily Steps & Lifestyle Changes**:\n"
                    "   - Focus on daily habits. Keep low sodium intake (under 1,500 mg per day) and follow the DASH diet (rich in fruits, vegetables, and whole grains).\n"
                    "   - Engage in moderate cardiovascular exercise (like 30 minutes of daily walking) if authorized by your primary practitioner.\n"
                    "   - Take blood pressure measurements daily, keeping a log for clinical consultations.\n\n"
                    "2. **Questions to Ask Your Doctor**:\n"
                    "   - Are my current exercise levels safe for my condition?\n"
                    "   - Should we evaluate my genetic profile or look for sarcomere gene mutations?\n"
                    "   - Is a referral to a clinical cardiologist indicated?"
                )
            else:
                response = "Simulated Response: The medical translation system is currently running in mock demonstration mode. This response represents clinical guidelines retrieved from the catalog."
            
            words = response.split(" ")
            for w in words:
                yield w + " "
                time.sleep(0.02)
            return

        try:
            stream = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.model,
                temperature=0.1,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            st.warning(f"Default model {self.model} failed, switching to fallback {self.fallback_model}: {e}")
            try:
                stream = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=self.fallback_model,
                    temperature=0.1,
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            except Exception as e2:
                yield f"\n\n[CRITICAL ERROR] Failed to query Groq models: {str(e2)}"

    def _call_llm_non_stream(self, system_prompt: str, user_prompt: str) -> str:
        """Helper to get full response in one go (for routing / fact-checking steps)."""
        if self.mock_mode:
            if "Router Agent" in system_prompt or "Clinical Router" in system_prompt:
                return "The query relates to cardiovascular therapeutics and management guidelines. Routing reasoning: evaluating retrieved FAISS vectors to extract relevant details."
            elif "Fact-Checking" in system_prompt:
                return (
                    "1. **Grounding Score**: 10/10\n"
                    "2. **Verification Checklist**:\n"
                    "   - Beta-blocker dosage guidance: Verified (Source guidelines)\n"
                    "   - DASH diet sodium restriction (<1,500 mg): Verified (Hypertension sheet)\n"
                    "3. **Analysis**: Perfect grounding. No clinical contradictions detected."
                )
            elif "clinical researcher" in system_prompt.lower():
                return "Analysis: Patient inquiries relate to high blood pressure management and lifestyle restrictions. Guidelines recommend low sodium intake and moderate walking."
            else:
                return "System running in simulated clinical mode. Grounding verified."

        try:
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.model,
                temperature=0.1
            )
            return completion.choices[0].message.content
        except Exception as e:
            try:
                completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=self.fallback_model,
                    temperature=0.1
                )
                return completion.choices[0].message.content
            except Exception as e2:
                return f"[CRITICAL ERROR] Failed to query Groq: {str(e2)}"

    def run_routing_agent(self, query: str, role: str) -> dict:
        """Orchestrator Agent: Logs routing reasoning and sets context parameters."""
        system_prompt = """
        You are the Clinical Router Agent of a Multi-Agent Medical RAG system.
        Your job is to analyze the query and the user's role, and output a concise routing reasoning.
        Specify what the query is about (e.g. diagnostic, medication, general advice) and how the system should handle it.
        Keep it under 3 sentences. Tone: analytical, coordinator.
        """
        user_prompt = f"User Role: {role}\nQuery: {query}"
        reasoning = self._call_llm_non_stream(system_prompt, user_prompt)
        return {
            "role": role,
            "routing_reasoning": reasoning
        }

    def run_clinical_research_agent_stream(self, query: str, contexts: list[dict]):
        """Clinical Research Agent (Doctor-Only): Deep medical literature review, jargon, ICD-10 and citations."""
        system_prompt = """
        You are a Senior Clinical Research Agent. Your task is to provide a highly detailed, professional, and technically accurate medical response to the user's query.
        You MUST rely on the provided retrieved medical context chunks.
        Include technical medical terminology, pathology details, potential ICD-10 or DSM-5 codes where relevant, and list clinical trials or research recommendations.
        When citing information, refer to the document name directly in parentheses, e.g. (Source: journal_article.pdf).
        Do NOT simplify or omit technical terms, as this output is strictly for Authorized Medical Practitioners (Doctors).
        If the context does not contain enough information, explain what is missing instead of making up facts.
        """
        
        context_str = ""
        for i, ctx in enumerate(contexts):
            context_str += f"--- Chunk {i+1} (Source: {ctx['source']}, Visibility: {ctx['visibility']}) ---\n{ctx['text']}\n\n"
            
        user_prompt = f"Retrieved Context:\n{context_str}\nPatient/Clinical Query: {query}"
        return self._call_llm_stream(system_prompt, user_prompt)

    def run_patient_layman_agent_stream(self, query: str, clinical_research: str, contexts: list[dict]):
        """Patient Summary Agent (Patient-Only): Warm, empathetic translation with actionable items."""
        system_prompt = """
        You are an empathetic Family Physician and Patient Layman Agent.
        Your task is to translate the provided technical medical research findings into clear, simple, patient-friendly language.
        Do NOT use complex medical jargon without translating it to plain terms.
        Maintain a warm, reassuring, yet realistic and empathetic tone.
        Organize your response with:
        1. A simple, easy-to-understand explanation of the clinical findings.
        2. Structured, bulleted "Action Items" (e.g. lifestyle, medication scheduling, self-care steps).
        3. A checklist of "Questions to ask your Doctor" during the next appointment.
        Use formatting like bolding and bullet points to make it readable.
        Include a warning to always consult a practitioner for major clinical changes.
        """
        
        context_str = ""
        for i, ctx in enumerate(contexts):
            context_str += f"--- Chunk {i+1} (Source: {ctx['source']}) ---\n{ctx['text']}\n\n"
            
        user_prompt = f"Patient Query: {query}\n\nTechnical Research Notes:\n{clinical_research}\n\nRaw Context:\n{context_str}"
        return self._call_llm_stream(system_prompt, user_prompt)

    def run_fact_checking_agent(self, agent_output: str, contexts: list[dict]) -> str:
        """Fact-Checking Agent: Validates retrieved contexts against LLM outputs, outputting a clear report."""
        system_prompt = """
        You are a Medical Integrity and Fact-Checking Agent.
        Your task is to compare the provided medical summary/agent response with the raw source contexts.
        Identify if there are any unsupported claims, hallucinations, or contradictions in the agent response.
        Output a structured Fact-Checking report:
        1. **Grounding Score**: X/10 (where 10/10 means everything is perfectly grounded in the context).
        2. **Verification Checklist**: A list of key medical facts stated in the agent response and their verification status (Verified / Unverified / Contradicting).
        3. **Analysis & Correction**: Explanations for any unverified or contradicting claims.
        Be very strict. If a claim is not explicitly mentioned or reasonably inferred from the context, mark it as Unverified.
        """
        
        context_str = ""
        for i, ctx in enumerate(contexts):
            context_str += f"--- Chunk {i+1} (Source: {ctx['source']}, Visibility: {ctx['visibility']}) ---\n{ctx['text']}\n\n"
            
        user_prompt = f"Raw Context:\n{context_str}\n\nAgent Output to Audit:\n{agent_output}"
        return self._call_llm_non_stream(system_prompt, user_prompt)
