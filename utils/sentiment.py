
import requests
from textblob import TextBlob
from bs4 import BeautifulSoup
import streamlit as st

@st.cache_data(ttl=600)
def fetch_news_sentiment():
    """
    Fetch crypto news from a source (simulated or real simple scraper) and analyze sentiment.
    This is a simplified example. For real production, use a News API.
    Here we will scrape CoinDesk (example) or CryptoPanic. 
    Note: Scraping might be brittle. We'll use a safer approach:
    Simulate fetching from a public RSS feed or simple API if available.
    For this demo, let's try to fetch headlines from a crypto news aggregate RSS if possible, 
    or just scraping titles from a popular site if allowed.
    
    Let's use a mock or simple request for now to avoid blocking.
    Actually, let's try to get data from Yahoo Finance News RSS for BTC.
    """
    
    rss_url = "https://finance.yahoo.com/rss/headline?s=BTC-USD"
    
    try:
        response = requests.get(rss_url, timeout=5)
        soup = BeautifulSoup(response.content, features="xml")
        items = soup.find_all('item')
        
        news_items = []
        total_polarity = 0
        
        for item in items[:10]:
            title = item.title.text
            link = item.link.text
            pub_date = item.pubDate.text
            
            blob = TextBlob(title)
            sentiment_score = blob.sentiment.polarity
            total_polarity += sentiment_score
            
            sentiment_label = "Neutral"
            if sentiment_score > 0.1:
                sentiment_label = "Positive"
            elif sentiment_score < -0.1:
                sentiment_label = "Negative"
                
            news_items.append({
                'title': title,
                'link': link,
                'published': pub_date,
                'sentiment': sentiment_label,
                'score': sentiment_score
            })
            
        avg_sentiment = total_polarity / len(news_items) if news_items else 0
        
        overall_sentiment = "Neutral"
        if avg_sentiment > 0.1:
            overall_sentiment = "Positive"
        elif avg_sentiment < -0.1:
            overall_sentiment = "Negative"
            
        return overall_sentiment, avg_sentiment, news_items
        
    except Exception as e:
        print(f"Error fetching news: {e}")
        return "Neutral", 0, []
