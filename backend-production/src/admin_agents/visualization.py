import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import uuid
from datetime import datetime, timedelta
import unicodedata
import re

def normalize_subject(text):
    """Normalise le nom d’une matière pour comparaison (minuscule, accents retirés, espaces enlevés)."""
    if not text or not isinstance(text, str):
        return ""
    text = text.lower()
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = ' '.join(text.split())
    return text.strip()

def extract_subjects_list(subjects, valid_subjects):
    """Prend un string/list de matières (séparés par virgule/et/and) et retourne la liste normalisée présente dans valid_subjects."""
    if subjects is None:
        return list(valid_subjects)  # Toutes les matières
    if isinstance(subjects, str):
        subjects = [s.strip() for s in re.split(r',|\bet\b|\band\b', subjects) if s.strip()]
    elif not isinstance(subjects, list):
        subjects = []

    normalized_valid = {normalize_subject(s): s for s in valid_subjects}
    filtered = []
    for s in subjects:
        norm_s = normalize_subject(s)
        if norm_s in normalized_valid:
            filtered.append(normalized_valid[norm_s])
        else:
            for valid_norm, valid_label in normalized_valid.items():
                if norm_s in valid_norm or valid_norm in norm_s:
                    if valid_label not in filtered:
                        filtered.append(valid_label)
    return filtered if filtered else list(valid_subjects)

