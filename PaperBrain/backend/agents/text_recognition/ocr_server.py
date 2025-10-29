import asyncio
import base64
import cv2
import numpy as np
import sys
import json
import os

# --- 1. Initialization ---
try:
    import easyocr
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("FATAL ERROR: easyocr not installed. Run: pip install easyocr", file=sys.stderr)
    sys.exit(1)

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

# Initialize EasyOCR Reader once
reader = None
if OCR_AVAILABLE:
    try:
        print("Initializing EasyOCR reader...", file=sys.stderr)
        # Suppress stdout from easyocr
        original_stdout = sys.stdout
        sys.stdout = sys.stderr
        try:
            reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        finally:
            sys.stdout = original_stdout # Restore stdout
        print("EasyOCR ready!", file=sys.stderr)
    except Exception as e:
        print(f"Failed to initialize EasyOCR: {e}", file=sys.stderr)
        OCR_AVAILABLE = False

# This is the ONLY 'app' definition
app = Server("easyocr-server")

# Create a folder to store our debug images
os.makedirs("debug_crops", exist_ok=True)


# --- 2. The Recognition Function (EasyOCR Version) ---
# *** CHANGED PADDING FROM 10 to 5 ***
# This should help fix the "ca" error by not grabbing the box line.
def recognize_from_rois_easyocr(image_base64: str, rois: list, padding: int = 20) -> list:
    """
    Crops and recognizes text from ROIs using EasyOCR.
    """
    if not OCR_AVAILABLE or reader is None:
        raise RuntimeError("EasyOCR is not available or failed to initialize.")
        
    try:
        nparr = np.frombuffer(base64.b64decode(image_base64), np.uint8)
        # Load as a 3-channel COLOR image, which easyocr prefers
        color_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if color_img is None: raise ValueError("Could not decode image")
            
        (img_h, img_w) = color_img.shape[:2]
        recognized_answers = []

        for i, box in enumerate(rois):
            x, y, w, h = box
            
            # Apply padding
            y_start = max(0, y - padding)
            y_end = min(img_h, y + h + padding)
            x_start = max(0, x - padding)
            x_end = min(img_w, x + w + padding)
            
            # Crop the padded region from the COLOR image
            padded_crop = color_img[y_start:y_end, x_start:x_end]
            
            # --- Save debug image ---
            crop_filename = f"debug_crops/roi_{i+1}.png"
            cv2.imwrite(crop_filename, padded_crop)
            
            # --- Call EasyOCR ---
            # We give it the raw color crop
            result = reader.readtext(
                padded_crop, 
                detail=0,
                allowlist='abc023456789' # *** REMOVED REDUNDANT UPPERCASE ***
            )
            
            if result:
                # result is like ['b'], so we take the first item
                answer = result[0].lower().strip()
                recognized_answers.append(answer)
                print(f"  ROI {i+1}: Found '{answer}'", file=sys.stderr)
            else:
                # No text found
                recognized_answers.append("") # Append empty string
                print(f"  ROI {i+1}: Found no text", file=sys.stderr)
                
        return recognized_answers
        
    except Exception as e:
        print(f"EasyOCR processing failed: {e}", file=sys.stderr)
        raise ValueError(f"EasyOCR processing failed: {str(e)}")


# --- 3. The Tool Definition and Caller (Unchanged) ---
@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="read_text_in_rois",
            description="Reads text from a list of specific regions (ROIs) of a base64 image.",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_base64": {"type": "string"},
                    "rois": {"type": "array", "items": { "type": "array", "items": { "type": "integer" } }}
                },
                "required": ["image_base64", "rois"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    if name == "read_text_in_rois":
        try:
            image_data = arguments["image_base64"]
            rois = arguments["rois"]
            
            print(f"--- Tool 'read_text_in_rois' (EasyOCR Model) called with {len(rois)} ROIs ---", file=sys.stderr)
            
            recognized_list = recognize_from_rois_easyocr(image_data, rois)
            
            # --- *** START CHANGE *** ---
            # Convert the list of answers into the desired dictionary format
            answers_dict = {}
            for i, answer in enumerate(recognized_list):
                # Format as "Q1", "Q2", etc.
                answers_dict[f"Q{i+1}"] = answer
                
            # Now, the output JSON will be {"Q1": "c", "Q2": "6", ...}
            output_json = json.dumps(answers_dict)
            # --- *** END CHANGE *** ---

            return [
                TextContent(type="text", text=f"Successfully processed {len(rois)} regions."),
                TextContent(type="text", text=output_json) # This now contains the new JSON
            ]
        except Exception as e:
            return [
                TextContent(
                    type="text",
                    text=f"Error recognizing text: {str(e)}"
                )
            ]
    
    raise ValueError(f"Unknown tool: {name}")

async def main():
    """Run the server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())