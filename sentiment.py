"""Comment sentiment scoring with VADER, AFINN, and TextBlob."""

import pandas as pd
from afinn import Afinn
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


def _label(score: float, negative: float, positive: float) -> str:
    if score >= positive:
        return "Positive"
    if score <= negative:
        return "Negative"
    return "Neutral"


def analyze_comments(comments: list[dict]) -> pd.DataFrame:
    """Score each original comment while retaining punctuation and casing."""
    vader = SentimentIntensityAnalyzer()
    afinn = Afinn()
    rows = []

    for comment in comments:
        text = comment.get("Comment", "")
        vader_score = vader.polarity_scores(text)["compound"]
        afinn_score = float(afinn.score(text))
        textblob_score = float(TextBlob(text).sentiment.polarity)
        row = dict(comment)
        row.update({
            "VADER Compound": vader_score,
            "VADER Sentiment": _label(vader_score, -0.05, 0.05),
            "AFINN Score": afinn_score,
            "AFINN Sentiment": _label(afinn_score, -1, 1),
            "TextBlob Polarity": textblob_score,
            "TextBlob Sentiment": _label(textblob_score, -0.05, 0.05),
        })
        rows.append(row)

    columns = [
        "Published at", "Author", "Likes", "Comment",
        "VADER Compound", "VADER Sentiment", "AFINN Score", "AFINN Sentiment",
        "TextBlob Polarity", "TextBlob Sentiment",
    ]
    results = pd.DataFrame(rows)
    if results.empty:
        return pd.DataFrame(columns=columns)
    results["Published at"] = pd.to_datetime(results["Published at"], errors="coerce", utc=True)
    return results.reindex(columns=columns)