def generate_all_feedback_charts_from_mongo(
    mongo_db,
    subjects=None,
    date="today",
    collection_name='history_student',
    valid_subjects=None,
    only_sentiment=None
):
    if valid_subjects is None:
        from .subject_validator import VALID_SUBJECTS
        valid_subjects = VALID_SUBJECTS

    chosen_subjects = extract_subjects_list(subjects, valid_subjects)

    # Date parsing
    if date == "today":
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=1)
    elif date == "yesterday":
        start_date = (datetime.now() - timedelta(days=1)).date()
        end_date = start_date + timedelta(days=1)
    elif date == "this_week":
        start_date = datetime.now().date() - timedelta(days=datetime.now().weekday())
        end_date = start_date + timedelta(days=7)
    elif date == "this_month":
        start_date = datetime.now().replace(day=1).date()
        end_date = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
    else:
        try:
            start_date = datetime.strptime(date, "%Y-%m-%d").date()
            end_date = start_date + timedelta(days=1)
        except Exception:
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=1)

    query = {
        "timestamp": {
            "$gte": datetime.combine(start_date, datetime.min.time()).timestamp(),
            "$lt": datetime.combine(end_date, datetime.min.time()).timestamp()
        }
    }
    all_feedbacks = list(mongo_db[collection_name].find(query))
    if not all_feedbacks:
        return {}, {"error": "Aucun feedback trouvé pour la période demandée."}

    # Sentiment filtering
    if only_sentiment is not None:
        all_feedbacks = [fb for fb in all_feedbacks if fb.get("sentiment") == only_sentiment]

    stats = {normalize_subject(s): {"label": s, "positive": 0, "negative": 0, "neutral": 0, "total": 0} for s in chosen_subjects}
    for fb in all_feedbacks:
        message = fb.get("message", "")
        sentiment = fb.get("sentiment", "neutral")
        for subj in chosen_subjects:
            subj_norm = normalize_subject(subj)
            if subj_norm in normalize_subject(message):
                stats[subj_norm]["total"] += 1
                stats[subj_norm][sentiment] += 1

    data_table = [v for v in stats.values() if v["total"] > 0]
    if not data_table:
        return {}, {"error": "Aucune matière officielle n'a reçu de feedback sur la période demandée."}

    data_table = sorted(data_table, key=lambda x: x["total"], reverse=True)
    labels = [x["label"] for x in data_table]
    counts_total = [x["total"] for x in data_table]
    counts_positive = [x["positive"] for x in data_table]
    counts_negative = [x["negative"] for x in data_table]
    counts_neutral = [x["neutral"] for x in data_table]

    static_dir = "static"
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    filenames = {}

    # Bar chart total
    fig, ax = plt.subplots()
    ax.bar(labels, counts_total, color='dodgerblue')
    ax.set_ylabel("Nombre de feedbacks")
    ax.set_title("Nombre de feedbacks par matière")
    plt.xticks(rotation=30, ha='right')
    filename = f"bar_total_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(static_dir, filename)
    plt.tight_layout()
    plt.savefig(filepath)
    filenames["bar_total"] = f"/static/{filename}"
    plt.close(fig)

    # Bar chart stacked
    fig, ax = plt.subplots()
    ax.bar(labels, counts_positive, label='Positifs', color='green')
    ax.bar(labels, counts_negative, bottom=counts_positive, label='Négatifs', color='red')
    ax.bar(labels, counts_neutral, bottom=[p + n for p, n in zip(counts_positive, counts_negative)], label='Neutres', color='gray')
    ax.set_ylabel("Nombre de feedbacks")
    ax.set_title("Feedbacks par matière et par sentiment")
    plt.xticks(rotation=30, ha='right')
    ax.legend()
    plt.tight_layout()
    filename = f"bar_stacked_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(static_dir, filename)
    plt.savefig(filepath)
    filenames["bar_stacked"] = f"/static/{filename}"
    plt.close(fig)

    # Pie chart
    fig, ax = plt.subplots()
    ax.pie(counts_total, labels=labels, autopct='%1.1f%%')
    ax.set_title("Répartition des feedbacks par matière")
    filename = f"pie_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(static_dir, filename)
    plt.tight_layout()
    plt.savefig(filepath)
    filenames["pie"] = f"/static/{filename}"
    plt.close(fig)

    # Interprétation comparative (ne sera jamais None)
    texte = "Comparaison des matières :<br>"
    max_pos_val = max((x["positive"] for x in data_table), default=0)
    max_neg_val = max((x["negative"] for x in data_table), default=0)
    max_neu_val = max((x["neutral"] for x in data_table), default=0)

    most_pos_label = ", ".join(x["label"] for x in data_table if x["positive"] == max_pos_val and max_pos_val > 0)
    most_neg_label = ", ".join(x["label"] for x in data_table if x["negative"] == max_neg_val and max_neg_val > 0)
    most_neu_label = ", ".join(x["label"] for x in data_table if x["neutral"] == max_neu_val and max_neu_val > 0)

    if max_pos_val > 0 and most_pos_label:
        texte += f"La matière la plus <b>positive</b> est <b>{most_pos_label}</b> ({max_pos_val} feedbacks positifs)<br>"
    else:
        texte += "Aucune matière n’a reçu de feedback <b>positif</b> sur la période.<br>"
    if max_neg_val > 0 and most_neg_label:
        texte += f"La matière la plus <b>négative</b> est <b>{most_neg_label}</b> ({max_neg_val} feedbacks négatifs)<br>"
    else:
        texte += "Aucune matière n’a reçu de feedback <b>négatif</b> sur la période.<br>"
    if max_neu_val > 0 and most_neu_label:
        texte += f"La matière la plus <b>neutre</b> est <b>{most_neu_label}</b> ({max_neu_val} feedbacks neutres)<br>"
    else:
        texte += "Aucune matière n’a reçu de feedback <b>neutre</b> sur la période.<br>"

    meta = {
        "most_positive": (most_pos_label, max_pos_val) if max_pos_val > 0 and most_pos_label else ("", 0),
        "most_negative": (most_neg_label, max_neg_val) if max_neg_val > 0 and most_neg_label else ("", 0),
        "most_neutral": (most_neu_label, max_neu_val) if max_neu_val > 0 and most_neu_label else ("", 0),
        "data_table": data_table,
        "interpretation": texte,
        "raw_feedbacks": all_feedbacks
    }
    return filenames, meta
