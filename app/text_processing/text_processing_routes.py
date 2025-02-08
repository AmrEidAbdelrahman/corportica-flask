from flask import Blueprint, request, jsonify
from nltk.tokenize import word_tokenize

text_processing_bp = Blueprint('text_processing_bp', __name__)

text_data = [
    "The quick brown fox jumps over the lazy dog",
    "A stitch in time saves nine",
    "An apple a day keeps the doctor away",
    "Birds of a feather flock together",
    "A picture is worth a thousand words",
    "Don't count your chickens before they hatch",
    "The early bird catches the worm",
    "The pen is mightier than the sword",
    "Actions speak louderthan words",
]

# Text Search Endpoint
@text_processing_bp.route('/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query', '')
    results = [text for text in text_data if query.lower() in text.lower()]
    return jsonify({"results": results})

# Text Categorization Endpoint
@text_processing_bp.route('/categorize', methods=['POST'])
def categorize():
    data = request.json
    text = data.get('text', '')
    categories = data.get('categories', [])
    if not categories:
        return jsonify({"error": "No categories provided"}), 400

    # Simple categorization based on keyword matching
    category_scores = {category: 0 for category in categories}
    for word in word_tokenize(text):
        print(word)
        for category in categories:
            if word.lower() in category.lower():
                category_scores[category] += 1
    print(category_scores)
    return jsonify(category_scores)
