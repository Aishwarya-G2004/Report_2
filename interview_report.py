import json
from pydantic import BaseModel, Field
from typing import List
from langchain.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


class ConversationEntry(BaseModel):
    question: str
    answer: str

class InterviewData(BaseModel):
    email: str = Field(..., title="Candidate Email")
    name: str = Field(..., title="Candidate Name")
    role: str = Field(..., title="Job Role")
    date: str = Field(..., title="Interview Date")
    conversation: List[ConversationEntry]


with open("interview_data.json", "r") as file:
    data = json.load(file)
interview = InterviewData(**data)

class InterviewEvaluation(BaseModel):
    overall_summary: str 
    technical_evaluation: str
    non_technical_evaluation: str
    strengths_areas_for_improvement: str
    final_evaluation: str
    next_steps: str

gemini = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0, google_api_key="AIzaSyA9usph-F3M_HaZoKrzg3BOSHfSrekGwmw")
parser = PydanticOutputParser(pydantic_object=InterviewEvaluation)


conversation_text = "\n".join(
    [f"Q: {entry.question}\nA: {entry.answer}\n" for entry in interview.conversation]
)


prompt = f"""
 Analyze the following interview transcript and generate a detailed evaluation report.
    Include a performance score (out of 10) at the beginning of the Overall Summary.
    Provide concise and structured responses in the following sections:
    1. Overall Summary (with score)
    2. Technical Evaluation (assess technical knowledge, problem-solving, relevant skills)
    3. Non-Technical Evaluation (evaluate communication, teamwork, adaptability)
    4. Strengths (highlight key strengths demonstrated)
    5. Areas for Improvement (identify gaps and suggest improvements)
    6. Final Evaluation (summarize suitability for the role)
    7. Next Steps (recommend follow-up actions)
    Format the response according to the provided Pydantic model.
Interview Transcript:
{conversation_text}
"""

response = gemini.invoke(prompt + "\n" + parser.get_format_instructions())
evaluation = parser.parse(response.content)

def generate_pdf(interview: InterviewData, evaluation: InterviewEvaluation):
    filename = f"Interview_Report_{interview.name.replace(' ', '_')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("AI-Based Interview Evaluation Report", styles['Title']))
    elements.append(Spacer(1, 12))

    # Candidate Info
    candidate_info = f"""
    <b>Candidate Name:</b> {interview.name}<br/>
    <b>Email:</b> {interview.email}<br/>
    <b>Role:</b> {interview.role}<br/>
    <b>Interview Date:</b> {interview.date}<br/>
    """
    elements.append(Paragraph(candidate_info, styles['Normal']))
    elements.append(Spacer(1, 12))

   
    sections = {
        "Overall Summary (including Score)": evaluation.overall_summary,
        "Technical Evaluation": evaluation.technical_evaluation,
        "Non-Technical Evaluation": evaluation.non_technical_evaluation,
        "Strengths & Areas for Improvement": evaluation.strengths_areas_for_improvement,
        "Final Evaluation": evaluation.final_evaluation,
        "Next Steps": evaluation.next_steps,
    }

    for section, content in sections.items():
        elements.append(Paragraph(f"<b>{section}</b>", styles['Heading2']))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(content, styles['Normal']))
        elements.append(Spacer(1,6))

  
    doc.build(elements)
    print(f"Report saved as {filename}")

generate_pdf(interview, evaluation)
