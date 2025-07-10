import matplotlib.pyplot as plt
import os
import uuid
from datetime import datetime, timedelta

def get_feedbacks_from_mongo(mongo_db, collection_name, subject=None, start_date=None, end_date=None):
    """
    Récupère les feedbacks filtrés depuis Mongo.
    """
    query = {}
    if subject:
        query['subject'] = subject
    if start_date and end_date:
        # suppose que timestamp = float (unix time)
        query['timestamp'] = {
            "$gte": datetime.combine(start_date, datetime.min.time()).timestamp(),
            "$lt": datetime.combine(end_date, datetime.min.time()).timestamp()
        }
    return list(mongo_db[collection_name].find(query))

def generate_feedback_chart_from_mongo(mongo_db, subject=None, date="today"):
    """
    Génère un graphique à partir des feedbacks mongo pour un sujet/date.
    """
    # -- Calcul période
    if date == "today":
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=1)
    elif date == "this_week":
        start_date = datetime.now().date() - timedelta(days=datetime.now().weekday())
        end_date = start_date + timedelta(days=7)
    elif date == "this_month":
        start_date = datetime.now().replace(day=1).date()
        end_date = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
    else:
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=1)

    # -- Récupère feedbacks
    feedbacks = get_feedbacks_from_mongo(mongo_db, 'history_student', subject, start_date, end_date)

    counts = {"positive": 0, "negative": 0, "neutral": 0}
    for fb in feedbacks:
        sentiment = fb.get("sentiment", "neutral")
        counts[sentiment] = counts.get(sentiment, 0) + 1

    # -- Génére le graphique
    labels = ['Positifs', 'Négatifs', 'Neutres']
    data = [counts.get('positive', 0), counts.get('negative', 0), counts.get('neutral', 0)]
    fig, ax = plt.subplots()
    ax.pie(data, labels=labels, autopct='%1.1f%%')
    ax.set_title('Répartition des feedbacks')
    static_dir = "static"
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    filename = f"feedback_chart_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join('static', filename)
    plt.savefig(filepath)
    plt.close(fig)
    return f"/static/{filename}", counts
