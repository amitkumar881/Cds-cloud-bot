import google.generativeai as genai
import yt_dlp
import requests
from fpdf import FPDF
import os
import time

# ==========================================
# 1. SETUP KEYS & INPUT
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
# 2. THE BRAIN (Gemini 2.5 Lite)
# ==========================================
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-lite-preview-09-2025")

def download_lecture(url):
    print("1. Downloading video...")
    filename = "lecture_vid.mp4"
    # Download tiny version to save speed
    ydl_opts = {'format': 'worst[ext=mp4]', 'outtmpl': filename, 'quiet': True}
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("✅ Download Complete.")
        return filename
    except Exception as e:
        print(f"❌ Download Failed: {e}")
        return None

def analyze_lecture(video_path):
    print("2. Uploading to Gemini...")
    video_file = genai.upload_file(path=video_path)
    
    # Wait for processing
    while video_file.state.name == "PROCESSING":
        time.sleep(5)
        video_file = genai.get_file(video_file.name)

    print("3. Generating Notes...")
    prompt = """
    You are an expert student taking notes.
    Task: Create a detailed 'Lecture Revision Sheet' from this video.
    
    Instructions:
    - Capture every formula, diagram label, and definition written on the board.
    - Summarize the teacher's spoken explanations.
    - Organize with clear Headings.
    """
    
    try:
        response = model.generate_content([video_file, prompt])
        return response.text.replace("**", "").replace("*", "").replace("#", "")
    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        return None

def create_pdf(text):
    print("4. Creating PDF...")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, txt="Daily Lecture Notes", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    
    safe_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 7, txt=safe_text)
    
    filename = "Lecture_Notes.pdf"
    pdf.output(filename)
    return filename

def send_pdf(filename):
    print("5. Sending to Telegram...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    with open(filename, 'rb') as f:
        payload = {"chat_id": CHANNEL_ID, "caption": f"🔥 **Notes for:** {YOUTUBE_URL}"}
        files = {"document": f}
        requests.post(url, data=payload, files=files)
        print("🚀 SUCCESS! PDF Sent.")

if __name__ == "__main__":
    vid = download_lecture(YOUTUBE_URL)
    if vid:
        notes = analyze_lecture(vid)
        if notes:
            pdf = create_pdf(notes)
            send_pdf(pdf)
          
