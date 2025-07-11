import matplotlib.pyplot as plt
import os
import uuid

def generate_feedback_chart(counts):
    """
    Génère un camembert des feedbacks, sauvegarde l'image, renvoie l'URL/chemin.
    """
    labels = ['Positifs', 'Négatifs', 'Neutres']
    data = [counts.get('positive', 0), counts.get('negative', 0), counts.get('neutral', 0)]
    fig, ax = plt.subplots()
    ax.pie(data, labels=labels, autopct='%1.1f%%')
    ax.set_title('Répartition des feedbacks')

    filename = f"feedback_chart_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join('static', filename)
    plt.savefig(filepath)
    plt.close(fig)
    # À afficher : /static/filename dans ton front (Flask sert /static)
    return f"/static/{filename}"
