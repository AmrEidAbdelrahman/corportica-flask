from flask import request, jsonify
from transformers import pipeline
from flask import Blueprint


# Initialize Hugging Face pipelines
summarizer = pipeline("summarization")
sentiment_analyzer = pipeline("sentiment-analysis")

text_analysis_bp = Blueprint("text_analysis_routes", __name__)


# Text Summarization Endpoint
@text_analysis_bp.route('/summarize', methods=['POST'])
def summarize():
    data = request.json
    text = data.get('text', '')
    max_length = data.get('max_length', 130)
    min_length = data.get('min_length', 30)
    summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
    return jsonify({"summary": summary[0]['summary_text']})

# Sentiment Analysis Endpoint
@text_analysis_bp.route('/sentiment', methods=['POST'])
def sentiment():
    data = request.json
    text = data.get('text', '')
    result = sentiment_analyzer(text)
    return jsonify({"sentiment": result[0]['label'], "score": result[0]['score']})
