import asyncio
import base64
import cv2
import numpy as np
import sys
import json
import os
from PIL import Image
from transformers import pipeline
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

# --- 1. Initialization ---
print("Initializing Hugging Face TrOCR model (microsoft/trocr-small-handwritten)...", file=sys.stderr)
ocr_pipeline = pipeline("image-to-text", model="microsoft/trocr-small-handwritten")
print("✅ TrOCR model ready!", file=sys.stderr)

# Initialize MCP server
app = Server("trocr-server")

# Create a folder to store cropped debug images
os.makedirs("debug_crops", exist_ok=True)

# --- 2. Recognition Function (TrOCR Version) ---
def recognize_from_rois_trocr(image_base64: str, rois: list, padding: int = 10) -> list:
    """
    Crops and recognizes handwritten text from ROIs using Hugging Face TrOCR.
    """
    try:
        nparr = np.frombuffer(base64.b64decode(image_base64), np.uint8)
        color_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if color_img is None:
            raise ValueError("Could not decode image")
        
        (img_h, img_w) = color_img.shape[:2]
        recognized_answers = []

        for i, box in enumerate(rois):
            x, y, w, h = box

            # Apply small padding (helps avoid cutoff)
            y_start = max(0, y - padding)
            y_end = min(img_h, y + h + padding)
            x_start = max(0, x - padding)
            x_end = min(img_w, x + w + padding)

            crop = color_img[y_start:y_end, x_start:x_end]

            # Save debug crop
            crop_filename = f"debug_crops/roi_{i+1}.png"
            cv2.imwrite(crop_filename, crop)

            if crop.size == 0:
                recognized_answers.append("")
                print(f"  ROI {i+1}: Empty crop, skipping.", file=sys.stderr)
                continue

            # Convert to RGB PIL Image
            pil_image = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))

            # Run TrOCR
            prediction = ocr_pipeline(pil_image)
            text = prediction[0]["generated_text"].strip()

            recognized_answers.append(text)
            print(f"  ROI {i+1}: Found '{text}'", file=sys.stderr)

        return recognized_answers

    except Exception as e:
        print(f"TrOCR processing failed: {e}", file=sys.stderr)
        raise ValueError(f"TrOCR processing failed: {str(e)}")

# --- 3. MCP Tool Definition and Caller ---
@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="read_text_in_rois",
            description="Reads handwritten text from specific ROIs of a base64-encoded image using Hugging Face TrOCR.",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_base64": {"type": "string"},
                    "rois": {
                        "type": "array",
                        "items": {"type": "array", "items": {"type": "integer"}}
                    }
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

            print(f"--- Tool 'read_text_in_rois' (TrOCR Model) called with {len(rois)} ROIs ---", file=sys.stderr)

            recognized_list = recognize_from_rois_trocr(image_data, rois)

            # Convert list of answers into {"Q1": "a", "Q2": "6", ...}
            answers_dict = {f"Q{i+1}": ans for i, ans in enumerate(recognized_list)}

            output_json = json.dumps(answers_dict)

            return [
                TextContent(type="text", text=f"Successfully processed {len(rois)} regions."),
                TextContent(type="text", text=output_json)
            ]
        except Exception as e:
            return [
                TextContent(type="text", text=f"Error recognizing text: {str(e)}")
            ]

    raise ValueError(f"Unknown tool: {name}")

async def main():
    """Run the TrOCR server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
