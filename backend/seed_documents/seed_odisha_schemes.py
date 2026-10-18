import os
import sys
import uuid
from fpdf import FPDF

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.models.database import SessionLocal, User, DocumentMetadata
from backend.rag.ingestion import process_document_ingestion

class SchemePDF(FPDF):
    def __init__(self, title):
        super().__init__()
        self.doc_title = title

    def header(self):
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 10, self.doc_title, 0, new_x="LMARGIN", new_y="NEXT", align='C')
        self.ln(5)

def build_pdf(filename: str, title: str, sections: list) -> str:
    pdf = SchemePDF(title)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    
    for item in sections:
        if len(item) == 2:
            sec_title, content = item
            table_data = None
        else:
            sec_title, content, table_data = item
            
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 8, sec_title, 0, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=10)
        for line in content.strip().split('\n'):
            pdf.cell(0, 6, line.strip(), 0, new_x="LMARGIN", new_y="NEXT")
        
        if table_data:
            pdf.ln(2)
            with pdf.table() as table:
                for row_data in table_data:
                    row = table.row()
                    for cell_data in row_data:
                        row.cell(str(cell_data))
        pdf.ln(4)
        
    out_dir = os.path.dirname(__file__)
    file_path = os.path.join(out_dir, filename)
    pdf.output(file_path)
    return file_path

