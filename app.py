import streamlit as st
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(page_title="Anime Recommender", page_icon="🎌", layout="wide")

@st.cache_data
def load_data():
    try:
        import os
        # this finds the CSV relative to where app.py lives
        base_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(base_dir, "myanilist.csv")
        df = pd.read_csv(csv_path)
        df = df.dropna(subset=["Title_Romaji", "Genres"])
        df = df[~df["Genres"].str.contains("Hentai", na=False)]
        df = df.drop_duplicates(subset=["Title_Romaji"])
        df["Average_Score"] = pd.to_numeric(df["Average_Score"], errors="coerce")
        df["Average_Score"] = df["Average_Score"].fillna(df["Average_Score"].mean())
        df["Title_Romaji_Lower"] = df["Title_Romaji"].str.lower().str.strip()
        df = df.reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        st.stop()

@st.cache_data
def build_similarity(df):
    tfidf = TfidfVectorizer(token_pattern=r"[^,]+")
    tfidf_matrix = tfidf.fit_transform(df["Genres"].fillna(""))
    return cosine_similarity(tfidf_matrix, tfidf_matrix)

df = load_data()
cosine_sim = build_similarity(df)
indices = pd.Series(df.index, index=df["Title_Romaji_Lower"]).drop_duplicates()

def recommend(title, n=10):
    title_clean = title.lower().strip()
    
    if title_clean in indices:
        idx = indices[title_clean]
        matched_title = df.loc[idx, "Title_Romaji"]
    else:
        matches = [t for t in indices.index if title_clean in t]
        if not matches:
            return None, None
        matches.sort(key=lambda x: abs(len(x) - len(title_clean)))
        idx = indices[matches[0]]
        matched_title = df.loc[idx, "Title_Romaji"]
    
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:n+1]
    
    anime_indices = [i[0] for i in sim_scores]
    similarity_values = [round(i[1], 3) for i in sim_scores]
    
    results = df[["Title_Romaji", "Genres", "Average_Score"]].iloc[anime_indices].copy()
    results["Similarity"] = similarity_values
    results["Norm_Score"] = results["Average_Score"] / 100
    results["Norm_Similarity"] = results["Similarity"] / results["Similarity"].max()
    results["Final_Score"] = (results["Norm_Similarity"] * 0.7) + (results["Norm_Score"] * 0.3)
    
    return results[["Title_Romaji", "Genres", "Average_Score", "Similarity", "Final_Score"]].sort_values("Final_Score", ascending=False).reset_index(drop=True), matched_title

# UI
st.title("🎌 Anime Recommender")
st.markdown("Find anime similar to what you love")

col1, col2 = st.columns([3, 1])
with col1:
    user_input = st.text_input("Enter an anime title", placeholder="e.g. Vinland Saga, Steins;Gate...")
with col2:
    n_results = st.slider("Number of results", 5, 20, 10)

if user_input:
    results, matched = recommend(user_input, n=n_results)
    
    if results is None:
        st.error(f"Could not find '{user_input}'. Try checking the spelling.")
    else:
        if matched.lower() != user_input.lower().strip():
            st.info(f"Showing results for: **{matched}**")
        
        st.success(f"Top {len(results)} recommendations")
        st.dataframe(results, use_container_width=True)
