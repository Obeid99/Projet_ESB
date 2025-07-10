# Liste des matières ESB
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
    On neutralise les accents, espaces et la casse.
    """
    if not subject:
        return False
    normalized = subject.strip().title()
    return normalized in VALID_SUBJECTS
