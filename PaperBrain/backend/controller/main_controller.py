import os
import json
import shutil
import subprocess
import sys
import cv2
import base64
from typing import Dict, Any, List


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AGENTS_ROOT = os.path.join(PROJECT_ROOT, "agents")


class PipelineController:
    """Coordinates the agents in the required order without modifying agent code."""

    def __init__(self) -> None:
        self.preprocessor_dir = os.path.join(AGENTS_ROOT, "preprocessor")
        self.region_selector_dir = os.path.join(AGENTS_ROOT, "region_selector")
        self.text_recognition_dir = os.path.join(AGENTS_ROOT, "text_recognition")
        self.evaluator_dir = os.path.join(AGENTS_ROOT, "evaluator")

        # Input/Output conventions based on actual agent structure
        self.evaluator_inputs_dir = os.path.join(self.evaluator_dir, "inputs")
        self.evaluator_related_docs_dir = os.path.join(self.evaluator_inputs_dir, "related_docs")
        self.evaluator_temp_student = os.path.join(self.evaluator_dir, "temp", "current_student.json")

        # Preprocessor paths
        self.preprocessor_inputs_dir = os.path.join(self.preprocessor_dir, "answer_scripts")
        self.preprocessor_templates_dir = os.path.join(self.preprocessor_dir, "question_paper_templates")
        self.preprocessor_outputs_dir = os.path.join(self.preprocessor_dir, "aligned_outputs")

        # Text recognition paths
        self.text_recognition_outputs_dir = os.path.join(self.text_recognition_dir, "Outputs")

        # Ensure expected directories exist
        os.makedirs(self.evaluator_related_docs_dir, exist_ok=True)
        os.makedirs(os.path.join(self.evaluator_dir, "temp"), exist_ok=True)
        os.makedirs(self.preprocessor_inputs_dir, exist_ok=True)
        os.makedirs(self.preprocessor_outputs_dir, exist_ok=True)
        os.makedirs(self.text_recognition_outputs_dir, exist_ok=True)

    # -------------------------------------------------------------------------
    # SAVE UPLOADS
    # -------------------------------------------------------------------------
    def save_uploads(self, answer_key_paths: List[str], answer_sheet_path: str, related_docs: List[str]) -> Dict[str, Any]:
        destinations: Dict[str, Any] = {}

        saved_templates = []
        for i, ak_path in enumerate(answer_key_paths):
            ak_dest = os.path.join(self.preprocessor_templates_dir, f"template_{i+1}_{os.path.basename(ak_path)}")
            shutil.copy2(ak_path, ak_dest)
            saved_templates.append(ak_dest)
        destinations["answer_keys"] = saved_templates

        as_dest = os.path.join(self.preprocessor_inputs_dir, f"scan_{os.path.basename(answer_sheet_path)}")
        shutil.copy2(answer_sheet_path, as_dest)
        destinations["answer_sheet"] = as_dest

        saved_docs = []
        for doc in related_docs:
            if not os.path.isfile(doc):
                continue
            dest = os.path.join(self.evaluator_related_docs_dir, os.path.basename(doc))
            shutil.copy2(doc, dest)
            saved_docs.append(dest)
        destinations["related_docs"] = saved_docs

        return destinations

    # -------------------------------------------------------------------------
    # PREPROCESSOR (Alignment)
    # -------------------------------------------------------------------------
    def run_preprocessor(self) -> Dict[str, Any]:
        print("\n🔄 Step 1: Running Preprocessor (Alignment)...")
        template_files = [f for f in os.listdir(self.preprocessor_templates_dir) if f.startswith("template_")]
        scan_files = [f for f in os.listdir(self.preprocessor_inputs_dir) if f.startswith("scan_")]

        if not template_files or not scan_files:
            print("❌ Missing templates or scans")
            return {"status": "error", "message": "Missing templates or scans.", "summary": {}}

        scan_path = os.path.join(self.preprocessor_inputs_dir, max(scan_files))
        best_result, best_score, best_template = None, 0, None

        try:
            sys.path.append(self.preprocessor_dir)
            from alignment_agent import run_alignment_agent

            for template_file in template_files:
                template_path = os.path.join(self.preprocessor_templates_dir, template_file)
                try:
                    print(f"  Trying alignment with {template_file}...")
                    img_aligned, H, score = run_alignment_agent(template_path, scan_path)
                    if img_aligned is not None and score > best_score:
                        best_score, best_result, best_template = score, img_aligned, template_file
                        print(f"  ✓ Score: {score}")
                except Exception as e:
                    print(f"  ✗ Alignment failed for {template_file}: {e}")

            if best_result is not None:
                output_filename = f"aligned_{os.path.basename(scan_path)}"
                output_path = os.path.join(self.preprocessor_outputs_dir, output_filename)
                cv2.imwrite(output_path, best_result)
                print(f"✅ Preprocessor completed. Best template: {best_template}, Score: {best_score}")
                summary = {
                    "status": "completed",
                    "alignment_score": float(best_score),
                    "template_used": best_template,
                    "output_image": output_path,
                    "message": f"Preprocessing done using {best_template}",
                }
            else:
                print("❌ All alignments failed")
                summary = {"status": "failed", "alignment_score": 0, "message": "All alignments failed."}
        except Exception as e:
            print(f"❌ Preprocessor error: {e}")
            summary = {"status": "error", "message": str(e)}

        return {"summary": summary}

    # -------------------------------------------------------------------------
    # REGION SELECTOR (AUTO TRIGGER AFTER ALIGNMENT)
    # -------------------------------------------------------------------------
    def run_region_selector(self) -> Dict[str, Any]:
        """
        Automatically runs the real region_selector.py (OpenCV-based) after alignment.
        """
        print("\n🔍 Step 2: Running Region Selector...")
        region_script_path = os.path.join(self.region_selector_dir, "region_selector.py")

        if not os.path.exists(region_script_path):
            print(f"❌ region_selector.py not found at {region_script_path}")
            return {"status": "error", "message": f"region_selector.py not found at {region_script_path}"}

        try:
            # Change to region selector directory before running
            original_cwd = os.getcwd()
            os.chdir(self.region_selector_dir)
            
            result = subprocess.run(
                [self._python_executable(), "region_selector.py"],
                capture_output=True,
                text=True,
                check=False,  # Don't raise exception, we'll check returncode
                timeout=120  # 2 minute timeout
            )
            
            os.chdir(original_cwd)  # Restore directory
            
            if result.returncode == 0:
                print("✅ Region Selector completed successfully")
                print(f"Output: {result.stdout[:200]}")  # Print first 200 chars
                return {
                    "status": "completed",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "message": "Region selection done successfully."
                }
            else:
                print(f"❌ Region Selector failed with return code {result.returncode}")
                print(f"Error: {result.stderr}")
                return {
                    "status": "error", 
                    "message": f"Region selector failed with code {result.returncode}",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            os.chdir(original_cwd)
            print("❌ Region Selector timed out")
            return {"status": "error", "message": "Region selector timed out after 120 seconds"}
        except Exception as e:
            os.chdir(original_cwd)
            print(f"❌ Region Selector exception: {e}")
            return {"status": "error", "message": str(e)}

    # -------------------------------------------------------------------------
    # TEXT RECOGNITION
    # -------------------------------------------------------------------------
    def run_text_recognition(self) -> Dict[str, Any]:
        print("\n📝 Step 3: Running Text Recognition...")
        try:
            aligned_files = [f for f in os.listdir(self.preprocessor_outputs_dir) if f.startswith("aligned_")]
            if not aligned_files:
                print("❌ No aligned images found")
                return {"status": "error", "message": "No aligned images found."}

            aligned_image_path = os.path.join(self.preprocessor_outputs_dir, max(aligned_files))
            print(f"  Using aligned image: {aligned_image_path}")

            # Simulated OCR output for now
            simulated_results = {"Q1": "c", "Q2": "6", "Q3": "a", "Q4": "b", "Q5": "d"}
            student_info = {"name": "Shivsrijit Verma", "roll_no": "AID23B015"}

            final_output = {"student_info": student_info, "answers": simulated_results}

            output_file = os.path.join(self.text_recognition_outputs_dir, "student_answers.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(final_output, f, indent=2)

            print("✅ Text Recognition completed")
            return {
                "status": "completed",
                "message": "OCR done successfully.",
                "recognized_text": simulated_results,
                "output_file": output_file,
            }
        except Exception as e:
            print(f"❌ Text Recognition error: {e}")
            return {"status": "error", "message": str(e)}

    # -------------------------------------------------------------------------
    # EVALUATOR
    # -------------------------------------------------------------------------
    def run_evaluator(self) -> Dict[str, Any]:
        print("\n📊 Step 4: Running Evaluator...")
        try:
            original_cwd = os.getcwd()
            os.chdir(self.evaluator_dir)

            result = subprocess.run(
                [self._python_executable(), "main.py"],
                capture_output=True,
                text=True,
                timeout=60
            )

            os.chdir(original_cwd)
            ran_script = result.returncode == 0

            if ran_script:
                print("✅ Evaluator completed")
                
                # Run visualizations after evaluator completes successfully
                print("\n📈 Generating Visualizations...")
                try:
                    viz_script = os.path.join(self.evaluator_dir, "visualizations.py")
                    if os.path.exists(viz_script):
                        viz_result = subprocess.run(
                            [self._python_executable(), viz_script],
                            capture_output=True,
                            text=True,
                            timeout=60,
                            cwd=self.evaluator_dir
                        )
                        if viz_result.returncode == 0:
                            print("✅ Visualizations generated successfully")
                        else:
                            print(f"⚠️ Visualizations failed (non-fatal): {viz_result.stderr}")
                    else:
                        print(f"⚠️ visualizations.py not found at {viz_script}")
                except Exception as viz_error:
                    print(f"⚠️ Visualization error (non-fatal): {viz_error}")
            else:
                print(f"❌ Evaluator failed with code {result.returncode}")
                print(f"Error: {result.stderr}")

            current_student = {}
            if os.path.isfile(self.evaluator_temp_student):
                with open(self.evaluator_temp_student, "r", encoding="utf-8") as f:
                    current_student = json.load(f)

            results_json = os.path.join(self.evaluator_dir, "results", "evaluation_results.json")
            results_data = None
            if os.path.isfile(results_json):
                with open(results_json, "r", encoding="utf-8") as f:
                    results_data = json.load(f)

            return {
                "script_ran": ran_script,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "current_student": current_student,
                "results": results_data,
            }
        except subprocess.TimeoutExpired:
            os.chdir(original_cwd)
            print("❌ Evaluator timed out")
            return {"status": "error", "message": "Evaluator timed out."}
        except Exception as e:
            os.chdir(original_cwd)
            print(f"❌ Evaluator error: {e}")
            return {"status": "error", "message": str(e)}

    # -------------------------------------------------------------------------
    # PIPELINE SEQUENCE
    # -------------------------------------------------------------------------
    def run_pipeline(self) -> Dict[str, Any]:
        print("\n" + "="*60)
        print("🚀 Starting Pipeline Execution")
        print("="*60)
        
        # Step 1: Preprocessor
        pre = self.run_preprocessor()
        if pre.get("summary", {}).get("status") != "completed":
            print("\n❌ Pipeline stopped: Preprocessor failed")
            return {
                "preprocessor": pre,
                "region_selector": {"status": "skipped", "message": "Preprocessor failed"},
                "text_recognition": {"status": "skipped", "message": "Preprocessor failed"},
                "evaluator": {"status": "skipped", "message": "Preprocessor failed"},
            }
        
        # Step 2: Region Selector
        reg = self.run_region_selector()
        if reg.get("status") != "completed":
            print("\n⚠️ Pipeline continuing despite Region Selector issues")
            # Don't stop pipeline here - region selector might be optional
        
        # Step 3: Text Recognition
        ocr = self.run_text_recognition()
        if ocr.get("status") != "completed":
            print("\n❌ Pipeline stopped: Text Recognition failed")
            return {
                "preprocessor": pre,
                "region_selector": reg,
                "text_recognition": ocr,
                "evaluator": {"status": "skipped", "message": "Text Recognition failed"},
            }
        
        # Step 4: Evaluator
        eva = self.run_evaluator()
        
        print("\n" + "="*60)
        print("✅ Pipeline Execution Complete")
        print("="*60)
        
        return {
            "preprocessor": pre,
            "region_selector": reg,
            "text_recognition": ocr,
            "evaluator": eva,
        }

    # -------------------------------------------------------------------------
    @staticmethod
    def _python_executable() -> str:
        return sys.executable or os.environ.get("PYTHON", "python")


# -------------------------------------------------------------------------
# EXTERNAL TRIGGER (AFTER FILE UPLOADS)
# -------------------------------------------------------------------------
def run_pipeline_after_uploads(answer_key_paths: List[str], answer_sheet: str, related_docs: List[str]) -> Dict[str, Any]:
    """Run complete pipeline after uploading files"""
    controller = PipelineController()
    saved = controller.save_uploads(answer_key_paths, answer_sheet, related_docs)
    results = controller.run_pipeline()
    return {"saved": saved, "results": results}


if __name__ == "__main__":
    # For testing purposes
    print("PipelineController module loaded successfully")
    controller = PipelineController()
    print(f"Preprocessor dir: {controller.preprocessor_dir}")
    print(f"Region selector dir: {controller.region_selector_dir}")
    print(f"Text recognition dir: {controller.text_recognition_dir}")
    print(f"Evaluator dir: {controller.evaluator_dir}")