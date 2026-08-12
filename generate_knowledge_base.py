import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_pdf(path, title, subtitle, paragraphs, access_boundary):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter
    
    # Draw Header Background Band
    c.setFillColorRGB(0.06, 0.32, 0.73)  # Professional Deep Blue
    c.rect(0, height - 80, width, 80, fill=True, stroke=False)
    
    # Title Text
    c.setFillColorRGB(1.0, 1.0, 1.0)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 35, title)
    
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 55, subtitle)
    
    # Access Banner
    c.setFillColorRGB(0.09, 0.45, 0.27)  # Forest Green
    c.rect(0, height - 105, width, 25, fill=True, stroke=False)
    
    c.setFillColorRGB(1.0, 1.0, 1.0)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, height - 98, f"SECURITY BOUNDARY: {access_boundary}")
    
    # Body Content
    c.setFillColorRGB(0.1, 0.1, 0.1)
    
    y = height - 140
    for title, text in paragraphs:
        # Check space
        if y < 80:
            c.showPage()
            y = height - 80
            
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, title)
        y -= 18
        
        c.setFont("Helvetica", 10)
        words = text.split(' ')
        line = []
        for w in words:
            line.append(w)
            # Simple word wrapping
            if len(" ".join(line)) * 5 > width - 100:
                c.drawString(50, y, " ".join(line[:-1]))
                y -= 14
                line = [w]
                if y < 50:
                    c.showPage()
                    y = height - 80
                    c.setFont("Helvetica", 10)
                    
        if line:
            c.drawString(50, y, " ".join(line))
            y -= 25

    c.save()
    print(f"Created PDF: {path}")

# 1. Public Patient Guide
public_paragraphs = [
    (
        "Introduction to Hypertension Management",
        "Hypertension, commonly known as high blood pressure, occurs when the force of blood pushing against the walls of your arteries is consistently elevated. Over time, untreated high blood pressure can lead to cardiovascular disease, stroke, and kidney failure. Managing your blood pressure is key to long-term health."
    ),
    (
        "Nutritional Recommendations (DASH Diet)",
        "The Dietary Approaches to Stop Hypertension (DASH) diet is highly recommended for lowering blood pressure. This eating plan focuses on consuming fruits, vegetables, whole grains, and lean proteins, such as poultry and fish. It strictly limits foods high in saturated fats, cholesterol, and refined sugars. Crucially, daily sodium intake should be reduced to under 1,500 milligrams to achieve the best therapeutic results."
    ),
    (
        "Physical Activity and Lifestyle Habits",
        "Engaging in regular aerobic physical activity, such as brisk walking, swimming, or cycling, for at least 150 minutes per week helps strengthen the cardiovascular system. Additionally, patients should avoid tobacco use, limit alcohol consumption, and practice stress-reduction techniques like meditation to maintain optimal vessel elasticity."
    ),
    (
        "Home Blood Pressure Monitoring",
        "Patients should monitor their blood pressure at home using a validated upper-arm cuff. Measurements should be taken at the same times each day, preferably in the morning before medication and in the evening. Keep a written log of your readings to share with your primary care provider during clinical consultations."
    )
]

# 2. Restricted Clinical Study
restricted_paragraphs = [
    (
        "Abstract: Genetic Profile of Familial Hypertrophic Cardiomyopathy",
        "Hypertrophic Cardiomyopathy (HCM) is an autosomal dominant genetic cardiac disorder characterized by unexplained left ventricular hypertrophy in the absence of other cardiac or systemic diseases. This clinical review examines mutations in sarcomere protein genes, specifically focusing on the cardiac myosin-binding protein-C (MYBPC3) gene and its implications for clinical risk assessment."
    ),
    (
        "Sarcomeric Gene Mutations & Pathophysiology",
        "Mutations in MYBPC3 represent approximately 30% to 40% of all identified genetic variants in familial HCM. Most MYBPC3 mutations are frameshift, splice-site, or nonsense mutations that lead to a C-terminal truncated protein, causing haploinsufficiency. This disruption of the sarcomeric structure impairs myofilament contractility, triggers secondary hypertrophic signaling pathways, and promotes interstitial fibrosis."
    ),
    (
        "Clinical Evaluation and Risk Stratification",
        "Evaluation of suspected HCM patients requires a 12-lead ECG, transthoracic echocardiogram (TTE), and cardiac magnetic resonance (CMR) imaging to quantify maximum wall thickness and identify late gadolinium enhancement (LGE). Risk stratification for Sudden Cardiac Death (SCD) must assess prior cardiac arrest, family history of premature SCD, unexplained syncope, non-sustained ventricular tachycardia (NSVT), and massive left ventricular hypertrophy (thickness >= 30mm)."
    ),
    (
        "Therapeutic Interventions & Management Guidelines",
        "First-line pharmacotherapy for symptomatic obstructive HCM consists of beta-blockers (e.g., metoprolol) or non-dihydropyridine calcium channel blockers (e.g., verapamil) to reduce the heart rate and prolong diastolic filling. For patients with drug-refractory severe symptoms and a left ventricular outflow tract (LVOT) gradient >= 50 mmHg, surgical septal myectomy or alcohol septal ablation is indicated. High-risk patients should receive an Implantable Cardioverter-Defibrillator (ICD) for primary prevention."
    )
]

create_pdf(
    "knowledge_base/public/hypertension_patient_guide.pdf",
    "DHANVA TEACH Public Patient Guide",
    "Hypertension Care & Dietary Guidelines",
    public_paragraphs,
    "PUBLIC - PATIENT ACCESSIBLE"
)

create_pdf(
    "knowledge_base/restricted/cardiology_clinical_study.pdf",
    "DHANVA TEACH Clinical Research Report",
    "Genetic Splice-Site Mutations in Familial Hypertrophic Cardiomyopathy",
    restricted_paragraphs,
    "RESTRICTED - AUTHORIZED MEDICAL PRACTITIONERS ONLY"
)
