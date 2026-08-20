import numpy as np
from sklearn.cluster import KMeans
from performance.models import PerformanceScore
from students.models import Student

def get_student_clusters():
    """
    Machine Learning Student Clustering: Uses K-Means to cluster students into 4 performance personas:
    1. High Performers
    2. High Academic / Low Participation
    3. Improving Students
    4. At-Risk Students
    """
    scores_qs = PerformanceScore.objects.select_related('student', 'student__class_obj', 'student__division_obj').all()
    if scores_qs.count() < 4:
        return {}

    data = []
    student_map = []
    for score in scores_qs:
        data.append([
            float(score.academic_score),
            float(score.attendance_score),
            float(score.behaviour_score),
            float(score.participation_score),
            float(score.assignment_score)
        ])
        student_map.append(score.student)

    X = np.array(data)
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)

    clusters = {
        'Cluster 1: High Performers': [],
        'Cluster 2: High Academic / Low Participation': [],
        'Cluster 3: Improving Students': [],
        'Cluster 4: At-Risk Students': []
    }

    cluster_names = [
        'Cluster 1: High Performers',
        'Cluster 2: High Academic / Low Participation',
        'Cluster 3: Improving Students',
        'Cluster 4: At-Risk Students'
    ]

    for idx, label in enumerate(labels):
        c_name = cluster_names[label % 4]
        clusters[c_name].append(student_map[idx])

    return clusters
