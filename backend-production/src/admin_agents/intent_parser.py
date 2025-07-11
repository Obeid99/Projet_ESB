import re
import datetime

def clean_message(msg):
    msg = msg.strip().lower()
    msg = msg.replace("’", "'")
    msg = re.sub(r'[\"“”\'’]', '', msg)
    msg = re.sub(r'[^\w\s]', ' ', msg)
    return msg

def extract_subject(msg):
    """
    Extraction robuste du nom de la matière dans la phrase.
    """
    # 1. "pour la matière finance", "pour la matière de finance", etc.
    m = re.search(r"(?:pour|de|en|sur)\s+(?:la|le|les|l')?\s*(?:mati[eè]re|subject)?\s*([a-z0-9\s\-]+)", msg)
    if m:
        subject = m.group(1)
        # Retire tous les mots de période/graphique de la fin (graphiques, hier, aujourd'hui, etc.)
        subject = re.sub(r"\b(hier|aujourd.*|semaine|mois|today|yesterday|this week|this month|chart|graphiques?|camembert|barres?|diagramme|graphique)\b.*$", "", subject).strip()
        return subject

    # 2. "matière finance", "matière ia", etc.
    m2 = re.search(r"mati[eè]re\s+([a-z0-9\s\-]+)", msg)
    if m2:
        subject = m2.group(1)
        subject = re.sub(r"\b(hier|aujourd.*|semaine|mois|today|yesterday|this week|this month|chart|graphiques?|camembert|barres?|diagramme|graphique)\b.*$", "", subject).strip()
        return subject

    # 3. Match direct sur la liste officielle des matières (robuste, inclusif)
    valid_subjects = [
        "machine learning", "marketing", "finance", "accounting", "business analytics",
        "digital marketing", "statistics", "business computing", "comptabilité",
        "compta", "ia", "informatique", "mathematiques", "mathématiques", "math",
        "business", "anglais"
    ]
    msg_ascii = msg.replace("’", "'")
    for matiere in valid_subjects:
        if matiere in msg_ascii:
            return matiere

    return None

def extract_date_from_msg(msg):
    """
    Extrait la date demandée dans le message (français ou anglais)
    Retourne une string 'YYYY-MM-DD' ou une clé (today/yesterday/this_week/this_month)
    """
    msg = msg.lower()
    # 1. Formats DD/MM/YYYY ou YYYY-MM-DD
    date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', msg)
    if date_match:
        # DD/MM/YYYY
        day, month, year = map(int, date_match.groups())
        try:
            dt = datetime.date(year, month, day)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass
    date_match2 = re.search(r'(\d{4})-(\d{2})-(\d{2})', msg)
    if date_match2:
        # YYYY-MM-DD
        year, month, day = map(int, date_match2.groups())
        try:
            dt = datetime.date(year, month, day)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # 2. Jours de la semaine (fr/en)
    jours_fr = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    jours_en = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    today = datetime.date.today()
    for idx, jour in enumerate(jours_fr):
        if jour in msg:
            diff = (today.weekday() - idx) % 7
            target = today - datetime.timedelta(days=diff)
            return target.strftime("%Y-%m-%d")
    for idx, jour in enumerate(jours_en):
        if jour in msg:
            diff = (today.weekday() - idx) % 7
            target = today - datetime.timedelta(days=diff)
            return target.strftime("%Y-%m-%d")

    # 3. Mots-clés classiques
    if "hier" in msg or "yesterday" in msg:
        return "yesterday"
    if "aujourd" in msg or "today" in msg:
        return "today"
    if "semaine" in msg or "week" in msg:
        return "this_week"
    if "mois" in msg or "month" in msg:
        return "this_month"

    return None

