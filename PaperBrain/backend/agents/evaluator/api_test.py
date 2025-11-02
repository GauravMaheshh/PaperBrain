import os, google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")  # or gemini-pro
response = model.generate_content("Hello Gemini!")
print(response.text)
