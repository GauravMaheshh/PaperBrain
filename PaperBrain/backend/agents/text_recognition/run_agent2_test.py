import asyncio
import base64
import json
import os
import glob   # <-- NEW
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# --- 1. CONFIGURE FOLDER PATHS ---
AGENT1_OUTPUT_FOLDER = "../region_selector/agent1_output"
FINAL_EVALUATIONS_FOLDER = "./Outputs"

# Create final output folder if it doesn't exist
os.makedirs(FINAL_EVALUATIONS_FOLDER, exist_ok=True)
# ---------------------------------

# Define the server to launch (Agent 2)
agent_2_server = StdioServerParameters(
    command="python3",
    args=["ocr_server.py"] 
)

async def run_batch_ocr():
    """
    Finds all data files from Agent 1, launches Agent 2,
    and calls the tool for each file.
    """
    
    # --- 2. FIND ALL JOBS FROM AGENT 1 ---
    json_files = glob.glob(os.path.join(AGENT1_OUTPUT_FOLDER, "*.json"))
    if not json_files:
        print(f"Error: No data files found in '{AGENT1_OUTPUT_FOLDER}'.")
        print("Please run the Agent 1 (ipynb) script first.")
        return
        
    print(f"Found {len(json_files)} answer sheets to evaluate.")
    
    # --- 3. LAUNCH AGENT 2 (ONCE) ---
    print(f"\n--- Client: Launching server 'python3 ocr_server.py' ---")
    
    async with stdio_client(agent_2_server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("--- Client: Server initialized. Starting batch... ---")
            
            # --- 4. LOOP THROUGH EACH JOB ---
            for job_file_path in json_files:
                print(f"\n--- Processing job: {job_file_path} ---")
                
                # --- 4a. Load data from Agent 1's file ---
                with open(job_file_path, 'r') as f:
                    data = json.load(f)
                
                image_base64_to_test = data.get("image_base64")
                rois_to_test = data.get("rois")
                
                if not image_base64_to_test or not rois_to_test:
                    print(f"Skipping job, data file is missing 'image_base64' or 'rois'.")
                    continue
                
                # --- 4b. Call the tool ---
                print(f"Calling tool 'read_text_in_rois' with {len(rois_to_test)} ROIs...")
                result = await session.call_tool(
                    "read_text_in_rois",
                    {
                        "image_base64": image_base64_to_test,
                        "rois": rois_to_test
                    }
                )
                
                # --- 4c. Process the result ---
                final_json_text = None
                for item in result.content:
                    if item.type == 'text' and item.text.startswith('{'):
                        final_json_text = item.text
                
                if final_json_text:
                    answers_dict = json.loads(final_json_text)

                    # Placeholder student info
                    student_info = {
                        "name": "STUDENT_NAME_HERE",
                        "roll_no": "ROLL_NO_HERE"
                    }
                    
                    final_output = {
                        "student_info": student_info,
                        "answers": answers_dict
                    }

                    # --- 4d. Save the final JSON ---
                    base_name = os.path.basename(job_file_path)
                    file_name_only = os.path.splitext(base_name)[0].replace('_data', '')
                    output_filename = f"{FINAL_EVALUATIONS_FOLDER}/{file_name_only}_evaluation.json"
                    
                    with open(output_filename, 'w') as f:
                        json.dump(final_output, f, indent=4)
                    
                    print(f"✅ Success! Saved final evaluation to {output_filename}")
                    
                else:
                    print(f"❌ Error: No JSON output found from server for this job.")

if __name__ == "__main__":
    asyncio.run(run_batch_ocr())