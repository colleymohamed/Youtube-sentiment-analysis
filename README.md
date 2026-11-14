# Youtube-sentiment-analysis

A small data app that turns public YouTube comments into an interactive sentiment report. Paste a video URL, compare three sentiment analyzers, explore trends, and download the results.

**Live demo:** [sentiment-analysis-colley.streamlit.app](https://sentiment-analysis-colley.streamlit.app)

## What it does

- Fetches up to a selected number of public top-level comments with the YouTube Data API v3.
- Scores comments with VADER, AFINN, and TextBlob, showing each model's results separately.
- Displays sentiment summaries, comment-level scores, and a timeline chart.
- Exports analyzed comments as CSV.

## Built with

Python · Streamlit · YouTube Data API v3 · pandas · VADER · AFINN · TextBlob

The project separates the app interface, YouTube data fetching, and sentiment scoring into `app.py`, `youtube_client.py`, and `sentiment.py`.