def parse_intent(message):
    msg = clean_message(message)

    # --- DEMANDE DE GRAPHIQUES --- (doit être tout en haut pour priorité)
    CHART_PATTERNS = [
        r"\b(graphique|graph|camembert|barres?|chart|diagramme|donut|pie)[s]?\b",
    ]
    for p in CHART_PATTERNS:
        if re.search(p, msg):
            entities = {}
            subject = extract_subject(msg)
            if subject:
                entities["subject"] = subject
            date_entity = extract_date_from_msg(msg)
            if date_entity:
                entities["date"] = date_entity
            return "get_feedback_chart", entities

    # ---------- NOUVEAU : feedback POSITIF uniquement -------------
    POSITIVE_PATTERNS = [
        r"\bpositive feedback(s)?\b",
        r"\bfeedback(s)? positif(s)?\b",
        r"\bfeedbacks?\s+positif\b",
        r"\bfeedback(s)? only positive\b",
        r"\bseulement\s+feedbacks?\s+positif(s)?\b",
    ]
    for p in POSITIVE_PATTERNS:
        if re.search(p, msg):
            entities = {}
            date_entity = extract_date_from_msg(msg)
            if date_entity:
                entities["date"] = date_entity
            subject = extract_subject(msg)
            if subject:
                entities["subject"] = subject
            return "get_positive_feedbacks", entities

    NEGATIVE_PATTERNS = [
        r"\bnegative feedback(s)?\b",
        r"\bfeedback(s)? n[ée]gatif(s)?\b",
        r"\bfeedbacks?\s+negative\b",
        r"\bseulement\s+feedbacks?\s+n[ée]gatif(s)?\b",
    ]
    for p in NEGATIVE_PATTERNS:
        if re.search(p, msg):
            entities = {}
            date_entity = extract_date_from_msg(msg)
            if date_entity:
                entities["date"] = date_entity
            subject = extract_subject(msg)
            if subject:
                entities["subject"] = subject
            return "get_negative_feedbacks", entities

    NEUTRAL_PATTERNS = [
        r"\bneutral feedback(s)?\b",
        r"\bfeedback(s)? neutre(s)?\b",
        r"\bfeedbacks?\s+neutre\b",
        r"\bseulement\s+feedbacks?\s+neutre(s)?\b",
    ]
    for p in NEUTRAL_PATTERNS:
        if re.search(p, msg):
            entities = {}
            date_entity = extract_date_from_msg(msg)
            if date_entity:
                entities["date"] = date_entity
            subject = extract_subject(msg)
            if subject:
                entities["subject"] = subject
            return "get_neutral_feedbacks", entities
        
    # ----------- NOUVEAU : total feedbacks (tous sentiments) -----------
    TOTAL_PATTERNS = [
        r"\btotal feedback(s)?\b",
        r"\bfeedbacks? today\b",
        r"\bfeedbacks?\s+d['’]aujourd'hui\b",
        r"\bfeedbacks?\s+aujourd'hui\b",
        r"\bnombre de feedbacks?\b",
        r"\bnombre total de feedbacks?\b",
        r"\bfeedback(s)?\s+total\b",
        r"\bfeedback(s)?\s+en tout\b",
        r"\bfeedbacks?\s+(ce|cette|la)\s+(semaine|mois|jour|today|week|month)\b"
    ]
    for p in TOTAL_PATTERNS:
        if re.search(p, msg):
            entities = {}
            date_entity = extract_date_from_msg(msg)
            if date_entity:
                entities["date"] = date_entity
            subject = extract_subject(msg)
            if subject:
                entities["subject"] = subject
            return "get_feedback_stats", entities

    # ---------- TOP N SUBJECTS ----------
    TOP_PATTERNS = [
        r"(quelle|quelles|top)\s*(\d*)\s*(mati[eè]res?|subjects?)\s*(ont|a)?\s*re(çu|cevoir|çu)?\s*le plus de feedbacks?\s*(hier|aujourd'hui|cette semaine|ce mois|this week|this month|today|yesterday)?",
        r"(top)\s*(\d*)\s*(mati[eè]res?|subjects?)",
        r"graphique\s*(\d*)\s*(mati[eè]res?|subjects?)\s*les plus feedbacks?",
        r"donne-moi\s*(le|la|les)?\s*top\s*(\d*)\s*(mati[eè]res?|subjects?)",
        r"quelles?\s*(mati[eè]res?|subjects?)\s*(ont|a)?\s*re(çu|cevoir|çu)?\s*le plus de feedbacks?"
    ]
    for p in TOP_PATTERNS:
        match = re.search(p, msg)
        if match:
            entities = {}
            # Capture N si précisé, sinon 1
            n = None
            # Essaye de trouver un nombre dans le pattern ou dans la question
            if match.group(2) and match.group(2).isdigit():
                n = int(match.group(2))
            else:
                find_n = re.search(r"\b(\d+)\b", msg)
                if find_n:
                    n = int(find_n.group(1))
                else:
                    n = 1
            entities["top_n"] = n

            # Cherche date
            date_entity = extract_date_from_msg(msg)
            if date_entity:
                entities["date"] = date_entity
            else:
                entities["date"] = "today"
            return "get_top_subjects", entities

    # ----------- LISTE BRUTE DE FEEDBACKS POUR UNE MATIÈRE -------------
    FEEDBACKS_SUBJECT_PATTERNS = [
        r"\bfeedbacks?\s+(de|en|pour|sur)\s+(la|le|l'|les)?\s*([a-z0-9\s\-]+)",
        r"(affiche|montre|donne).*(feedbacks?)\s+(de|en|pour|sur)\s+([a-z0-9\s\-]+)"
    ]
    for p in FEEDBACKS_SUBJECT_PATTERNS:
        match = re.search(p, msg)
        if match:
            entities = {}
            subject = None
            # Selon le pattern matché, le groupe change
            if match.lastindex == 3:
                subject = match.group(3)
            elif match.lastindex == 5:
                subject = match.group(5)
            else:
                continue
            if subject:
                # On retire 'matiere', 'matière', 'subject' en début si présent
                subject = re.sub(r"^(mati[eè]re|subject)\s+", "", subject.strip())
                entities["subject"] = subject.strip()
            date_entity = extract_date_from_msg(msg)
            if date_entity:
                entities["date"] = date_entity
            return "get_feedback_stats", entities

    # 8. Fallback
    return "unknown", {}
