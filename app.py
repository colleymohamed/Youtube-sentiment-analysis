"""Streamlit interface for YouTube comment sentiment analysis."""

import os

import pandas as pd
import streamlit as st

from sentiment import analyze_comments
from youtube_client import YouTubeAPIError, extract_video_id, fetch_comments


st.set_page_config(page_title="YouTube Comment Sentiment", page_icon="💬", layout="wide")
st.title("YouTube Comment Sentiment")
st.write("Explore the tone of a video's public comments with VADER, AFINN, and TextBlob.")


def get_api_key() -> str:
    """Read the key from Streamlit secrets or the process environment."""
    try:
        return st.secrets.get("YOUTUBE_API_KEY", "") or os.environ.get("YOUTUBE_API_KEY", "")
    except (FileNotFoundError, RuntimeError):
        return os.environ.get("YOUTUBE_API_KEY", "")


with st.sidebar:
    st.header("Analysis settings")
    max_comments = st.number_input(
        "Maximum comments", min_value=100, max_value=5000, value=500, step=100,
        help="Comments are fetched in pages of up to 100. Larger requests use more API quota.",
    )
    st.caption("Only top-level comments are included. Comments are not stored by this app.")

with st.form("analyze_video"):
    video_url = st.text_input("YouTube video URL or ID", placeholder="https://www.youtube.com/watch?v=…")
    submitted = st.form_submit_button("Analyze comments", type="primary")

if submitted:
    api_key = get_api_key()
    if not api_key:
        st.error("YouTube API key not configured. Add YOUTUBE_API_KEY to .streamlit/secrets.toml or your environment.")
        st.stop()

    try:
        video_id = extract_video_id(video_url)
        with st.spinner("Fetching comments and analyzing sentiment…"):
            comments = fetch_comments(api_key, video_id, int(max_comments))
            results = analyze_comments(comments)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
    except YouTubeAPIError as exc:
        st.error(str(exc))
        st.stop()

    if results.empty:
        st.warning("No comments were found for this video. Comments may be disabled or unavailable.")
        st.stop()

    st.session_state["analysis"] = results
    st.session_state["video_id"] = video_id

if "analysis" in st.session_state:
    results = st.session_state["analysis"]
    st.subheader(f"Results for video `{st.session_state['video_id']}`")

    col1, col2, col3 = st.columns(3)
    col1.metric("Comments analyzed", f"{len(results):,}")
    col2.metric("Positive (VADER)", f"{(results['VADER Sentiment'] == 'Positive').mean():.0%}")
    col3.metric("Negative (VADER)", f"{(results['VADER Sentiment'] == 'Negative').mean():.0%}")

    left, right = st.columns(2)
    with left:
        st.markdown("#### Sentiment by model")
        counts = pd.DataFrame({
            model: results[f"{model} Sentiment"].value_counts().reindex(
                ["Positive", "Neutral", "Negative"], fill_value=0
            )
            for model in ("VADER", "AFINN", "TextBlob")
        })
        st.bar_chart(counts)
    with right:
        st.markdown("#### VADER score over time")
        dated = results.dropna(subset=["Published at"]).copy()
        if dated.empty:
            st.caption("No usable publication dates were returned.")
        else:
            daily = dated.set_index("Published at").resample("D")["VADER Compound"].mean().dropna()
            st.line_chart(daily)

    st.markdown("#### Analyzed comments")
    st.dataframe(results, use_container_width=True, hide_index=True)
    st.download_button(
        "Download results as CSV",
        data=results.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"youtube_sentiment_{st.session_state['video_id']}.csv",
        mime="text/csv",
    )
