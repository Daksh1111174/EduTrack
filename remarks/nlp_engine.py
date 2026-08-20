import re
from remarks.models import TeacherRemark

def analyze_teacher_remarks_nlp(student):
    """
    NLP Teacher Remark Analysis Engine:
    Parses natural language teacher remarks to extract key Strengths, Weaknesses,
    Behavioral Indicators, Academic Indicators, and Recommended Interventions.
    """
    remarks_qs = TeacherRemark.objects.filter(student=student)
    text_corpus = " ".join([r.remark for r in remarks_qs]) if remarks_qs.exists() else ""

    strengths = []
    weaknesses = []
    recommendations = []

    text_lower = text_corpus.lower()

    # Strength patterns
    if re.search(r'\b(excellent|good|strong|understands|concept|conceptually|talented|bright|active)\b', text_lower):
        strengths.append("Strong conceptual understanding & learning agility")
    if re.search(r'\b(disciplined|respectful|polite|cooperative|well-behaved)\b', text_lower):
        strengths.append("High discipline and classroom conduct")
    if re.search(r'\b(leadership|leader|presents|creative|team player)\b', text_lower):
        strengths.append("Demonstrates leadership and peer teamwork")

    if not strengths:
        strengths.append("Steady learning progress and receptiveness to feedback")

    # Weakness patterns
    if re.search(r'\b(rarely|hardly|low|lacks|quiet|silent|shy)\b', text_lower) or 'participate' in text_lower:
        weaknesses.append("Classroom participation and verbal engagement")
    if re.search(r'\b(late|delay|missed|missing|incomplete|homework|assignment)\b', text_lower):
        weaknesses.append("Assignment punctuality and submission deadlines")
    if re.search(r'\b(distracted|inattentive|talkative|absent|attendance)\b', text_lower):
        weaknesses.append("Classroom focus and attendance consistency")

    if not weaknesses:
        weaknesses.append("Scope for higher exam scores in complex problem solving")

    # Recommendation extraction
    if "participation" in " ".join(weaknesses).lower():
        recommendations.append("Encourage student during group presentations and Q&A sessions.")
    if "assignment" in " ".join(weaknesses).lower():
        recommendations.append("Set up weekly assignment reminders with parent follow-up.")
    if "focus" in " ".join(weaknesses).lower():
        recommendations.append("Assign front-row seating and conduct bi-weekly check-ins.")

    if not recommendations:
        recommendations.append("Provide advanced learning exercises to maintain high engagement.")

    return {
        'strengths': strengths,
        'weaknesses': weaknesses,
        'recommendations': recommendations,
        'total_remarks_analyzed': remarks_qs.count()
    }
