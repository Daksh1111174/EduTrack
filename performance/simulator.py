from performance.models import PerformanceScore, PerformanceSetting

def simulate_what_if_hpi(perf_record, att_delta=0, acad_delta=0, ass_delta=0):
    """
    What-If Performance Simulator:
    Simulates how improvements in Attendance %, Academic Marks %, or Assignment Completion %
    project onto the student's Holistic Performance Index (HPI).
    """
    if not perf_record:
        return 75.0, 75.0, 0.0

    setting = PerformanceSetting.objects.first()
    w_acad = float(setting.weight_academic) if setting else 40.0
    w_att = float(setting.weight_attendance) if setting else 15.0
    w_beh = float(setting.weight_behaviour) if setting else 15.0
    w_part = float(setting.weight_participation) if setting else 10.0
    w_ass = float(setting.weight_assignments) if setting else 5.0
    w_imp = float(setting.weight_improvement) if setting else 10.0
    w_ach = float(setting.weight_achievements) if setting else 5.0

    total_weight = w_acad + w_att + w_beh + w_part + w_ass + w_imp + w_ach
    if total_weight <= 0: total_weight = 100.0

    current_hpi = float(perf_record.holistic_score)

    s_acad = min(100.0, max(0.0, float(perf_record.academic_score) + acad_delta))
    s_att = min(100.0, max(0.0, float(perf_record.attendance_score) + att_delta))
    s_beh = float(perf_record.behaviour_score)
    s_part = float(perf_record.participation_score)
    s_ass = min(100.0, max(0.0, float(perf_record.assignment_score) + ass_delta))
    s_imp = float(perf_record.improvement_score)
    s_ach = float(perf_record.achievement_score)

    projected_sum = (
        (s_acad * w_acad) +
        (s_att * w_att) +
        (s_beh * w_beh) +
        (s_part * w_part) +
        (s_ass * w_ass) +
        (s_imp * w_imp) +
        (s_ach * w_ach)
    )

    projected_hpi = round(projected_sum / total_weight, 2)
    delta = round(projected_hpi - current_hpi, 2)

    return current_hpi, projected_hpi, delta
