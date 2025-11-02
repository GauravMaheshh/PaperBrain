import os
import json
from typing import Any, Dict
import glob
import traceback

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

# Import controller
try:
    from controller.main_controller import PipelineController, run_pipeline_after_uploads
    print("✅ Controller imported successfully")
except ImportError as e:
    print(f"❌ Failed to import controller: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {os.sys.path}")
    raise


app = Flask(__name__)
CORS(app)


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "paperbrain"))
UPLOAD_ROOT = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_ROOT, exist_ok=True)

print(f"📁 Base directory: {BASE_DIR}")
print(f"📁 Frontend directory: {FRONTEND_DIR}")
print(f"📁 Upload directory: {UPLOAD_ROOT}")


def _save_file(field_name: str) -> str:
    """Save uploaded file and return path"""
    file = request.files.get(field_name)
    if not file or not file.filename:
        return ""
    dest = os.path.join(UPLOAD_ROOT, file.filename)
    file.save(dest)
    print(f"  Saved {field_name}: {dest}")
    return dest


@app.route("/", methods=["GET"])
def index():
    """Serve index page"""
    return """<html><body style='font-family: sans-serif; padding: 40px; background:#0b0f19; color:#e5e7eb'>
        <h1>🧠 PaperBrain API Server</h1>
        <p style='color: #10b981; font-size: 18px;'>✅ Server is running successfully!</p>
        <h2>Available Endpoints:</h2>
        <ul style='line-height: 2;'>
            <li><a href='/api/health' style='color: #60a5fa;'>Health Check</a></li>
            <li><a href='/api/outputs/list' style='color: #60a5fa;'>List Outputs</a></li>
            <li><a href='/ui' style='color: #60a5fa;'>Open Frontend UI</a></li>
        </ul>
        <h3>Upload & Run Pipeline:</h3>
        <p>POST to <code>/api/upload</code> then <code>/api/run</code></p>
        <p style='color: #9ca3af; margin-top: 40px;'>
            💡 Tip: For the React UI, open <code>/ui</code> so Babel can load modules over HTTP.
        </p>
    </body></html>"""


