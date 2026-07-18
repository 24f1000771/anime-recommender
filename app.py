from flask import Flask, render_template, request, jsonify
import requests
import random
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

ANILIST_URL = "https://graphql.anilist.co"

def search_media(title, media_type):
    query = """
    query ($search: String, $type: MediaType) {
        Page(perPage: 5) {
            media(search: $search, type: $type, sort: SEARCH_MATCH) {
                id
                title { romaji english }
                genres
                averageScore
                popularity
                format
                status
                coverImage { large }
            }
        }
    }
    """
    variables = {"search": title, "type": media_type}
    response = requests.post(ANILIST_URL, json={"query": query, "variables": variables})

    if response.status_code != 200:
        return None, media_type

    data = response.json()
    if "errors" in data:
        return None, media_type

    results = data["data"]["Page"]["media"]

    if not results:
        fallback_type = "MANGA" if media_type == "ANIME" else "ANIME"
        variables["type"] = fallback_type
        response = requests.post(ANILIST_URL, json={"query": query, "variables": variables})
        data = response.json()
        if "errors" in data or not data["data"]["Page"]["media"]:
            return None, media_type
        return data["data"]["Page"]["media"], fallback_type

    return results, media_type

def fetch_recommendations_anime(genres, n=20):
    genre_filter = genres[:2] if len(genres) >= 2 else genres
    query = """
    query ($genres: [String]) {
        Page(perPage: 50) {
            media(genre_in: $genres, type: ANIME, sort: SCORE_DESC) {
                title { romaji english }
                genres
                averageScore
                popularity
                coverImage { large }
                format
                status
            }
        }
    }
    """
    variables = {"genres": genre_filter}
    response = requests.post(ANILIST_URL, json={"query": query, "variables": variables})
    if response.status_code != 200:
        return None
    data = response.json()
    if "errors" in data:
        return None
    return data["data"]["Page"]["media"]

def fetch_recommendations_manga(genres, country, n=20):
    genre_filter = genres[:2] if len(genres) >= 2 else genres
    query = """
    query ($genres: [String], $country: CountryCode) {
        Page(perPage: 50) {
            media(genre_in: $genres, type: MANGA, countryOfOrigin: $country, sort: SCORE_DESC) {
                title { romaji english }
                genres
                averageScore
                popularity
                coverImage { large }
                format
                status
            }
        }
    }
    """
    variables = {"genres": genre_filter, "country": country}
    response = requests.post(ANILIST_URL, json={"query": query, "variables": variables})
    if response.status_code != 200:
        return None
    data = response.json()
    if "errors" in data:
        return None
    return data["data"]["Page"]["media"]

def fetch_ongoing():
    query = """
    query {
        Page(perPage: 50) {
            media(type: ANIME, status: RELEASING, sort: POPULARITY_DESC) {
                id
                title { romaji english }
                genres
                averageScore
                popularity
                coverImage { large }
                format
                status
                nextAiringEpisode { episode airingAt }
            }
        }
    }
    """
    response = requests.post(ANILIST_URL, json={"query": query})
    if response.status_code != 200:
        return None
    data = response.json()
    if "errors" in data:
        return None
    return data["data"]["Page"]["media"]

def fetch_random():
    sequel_keywords = [
        "season 2", "season 3", "season 4", "2nd season", "3rd season",
        "part 2", "part 3", " ii", " iii", " iv", ": re", "final season",
        "the final", "2nd cour", "3rd cour"
    ]

    attempts = 0
    while attempts < 10:
        page = random.randint(1, 50)
        query = """
        query ($page: Int) {
            Page(page: $page, perPage: 5) {
                media(type: ANIME, sort: SCORE_DESC, averageScore_greater: 75, format: TV) {
                    id
                    title { romaji english }
                    genres
                    averageScore
                    popularity
                    coverImage { large }
                    format
                    status
                    description
                }
            }
        }
        """
        variables = {"page": page}
        response = requests.post(ANILIST_URL, json={"query": query, "variables": variables})
        if response.status_code != 200:
            attempts += 1
            continue
        data = response.json()
        if "errors" in data:
            attempts += 1
            continue
        results = data["data"]["Page"]["media"]
        for r in results:
            title = (r["title"]["romaji"] or r["title"]["english"] or "").lower()
            if not any(kw in title for kw in sequel_keywords):
                return r
        attempts += 1
    return None

def fetch_browse(genre=None, format=None, search=None):
    if search:
        query = """
        query ($search: String) {
            Page(perPage: 30) {
                media(search: $search, type: ANIME, sort: SEARCH_MATCH) {
                    id
                    title { romaji english }
                    genres
                    averageScore
                    popularity
                    coverImage { large }
                    format
                    status
                }
            }
        }
        """
        variables = {"search": search}
    else:
        query = """
        query ($genre: String, $format: MediaFormat) {
            Page(perPage: 30) {
                media(type: ANIME, genre: $genre, format: $format, sort: SCORE_DESC, averageScore_greater: 70) {
                    id
                    title { romaji english }
                    genres
                    averageScore
                    popularity
                    coverImage { large }
                    format
                    status
                }
            }
        }
        """
        variables = {
            "genre": genre if genre else None,
            "format": format if format else None
        }

    response = requests.post(ANILIST_URL, json={"query": query, "variables": variables})
    if response.status_code != 200:
        return None
    data = response.json()
    if "errors" in data:
        return None
    return data["data"]["Page"]["media"]

