# main.py
print("--- Script starting ---")

import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai
from newsapi import NewsApiClient
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# --- CONFIGURATION ---
print("Loading .env file...")
load_dotenv()

# Get API keys from the .env file
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
YOUR_EMAIL_ADDRESS = os.getenv('YOUR_EMAIL_ADDRESS')

# --- DEBUG CHECKS ---
print(f"NEWS_API_KEY loaded: {bool(NEWS_API_KEY)}")
print(f"GEMINI_API_KEY loaded: {bool(GEMINI_API_KEY)}")

if not all([NEWS_API_KEY, GEMINI_API_KEY]):
    print("\nError: A required API key is missing from the .env file.")
    sys.exit()

# Configure the Gemini API client
print("Configuring API clients...")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro-latest')
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

# Define the topic for our briefing
TOPIC = 'Liverpool FC'

# --- 1. FETCH NEWS ARTICLES ---
def fetch_news(topic):
    """Fetches the top 5 news articles for a given topic."""
    print(f"Fetching top 5 news articles for '{topic}'...")
    try:
        top_headlines = newsapi.get_everything(q=f'"{topic}"', language='en', sort_by='publishedAt', page_size=5)
        return top_headlines.get('articles', [])
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []

# --- 2. SUMMARIZE ARTICLES WITH AI ---
def summarize_with_ai(articles, topic):
    """Sends articles to Gemini and gets a one-paragraph summary."""
    if not articles:
        return "Could not generate a summary because no articles were found."
    print("Sending articles to Gemini 1.5 Pro for summarization...")
    articles_text = ""
    for article in articles:
        articles_text += f"- \"{article.get('title', 'N/A')}\" (Source: {article.get('source', {}).get('name', 'N/A')})\n"
    prompt = f"You are a world-class sports news analyst. Summarize the key events related to {topic} from these headlines into one cohesive paragraph (max 120 words):\n\n{articles_text}"
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating AI summary: {e}"

# --- 3. SEND EMAIL BRIEFING ---
def send_email_briefing(summary, articles):
    """Formats and sends the final briefing via email using SendGrid."""
    if not YOUR_EMAIL_ADDRESS or not SENDGRID_API_KEY:
        print("\nEmail credentials not found in .env file. Skipping email and printing to console.")
        return False
    print(f"Attempting to send email briefing to {YOUR_EMAIL_ADDRESS}...")
    headlines_html = "".join([f"<li><a href='{a.get('url','#')}'>{a.get('title','N/A')}</a> ({a.get('source',{}).get('name','N/A')})</li>" for a in articles])
    summary_html = summary.replace("\n", "<br>")
    html_content = f"""
    <html><body><div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #ddd; padding: 20px;">
        <h2>The Kop AI Daily Briefing</h2><p><strong>AI-Generated Summary:</strong></p><p>{summary_html}</p><hr>
        <p><strong>Today's Top Headlines:</strong></p><ul>{headlines_html}</ul>
    </div></body></html>"""
    
    # CORRECTED: Use your verified email as the "from" address
    message = Mail(
        from_email=YOUR_EMAIL_ADDRESS,
        to_emails=YOUR_EMAIL_ADDRESS,
        subject='Your Liverpool FC Briefing for Today',
        html_content=html_content
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent successfully! Status code: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# --- 4. MAIN EXECUTION BLOCK ---
def main():
    """The main function to run the daily briefing script."""
    print("\n--- Main function starting ---")
    articles = fetch_news(TOPIC)
    if not articles:
        print("Could not retrieve any news articles. Exiting.")
        return

    ai_summary = summarize_with_ai(articles, TOPIC)
    if "Error" in str(ai_summary):
        print(ai_summary)
        return

    email_sent = send_email_briefing(ai_summary, articles)
    if not email_sent:
        print("\n--- AI-Generated Summary (Console Fallback) ---")
        print(ai_summary)
    print("\n--- End of Briefing ---")

if __name__ == "__main__":
    main()