# main.py

import os
import google.generativeai as genai
from dotenv import load_dotenv
from newsapi import NewsApiClient
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# --- CONFIGURATION ---
# Load the environment variables from the .env file
load_dotenv()

# Get API keys from the .env file
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
YOUR_EMAIL_ADDRESS = os.getenv('YOUR_EMAIL_ADDRESS')

# Configure the Gemini API client
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro-latest')

# Configure the NewsAPI client
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

# Define the topic for our briefing
TOPIC = 'Liverpool FC'

# --- 1. FETCH NEWS ARTICLES ---
def fetch_news(topic):
    """Fetches the top 5 news articles for a given topic."""
    print(f"Fetching top 5 news articles for '{topic}'...")
    try:
        top_headlines = newsapi.get_everything(
            q=f'"{topic}"',
            language='en',
            sort_by='publishedAt',
            page_size=5
        )
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
    for i, article in enumerate(articles):
        source_name = article.get('source', {}).get('name', 'N/A')
        articles_text += f"Article {i+1}: \"{article.get('title', 'N/A')}\" (Source: {source_name})\n"

    prompt = (
        f"You are a world-class sports news analyst for an executive briefing. "
        f"Your task is to provide a clear, concise, and neutral summary of the key events related to {topic}, "
        f"based on the following news headlines. Synthesize the information into a single, cohesive paragraph "
        f"of no more than 120 words. Focus only on verifiable facts and key developments mentioned in the titles.\n\n"
        f"--- NEWS ARTICLES ---\n{articles_text}"
    )
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating AI summary: {e}"

# --- 3. SEND EMAIL BRIEFING (CORRECTED) ---
def send_email_briefing(summary, articles):
    """Formats and sends the final briefing via email using SendGrid."""
    if not YOUR_EMAIL_ADDRESS or not SENDGRID_API_KEY:
        print("\nEmail credentials not found in .env file. Skipping email.")
        return False

    print(f"Sending email briefing to {YOUR_EMAIL_ADDRESS}...")
    
    # Build the list of headlines as HTML list items
    headlines_html = ""
    for article in articles:
        title = article.get('title', 'N/A')
        url = article.get('url', '#')
        source = article.get('source', {}).get('name', 'N/A')
        headlines_html += f"<li><a href='{url}'>{title}</a> ({source})</li>"

    # Sanitize the summary for HTML by replacing newlines with <br> tags
    summary_html = summary.replace("\n", "<br>")

    # Assemble the final HTML using a clean f-string
    html_content = f"""
    <html>
    <body>
        <div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #ddd; padding: 20px;">
            <h2>The Kop AI Daily Briefing</h2>
            <p><strong>AI-Generated Summary:</strong></p>
            <p>{summary_html}</p>
            <hr>
            <p><strong>Today's Top Headlines:</strong></p>
            <ul>
                {headlines_html}
            </ul>
        </div>
    </body>
    </html>
    """

    message = Mail(
        from_email='briefing@thekopai.com',
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


# --- 4. RUN THE APPLICATION ---
def main():
    """The main function to run the daily briefing script."""
    print(f"--- The Kop AI Daily Briefing ---")
    
    articles = fetch_news(TOPIC)

    if articles:
        ai_summary = summarize_with_ai(articles, TOPIC)
        
        email_sent = send_email_briefing(ai_summary, articles)

        if not email_sent:
            print("\n--- AI-Generated Summary (Console Fallback) ---")
            print(ai_summary)
            print("\n--- Today's Top Headlines (Console Fallback) ---")
            for article in articles:
                print(f"- {article.get('title')} ({article.get('source', {}).get('name', 'N/A')})")
    else:
        print("\nCould not retrieve any news articles.")

    print("\n--- End of Briefing ---")


if __name__ == "__main__":
    main()
