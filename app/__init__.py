import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_cors import CORS
import nltk

# Load environment variables from .env
load_dotenv()

db = SQLAlchemy()

def create_app():

    # Download NLTK data if not already downloaded
    def download_nltk_resources():
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')

        try:
            nltk.data.find('corpora/punkt_tab')
        except LookupError:
            nltk.download('punkt_tab')

    # Call the function to download NLTK resources
    download_nltk_resources()
    app = Flask(__name__, static_folder='static')
    CORS(app)  # Enable CORS for all routes

    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT")
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    # Read PostgreSQL credentials from environment variables
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    print(app.config["SQLALCHEMY_DATABASE_URI"])
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    migrate = Migrate(app, db)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    from app.datasets.dataset_routes import bp as dataset_routes_bp
    app.register_blueprint(dataset_routes_bp, url_prefix="/api/dataset")
    from app.image_processing.image_routes import image_bp
    app.register_blueprint(image_bp, url_prefix="/api/images")
    from app.text_processing.text_analysis_routes import text_analysis_bp
    app.register_blueprint(text_analysis_bp, url_prefix="/api/text_analysis")
    from app.text_processing.text_processing_routes import text_processing_bp
    app.register_blueprint(text_processing_bp, url_prefix="/api/text_processing")

    return app
