import google.generativeai as genai
import yt_dlp
import requests
from fpdf import FPDF
import os
import time
import youtube_transcript_api as yta # FIX: Robust import method
import datetime
import pytz

# ==========================================
# 1. CONFIGURATION
# ==========================================
GEMINI_KEY = os.environ.get("GEMINI_KEY")
BOT_TOKEN  = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

# Read the link from the file
try:
    with open("video_link.txt", "r") as f:
        YOUTUBE_URL = f.read().strip()
except FileNotFoundError:
    print("❌ Error: video_link.txt not found!")
    exit(1)

print(f"🎯 Target Video: {YOUTUBE_URL}")

# ==========================================
# 2. THE LISTENER (Transcript API)
# ==========================================
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-lite-preview-09-2025")

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
        # FIX: Calling the method correctly on the imported class
        transcript_list = yta.YouTubeTranscriptApi.get_transcript(video_id) 
        full_text = " ".join([line['text'] for line in transcript_list])
        print(f"✅ Transcript Extracted! ({len(full_text)} characters)")
        return full_text
    except Exception as e:
        print(f"❌ Error: Transcript API Failed. {e}")
        return None

# ==========================================
# 3. THE BRAIN (Structure Generator)
# ==========================================
def generate_notes(video_text):
    print("2. Generating Structured Notes...")
    prompt = f"""
    You are an expert student taking revision notes for the UPSC CDS exam.
    TASK: Convert the following raw lecture transcript into a highly structured, dense study guide.
    
    CRITICAL INSTRUCTIONS:
    1. Organize the content using **Headings** (bold text).
    2. Use **Bullet Points** extensively for key facts and lists.
    3. Extract and present **Formulas or Definitions** clearly on separate lines.
    
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
    
    # Title with date
    IST = pytz.timezone('Asia/Kolkata')
    date_str = datetime.datetime.now(IST).strftime("%d %B %Y")
    
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, txt=f"CDS Revision Notes - {date_str}", ln=True, align='C')
    pdf.ln(10)
    
    # Content
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
    # Check if running locally without key (optional warning)
    if "PASTE_YOUR_GEMINI_KEY_HERE" in GEMINI_KEY:
        print("🛑 WARNING: Please replace the placeholder key.")

    # 1. Get Text
    lecture_text = get_transcript(YOUTUBE_URL)
    
    if lecture_text:
        # 2. Generate Notes
        notes = generate_notes(lecture_text)
        
        if notes:
            # 3. Create & Send PDF
            pdf_file = create_pdf(notes)
            send_pdf(pdf_file)
        else:
            print("🛑 STOPPING: Gemini failed to generate notes.")
    else:
        print("🛑 STOPPING: Could not get YouTube transcript.")
        
