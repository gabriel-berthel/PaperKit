import asyncio
import random
from functools import lru_cache
from urllib.parse import quote

from curl_cffi.requests import AsyncSession
from sentence_transformers import SentenceTransformer, CrossEncoder
from sklearn.metrics.pairwise import cosine_similarity

BROWSERS = ["chrome110", "chrome107"]

@lru_cache(maxsize=1)
def get_embedding_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

@lru_cache(maxsize=1)
def get_reranker():
    return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


async def fetch_wikipedia_candidates(
    session: AsyncSession,
    search_term: str,
    top_k: int,
):
    search_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": search_term,
        "format": "json",
        "srlimit": top_k,
    }

    response = await session.get(search_url, params=params)
    if response.status_code != 200:
        return []

    return response.json().get("query", {}).get("search", [])

async def fetch_candidate_summaries(
    session: AsyncSession,
    results: list[dict],
    limit: int = 5,
):
    candidates = []

    for result in results[:limit]:
        title = result["title"]

        summary_url = (
            "https://en.wikipedia.org/api/rest_v1/page/summary/"
            f"{quote(title.replace(' ', '_'))}"
        )

        await asyncio.sleep(random.uniform(0.3, 0.7))

        response = await session.get(summary_url)
        if response.status_code != 200:
            continue

        data = response.json()

        candidates.append({
            "title": title,
            "summary": data.get("extract", ""),
            "description": data.get("description", ""),
        })

    return candidates

def rank_candidates(
    candidates: list[dict],
    context: str,
    rerank_top_k: int,
):
    """
    Ranks Wikipedia results using a bi-encoder and a cross-encoder pipeline:

    1. Uses a bi-encoder to compute embeddings for the context and each result,
    then ranks candidates by cosine similarity.
    2. Sorts candidates and keeps the top-K highest scoring results.
    3. Applies a cross-encoder to re-rank the shortlisted candidates by jointly
    encoding the context and each result for finer-grained relevance scoring.
    """
    
    texts = [
        f"{c['title']} {c['description']} {c['summary']}"
        for c in candidates
    ]

    model = get_embedding_model()

    context_emb = model.encode([context])
    text_embs = model.encode(texts)

    sims = cosine_similarity(context_emb, text_embs)[0]

    for candidate, score in zip(candidates, sims):
        candidate["embedding_score"] = float(score)

    candidates = sorted(
        candidates,
        key=lambda x: x["embedding_score"],
        reverse=True,
    )[:rerank_top_k]

    pairs = [
        (
            context,
            f"{c['title']} {c['description']} {c['summary']}",
        )
        for c in candidates
    ]

    rerank_scores = get_reranker().predict(pairs)

    for candidate, score in zip(candidates, rerank_scores):
        candidate["rerank_score"] = float(score)

    return max(candidates, key=lambda x: x["rerank_score"])

async def wikipedia_best_match(
    search_term: str,
    context: str,
    top_k: int = 10,
    rerank_top_k: int = 5,
):
    try:
        async with AsyncSession(
            impersonate=random.choice(BROWSERS)
        ) as session:

            await asyncio.sleep(random.uniform(0.2, 0.6))

            results = await fetch_wikipedia_candidates(
                session,
                search_term,
                top_k,
            )

            if not results:
                return None

            candidates = await fetch_candidate_summaries(
                session,
                results,
            )

    except Exception as e:
        print(f"Wikipedia fetch error: {e}")
        return None

    if not candidates:
        return None

    best = rank_candidates(
        candidates,
        context,
        rerank_top_k,
    )

    return best.get("description")