def compute_similarity(source_genres, candidate_genres):
    source = set(source_genres)
    candidate = set(candidate_genres)
    if not source or not candidate:
        return 0.0
    return len(source & candidate) / len(source | candidate)

def build_recommendations(source, actual_type, country, n=10):
    matched_title = source["title"]["romaji"] or source["title"]["english"]
    source_genres = source["genres"]

    if actual_type == "ANIME":
        candidates = fetch_recommendations_anime(source_genres, n)
    else:
        candidates = fetch_recommendations_manga(source_genres, country or "JP", n)

    if not candidates:
        return None, matched_title

    results = []
    for c in candidates:
        candidate_title = c["title"]["romaji"] or c["title"]["english"]
        if candidate_title.lower() == matched_title.lower():
            continue
        similarity = compute_similarity(source_genres, c["genres"])
        avg_score = c["averageScore"] or 0
        norm_score = avg_score / 100
        final_score = (similarity * 0.7) + (norm_score * 0.3)
        results.append({
            "title": candidate_title,
            "genres": ", ".join(c["genres"]),
            "average_score": avg_score,
            "similarity": round(similarity, 3),
            "final_score": round(final_score, 3),
            "cover": c.get("coverImage", {}).get("large", ""),
            "format": c.get("format", ""),
            "status": c.get("status", "")
        })

    results = sorted(results, key=lambda x: x["final_score"], reverse=True)
    seen = set()
    unique = []
    for r in results:
        if r["title"] not in seen:
            seen.add(r["title"])
            unique.append(r)

    return unique[:n], matched_title

# Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ongoing")
def ongoing():
    return render_template("ongoing.html")

@app.route("/browse")
def browse():
    return render_template("browse.html")

@app.route("/mood")
def mood():
    return render_template("mood.html")

@app.route("/random")
def random_page():
    return render_template("random.html")

# API endpoints
@app.route("/api/search", methods=["POST"])
def api_search():
    data = request.json
    title = data.get("title", "")
    media_type = data.get("media_type", "ANIME")
    results, actual_type = search_media(title, media_type)
    if not results:
        return jsonify({"error": "Not found"}), 404
    formatted = []
    for r in results:
        formatted.append({
            "id": r["id"],
            "title": r["title"]["romaji"] or r["title"]["english"],
            "genres": r["genres"],
            "average_score": r["averageScore"],
            "format": r.get("format", ""),
            "status": r.get("status", ""),
            "cover": r.get("coverImage", {}).get("large", ""),
            "actual_type": actual_type
        })
    return jsonify({"results": formatted, "actual_type": actual_type})

@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    data = request.json
    source = data.get("source")
    actual_type = data.get("actual_type", "ANIME")
    country = data.get("country", None)
    n = data.get("n", 10)
    results, matched = build_recommendations(source, actual_type, country, n)
    if not results:
        return jsonify({"error": "No recommendations found"}), 404
    return jsonify({"results": results, "matched_title": matched})

@app.route("/api/ongoing", methods=["GET"])
def api_ongoing():
    results = fetch_ongoing()
    if not results:
        return jsonify({"error": "Could not fetch ongoing anime"}), 500
    formatted = []
    for r in results:
        next_ep = r.get("nextAiringEpisode")
        formatted.append({
            "id": r["id"],
            "title": r["title"]["romaji"] or r["title"]["english"],
            "genres": r["genres"],
            "average_score": r["averageScore"],
            "format": r.get("format", ""),
            "cover": r.get("coverImage", {}).get("large", ""),
            "next_episode": next_ep["episode"] if next_ep else None,
        })
    return jsonify({"results": formatted})

@app.route("/api/random", methods=["GET"])
def api_random():
    result = fetch_random()
    if not result:
        return jsonify({"error": "Could not fetch random anime"}), 500
    return jsonify({
        "id": result["id"],
        "title": result["title"]["romaji"] or result["title"]["english"],
        "genres": result["genres"],
        "average_score": result["averageScore"],
        "cover": result.get("coverImage", {}).get("large", ""),
        "format": result.get("format", ""),
        "status": result.get("status", ""),
        "description": result.get("description", "")
    })

@app.route("/api/browse", methods=["GET"])
def api_browse():
    genre = request.args.get("genre", None)
    format = request.args.get("format", None)
    search = request.args.get("search", None)
    results = fetch_browse(genre, format, search)
    if not results:
        return jsonify({"results": []})
    formatted = []
    for r in results:
        formatted.append({
            "id": r["id"],
            "title": r["title"]["romaji"] or r["title"]["english"],
            "genres": r["genres"],
            "average_score": r["averageScore"],
            "cover": r.get("coverImage", {}).get("large", ""),
            "format": r.get("format", ""),
            "status": r.get("status", "")
        })
    return jsonify({"results": formatted})

if __name__ == "__main__":
    app.run(debug=True)