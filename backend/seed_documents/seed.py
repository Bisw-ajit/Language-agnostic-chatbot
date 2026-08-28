from fpdf import FPDF
import os

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Institutional Scholarship Policy 2024-2025', 0, 1, 'C')
        self.ln(10)

def create_pdf():
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    content = """
    English:
    The deadline for the Merit Scholarship is October 31st, 2024. 
    Eligibility criteria: 
    - Must be a full-time student
    - Minimum GPA of 3.5
    Required documents: Transcripts, Recommendation Letter.
    Amount: $5000 per academic year.

    Hindi (Transliterated for FPDF support):
    Merit Scholarship ki antim tithi 31 October 2024 hai.
    Patrata mandand:
    - Purnakalik chhatra hona chahiye
    - Nyuntam GPA 3.5
    Aavashyak dastavez: Transcripts, Sifarish patra.
    Rashi: $5000 prativarsh.
    """
    
    for line in content.split('\n'):
        pdf.cell(0, 10, txt=line.strip(), ln=1)
        
    output_path = os.path.join(os.path.dirname(__file__), "sample_scholarship.pdf")
    pdf.output(output_path)
    print(f"Generated {output_path}")

if __name__ == "__main__":
    create_pdf()
