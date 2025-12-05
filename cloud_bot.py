import google.generativeai as genai
import requests
from fpdf import FPDF
import os

# ==========================================
# 1. GET KEYS FROM CLOUD VAULT
# ==========================================
GEMINI_KEY = os.environ.get("GEMINI_KEY")
BOT_TOKEN  = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

# ==========================================
# 2. THE BRAIN (Gemini 2.5 Lite)
# ==========================================
genai.configure(api_key=GEMINI_KEY)

# UPDATED: Back to the ONLY model you have access to.
# Since you have a new key, this should work without Error 429.
model = genai.GenerativeModel("gemini-2.5-flash-lite-preview-09-2025")

def generate_exam():
    print("1. Asking Gemini to create the CDS 2025 paper...")
    prompt = """
    You are a senior paper setter for the UPSC CDS Exam. Create a 'Daily Practice Paper' with exactly 25 Questions.
    
    The paper must cover exactly these 5 topics (5 questions each):
    1. Discourse Markers
    2. Parts of Speech (Underlined word identification)
    3. Idioms and Phrases
    4. Ordering of Sentences (PQRS)
    5. Prepositions
    
    FORMATTING RULES FOR PDF:
    - Do NOT use any markdown (no bold stars, no italics).
    - Use standard numbering (1., 2., 3...).
    - SECTION A: The 25 Questions.
    - SECTION B: The Answer Key & Explanations (at the very bottom).
    """
    try:
        response = model.generate_content(prompt)
        if not response.text:
            print("❌ FAILURE: Google gave empty text.")
            return None
        return response.text.replace("**", "").replace("*", "").replace("#", "")
        
    except Exception as e:
        print(f"❌ GEMINI ERROR: {e}")
        return None

# ==========================================
# 3. THE PDF MAKER
# ==========================================
def create_pdf(text):
    print("2. Creating PDF...")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, txt="CDS Daily Practice Sheet", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    
    safe_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=safe_text)
    
    filename = "CDS_Practice.pdf"
    pdf.output(filename)
    return filename

# ==========================================
# 4. THE TELEGRAM SENDER
# ==========================================
def send_pdf(filename):
    print("3. Sending to Telegram...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    
    with open(filename, 'rb') as f:
        payload = {"chat_id": CHANNEL_ID, "caption": "🔥 **Daily CDS 2025 Practice Set**"}
        files = {"document": f}
        
        resp = requests.post(url, data=payload, files=files)
        
        if resp.status_code == 200:
            print("🚀 SUCCESS! PDF Sent.")
        else:
            print(f"❌ TELEGRAM ERROR: {resp.text}")

if __name__ == "__main__":
    text = generate_exam()
    if text:
        pdf = create_pdf(text)
        send_pdf(pdf)
    else:
        print("🛑 STOPPING: Could not generate quiz due to Google Error.")
        