@app.route("/api/health", methods=["GET"]) 
def health() -> Any:
    """Health check endpoint"""
    try:
        controller = PipelineController()
        return jsonify({
            "status": "ok",
            "message": "Server is healthy",
            "paths": {
                "preprocessor": os.path.exists(controller.preprocessor_dir),
                "region_selector": os.path.exists(controller.region_selector_dir),
                "text_recognition": os.path.exists(controller.text_recognition_dir),
                "evaluator": os.path.exists(controller.evaluator_dir),
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }), 500


# Serve frontend over HTTP so Babel can fetch JSX files
@app.route('/ui')
def ui_index():
    """Serve frontend index.html"""
    index_path = os.path.join(FRONTEND_DIR, 'index.html')
    if os.path.isfile(index_path):
        return send_file(index_path)
    return jsonify({"error": "frontend index not found", "path": index_path}), 404


@app.route('/ui/<path:path>')
def ui_static(path: str):
    """Serve frontend static files"""
    target = os.path.join(FRONTEND_DIR, path)       
    if os.path.isfile(target):
        return send_from_directory(FRONTEND_DIR, path)
    return jsonify({"error": "asset not found", "path": path}), 404


@app.route("/api/upload", methods=["POST"]) 
def upload() -> Any:
    """
    Accepts multipart/form-data with fields:
    - answer_key[]: multiple files (answer keys/templates) - REQUIRED
    - answer_sheet[]: multiple files (answer sheets) - REQUIRED (can be single or multiple)
    - related_docs[]: multiple files - OPTIONAL
    """
    try:
        print("\n" + "="*60)
        print("📤 Processing file uploads...")
        
        # Handle multiple answer keys (REQUIRED)
        answer_key_files = request.files.getlist("answer_key[]") or request.files.getlist("answer_key")
        answer_key_paths = []
        for f in answer_key_files:
            if f.filename:
                dest = os.path.join(UPLOAD_ROOT, f.filename)
                f.save(dest)
                answer_key_paths.append(dest)
                print(f"  ✓ Answer key: {f.filename}")
        
        # Handle multiple answer sheets (REQUIRED)
        answer_sheet_files = request.files.getlist("answer_sheet[]") or request.files.getlist("answer_sheet")
        answer_sheet_paths = []
        for f in answer_sheet_files:
            if f.filename:
                dest = os.path.join(UPLOAD_ROOT, f.filename)
                f.save(dest)
                answer_sheet_paths.append(dest)
                print(f"  ✓ Answer sheet: {f.filename}")
        
        # Also check for single answer_sheet (backward compatibility)
        if not answer_sheet_paths:
            answer_sheet_path = _save_file("answer_sheet")
            if answer_sheet_path:
                answer_sheet_paths = [answer_sheet_path]
                print(f"  ✓ Answer sheet: {os.path.basename(answer_sheet_path)}")

        # related_docs is OPTIONAL
        related_docs_files = request.files.getlist("related_docs") or request.files.getlist("related_docs[]")
        related_doc_paths = []
        for f in related_docs_files:
            if f.filename:
                dest = os.path.join(UPLOAD_ROOT, f.filename)
                f.save(dest)
                related_doc_paths.append(dest)
                print(f"  ✓ Related doc: {f.filename}")

        if not answer_key_paths or not answer_sheet_paths:
            print("❌ Missing required files")
            return jsonify({"error": "at least one answer_key and one answer_sheet are required"}), 400

        controller = PipelineController()
        
        # Clean up old outputs before uploading new files
        print("\n🧹 Cleaning up previous session outputs...")
        cleanup_result = controller.cleanup_session_outputs()
        print(f"  Cleaned up {cleanup_result.get('total_files', 0)} files\n")
        
        saved = controller.save_uploads(answer_key_paths, answer_sheet_paths, related_doc_paths)
        
        print("✅ All files uploaded successfully")
        print("="*60)
        
        return jsonify({
            "status": "success",
            "message": "Files uploaded successfully",
            "saved": saved
        })
    
    except Exception as e:
        print(f"❌ Upload error: {e}")
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route("/api/run", methods=["POST"]) 
def run_pipeline() -> Any:
    """Run the complete pipeline"""
    try:
        print("\n" + "="*60)
        print("🚀 Starting pipeline via API...")
        print("="*60)
        
        data: Dict[str, Any] = request.get_json(silent=True) or {}
        
        # Optional: accept paths if already uploaded via other means
        answer_keys = data.get("answer_key_paths", [])
        answer_sheet = data.get("answer_sheet_path")
        related = data.get("related_docs_paths", [])

        if answer_keys and (answer_sheet or (isinstance(answer_sheet, list) and len(answer_sheet) > 0)):
            print("Running pipeline with provided paths...")
            answer_sheets = answer_sheet if isinstance(answer_sheet, list) else [answer_sheet]
            results = run_pipeline_after_uploads(answer_keys, answer_sheets, related)
            return jsonify(results)

        # Otherwise run pipeline on already saved files in agents dirs
        print("Running pipeline on existing files...")
        controller = PipelineController()
        results = controller.run_pipeline()
        
        return jsonify({
            "status": "success",
            "saved": {},
            "results": results
        })
    
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route("/api/results/current-student", methods=["GET"]) 
def current_student() -> Any:
    """Get current student JSON"""
    try:
        controller = PipelineController()
        path = controller.evaluator_temp_student
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return jsonify(data)
        return jsonify({"error": "current_student.json not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/outputs/preprocessor", methods=["GET"])
def get_preprocessor_outputs() -> Any:
    """Get list of aligned output images from preprocessor"""
    try:
        controller = PipelineController()
        outputs_dir = controller.preprocessor_outputs_dir
        images = []
        if os.path.isdir(outputs_dir):
            image_files = glob.glob(os.path.join(outputs_dir, "*.jpg")) + \
                         glob.glob(os.path.join(outputs_dir, "*.png"))
            images = [os.path.basename(f) for f in image_files]
        return jsonify({"images": images})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/outputs/preprocessor/<filename>")
def serve_preprocessor_image(filename: str):
    """Serve aligned output images"""
    try:
        controller = PipelineController()
        return send_from_directory(controller.preprocessor_outputs_dir, filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@app.route("/api/outputs/text-recognition", methods=["GET"])
def get_text_recognition_outputs() -> Any:
    """Get list of debug crop images from text recognition"""
    try:
        controller = PipelineController()
        debug_dir = os.path.join(controller.text_recognition_dir, "debug_crops")
        images = []
        if os.path.isdir(debug_dir):
            image_files = glob.glob(os.path.join(debug_dir, "*.png")) + \
                         glob.glob(os.path.join(debug_dir, "*.jpg"))
            images = sorted([os.path.basename(f) for f in image_files])
        return jsonify({"images": images})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/outputs/text-recognition/<filename>")
def serve_text_recognition_image(filename: str):
    """Serve debug crop images"""
    try:
        controller = PipelineController()
        debug_dir = os.path.join(controller.text_recognition_dir, "debug_crops")
        return send_from_directory(debug_dir, filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@app.route("/api/outputs/region-selector", methods=["GET"])
def get_region_selector_outputs() -> Any:
    """Get list of region selector evaluation result images"""
    try:
        controller = PipelineController()
        region_selector_dir = os.path.join(controller.region_selector_dir, "evaluation_results")
        images = []
        if os.path.isdir(region_selector_dir):
            image_files = glob.glob(os.path.join(region_selector_dir, "*.png")) + \
                         glob.glob(os.path.join(region_selector_dir, "*.jpg"))
            images = sorted([os.path.basename(f) for f in image_files])
        return jsonify({"images": images})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/outputs/region-selector/<filename>")
def serve_region_selector_image(filename: str):
    """Serve region selector evaluation result images"""
    try:
        controller = PipelineController()
        region_selector_dir = os.path.join(controller.region_selector_dir, "evaluation_results")
        return send_from_directory(region_selector_dir, filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@app.route("/api/outputs/visualizations", methods=["GET"])
def get_visualizations() -> Any:
    """Get list of visualization images"""
    try:
        controller = PipelineController()
        viz_dir = os.path.join(controller.evaluator_dir, "results", "visualizations")
        images = []
        if os.path.isdir(viz_dir):
            image_files = glob.glob(os.path.join(viz_dir, "*.png"))
            images = sorted([os.path.basename(f) for f in image_files])
        return jsonify({"images": images})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/outputs/visualizations/<filename>")
def serve_visualization(filename: str):
    """Serve visualization images"""
    try:
        controller = PipelineController()
        viz_dir = os.path.join(controller.evaluator_dir, "results", "visualizations")
        return send_from_directory(viz_dir, filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@app.route("/api/outputs/list", methods=["GET"])
def list_all_outputs() -> Any:
    """Get all available outputs from all stages"""
    try:
        controller = PipelineController()
        
        # Preprocessor outputs (aligned images)
        preprocessor_images = []
        if os.path.isdir(controller.preprocessor_outputs_dir):
            image_files = glob.glob(os.path.join(controller.preprocessor_outputs_dir, "*.jpg")) + \
                         glob.glob(os.path.join(controller.preprocessor_outputs_dir, "*.png"))
            preprocessor_images = [os.path.basename(f) for f in image_files]
        
        # Region selector evaluation results
        region_selector_dir = os.path.join(controller.region_selector_dir, "evaluation_results")
        region_selector_images = []
        if os.path.isdir(region_selector_dir):
            image_files = glob.glob(os.path.join(region_selector_dir, "*.png")) + \
                         glob.glob(os.path.join(region_selector_dir, "*.jpg"))
            region_selector_images = sorted([os.path.basename(f) for f in image_files])
        
        # Text recognition debug crops
        debug_dir = os.path.join(controller.text_recognition_dir, "debug_crops")
        debug_images = []
        if os.path.isdir(debug_dir):
            image_files = glob.glob(os.path.join(debug_dir, "*.png")) + \
                         glob.glob(os.path.join(debug_dir, "*.jpg"))
            debug_images = sorted([os.path.basename(f) for f in image_files])
        
        # Text recognition JSON outputs
        text_recognition_json = os.path.join(controller.text_recognition_outputs_dir, "student_answers.json")
        text_recognition_json_exists = os.path.isfile(text_recognition_json)
        text_recognition_data = None
        if text_recognition_json_exists:
            try:
                with open(text_recognition_json, "r", encoding="utf-8") as f:
                    text_recognition_data = json.load(f)
            except Exception as e:
                print(f"Error reading text recognition JSON: {e}")
        
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
        current_student_data = None
        if current_student_exists:
            try:
                with open(controller.evaluator_temp_student, "r", encoding="utf-8") as f:
                    current_student_data = json.load(f)
            except Exception as e:
                print(f"Error reading current student JSON: {e}")
        
        return jsonify({
            "preprocessor": {
                "images": preprocessor_images,
                "count": len(preprocessor_images)
            },
            "region_selector": {
                "images": region_selector_images,
                "count": len(region_selector_images)
            },
            "text_recognition": {
                "debug_crops": debug_images,
                "count": len(debug_images),
                "json_exists": text_recognition_json_exists,
                "json_data": text_recognition_data
            },
            "evaluator": {
                "visualizations": visualization_images,
                "count": len(visualization_images),
                "results_file": results_exists,
                "current_student_file": current_student_exists,
                "current_student_data": current_student_data
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/results/evaluation", methods=["GET"]) 
def evaluation_results() -> Any:
    """Get the full evaluation results JSON"""
    try:
        controller = PipelineController()
        results_path = os.path.join(controller.evaluator_dir, "results", "evaluation_results.json")
        if os.path.isfile(results_path):
            with open(results_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return jsonify(data)
        return jsonify({"error": "evaluation_results.json not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/results/all-students", methods=["GET"]) 
def all_students_results() -> Any:
    """Get all students' results with processed data for frontend"""
    try:
        controller = PipelineController()
        results_path = os.path.join(controller.evaluator_dir, "results", "evaluation_results.json")
        if not os.path.isfile(results_path):
            return jsonify({"error": "evaluation_results.json not found"}), 404
            
        with open(results_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        students = data.get("students", [])
        processed_students = []
        
        for student in students:
            # Process student data to match frontend expectations
            student_info = student.get("student_info", {})
            total_awarded = student.get("total_awarded_marks", 0)
            total_possible = student.get("total_possible_marks", 0)
            answers = student.get("answers", {})
            
            # Calculate additional metrics
            correct_count = sum(1 for q in answers.values() if q.get("awarded_marks", 0) > 0)
            incorrect_count = len(answers) - correct_count
            percentage = (total_awarded / total_possible * 100) if total_possible > 0 else 0
            
            # Convert answers to question_results format for frontend
            question_results = []
            for q_num, q_data in answers.items():
                question_results.append({
                    "question_number": q_num,
                    "student_answer": q_data.get("answer", ""),
                    "correct_answer": "",  # We don't have this in current format
                    "is_correct": q_data.get("awarded_marks", 0) > 0,
                    "marks": q_data.get("awarded_marks", 0),
                    "max_marks": q_data.get("max_marks", 0),
                    "feedback": q_data.get("feedback", "")
                })
            
            processed_student = {
                "student_id": student_info.get("roll_no", ""),
                "name": student_info.get("name", ""),
                "total_score": total_awarded,
                "max_score": total_possible,
                "score": total_awarded,
                "total": total_awarded,
                "percentage": percentage,
                "correct_count": correct_count,
                "incorrect_count": incorrect_count,
                "total_questions": len(answers),
                "question_results": question_results,
                "answers": answers,  # Keep original format too
                "raw_data": student  # Keep original data
            }
            
            processed_students.append(processed_student)
        
        return jsonify({
            "students": processed_students,
            "total_students": len(processed_students),
            "summary": {
                "average_score": sum(s["total_score"] for s in processed_students) / len(processed_students) if processed_students else 0,
                "highest_score": max(s["total_score"] for s in processed_students) if processed_students else 0,
                "lowest_score": min(s["total_score"] for s in processed_students) if processed_students else 0
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reference-answers/questions", methods=["GET"])
def get_questions_for_reference() -> Any:
    """Get list of questions detected from student answers or region selector"""
    try:
        controller = PipelineController()
        questions = []
        
        # Try to get questions from student answers JSON (after text recognition)
        student_answers_path = os.path.join(controller.text_recognition_outputs_dir, "student_answers.json")
        if os.path.isfile(student_answers_path):
            with open(student_answers_path, "r", encoding="utf-8") as f:
                student_data = json.load(f)
                answers = student_data.get("answers", {})
                if answers:
                    questions = sorted([q for q in answers.keys()], key=lambda x: int(x.replace('Q', '')) if x.replace('Q', '').isdigit() else 0)
                    return jsonify({
                        "questions": questions,
                        "count": len(questions),
                        "source": "student_answers"
                    })
        
        # Try to get from region selector agent1_output (count ROIs)
        agent1_output_dir = os.path.join(controller.region_selector_dir, "agent1_output")
        if os.path.isdir(agent1_output_dir):
            json_files = glob.glob(os.path.join(agent1_output_dir, "*_data.json"))
            if json_files:
                # Get the latest file
                latest_file = max(json_files, key=os.path.getctime)
                with open(latest_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    rois = data.get("rois", [])
                    if rois:
                        questions = [f"Q{i+1}" for i in range(len(rois))]
                        return jsonify({
                            "questions": questions,
                            "count": len(questions),
                            "source": "region_selector"
                        })
        
        # Try to get from existing reference answers
        reference_path = os.path.join(controller.evaluator_dir, "inputs", "reference_answers.json")
        if os.path.isfile(reference_path):
            with open(reference_path, "r", encoding="utf-8") as f:
                ref_data = json.load(f)
                if ref_data:
                    questions = sorted([q for q in ref_data.keys()], key=lambda x: int(x.replace('Q', '')) if x.replace('Q', '').isdigit() else 0)
                    return jsonify({
                        "questions": questions,
                        "count": len(questions),
                        "source": "reference_answers"
                    })
        
        return jsonify({
            "questions": [],
            "count": 0,
            "source": "none",
            "message": "No questions detected. Please run text recognition first."
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reference-answers/update", methods=["POST"])
def update_reference_answers() -> Any:
    """Update reference answers JSON with provided answers"""
    try:
        controller = PipelineController()
        reference_path = os.path.join(controller.evaluator_dir, "inputs", "reference_answers.json")
        
        data = request.get_json(silent=True) or {}
        answers = data.get("answers", {})
        
        if not answers:
            return jsonify({"error": "No answers provided"}), 400
        
        # Load existing reference answers
        existing_refs = {}
        if os.path.isfile(reference_path):
            with open(reference_path, "r", encoding="utf-8") as f:
                existing_refs = json.load(f)
        
        # Update with new answers
        updated_count = 0
        for qno, answer_data in answers.items():
            # Format: { "Q1": { "answer": "c", "marks": 2 } }
            if isinstance(answer_data, dict):
                existing_refs[qno] = {
                    "question": "",
                    "answer": answer_data.get("answer", ""),
                    "marks": answer_data.get("marks", 1)
                }
                updated_count += 1
            elif isinstance(answer_data, str):
                # Simple format: just the answer string, use default marks
                existing_refs[qno] = {
                    "question": "",
                    "answer": answer_data,
                    "marks": existing_refs.get(qno, {}).get("marks", 1)  # Keep existing marks if available
                }
                updated_count += 1
        
        # Save updated reference answers
        os.makedirs(os.path.dirname(reference_path), exist_ok=True)
        with open(reference_path, "w", encoding="utf-8") as f:
            json.dump(existing_refs, f, indent=4, ensure_ascii=False)
        
        print(f"\n✅ Updated reference answers: {updated_count} questions")
        print(f"📁 Saved to: {reference_path}")
        
        return jsonify({
            "status": "success",
            "message": f"Updated {updated_count} reference answers",
            "updated": updated_count,
            "total_questions": len(existing_refs)
        })
        
    except Exception as e:
        print(f"❌ Reference answers update error: {e}")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route("/api/student-info", methods=["POST"])
def save_student_info() -> Any:
    """Save student name and roll number mapping for answer sheets"""
    try:
        controller = PipelineController()
        data = request.get_json(silent=True) or {}
        student_info_map = data.get("student_info", {})  # {filename: {name: "...", roll_no: "..."}}
        
        if not student_info_map:
            return jsonify({"error": "No student info provided"}), 400
        
        # Load existing mapping if it exists
        existing_map = {}
        if os.path.isfile(controller.student_info_file):
            with open(controller.student_info_file, "r", encoding="utf-8") as f:
                existing_map = json.load(f)
        
        # Update with new mappings
        existing_map.update(student_info_map)
        
        # Save updated mapping
        os.makedirs(os.path.dirname(controller.student_info_file), exist_ok=True)
        with open(controller.student_info_file, "w", encoding="utf-8") as f:
            json.dump(existing_map, f, indent=4, ensure_ascii=False)
        
        print(f"\n✅ Saved student info for {len(student_info_map)} answer sheet(s)")
        
        return jsonify({
            "status": "success",
            "message": f"Saved student info for {len(student_info_map)} answer sheet(s)",
            "mapped": len(existing_map)
        })
        
    except Exception as e:
        print(f"❌ Student info save error: {e}")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route("/api/reference-answers", methods=["GET"])
def get_reference_answers() -> Any:
    """Get current reference answers"""
    try:
        controller = PipelineController()
        reference_path = os.path.join(controller.evaluator_dir, "inputs", "reference_answers.json")
        
        if os.path.isfile(reference_path):
            with open(reference_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return jsonify(data)
        
        return jsonify({})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/session/close", methods=["POST"])
def close_session() -> Any:
    """Clear all output directories when session is closed"""
    try:
        print("\n" + "="*60)
        print("🔒 Closing session and cleaning up outputs...")
        print("="*60)
        
        controller = PipelineController()
        result = controller.cleanup_session_outputs()
        
        return jsonify(result)
    
    except Exception as e:
        print(f"❌ Session close error: {e}")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Starting PaperBrain API Server")
    print("="*60)
    
    port = int(os.environ.get("PORT", 5000))
    
    print(f"📍 Server will run on http://0.0.0.0:{port}")
    print(f"📍 Access at http://localhost:{port}")
    print(f"📍 Frontend UI at http://localhost:3000/ui")
    print("="*60 + "\n")
    
    app.run(host="0.0.0.0", port=port, debug=True)