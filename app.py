from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
import spacy
import random
from collections import Counter
from PyPDF2 import PdfReader

# Initialize Flask app
app = Flask(__name__)
Bootstrap(app)

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")


def process_pdf(file):
    """Extract text from a PDF file."""
    text = ""
    reader = PdfReader(file)
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text


def generate_mcqs(text, num_questions=5):
    """Generate multiple-choice questions from input text."""
    if not text:
        return []

    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]
    num_questions = min(num_questions, len(sentences))
    selected_sentences = random.sample(sentences, num_questions)

    mcqs = []
    for sentence in selected_sentences:
        sent_doc = nlp(sentence)
        nouns = [token.text for token in sent_doc if token.pos_ == "NOUN"]

        if len(nouns) < 2:
            continue

        noun_counts = Counter(nouns)
        subject = noun_counts.most_common(1)[0][0]

        question_stem = sentence.replace(subject, "______")
        answer_choices = [subject]
        distractors = list(set(nouns) - {subject})

        while len(distractors) < 3:
            distractors.append("[Distractor]")  # filler if not enough distractors

        answer_choices += random.sample(distractors, 3)
        random.shuffle(answer_choices)

        correct_letter = chr(65 + answer_choices.index(subject))
        mcqs.append((question_stem, answer_choices, correct_letter))

    return mcqs


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text = ""

        uploaded_files = request.files.getlist('files[]')
        for file in uploaded_files:
            if file.filename.endswith('.pdf'):
                text += process_pdf(file)
            elif file.filename.endswith('.txt'):
                text += file.read().decode('utf-8')

        # Fallback to manual input if no files
        if not text:
            text = request.form.get('text', '')

        num_questions = int(request.form.get('num_questions', 5))
        mcqs = generate_mcqs(text, num_questions)
        mcqs_with_index = [(i + 1, mcq) for i, mcq in enumerate(mcqs)]

        return render_template('mcqs.html', mcqs=mcqs_with_index)

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
