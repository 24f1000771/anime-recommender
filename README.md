# AniRec 🎌

A full-stack anime and manga recommendation platform built with Flask and the AniList GraphQL API.

## Live Demo
[coming soon]

## What it does

- **Search & Recommend** — search any anime, manga, manhwa or manhua and get recommendations based on genre similarity and average score
- **Browse** — filter anime by genre tags and format with a live search bar
- **Ongoing** — real-time feed of currently airing anime sorted by popularity
- **Random** — discover a highly rated anime you've never seen, sequels filtered out automatically
- **Mood Search** — describe what you feel like watching in plain English and get AI-powered recommendations (coming soon)

## Tech Stack

- **Backend** — Python, Flask
- **Data** — AniList GraphQL API (live data, no static dataset)
- **Recommendation Engine** — Jaccard similarity on genre vectors, blended with normalized average score (70/30 split)
- **Frontend** — HTML, CSS, JavaScript
- **AI Layer** — Groq (Llama 3) for mood-based query parsing (coming soon)

## How the recommendation engine works

Each anime is represented by its genre set. When you search a title:
1. AniList returns that title's genres
2. We fetch the top 50 anime sharing those genres
3. Jaccard similarity measures genre overlap between source and each candidate
4. Final score = (similarity × 0.7) + (normalized average score × 0.3)
5. Results sorted by final score

## Supported media types

- Anime
- Manga (Japanese)
- Manhwa (Korean)
- Manhua (Chinese)

## Setup

```bash
git clone https://github.com/24f1000771/anime-recommender.git
cd anime-recommender
pip install -r requirements.txt
```

Create a `.env` file:
