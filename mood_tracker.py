import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
import os
import sqlite3

# Configure the API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize the model
model = genai.GenerativeModel('gemini-pro')

st.title('Mood Tracker')

# Database setup
def init_db():
    conn = sqlite3.connect('mood_tracker.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS entries
                 (date TEXT, entry TEXT, sentiment INTEGER)''')
    conn.commit()
    conn.close()

def add_entry(date, entry, sentiment):
    conn = sqlite3.connect('mood_tracker.db')
    c = conn.cursor()
    c.execute("INSERT INTO entries (date, entry, sentiment) VALUES (?, ?, ?)",
              (date, entry, sentiment))
    conn.commit()
    conn.close()

def get_entries():
    conn = sqlite3.connect('mood_tracker.db')
    entries = pd.read_sql_query("SELECT * FROM entries ORDER BY date DESC", conn)
    conn.close()
    return entries

# Initialize database
init_db()

def analyze_sentiment(text):
    prompt = f"Analyze the sentiment of the following journal entry and rate it on a scale of 1 to 5, where 1 is very negative and 5 is very positive. Only return the number:\n\n{text}"
    response = model.generate_content(prompt)
    return int(response.text.strip())

# Date selection
selected_date = st.date_input("Select date for your journal entry", date.today())

# Journal entry input
entry = st.text_area("Write your journal entry:")
if st.button("Save Entry"):
    if entry:
        sentiment = analyze_sentiment(entry)
        add_entry(selected_date.strftime("%Y-%m-%d"), entry, sentiment)
        st.success("Entry saved and analyzed!")
    else:
        st.warning("Please write an entry before saving.")

# Display mood trend
entries_df = get_entries()
if not entries_df.empty:
    entries_df['date'] = pd.to_datetime(entries_df['date'])
    # Filter for the last 7 days
    seven_days_ago = datetime.now() - timedelta(days=7)
    filtered_entries = entries_df[entries_df['date'] >= seven_days_ago]
    fig = px.line(filtered_entries, x="date", y="sentiment", title="Mood Trend Over the Last 7 Days")
    fig.update_xaxes(tickformat='%Y-%m-%d', dtick="D1")  # Update to show only the date
    st.plotly_chart(fig)

# Display past entries
st.subheader("Past Entries")
for _, row in entries_df.iterrows():
    st.text(f"Date: {row['date'].date()}")
    st.text(f"Sentiment: {row['sentiment']}/5")
    st.text(row['entry'])
    st.divider()
