from assignments.models import AssignmentSubmission

def evaluate_student_risk(student, perf_score, setting=None):
    """
    Evaluates student risk level (LOW, MEDIUM, HIGH) based on multi-indicator thresholds
    and returns (risk_level, recommendation_string).
    """
    min_att = float(setting.min_attendance_threshold) if setting else 75.0

    acad = float(perf_score.academic_score)
    att = float(perf_score.attendance_score)
    beh = float(perf_score.behaviour_score)
    hpi = float(perf_score.holistic_score)
    imp = float(perf_score.improvement_score)

    # Check assignment missing rate
    submissions = AssignmentSubmission.objects.filter(student=student)
    total_subs = submissions.count()
    missing_subs = submissions.filter(status=AssignmentSubmission.Status.MISSING).count()
    missing_pct = (missing_subs / total_subs * 100.0) if total_subs > 0 else 0.0

    risk_factors = []
    recommendations = []

    # Check High Risk Criteria
    if att < 70.0:
        risk_factors.append(f"Severe attendance drop ({att:.1f}% vs threshold {min_att:.1f}%)")
        recommendations.append("Schedule urgent parent-teacher meeting regarding attendance.")

    if acad < 50.0:
        risk_factors.append(f"Failing academic average ({acad:.1f}%)")
        recommendations.append("Provide remedial tutoring in core subjects.")

    if hpi < 55.0:
        risk_factors.append(f"Critically low Holistic Performance Index ({hpi:.1f})")
        recommendations.append("Assign counselor mentor for academic & personal guidance.")

    if imp < 45.0:
        risk_factors.append("Declining overall performance trajectory")
        recommendations.append("Review recent classroom engagement and assignment workload.")

    # High Risk determination
    if len(risk_factors) >= 2 or att < 65.0 or acad < 45.0 or hpi < 50.0:
        risk_level = 'HIGH'
        if not recommendations:
            recommendations.append("Immediate teacher intervention and academic support plan required.")
        return risk_level, "\n".join(recommendations)

    # Check Medium Risk Criteria
    med_factors = []
    if att < min_att:
        med_factors.append(f"Attendance below threshold ({att:.1f}%)")
        recommendations.append("Monitor daily attendance closely and notify parent.")

    if acad < 60.0:
        med_factors.append(f"Below average academic score ({acad:.1f}%)")
        recommendations.append("Recommend extra study sessions before upcoming exams.")

    if beh < 65.0:
        med_factors.append(f"Behaviour score requires improvement ({beh:.1f}%)")
        recommendations.append("Focus on classroom discipline and team cooperation activities.")

    if missing_pct > 25.0:
        med_factors.append(f"High missing assignment rate ({missing_pct:.1f}%)")
        recommendations.append("Set strict homework deadlines with daily submission tracking.")

    if len(med_factors) >= 1 or hpi < 68.0:
        risk_level = 'MEDIUM'
        if not recommendations:
            recommendations.append("Regular performance tracking recommended.")
        return risk_level, "\n".join(recommendations)

    # Default Low Risk
    risk_level = 'LOW'
    recommendations = ["Student is performing well across all pillars. Continue encouraging positive performance."]
    return risk_level, "\n".join(recommendations)
