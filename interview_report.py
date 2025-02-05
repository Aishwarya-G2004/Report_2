import json
from pydantic import BaseModel, Field
from typing import List
from langchain.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

class ConversationEntry(BaseModel):
    question: str
    answer: str

class InterviewData(BaseModel):
    email: str = Field(..., title="Candidate Email")
    name: str = Field(..., title="Candidate Name")
    role: str = Field(..., title="Job Role")
    date: str = Field(..., title="Interview Date")
    conversation: List[ConversationEntry]

class InterviewEvaluation(BaseModel):
    performance_score: float
    overall_summary: str 
    technical_competence: str
    communication_skills: str
    professional_demeanor: str
    growth_potential: str
    final_recommendation: str

def create_apa_prompt(conversation_text):
    return f"""Conduct a comprehensive, academically rigorous evaluation of the interview transcript using a systematic, evidence-based approach.

Evaluation Framework:
- Utilize a holistic, multi-dimensional assessment methodology
- Provide quantitative and qualitative insights
- Maintain objectivity and professional neutrality

Specific Assessment Criteria:
1. Performance Score (0-10 scale):
   - Derive from comprehensive analysis of candidate's responses
   - Consider technical knowledge, communication clarity

2. Technical Competence Evaluation:
   - Assess depth of domain-specific knowledge
   - Analyze complexity of technical understanding
   - Evaluate practical application capabilities

3. Communication Skills Assessment:
   - Analyze clarity, structure, and coherence of responses
   - Evaluate ability to articulate complex ideas
   - Assess professional communication effectiveness

4. Professional Demeanor:
   - Assess cultural alignment
   - Evaluate interpersonal skills
   - Analyze adaptability and learning orientation

5. Growth Potential:
   - Identify potential for professional development
   - Assess alignment with organizational growth trajectory
   - Evaluate long-term contribution potential

6. Final Recommendation:
   - Provide clear, evidence-based hiring recommendation
   - Highlight potential risks and opportunities

Interview Transcript:
{conversation_text}

Provide a structured, academic-style evaluation addressing each specified dimension."""

gemini = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0, google_api_key="AIzaSyA9usph-F3M_HaZoKrzg3BOSHfSrekGwmw")
parser = PydanticOutputParser(pydantic_object=InterviewEvaluation)

def generate_apa_pdf(interview: InterviewData, evaluation: InterviewEvaluation):
    filename = f"Interview_Report_{interview.name.replace(' ', '_')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4, leftMargin=inch, rightMargin=inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='APATitle', parent=styles['Title'], fontSize=16, alignment=1))
    styles.add(ParagraphStyle(name='APAHeading', parent=styles['Heading2'], fontSize=12, spaceAfter=6))
    styles.add(ParagraphStyle(name='APANormal', parent=styles['Normal'], fontSize=11, leading=14))
    
    elements = []

    # Title Page
    elements.append(Paragraph("Interview Evaluation Report", styles['APATitle']))
    elements.append(Spacer(1, 12))
    
    # Candidate Information Table
    candidate_data = [
        ['Candidate Name', interview.name],
        ['Email', interview.email],
        ['Position', interview.role],
        ['Interview Date', interview.date]
    ]
    candidate_table = Table(candidate_data, colWidths=[2*inch, 4*inch])
    candidate_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (0,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    elements.append(candidate_table)
    elements.append(Spacer(1, 12))

    # Performance Sections
    sections = [
        ('Performance Score', f"{evaluation.performance_score}/10"),
        ('Overall Summary', evaluation.overall_summary),
        ('Technical Competence', evaluation.technical_competence),
        ('Communication Skills', evaluation.communication_skills),
        ('Professional Demeanor', evaluation.professional_demeanor),
        ('Growth Potential', evaluation.growth_potential),
        ('Final Recommendation', evaluation.final_recommendation)
    ]

    for title, content in sections:
        elements.append(Paragraph(title, styles['APAHeading']))
        elements.append(Paragraph(content, styles['APANormal']))
        elements.append(Spacer(1, 6))

    doc.build(elements)
    print(f"APA-formatted report saved as {filename}")

# Main execution
with open("interview_data.json", "r") as file:
    data = json.load(file)
interview = InterviewData(**data)

conversation_text = "\n".join(
    [f"Q: {entry.question}\nA: {entry.answer}\n" for entry in interview.conversation]
)

prompt = create_apa_prompt(conversation_text)
response = gemini.invoke(prompt + "\n" + parser.get_format_instructions())
evaluation = parser.parse(response.content)

generate_apa_pdf(interview, evaluation)
