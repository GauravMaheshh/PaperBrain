import asyncio
import base64
import json
import os
import cv2  # Import OpenCV
import numpy as np
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# --- 1. CONFIGURE YOUR TEST DATA HERE ---

# ❗️ Update these paths to match your files
BLANK_IMAGE_PATH = "../preprocessor/question_paper_templates/template_1_question.jpg"
MARKED_IMAGE_PATH = "../preprocessor/aligned_outputs/aligned_scan_answers.jpg" 

# ❗️ These are the ROIs from your Agent 1 script (they are for the RESIZED image)
rois_to_test = [
    [1389, 916, 164, 69],
    [1399, 1107, 151, 81],
    [1414, 1271, 131, 65],
    [1399, 1401, 151, 83],
    [1385, 1572, 152, 62],
    [1402, 1932, 115, 28],
    [1009, 2085, 171, 61]
]

# ----------------------------------------

# Define the server to launch (Agent 2)
agent_2_server = StdioServerParameters(
    command="python",
    args=["ocr_server.py"] 
)

async def run_test():
    """
    Loads BOTH images, RESIZES the marked one, launches Agent 2,
    and then calls the tool.
    """
    
    # --- 2. PREPARE INPUTS (This is the critical fix) ---
    print(f"--- Client: Loading blank image from {BLANK_IMAGE_PATH} ---")
    img_blank = cv2.imread(BLANK_IMAGE_PATH)
    if img_blank is None:
        print(f"Error: Blank image not found at '{BLANK_IMAGE_PATH}'")
        return

    print(f"--- Client: Loading marked image from {MARKED_IMAGE_PATH} ---")
    img_filled = cv2.imread(MARKED_IMAGE_PATH)
    if img_filled is None:
        print(f"Error: Marked image not found at '{MARKED_IMAGE_PATH}'")
        return

    # Get target dimensions from the blank image
    h, w = img_blank.shape[:2]
    
    print(f"--- Client: Resizing marked image to {w}x{h} (to match blank) ---")
    # Resize the marked image, just like Agent 1 did
    img_filled_resized = cv2.resize(img_filled, (w, h))

    # Now, encode the *RESIZED* image to base64
    _, buffer = cv2.imencode('.jpg', img_filled_resized)
    image_base64_to_test = base64.b64encode(buffer).decode('utf-8')
    
    print("--- Client: Resized image encoded successfully. ---")
    
    
    # --- 3. LAUNCH AND CALL AGENT 2 ---
    print(f"--- Client: Launching server 'python ocr_server.py' ---")
    
    async with stdio_client(agent_2_server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print(f"--- Client: Server initialized. Calling tool 'read_text_in_rois' ---")
            
            # Call the tool with the RESIZED base64 string
            result = await session.call_tool(
                "read_text_in_rois",
                {
                    "image_base64": image_base64_to_test,
                    "rois": rois_to_test
                }
            )
            
            # --- 4. SHOW THE OUTPUT ---
            print("\n--- Client: Received Result from Server ---")
            
            final_json_text = None
            for item in result.content:
                if item.type == 'text':
                    print(f"  > Server message: '{item.text}'")
                    if item.text.startswith('{'):
                        final_json_text = item.text
            
            # --- *** START CHANGE *** ---
            if final_json_text:
                # 1. This is the dictionary from Agent 2: {"Q1": "c", "Q2": "6", ...}
                answers_dict = json.loads(final_json_text)

                # 2. Define the student_info (hard-coded for this test)
                #    In a real system, you'd get this by running OCR on other ROIs.
                student_info = {
                    "name": "STUDENT_NAME_HERE", # Placeholder
                    "roll_no": "ROLL_NO_HERE"     # Placeholder
                }
                
                # 3. Combine them into the final desired format
                final_output = {
                    "student_info": student_info,
                    "answers": answers_dict
                }

                # 4. Print the beautiful, final JSON
                print("\n" + "="*30)
                print("  FINAL EVALUATION JSON")
                print("="*30)
                # Use json.dumps with indent=4 for pretty-printing
                print(json.dumps(final_output, indent=4))
                
            # --- *** END CHANGE *** ---
            else:
                print("--- Error: No JSON output found from server. ---")

if __name__ == "__main__":
    asyncio.run(run_test())