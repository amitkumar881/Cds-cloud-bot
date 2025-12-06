import google.generativeai as genai
import requests
from fpdf import FPDF
from youtube_transcript_api import YouTubeTranscriptApi
import os

# ==========================================
# 1. CONFIGURATION
# ==========================================
GEMINI_KEY = os.environ.get("GEMINI_KEY")
BOT_TOKEN  = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

# --- PASTE THE LECTURE LINK HERE ---
YOUTUBE_URL = "https://www.youtube.com/watch?v=Hu4Yvq-g7_Y" 
# NOTE: Replace with your actual lecture link for testing!

# ==========================================
# 2. THE LISTENER (Transcript API)
# ==========================================
def get_video_id(url):
    """Extracts the video ID from the URL."""
    if "v=" in url: return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url: return url.split("youtu.be/")[1]
    return None

def get_transcript(url):
    print("1. Extracting text from YouTube Transcript API...")
    video_id = get_video_id(url)
    if not video_id: 
        print("❌ Error: Invalid YouTube URL")
        return None
        
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join([line['text'] for line in transcript_list])
        print(f"✅ Transcript Extracted! ({len(full_text)} characters)")
        return full_text
    except Exception as e:
        print(f"❌ Error: Transcript API Failed. {e}")
        return None

# ==========================================
# 3. THE BRAIN (Structure Generator)
# ==========================================
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash") # The stable model

def generate_notes(video_text):
    print("2. Generating Structured Notes...")
    
    # This prompt forces the AI to structure the content, making it look like notes
    prompt = f"""
    You are an expert student taking revision notes for the UPSC CDS exam.
    TASK: Convert the following raw lecture transcript into a highly structured, dense study guide.
    
    CRITICAL INSTRUCTIONS:
    1. Organize the content using **Headings** (bold text).
    2. Use **Bullet Points** extensively for key facts and lists.
    3. Extract and present **Formulas or Definitions** clearly on separate lines.
    4. Ensure the output is optimized for PDF reading (plain text, no complex markdown).
    
    TRANSCRIPT:
    {video_text}
    """
    
    try:
        response = model.generate_content(prompt)
        # Clean text for PDF compatibility
        return response.text.replace("**", "").replace("*", "").replace("#", "") 
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        return None

# ==========================================
# 4. PDF & TELEGRAM
# ==========================================
def create_pdf(text):
    print("3. Formatting PDF...")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, txt="CDS Detailed Revision Notes", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    
    safe_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 7, txt=safe_text)
    
    filename = "Structured_Notes.pdf"
    pdf.output(filename)
    return filename

def send_pdf(filename):
    print("4. Sending to Telegram...")
    url = f"https://api.telegram.org/bot{os.environ.get('BOT_TOKEN')}/sendDocument"
    
    with open(filename, 'rb') as f:
        payload = {"chat_id": os.environ.get("CHANNEL_ID"), "caption": f"🔥 **Structured Notes for Today's Lecture**\nLink: {YOUTUBE_URL}"}
        files = {"document": f}
        requests.post(url, data=payload, files=files)
        print("🚀 SUCCESS! PDF Sent.")

# ==========================================
# 5. EXECUTION
# ==========================================
if __name__ == "__main__":
    # Check if we're running locally or on Cloud
    if "PASTE_YOUR_GEMINI_KEY_HERE" in GEMINI_KEY:
        print("🛑 ERROR: Please update GEMINI_KEY with your actual key!")
        exit()

    # 1. Get Text
    lecture_text = get_transcript(YOUTUBE_URL)
    
    if lecture_text:
        # 2. Generate Notes
        notes = generate_notes(lecture_text)
        
        if notes:
            # 3. Create & Send PDF
            pdf_file = create_pdf(notes)
            send_pdf(pdf_file)
            
