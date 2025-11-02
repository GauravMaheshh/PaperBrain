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
        
        # Student info mapping file (maps answer sheet filenames to student info)
        self.student_info_file = os.path.join(self.text_recognition_dir, "Outputs", "student_info_mapping.json")

        # Ensure expected directories exist
        os.makedirs(self.evaluator_related_docs_dir, exist_ok=True)
        os.makedirs(os.path.join(self.evaluator_dir, "temp"), exist_ok=True)
        os.makedirs(self.preprocessor_inputs_dir, exist_ok=True)
        os.makedirs(self.preprocessor_outputs_dir, exist_ok=True)
        os.makedirs(self.text_recognition_outputs_dir, exist_ok=True)

    # -------------------------------------------------------------------------
    # SAVE UPLOADS
    # -------------------------------------------------------------------------
    def save_uploads(self, answer_key_paths: List[str], answer_sheet_paths: List[str], related_docs: List[str]) -> Dict[str, Any]:
        destinations: Dict[str, Any] = {}

        saved_templates = []
        for i, ak_path in enumerate(answer_key_paths):
            ak_dest = os.path.join(self.preprocessor_templates_dir, f"template_{i+1}_{os.path.basename(ak_path)}")
            shutil.copy2(ak_path, ak_dest)
            saved_templates.append(ak_dest)
        destinations["answer_keys"] = saved_templates

        saved_answer_sheets = []
        for as_path in answer_sheet_paths:
            as_dest = os.path.join(self.preprocessor_inputs_dir, f"scan_{os.path.basename(as_path)}")
            shutil.copy2(as_path, as_dest)
            saved_answer_sheets.append(as_dest)
        destinations["answer_sheets"] = saved_answer_sheets
        
        # For backward compatibility, also include single answer_sheet
        if saved_answer_sheets:
            destinations["answer_sheet"] = saved_answer_sheets[0]

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
        scan_files = sorted([f for f in os.listdir(self.preprocessor_inputs_dir) if f.startswith("scan_")])

        if not template_files or not scan_files:
            print("❌ Missing templates or scans")
            return {"status": "error", "message": "Missing templates or scans.", "summary": {}}

        print(f"  Processing {len(scan_files)} answer sheet(s) with {len(template_files)} template(s)")

        summaries = []
        try:
            sys.path.append(self.preprocessor_dir)
            from alignment_agent import run_alignment_agent

            # Process each answer sheet
            for scan_file in scan_files:
                scan_path = os.path.join(self.preprocessor_inputs_dir, scan_file)
                print(f"\n  Processing: {scan_file}")
                best_result, best_score, best_template = None, 0, None

                # Try each template with this scan
                for template_file in template_files:
                    template_path = os.path.join(self.preprocessor_templates_dir, template_file)
                    try:
                        print(f"    Trying alignment with {template_file}...")
                        img_aligned, H, score = run_alignment_agent(template_path, scan_path)
                        if img_aligned is not None and score > best_score:
                            best_score, best_result, best_template = score, img_aligned, template_file
                            print(f"    ✓ Score: {score}")
                    except Exception as e:
                        print(f"    ✗ Alignment failed for {template_file}: {e}")

                if best_result is not None:
                    output_filename = f"aligned_{os.path.basename(scan_path)}"
                    output_path = os.path.join(self.preprocessor_outputs_dir, output_filename)
                    cv2.imwrite(output_path, best_result)
                    print(f"  ✓ Aligned: {output_filename} (template: {best_template}, score: {best_score})")
                    summaries.append({
                        "status": "completed",
                        "scan_file": scan_file,
                        "alignment_score": float(best_score),
                        "template_used": best_template,
                        "output_image": output_path,
                    })
                else:
                    print(f"  ✗ Alignment failed for {scan_file}")
                    summaries.append({
                        "status": "failed",
                        "scan_file": scan_file,
                        "alignment_score": 0,
                        "message": "All alignments failed for this scan."
                    })

            if any(s["status"] == "completed" for s in summaries):
                print(f"\n✅ Preprocessor completed. Processed {len([s for s in summaries if s['status'] == 'completed'])}/{len(scan_files)} answer sheet(s)")
            else:
                print("\n❌ All alignments failed")
                summary = {"status": "failed", "alignment_score": 0, "message": "All alignments failed."}
                return {"summary": summary}

        except Exception as e:
            print(f"❌ Preprocessor error: {e}")
            import traceback
            traceback.print_exc()
            summary = {"status": "error", "message": str(e)}
            return {"summary": summary}

        return {"summary": {"status": "completed", "processed": len(summaries), "details": summaries}}

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
            # Check if agent1_output files exist (from region selector)
            agent1_output_dir = os.path.join(self.region_selector_dir, "agent1_output")
            if not os.path.isdir(agent1_output_dir):
                print("❌ agent1_output directory not found")
                return {"status": "error", "message": "Region selector output not found."}
            
            json_files = [f for f in os.listdir(agent1_output_dir) if f.endswith("_data.json")]
            if not json_files:
                print("❌ No region selector output files found")
                return {"status": "error", "message": "No region selector output files found."}

            print(f"  Found {len(json_files)} region selector output file(s)")
            
            # Run the actual OCR script
            original_cwd = os.getcwd()
            os.chdir(self.text_recognition_dir)
            
            try:
                result = subprocess.run(
                    [self._python_executable(), "run_agent2_test.py"],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                os.chdir(original_cwd)
                
                # Even if script exits with error, check if output files were created
                # (Sometimes Unicode errors in print statements cause exit code 1 but file is still saved)
                outputs_dir = os.path.join(self.text_recognition_dir, "Outputs")
                output_files = [f for f in os.listdir(outputs_dir) if f.endswith("_evaluation.json") and os.path.getsize(os.path.join(outputs_dir, f)) > 0] if os.path.isdir(outputs_dir) else []
                
                if result.returncode != 0:
                    if not output_files:
                        # Only fail if no output files were created
                        print(f"❌ OCR script failed with code {result.returncode}")
                        print(f"Error output: {result.stderr}")
                        return {"status": "error", "message": f"OCR script failed: {result.stderr}"}
                    else:
                        # Output files exist, script probably just had a print error
                        print(f"⚠️  OCR script had warnings (code {result.returncode}) but output files were created")
                
                print("  OCR processing completed")
                
                # Find the generated output file(s) in Outputs folder
                outputs_dir = os.path.join(self.text_recognition_dir, "Outputs")
                
                # Wait a moment for files to be written
                import time
                time.sleep(0.5)
                
                output_files = [f for f in os.listdir(outputs_dir) if f.endswith("_evaluation.json") and os.path.getsize(os.path.join(outputs_dir, f)) > 0]
                
                if not output_files:
                    print("❌ No OCR output files generated or all files are empty")
                    return {"status": "error", "message": "No OCR output files generated."}
                
                print(f"  Found {len(output_files)} OCR output file(s) to process")
                
                # Load student info mapping
                student_info_map = {}
                if os.path.isfile(self.student_info_file):
                    try:
                        with open(self.student_info_file, "r", encoding="utf-8") as f:
                            student_info_map = json.load(f)
                    except:
                        pass
                
                # Process all OCR output files and update student_info in each
                processed_count = 0
                for output_file in output_files:
                    output_path = os.path.join(outputs_dir, output_file)
                    
                    try:
                        # Read the generated OCR output
                        with open(output_path, "r", encoding="utf-8") as f:
                            content = f.read().strip()
                            if not content:
                                continue
                            ocr_output = json.loads(content)
                    except json.JSONDecodeError as e:
                        print(f"  ⚠️  Skipping {output_file}: Invalid JSON ({e})")
                        continue
                    except Exception as e:
                        print(f"  ⚠️  Skipping {output_file}: {e}")
                        continue
                    
                    # Extract answers and student_info
                    recognized_answers = ocr_output.get("answers", {})
                    student_info = ocr_output.get("student_info", {})

                    # Validate that we have answers
                    if not recognized_answers or len(recognized_answers) == 0:
                        print(f"  ⚠️  Skipping {output_file}: No answers found")
                        continue

                    # Try to get student info from mapping file using the filename
                    # The filename format is: aligned_scan_<original_filename>_evaluation.json
                    # We need to match it with scan_<original_filename>
                    file_key = output_file.replace("_evaluation.json", "").replace("aligned_", "scan_")
                    
                    # Try to find matching student info from mapping
                    mapped_info = None
                    if file_key in student_info_map:
                        mapped_info = student_info_map[file_key]
                    elif file_key.replace("scan_", "") in student_info_map:
                        mapped_info = student_info_map[file_key.replace("scan_", "")]
                    else:
                        # Try matching by base filename
                        base_name = os.path.splitext(output_file)[0].replace("aligned_", "").replace("_evaluation", "")
                        for key, info in student_info_map.items():
                            if base_name in key or key in base_name:
                                mapped_info = info
                                break
                    
                    if mapped_info:
                        student_info = {
                            "name": mapped_info.get("name", "Unknown Student"),
                            "roll_no": mapped_info.get("roll_no", "UNKNOWN")
                        }
                    elif not student_info.get("name") or student_info.get("name") == "STUDENT_NAME_HERE":
                        # Try to extract from filename
                        base_name = os.path.splitext(output_file)[0].replace("aligned_", "").replace("_evaluation", "").replace("scan_", "")
                        student_info["name"] = base_name.replace("_", " ").title()
                        student_info["roll_no"] = base_name.upper()

                    # Ensure student_info has both fields
                    if "name" not in student_info:
                        student_info["name"] = "Unknown Student"
                    if "roll_no" not in student_info:
                        student_info["roll_no"] = "UNKNOWN"
                    
                    # Update the OCR output file with correct student_info
                    ocr_output["student_info"] = student_info
                    
                    # Save updated output
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(ocr_output, f, indent=2, ensure_ascii=False)
                    
                    processed_count += 1
                    print(f"  ✓ Updated {output_file} with student info: {student_info['name']} ({student_info['roll_no']})")
                
                if processed_count == 0:
                    return {"status": "error", "message": "No valid OCR outputs to process."}
                
                print(f"✅ Text Recognition completed")
                print(f"  Processed {processed_count} answer sheet(s)")
                
                return {
                    "status": "completed",
                    "message": f"OCR done successfully. Processed {processed_count} answer sheet(s).",
                    "processed_count": processed_count,
                    "output_files": output_files
                }
                
            except subprocess.TimeoutExpired:
                os.chdir(original_cwd)
                print("❌ OCR script timed out")
                return {"status": "error", "message": "OCR script timed out."}
            except Exception as e:
                os.chdir(original_cwd)
                print(f"❌ Text Recognition error: {e}")
                import traceback
                traceback.print_exc()
                return {"status": "error", "message": str(e)}
                
        except Exception as e:
            print(f"❌ Text Recognition error: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    # -------------------------------------------------------------------------
    # EVALUATOR
    # -------------------------------------------------------------------------
    def run_evaluator(self) -> Dict[str, Any]:
        print("\n📊 Step 4: Running Evaluator...")
        
        # Check if reference answers exist before running evaluator
        reference_path = os.path.join(self.evaluator_dir, "inputs", "reference_answers.json")
        student_answers_path = os.path.join(self.text_recognition_outputs_dir, "student_answers.json")
        
        # Check if we have student answers to know what questions to expect
        questions_need_answers = []
        existing_refs = {}
        if os.path.isfile(reference_path):
            with open(reference_path, "r", encoding="utf-8") as f:
                existing_refs = json.load(f)
        
        if os.path.isfile(student_answers_path):
            with open(student_answers_path, "r", encoding="utf-8") as f:
                student_data = json.load(f)
                student_answers = student_data.get("answers", {})
                if student_answers:
                    # Check which questions don't have reference answers
                    for qno in student_answers.keys():
                        if qno not in existing_refs or not existing_refs[qno].get("answer"):
                            questions_need_answers.append(qno)
        
        if questions_need_answers:
            print(f"\n⚠️  Missing reference answers for questions: {', '.join(questions_need_answers)}")
            print("   Please provide reference answers before evaluation can proceed.")
            return {
                "status": "error",
                "message": f"Missing reference answers for {len(questions_need_answers)} question(s). Please provide reference answers first.",
                "missing_questions": questions_need_answers,
                "requires_reference_answers": True
            }
        
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
    # CLEANUP / SESSION CLOSE
    # -------------------------------------------------------------------------
    def cleanup_session_outputs(self) -> Dict[str, Any]:
        """
        Clears all output directories when session is closed.
        Removes files from:
        - aligned_outputs (preprocessor)
        - evaluation_results (region_selector)
        - agent1_output (region_selector)
        - answer_scripts (preprocessor)
        - question_paper_templates (preprocessor)
        - visualizations (evaluator)
        - debug_crops (text_recognition)
        """
        print("\n" + "="*60)
        print("🧹 Cleaning up session outputs...")
        print("="*60)
        
        cleaned = {
            "aligned_outputs": [],
            "evaluation_results": [],
            "agent1_output": [],
            "answer_scripts": [],
            "question_paper_templates": [],
            "visualizations": [],
            "debug_crops": []
        }
        
        try:
            # 1. Clear aligned_outputs (preprocessor outputs)
            if os.path.isdir(self.preprocessor_outputs_dir):
                for filename in os.listdir(self.preprocessor_outputs_dir):
                    file_path = os.path.join(self.preprocessor_outputs_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        cleaned["aligned_outputs"].append(filename)
                        print(f"  ✓ Removed: {filename} from aligned_outputs")
            
            # 2. Clear evaluation_results (region_selector)
            evaluation_results_dir = os.path.join(self.region_selector_dir, "evaluation_results")
            if os.path.isdir(evaluation_results_dir):
                for filename in os.listdir(evaluation_results_dir):
                    file_path = os.path.join(evaluation_results_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        cleaned["evaluation_results"].append(filename)
                        print(f"  ✓ Removed: {filename} from evaluation_results")
            
            # 3. Clear agent1_output (region_selector)
            agent1_output_dir = os.path.join(self.region_selector_dir, "agent1_output")
            if os.path.isdir(agent1_output_dir):
                for filename in os.listdir(agent1_output_dir):
                    file_path = os.path.join(agent1_output_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        cleaned["agent1_output"].append(filename)
                        print(f"  ✓ Removed: {filename} from agent1_output")
            
            # 4. Clear answer_scripts (preprocessor inputs)
            if os.path.isdir(self.preprocessor_inputs_dir):
                for filename in os.listdir(self.preprocessor_inputs_dir):
                    file_path = os.path.join(self.preprocessor_inputs_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        cleaned["answer_scripts"].append(filename)
                        print(f"  ✓ Removed: {filename} from answer_scripts")
            
            # 5. Clear question_paper_templates (preprocessor templates)
            if os.path.isdir(self.preprocessor_templates_dir):
                for filename in os.listdir(self.preprocessor_templates_dir):
                    file_path = os.path.join(self.preprocessor_templates_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        cleaned["question_paper_templates"].append(filename)
                        print(f"  ✓ Removed: {filename} from question_paper_templates")
            
            # 6. Clear visualizations (evaluator)
            visualizations_dir = os.path.join(self.evaluator_dir, "results", "visualizations")
            if os.path.isdir(visualizations_dir):
                for filename in os.listdir(visualizations_dir):
                    file_path = os.path.join(visualizations_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        cleaned["visualizations"].append(filename)
                        print(f"  ✓ Removed: {filename} from visualizations")
            
            # 7. Clear debug_crops (text_recognition)
            debug_crops_dir = os.path.join(self.text_recognition_dir, "debug_crops")
            if os.path.isdir(debug_crops_dir):
                for filename in os.listdir(debug_crops_dir):
                    file_path = os.path.join(debug_crops_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        cleaned["debug_crops"].append(filename)
                        print(f"  ✓ Removed: {filename} from debug_crops")
            
            total_cleaned = sum(len(files) for files in cleaned.values())
            print(f"\n✅ Cleanup completed. Removed {total_cleaned} files total.")
            print("="*60)
            
            return {
                "status": "success",
                "message": f"Cleaned up {total_cleaned} files",
                "cleaned": cleaned,
                "total_files": total_cleaned
            }
            
        except Exception as e:
            print(f"\n❌ Cleanup error: {e}")
            print("="*60)
            return {
                "status": "error",
                "message": str(e),
                "cleaned": cleaned
            }

    # -------------------------------------------------------------------------
    @staticmethod
    def _python_executable() -> str:
        return sys.executable or os.environ.get("PYTHON", "python")


# -------------------------------------------------------------------------
# EXTERNAL TRIGGER (AFTER FILE UPLOADS)
# -------------------------------------------------------------------------
def run_pipeline_after_uploads(answer_key_paths: List[str], answer_sheet_paths: List[str], related_docs: List[str]) -> Dict[str, Any]:
    """Run complete pipeline after uploading files"""
    controller = PipelineController()
    saved = controller.save_uploads(answer_key_paths, answer_sheet_paths, related_docs)
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