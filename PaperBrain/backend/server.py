import os
import json
from typing import Any, Dict
import glob

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

from controller.main_controller import PipelineController, run_pipeline_after_uploads


app = Flask(__name__)
CORS(app)


UPLOAD_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "uploads"))
os.makedirs(UPLOAD_ROOT, exist_ok=True)


def _save_file(field_name: str) -> str:
    file = request.files.get(field_name)
    if not file:
        return ""
    dest = os.path.join(UPLOAD_ROOT, file.filename)
    file.save(dest)
    return dest


@app.route("/api/health", methods=["GET"]) 
def health() -> Any:
    return jsonify({"status": "ok"})


@app.route("/api/upload", methods=["POST"]) 
def upload() -> Any:
    """
    Accepts multipart/form-data with fields:
    - answer_key[]: multiple files (answer keys/templates)
    - answer_sheet: file
    - related_docs[]: multiple files
    """
    # Handle multiple answer keys
    answer_key_files = request.files.getlist("answer_key[]") or request.files.getlist("answer_key")
    answer_key_paths = []
    for f in answer_key_files:
        dest = os.path.join(UPLOAD_ROOT, f.filename)
        f.save(dest)
        answer_key_paths.append(dest)
    
    answer_sheet_path = _save_file("answer_sheet")

    # related_docs can be multiple
    related_docs_files = request.files.getlist("related_docs") or request.files.getlist("related_docs[]")
    related_doc_paths = []
    for f in related_docs_files:
        dest = os.path.join(UPLOAD_ROOT, f.filename)
        f.save(dest)
        related_doc_paths.append(dest)

    if not answer_key_paths or not answer_sheet_path:
        return jsonify({"error": "at least one answer_key and answer_sheet are required"}), 400

    controller = PipelineController()
    saved = controller.save_uploads(answer_key_paths, answer_sheet_path, related_doc_paths)
    return jsonify({"saved": saved})


@app.route("/api/run", methods=["POST"]) 
def run_pipeline() -> Any:
    data: Dict[str, Any] = request.get_json(silent=True) or {}
    # optional: accept paths if already uploaded via other means
    answer_keys = data.get("answer_key_paths", [])
    answer_sheet = data.get("answer_sheet_path")
    related = data.get("related_docs_paths", [])

    if answer_keys and answer_sheet:
        results = run_pipeline_after_uploads(answer_keys, answer_sheet, related)
        return jsonify(results)

    # Otherwise run pipeline on already saved files in agents dirs
    controller = PipelineController()
    results = controller.run_pipeline()
    return jsonify({"saved": {}, "results": results})


@app.route("/api/results/current-student", methods=["GET"]) 
def current_student() -> Any:
    controller = PipelineController()
    path = controller.evaluator_temp_student
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return jsonify(data)
        except Exception:
            return jsonify({"error": "failed to read current_student.json"}), 500
    return jsonify({"error": "current_student.json not found"}), 404


@app.route("/api/outputs/preprocessor", methods=["GET"])
def get_preprocessor_outputs() -> Any:
    """Get list of aligned output images from preprocessor"""
    controller = PipelineController()
    outputs_dir = controller.preprocessor_outputs_dir
    images = []
    if os.path.isdir(outputs_dir):
        image_files = glob.glob(os.path.join(outputs_dir, "*.jpg")) + \
                     glob.glob(os.path.join(outputs_dir, "*.png"))
        images = [os.path.basename(f) for f in image_files]
    return jsonify({"images": images})


@app.route("/api/outputs/preprocessor/<filename>")
def serve_preprocessor_image(filename: str):
    """Serve aligned output images"""
    controller = PipelineController()
    return send_from_directory(controller.preprocessor_outputs_dir, filename)


@app.route("/api/outputs/text-recognition", methods=["GET"])
def get_text_recognition_outputs() -> Any:
    """Get list of debug crop images from text recognition"""
    controller = PipelineController()
    debug_dir = os.path.join(controller.text_recognition_dir, "debug_crops")
    images = []
    if os.path.isdir(debug_dir):
        image_files = glob.glob(os.path.join(debug_dir, "*.png")) + \
                     glob.glob(os.path.join(debug_dir, "*.jpg"))
        images = sorted([os.path.basename(f) for f in image_files])
    return jsonify({"images": images})


@app.route("/api/outputs/text-recognition/<filename>")
def serve_text_recognition_image(filename: str):
    """Serve debug crop images"""
    controller = PipelineController()
    debug_dir = os.path.join(controller.text_recognition_dir, "debug_crops")
    return send_from_directory(debug_dir, filename)


@app.route("/api/outputs/visualizations", methods=["GET"])
def get_visualizations() -> Any:
    """Get list of visualization images"""
    controller = PipelineController()
    viz_dir = os.path.join(controller.evaluator_dir, "results", "visualizations")
    images = []
    if os.path.isdir(viz_dir):
        image_files = glob.glob(os.path.join(viz_dir, "*.png"))
        images = sorted([os.path.basename(f) for f in image_files])
    return jsonify({"images": images})


@app.route("/api/outputs/visualizations/<filename>")
def serve_visualization(filename: str):
    """Serve visualization images"""
    controller = PipelineController()
    viz_dir = os.path.join(controller.evaluator_dir, "results", "visualizations")
    return send_from_directory(viz_dir, filename)


@app.route("/api/outputs/list", methods=["GET"])
def list_all_outputs() -> Any:
    """Get all available outputs from all stages"""
    controller = PipelineController()
    
    # Preprocessor outputs
    preprocessor_images = []
    if os.path.isdir(controller.preprocessor_outputs_dir):
        image_files = glob.glob(os.path.join(controller.preprocessor_outputs_dir, "*.jpg")) + \
                     glob.glob(os.path.join(controller.preprocessor_outputs_dir, "*.png"))
        preprocessor_images = [os.path.basename(f) for f in image_files]
    
    # Text recognition debug crops
    debug_dir = os.path.join(controller.text_recognition_dir, "debug_crops")
    debug_images = []
    if os.path.isdir(debug_dir):
        image_files = glob.glob(os.path.join(debug_dir, "*.png")) + \
                     glob.glob(os.path.join(debug_dir, "*.jpg"))
        debug_images = sorted([os.path.basename(f) for f in image_files])
    
    # Evaluator visualizations
    viz_dir = os.path.join(controller.evaluator_dir, "results", "visualizations")
    visualization_images = []
    if os.path.isdir(viz_dir):
        image_files = glob.glob(os.path.join(viz_dir, "*.png"))
        visualization_images = sorted([os.path.basename(f) for f in image_files])
    
    # Evaluation results
    results_json = os.path.join(controller.evaluator_dir, "results", "evaluation_results.json")
    results_exists = os.path.isfile(results_json)
    
    # Current student file
    current_student_exists = os.path.isfile(controller.evaluator_temp_student)
    
    return jsonify({
        "preprocessor": {
            "images": preprocessor_images,
            "count": len(preprocessor_images)
        },
        "text_recognition": {
            "debug_crops": debug_images,
            "count": len(debug_images)
        },
        "evaluator": {
            "visualizations": visualization_images,
            "count": len(visualization_images),
            "results_file": results_exists,
            "current_student_file": current_student_exists
        }
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)


