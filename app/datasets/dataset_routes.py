import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from flask import request, jsonify, send_file
from werkzeug.utils import secure_filename
from app.models import DatasetFile, User
from app import db
from flask import Blueprint

bp = Blueprint("dataset_routes", __name__)


UPLOAD_FOLDER = "uploads/datasets"
ALLOWED_EXTENSIONS = {"csv", "xlsx"}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Helper function to check file extension
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# 1. Upload File Endpoint
@bp.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files or "user_id" not in request.form:
        return jsonify({"error": "Missing file or user_id"}), 400
    
    file = request.files["file"]
    user_id = request.form["user_id"]
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    dataset = DatasetFile(filename=filename, filepath=file_path, user_id=user.id)
    db.session.add(dataset)
    db.session.commit()
    
    return jsonify({"message": "File uploaded successfully", "file_id": dataset.id}), 201


# 2. Retrieve Data Endpoint
@bp.route("/datasets", methods=["GET"])
def get_datasets():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    datasets = DatasetFile.query.filter_by(user_id=user_id).all()
    return jsonify([{ "id": d.id, "filename": d.filename, "filepath": d.filepath, "user_id": d.user_id } for d in datasets])

@bp.route("/datasets/<int:dataset_id>", methods=["GET"])
def get_dataset(dataset_id):
    dataset = DatasetFile.query.get(dataset_id)
    if not dataset:
        return jsonify({"error": "Dataset not found"}), 404
    data = pd.read_csv(dataset.filepath)
    
    return jsonify({ "id": dataset.id, "filename": dataset.filename, "filepath": dataset.filepath, "user_id": dataset.user_id, "data": data.to_dict(orient="records") })

# delete dataset
@bp.route("/datasets/<int:dataset_id>", methods=["DELETE"])
def delete_dataset(dataset_id):
    dataset = DatasetFile.query.get(dataset_id)
    if not dataset:
        return jsonify({"error": "Dataset not found"}), 404
    db.session.delete(dataset)
    db.session.commit()
    return jsonify({"message": "Dataset deleted successfully"}), 200

@bp.route("/datasets/<int:dataset_id>/statistics", methods=["GET"])
def get_statistics(dataset_id):
    dataset = DatasetFile.query.get(dataset_id)
    if not dataset:
        return jsonify({"error": "Dataset not found"}), 404

    if dataset.filename.endswith(".csv"):
        df = pd.read_csv(dataset.filepath)
    elif dataset.filename.endswith(".xlsx"):
        df = pd.read_excel(dataset.filepath)
    else:
        return jsonify({"error": "Invalid file format"}), 400

    stats = df.describe().to_dict()
    return jsonify(stats)
