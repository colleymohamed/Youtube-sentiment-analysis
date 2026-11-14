"""Small client for retrieving public top-level YouTube comments."""

import re
from urllib.parse import parse_qs, urlparse

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class YouTubeAPIError(Exception):
    """A readable error returned while communicating with YouTube."""


def extract_video_id(value: str) -> str:
    value = value.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value

    parsed = urlparse(value if "://" in value else f"https://{value}")
    host = parsed.netloc.lower().split(":")[0]
    video_id = ""
    if host in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.strip("/").split("/")[0]
    elif host.endswith("youtube.com"):
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        elif parsed.path.startswith(("/shorts/", "/embed/", "/live/")):
            video_id = parsed.path.split("/")[2]

    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError("Enter a valid YouTube video URL or 11-character video ID.")
    return video_id


def fetch_comments(api_key: str, video_id: str, max_comments: int) -> list[dict]:
    """Fetch up to max_comments top-level comments, in newest-first order."""
    youtube = build("youtube", "v3", developerKey=api_key, cache_discovery=False)
    comments: list[dict] = []
    page_token = None

    try:
        while len(comments) < max_comments:
            page_size = min(100, max_comments - len(comments))
            response = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                textFormat="plainText",
                order="time",
                maxResults=page_size,
                pageToken=page_token,
            ).execute()
            for item in response.get("items", []):
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "Comment": snippet.get("textDisplay", ""),
                    "Published at": snippet.get("publishedAt"),
                    "Likes": snippet.get("likeCount", 0),
                    "Author": snippet.get("authorDisplayName", ""),
                })
            page_token = response.get("nextPageToken")
            if not page_token or not response.get("items"):
                break
    except HttpError as exc:
        status = getattr(exc.resp, "status", None)
        if status == 403:
            detail = "YouTube denied the request. Check that the API key is valid and YouTube Data API v3 is enabled; comments may also be disabled."
        elif status == 404:
            detail = "The video was not found or is not available."
        else:
            detail = f"YouTube API request failed (HTTP {status or 'unknown'}). Check your API quota and key settings."
        raise YouTubeAPIError(detail) from exc
    except (KeyError, TypeError) as exc:
        raise YouTubeAPIError("YouTube returned an unexpected comments response.") from exc

    return comments
