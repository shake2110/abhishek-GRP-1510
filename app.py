from pymongo import MongoClient
from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import pipeline
import re
import logging

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['product_reviews']
reviews_collection = db['reviews']

# Load sentiment analysis model
aspect_sentiment_model = pipeline('text-classification', model='nlptown/bert-base-multilingual-uncased-sentiment')

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

def analyze_sentiment(text):
    """
    Analyze sentiment using a pre-trained machine learning model.
    Returns 'positive' or 'negative' based on the majority of sentences.
    """
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    sentiments = []

    for sentence in sentences:
        result = aspect_sentiment_model(sentence)[0]
        sentiments.append(result['label'])

    return 'positive' if sentiments.count('POSITIVE') >= sentiments.count('NEGATIVE') else 'negative'

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