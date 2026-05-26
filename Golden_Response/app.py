from pymongo import MongoClient
from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import pipeline
import os
from pymongo import MongoClient
from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import pipeline
import re
import logging
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connect to MongoDB (use environment variable when available)
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(mongo_uri)
db = client.get_database('product_reviews')
reviews_collection = db.get_collection('reviews')

# Load a lightweight DistilBERT sentiment model (outputs POSITIVE/NEGATIVE)
aspect_sentiment_model = pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')

# Support a lightweight mock model for CI or environments without heavy model downloads.
if os.getenv('USE_MOCK_MODEL', '0') == '1':
    def _mock_pipeline(text, return_all_scores=False):
        """Very small deterministic heuristic used for CI/tests.

        Returns the same structure as `transformers.pipeline` so the rest
        of the app can use it unchanged.
        """
        lower = (text or '').lower()
        neg_words = ['not', 'no', 'bad', 'poor', 'drains', 'hate', 'disappoint']
        pos_words = ['good', 'great', 'excellent', 'amazing', 'love', 'awesome', 'best']

        if any(w in lower for w in neg_words):
            pos, neg = 0.1, 0.9
        elif any(w in lower for w in pos_words):
            pos, neg = 0.9, 0.1
        else:
            pos, neg = 0.55, 0.45

        if return_all_scores:
            return [[{'label': 'POSITIVE', 'score': pos}, {'label': 'NEGATIVE', 'score': neg}]]
        # single-call format: list of dicts
        return [{'label': 'POSITIVE' if pos >= neg else 'NEGATIVE', 'score': max(pos, neg)}]

    aspect_sentiment_model = _mock_pipeline

# Define aspects and their keywords
aspects = {
    'battery': ['battery', 'charge', 'charging', 'power', 'life'],
    'display': ['display', 'screen', 'resolution', 'brightness', 'clarity'],
    'camera': ['camera', 'photo', 'picture', 'image', 'video'],
    'build_quality': ['quality', 'build', 'material', 'durability', 'design'],
    'looks': ['looks', 'design', 'style', 'appearance', 'aesthetics']
}

# Pattern to split sentences
split_patterns = r'\band\b|\balso\b|\bHowever\b|\bhowever\b|\bbut\b|\byet\b|\balthough\b|\bthough\b|\bwhile\b|\bwhereas\b|\bsince\b|\bbecause\b|,|;|:|\band\b|\bor\b|\s.\s|\?\s|!\s'

def extract_aspects(review):
    """
    Extract clauses or phrases corresponding to each aspect based on the keywords.
    """
    extracted_aspects = {aspect: [] for aspect in aspects}

    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', review)

    for sentence in sentences:
        clauses = re.split(split_patterns, sentence, flags=re.IGNORECASE)
        for clause in clauses:
            for aspect, keywords in aspects.items():
                if any(keyword.lower() in clause.lower() for keyword in keywords):
                    extracted_aspects[aspect].append(clause.strip())

    return {aspect: ' '.join(extracted_aspects[aspect]) for aspect in extracted_aspects if extracted_aspects[aspect]}

def analyze_sentiment(text, neutral_margin=0.15):
    """
    Analyze sentiment using the loaded model.
    Returns one of: 'positive', 'negative', 'neutral'.

    The function uses the probability scores for POSITIVE and NEGATIVE
    and classifies as neutral when the absolute difference is below
    the `neutral_margin` threshold.
    """
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)

    # Aggregate probabilities across sentences
    pos_scores = []
    neg_scores = []

    for sentence in sentences:
        if not sentence or sentence.isspace():
            continue
        try:
            # request scores for both labels
            result = aspect_sentiment_model(sentence, return_all_scores=True)[0]
        except Exception:
            # fallback to single-label call
            single = aspect_sentiment_model(sentence)[0]
            label = single.get('label', '').upper()
            score = float(single.get('score', 0.0))
            if label == 'POSITIVE':
                pos_scores.append(score)
            elif label == 'NEGATIVE':
                neg_scores.append(score)
            continue

        # result is a list of label/score dicts
        pos = next((r['score'] for r in result if r['label'].upper() == 'POSITIVE'), None)
        neg = next((r['score'] for r in result if r['label'].upper() == 'NEGATIVE'), None)

        if pos is not None:
            pos_scores.append(pos)
        if neg is not None:
            neg_scores.append(neg)

    # compute mean scores (safe defaults if empty)
    avg_pos = sum(pos_scores) / len(pos_scores) if pos_scores else 0.0
    avg_neg = sum(neg_scores) / len(neg_scores) if neg_scores else 0.0

    if abs(avg_pos - avg_neg) < neutral_margin:
        return 'neutral'
    return 'positive' if avg_pos > avg_neg else 'negative'

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        review = data.get('review', '')

        if not review:
            return jsonify({'status': 'error', 'message': 'Review is missing.'}), 400

        aspects_in_review = extract_aspects(review)
        sentiment_analysis = {}

        for aspect, aspect_review in aspects_in_review.items():
            if aspect_review:
                sentiment_analysis[aspect] = {
                    'review': aspect_review,
                    'sentiment': analyze_sentiment(aspect_review)
                }

        # Save review and analysis to MongoDB
        reviews_collection.insert_one({
            'review': review,
            'analysis': sentiment_analysis
        })

        logger.info(f"Sentiment analysis: {sentiment_analysis}")
        return jsonify(sentiment_analysis)

    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'status': 'error', 'message': 'An error occurred on the server.'}), 500

if __name__ == '__main__':
    app.run(debug=True)