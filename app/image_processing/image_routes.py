from datetime import datetime
import os
from flask import Blueprint, flash, redirect, render_template, request, jsonify
from werkzeug.utils import secure_filename
from app.models import ImageFile
from app import db
import cv2
import numpy as np
import matplotlib.pyplot as plt
from flask import send_file
from skimage.segmentation import slic, mark_boundaries

from app.models.user_model import User
from PIL import Image


image_bp = Blueprint("images_routes", __name__)

UPLOAD_FOLDER = "uploads/images"
MASK_FOLDER = "uploads/images/segments"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@image_bp.route("/upload", methods=["POST"])
def upload_images():
    """Handles single and batch image uploads."""
    if "file" not in request.files:
        return jsonify({"error": "No files provided"}), 400
    
    user_id = request.form["user_id"]
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    file = request.files.get("file")
    uploaded_files = []


    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file"}), 400
        
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Save to database
    image_entry = ImageFile(filename=filename, filepath=filepath, user_id=user.id)
    db.session.add(image_entry)
    uploaded_files.append(filename)
    
    db.session.commit()
    return jsonify({"message": "Files uploaded successfully", "files": uploaded_files}), 201


@image_bp.route("/histogram/<int:image_id>", methods=["GET"])
def generate_histogram(image_id):
    """Generate and return a color histogram with adjustable parameters."""

    # Retrieve image entry from database
    image_entry = ImageFile.query.get(image_id)
    if not image_entry:
        return jsonify({"error": "Image not found"}), 404

    image_path = image_entry.filepath
    image = cv2.imread(image_path)

    if image is None:
        return jsonify({"error": "Unable to read image"}), 500

    # Get query parameters
    bins = int(request.args.get("bins", 256))  # Default: 256
    channel = request.args.get("channel", "all")  # Default: "all"
    x = request.args.get("x", type=int)
    y = request.args.get("y", type=int)
    w = request.args.get("w", type=int)
    h = request.args.get("h", type=int)
    print(x, y, w, h)
    # Crop the image if region parameters are provided
    if x is not None and y is not None and w is not None and h is not None:
        image = image[y:y+h, x:x+w]

    # Define color channels
    color_map = {"b": 0, "g": 1, "r": 2}
    colors = {"b": "blue", "g": "green", "r": "red"}
    
    plt.figure()
    plt.title(f"Color Histogram for {image_entry.filename}")
    plt.xlabel("Bins")
    plt.ylabel("# of Pixels")

    if channel in color_map:
        # Process a single channel
        print("Processing single channel")
        hist = cv2.calcHist([image], [color_map[channel]], None, [bins], [0, 256])
        plt.plot(hist, color=colors[channel])
    else:
        # Process all channels
        for ch, idx in color_map.items():
            hist = cv2.calcHist([image], [idx], None, [bins], [0, 256])
            plt.plot(hist, color=colors[ch])

    # the uploads folder is outside the app folder
    file_path = os.path.join(UPLOAD_FOLDER, "histograms", f"{image_entry.id}_hist3.png")
    hist_path = os.path.join("app", UPLOAD_FOLDER, "histograms", f"{image_entry.id}_hist3.png")
    plt.savefig(hist_path)
    plt.close()

    return send_file(file_path, mimetype="image/png")


@image_bp.route("/segment/<int:image_id>", methods=["GET"])
def segment_image(image_id):
    # Retrieve image entry from database
    image_entry = ImageFile.query.get(image_id)
    if not image_entry:
        return jsonify({"error": "Image not found"}), 404

    image_path = image_entry.filepath
    image = cv2.imread(image_path)

    if image is None:
        return jsonify({"error": "Unable to read image"}), 500

    # Load image
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Apply SLIC segmentation (Superpixel segmentation)
    n_segments = int(request.args.get("n_segments", 100))
    segments = slic(image_rgb, n_segments=n_segments, compactness=10)

    # Generate segmentation mask
    segmented_image = mark_boundaries(image_rgb, segments)

    # Save mask image
    now = datetime.now()
    file_path = os.path.join(MASK_FOLDER, f"{image_entry.id}{datetime.timestamp(now)}.png")
    mask_path = os.path.join("app", MASK_FOLDER, f"{image_entry.id}{datetime.timestamp(now)}.png")
    plt.imsave(mask_path, segmented_image)
    plt.close()

    return send_file(file_path, mimetype="image/png")

    # return jsonify({"message": "Segmentation completed", "mask_path": mask_path})



UPLOAD_FOLDER = "app/static/uploads"
PROCESSED_FOLDER = "app/static/processed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@image_bp.route("/manipulate_image", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file selected", "error")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "" or not allowed_file(file.filename):
            flash("Invalid file type", "error")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Open the image
        img = Image.open(file_path)

        # Resize
        width = request.form.get("width")
        height = request.form.get("height")
        if width and height:
            img = img.resize((int(width), int(height)))

        # Crop
        x, y, w, h = request.form.get("x"), request.form.get("y"), request.form.get("w"), request.form.get("h")
        if x and y and w and h:
            img = img.crop((int(x), int(y), int(x) + int(w), int(y) + int(h)))

        # Format conversion
        format_type = request.form.get("format") or img.format
        output_filename = f"processed_{filename.split('.')[0]}.{format_type or 'png'}"
        output_path = os.path.join(PROCESSED_FOLDER, output_filename)
        img.save(output_path, format=format_type or "PNG")

        return render_template("image_manipulation.html", uploaded_file=filename, processed_file=output_filename)

    return render_template("image_manipulation.html")
