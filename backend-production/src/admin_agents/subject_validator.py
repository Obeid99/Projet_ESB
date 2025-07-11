# Liste des matières ESB (exemple, adapte à ta réalité)
VALID_SUBJECTS = {
    "Machine Learning",
    "Marketing",
    "Finance",
    "Accounting",
    "Business Analytics",
    "Digital Marketing",
    "Statistics",
    "Business Computing"
}

def is_valid_subject(subject):
    """
    Vérifie si le sujet demandé est bien dans le syllabus officiel.
    """
    if not subject:
        return False
    return subject.strip().title() in VALID_SUBJECTS