def seed_all_schemes():
    print("Generating official scheme documents...")
    
    # 1. KALIA Scheme Document
    kalia_sections = [
        ("1. Scheme Overview and Objectives", 
         "The KALIA Scheme (Krushak Assistance for Livelihood and Income Augmentation) is launched by the Government of Odisha to support farmers, cultivators, and landless agricultural laborers.\n"
         "Department: Agriculture and Farmers Empowerment, Government of Odisha.\n"
         "The scheme aims to accelerate agricultural prosperity and eradicate poverty."),
        ("2. Financial Assistance and Benefits",
         "- Small and Marginal Farmers receive Rs 10000 per family per year provided in two installments for Kharif and Rabi seasons.\n"
         "- Landless Agricultural Households receive Rs 12500 for livelihood activities such as goat rearing, poultry, duckery, and bee keeping.\n"
         "- Vulnerable Cultivators receive financial aid of Rs 10000 per family for sustenance.\n"
         "- Life Insurance cover of Rs 200000 at a nominal premium for all savings bank account holders between 18 to 50 years.",
         (
             ("Beneficiary Category", "Financial Assistance", "Installments / Details"),
             ("Small & Marginal Farmers", "Rs 10,000 per family per year", "2 Installments (Kharif and Rabi)"),
             ("Landless Agricultural Households", "Rs 12,500 per family", "Livelihood activities"),
             ("Vulnerable Cultivators", "Rs 10,000 per family", "Annual sustenance assistance"),
             ("Life Insurance Cover", "Rs 2,00,000 cover", "Nominal premium (18 to 50 years)")
         )),
        ("3. Eligibility Criteria",
         "- Permanent resident of Odisha.\n"
         "- Small and marginal farmers with landholding up to 2 hectares (5 acres).\n"
         "- Landless agricultural households whose primary income is derived from agricultural activities.\n"
         "- Government employees and income tax payees are strictly excluded."),
        ("4. Required Documents for Application",
         "- Aadhaar Card.\n"
         "- Bank Account Passbook seeded with Aadhaar.\n"
         "- Land Record RoR (Record of Rights) for cultivators.\n"
         "- Ration Card (NFSA / SFSS).\n"
         "- Mobile number registered with bank account."),
        ("5. Hindi / Hinglish Summary",
         "KALIA Yojana Odisha sarkar dwara kisanon ke liye shuru ki gayi hai.\n"
         "Kharif aur Rabi fasal ke liye Rs 10000 prativarsh diye jaate hain.\n"
         "Aavashyak Dastavez: Aadhaar Card, Bank Passbook, RoR Khatiyan, Ration Card.\n"
         "Bhoomiheen shramikon ko Rs 12500 diye jaate hain.")
    ]
    kalia_path = build_pdf("kalia_yojana_guidelines.pdf", "KALIA Yojana Official Guidelines - Govt of Odisha", kalia_sections)

    # 2. BSKY Health Insurance Document
    bsky_sections = [
        ("1. Scheme Overview and Medical Coverage",
         "Biju Swasthya Kalyan Yojana (BSKY) / Gopabandhu Jan Arogya Yojana provides cashless healthcare coverage to citizens of Odisha.\n"
         "Department: Health and Family Welfare Department, Government of Odisha.\n"
         "Coverage Amount: Up to Rs 500000 per family per annum for secondary and tertiary healthcare, and up to Rs 1000000 per annum for women members in the family."),
        ("2. Hospital Network and Facilities",
         "- Cashless treatment is available across all Odisha Government Hospitals from District Headquarter Hospitals to Medical Colleges.\n"
         "- Cashless treatment is also available in more than 800 empaneled premier private hospitals within and outside Odisha (including AIIMS, Apollo, Fortis, Tata Medical Center).\n"
         "- Covers 4036 surgical procedures, diagnostic tests, medicines, ICU charges, and post-operative care.",
         (
             ("Beneficiary Category", "Annual Health Coverage", "Hospital Network"),
             ("General Family Members", "Up to Rs 5,00,000 per annum", "All Govt & 800+ Empaneled Hospitals"),
             ("Women Family Members", "Up to Rs 10,00,000 per annum", "All Govt & 800+ Empaneled Hospitals"),
             ("Critical & Surgical Care", "4,036 surgical procedures", "Free medicines, ICU & diagnostics")
         )),
        ("3. Eligibility and Beneficiary Identification",
         "- All holders of BSKY Smart Health Card.\n"
         "- All National Food Security Act (NFSA) and State Food Security Scheme (SFSS) ration card holders.\n"
         "- All rural and urban families covered under state food schemes."),
        ("4. Required Documents for Hospital Admission",
         "- BSKY Smart Health Card or Valid Ration Card.\n"
         "- Aadhaar Card of the patient / family head.\n"
         "- Hospital referral slip for private empaneled hospital admissions."),
        ("5. Hindi / Hinglish Summary",
         "BSKY Yojana mein Rs 5 Lakh tak ka cashless ilaj milta hai aur mahilaon ke liye Rs 10 Lakh tak ka.\n"
         "800 se zyada private aur sabhi sarkari aspatalon mein ilaj uplabdh hai.\n"
         "Dastavez: BSKY Card ya Ration Card aur Aadhaar Card.")
    ]
    bsky_path = build_pdf("bsky_health_policy.pdf", "Biju Swasthya Kalyan Yojana (BSKY) - Govt of Odisha", bsky_sections)

    # 3. Madhu Babu Pension Yojana (MBPY)
    mbpy_sections = [
        ("1. Pension Scheme Overview",
         "Madhu Babu Pension Yojana (MBPY) is a comprehensive social security pension scheme launched by the Government of Odisha.\n"
         "Department: Social Security and Empowerment of Persons with Disabilities (SSEPD).\n"
         "Objective: To provide monthly financial support to old-aged, widows, disabled persons, and destitute citizens."),
        ("2. Pension Amounts and Categories",
         "- Beneficiaries aged 60 to 79 years: Rs 500 per month (revised up to Rs 1000 per month).\n"
         "- Beneficiaries aged 80 years and above: Rs 700 to Rs 1200 per month.\n"
         "- Persons with Disabilities (PwD) with 40% to 59% disability: Rs 500 per month.\n"
         "- Persons with Disabilities (PwD) with 60% or more disability: Rs 700 to Rs 1400 per month.",
         (
             ("Beneficiary Category", "Age / Disability Criteria", "Monthly Pension Amount"),
             ("Senior Citizens (Old Age)", "Aged 60 to 79 years", "Rs 500 to Rs 1,000 per month"),
             ("Super Senior Citizens", "Aged 80 years and above", "Rs 700 to Rs 1,200 per month"),
             ("Persons with Disabilities", "40% to 59% disability", "Rs 500 per month"),
             ("Severe Disabilities", "60% or more disability", "Rs 700 to Rs 1,400 per month")
         )),
        ("3. Eligibility Criteria",
         "- Minimum age of 60 years for Old Age Pension.\n"
         "- Permanent resident and domicile of Odisha.\n"
         "- Annual family income must not exceed Rs 24000 per annum from all sources.\n"
         "- Not receiving any other state or central pension."),
        ("4. Required Documents for Application",
         "- Age Proof (Aadhaar Card, Birth Certificate, or Voter ID).\n"
         "- Income Certificate issued by Revenue Officer / Tahsildar.\n"
         "- Disability Certificate issued by Medical Board (for disability pension).\n"
         "- Death Certificate of Husband (for widow pension).\n"
         "- Bank Passbook with active IFSC and account number."),
        ("5. Hindi / Hinglish Summary",
         "Madhu Babu Pension Yojana vridhjan, vidhwa aur divyang vyaktiyon ke liye hai.\n"
         "60 varsh se adhik aayu ke logon ko masik pension milti hai.\n"
         "Parivarik aay Rs 24000 se kam honi chahiye.\n"
         "Dastavez: Aadhaar Card, Aay Praman Patra, Bank Passbook, Disability Certificate.")
    ]
    mbpy_path = build_pdf("madhu_babu_pension_scheme.pdf", "Madhu Babu Pension Yojana (MBPY) - Govt of Odisha", mbpy_sections)

    # 4. Odisha State Scholarship Scheme
    scholarship_sections = [
        ("1. Scholarship Scheme Overview",
         "Odisha State Scholarship Portal (e-Medhabruti & Post-Matric Scholarships) provides financial assistance to meritorious and socio-economically disadvantaged students.\n"
         "Department: Higher Education and ST & SC Development Department, Govt of Odisha.\n"
         "Application Portal: scholarship.odisha.gov.in"),
        ("2. Scholarship Categories and Amounts",
         "- Junior Merit Scholarship: Rs 3000 per year for +2 students.\n"
         "- Senior Merit Scholarship: Rs 5000 per year for +3 (Degree) students.\n"
         "- Technical and Professional Scholarship (B.Tech, MBBS, MBA, MCA): Rs 10000 per year.\n"
         "- Post-Matric Scholarship for SC/ST/OBC: Covers 100% course fee plus monthly maintenance allowance.",
         (
             ("Scholarship Scheme", "Eligible Course / Level", "Annual Financial Support"),
             ("Junior Merit Scholarship", "+2 (Higher Secondary) students", "Rs 3,000 per year"),
             ("Senior Merit Scholarship", "+3 (Degree / Graduation) students", "Rs 5,000 per year"),
             ("Technical & Professional", "B.Tech, MBBS, MBA, MCA courses", "Rs 10,000 per year"),
             ("Post-Matric SC/ST/OBC", "Higher Education after Matric", "100% course fee + allowance")
         )),
        ("3. Eligibility Criteria and Deadlines",
         "- Minimum 60% aggregate marks in the previous qualifying examination.\n"
         "- Family annual income should not exceed Rs 250000 (Rs 2.5 Lakh) per annum.\n"
         "- Student must be enrolled as a regular full-time student in an approved college/university.\n"
         "- Application Deadline: October 31st annually."),
        ("4. Required Documents",
         "- Marksheets and Certificates of last qualifying examination.\n"
         "- Aadhaar Card.\n"
         "- Resident / Domicile Certificate issued by Tahsildar.\n"
         "- Income Certificate of parents.\n"
         "- Caste Certificate for SC/ST/OBC candidates.\n"
         "- College Bonafide Certificate and Fee Receipt.\n"
         "- Student Bank Account Passbook."),
        ("5. Hindi / Hinglish Summary",
         "Odisha State Scholarship Yojana me regular students ko Rs 3000 se Rs 10000 prativarsh milte hain.\n"
         "Yogyata: Pichhli pariksha me kam se kam 60% ank aur parivarik aay Rs 2.5 Lakh se kam.\n"
         "Antim Tithi: 31 October.\n"
         "Dastavez: Marksheet, Aadhaar Card, Aay Praman Patra, Jati Praman Patra, Bonafide Certificate.")
    ]
    scholarship_path = build_pdf("odisha_scholarship_policy.pdf", "Odisha State Scholarship Guidelines - Govt of Odisha", scholarship_sections)

    # Index into database and Chroma
    db_init = SessionLocal()
    admin = db_init.query(User).filter(User.role == 'admin').first()
    if not admin:
        admin = User(id="admin-seed-id", email="admin@demo.com", hashed_password="x", role="admin")
        db_init.add(admin)
        db_init.commit()
    admin_id = admin.id
    db_init.close()

    docs_to_index = [
        (kalia_path, "kalia-scheme-doc", "KALIA Yojana Guidelines", "KALIA Yojana Official Guidelines.pdf", "Agriculture & Farmers Empowerment", "en", "2024.1", "https://kalia.odisha.gov.in"),
        (bsky_path, "bsky-health-doc", "Biju Swasthya Kalyan Yojana Policy", "Biju Swasthya Kalyan Yojana Policy.pdf", "Health & Family Welfare", "en", "2024.1", "https://bsky.odisha.gov.in"),
        (mbpy_path, "mbpy-pension-doc", "Madhu Babu Pension Yojana Guidelines", "Madhu Babu Pension Yojana Guidelines.pdf", "Social Security & Empowerment", "en", "2024.1", "https://ssepd.gov.in"),
        (scholarship_path, "scholarship-odisha-doc", "Odisha State Scholarship Scheme", "Odisha State Scholarship Scheme.pdf", "Higher Education", "en", "2024.1", "https://scholarship.odisha.gov.in")
    ]

    for fpath, doc_id, doc_title, filename, dept, lang, ver, url in docs_to_index:
        db = SessionLocal()
        existing = db.query(DocumentMetadata).filter(DocumentMetadata.id == doc_id).first()
        if not existing:
            meta = DocumentMetadata(
                id=doc_id,
                title=doc_title,
                filename=filename,
                department=dept,
                category="Scheme",
                language=lang,
                version=ver,
                source_type="demo",
                authority_level="demo",
                source_url=url,
                publisher="Govt of Odisha (Demo Knowledge Base)",
                status="pending",
                uploaded_by=admin_id
            )
            db.add(meta)
            db.commit()
        else:
            existing.title = doc_title
            existing.source_type = "demo"
            existing.authority_level = "demo"
            existing.source_url = url
            db.commit()
        db.close()

        print(f"Ingesting {filename} (source_type=demo)...")
        process_document_ingestion(
            file_path=fpath,
            doc_id=doc_id,
            department=dept,
            language=lang,
            version=ver,
            title=doc_title,
            category="Scheme",
            source_type="demo",
            authority_level="demo",
            source_url=url,
            publisher="Govt of Odisha (Demo Knowledge Base)",
            auto_activate=True
        )

    print("All Odisha official schemes successfully generated and indexed into ChromaDB + BM25 with demo provenance tags!")

if __name__ == "__main__":
    seed_all_schemes()
