import unicodedata


# Liste des matières ESB
VALID_SUBJECTS = {
    "machine learning",
    "marketing",
    "finance",
    "accounting",
    "business analytics",
    "digital marketing",
    "statistics",
    "business computing",
    "comptabilité",
    "compta",
    "ia",
    "informatique",
    "mathematiques",
    "mathématiques",
    "math",
    "business",
    "anglais",
}

def strip_accents(text):
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

def normalize_subject(subject):
    if not subject or not isinstance(subject, str):
        return ""
    s = subject.strip().lower()
    s = strip_accents(s)
    s = ' '.join(s.split())  # supprime espaces multiples
    return s

def is_valid_subject(subject):
    """
    Vérifie si le sujet demandé est bien dans le syllabus officiel.
    On neutralise les accents, espaces et la casse.
    """
    norm = normalize_subject(subject)
    for valid in VALID_SUBJECTS:
        if norm == normalize_subject(valid):
            return True
    return False
