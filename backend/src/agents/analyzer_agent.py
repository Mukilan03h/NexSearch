"""
Analyzer Agent — ranks papers by relevance, indexes in Vespa, and extracts themes.
Uses embeddings for semantic ranking and clustering for theme identification.
"""
import json
from typing import List, Optional
import math

from pydantic import BaseModel, Field

from src.agents.base_agent import BaseAgent
from src.llm.embeddings import EmbeddingProvider
from src.llm.prompts import ANALYSIS_PROMPT
from src.storage.vespa_client import VespaClient
from src.utils.config import settings
from models.schemas import Paper, Theme

# Internal model for LLM theme extraction
class ThemeList(BaseModel):
    themes: List[Theme] = Field(default_factory=list)


class AnalyzerAgent(BaseAgent):
    """
    Analyzes and ranks fetched papers using:
    1. Embedding-based semantic similarity (via Vespa ANN)
    2. BM25 text matching (via Vespa)
    3. LLM-based theme extraction
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.embedder = EmbeddingProvider()
        self.vespa: Optional[VespaClient] = None

    def _get_vespa(self) -> Optional[VespaClient]:
        """Lazy-init Vespa client."""
        if self.vespa is None:
            try:
                self.vespa = VespaClient()
                if not self.vespa.is_healthy():
                    self.logger.warning("Vespa is not healthy, will use fallback ranking")
                    self.vespa = None
            except Exception as e:
                self.logger.warning(f"Vespa not available: {e}")
        return self.vespa

    def execute(self, papers: List[Paper], query: str, top_k: int = 10) -> List[Paper]:
        """Alias for rank_and_filter."""
        return self.rank_and_filter(papers, query, top_k)

    def rank_and_filter(
        self, papers: List[Paper], query: str, top_k: int = None
    ) -> List[Paper]:
        """
        Rank papers by relevance and return top-K.

        Strategy:
        1. Generate embeddings for all papers
        2. Index in Vespa (if available)
        3. Hybrid search to rank
        4. Fallback: cosine similarity if Vespa unavailable

        Args:
            papers: List of papers to rank
            query: Original research query
            top_k: Number of top papers to return

        Returns:
            Top-K most relevant papers, sorted by relevance
        """
        top_k = top_k or settings.top_k_papers

        if not papers:
            self.logger.warning("No papers to analyze")
            return []

        self.logger.info(f"Analyzing {len(papers)} papers, selecting top {top_k}")

        # Generate embeddings for paper abstracts
        abstracts = [p.abstract for p in papers]
        try:
            embeddings = self.embedder.generate(abstracts)
            query_embedding = self.embedder.generate_single(query)
        except Exception as e:
            self.logger.error(f"Embedding generation failed: {e}")
            # Fallback: return first top_k papers
            return papers[:top_k]

        # Try Vespa indexing + search
        vespa = self._get_vespa()
        if vespa:
            try:
                vespa.index_papers(papers, embeddings)
                results = vespa.search(
                    query=query,
                    query_embedding=query_embedding,
                    top_k=top_k,
                    rank_profile="hybrid",
                )
                if results:
                    return self._match_results_to_papers(results, papers, top_k)
            except Exception as e:
                self.logger.warning(f"Vespa search failed, using fallback: {e}")

        # Fallback: cosine similarity ranking
        ranked = self._cosine_rank(papers, embeddings, query_embedding, top_k)
        return ranked

    def extract_themes(self, papers: List[Paper], query: str) -> List[Theme]:
        """
        Use clustering + LLM to identify meaningful themes across papers.

        Strategy:
        1. Cluster papers by embedding similarity (k-means)
        2. For each cluster, use LLM to generate theme name and description
        3. Calculate relevance scores based on query similarity

        Args:
            papers: List of analyzed papers
            query: Original research query

        Returns:
            List of Theme objects
        """
        if not papers:
            return []

        # Generate embeddings for clustering
        try:
            abstracts = [p.abstract for p in papers]
            embeddings = self.embedder.generate(abstracts)
            query_embedding = self.embedder.generate_single(query)
        except Exception as e:
            self.logger.error(f"Embedding generation failed for themes: {e}")
            return [Theme(name="General Findings", description="Combined findings from all papers",
                         paper_ids=[p.id for p in papers], relevance_score=0.5)]

        # Determine number of clusters (2-4 based on paper count)
        n_clusters = min(max(2, len(papers) // 3), 4)

        # Cluster papers using k-means
        clusters = self._kmeans_cluster(embeddings, n_clusters)

        # Calculate relevance scores for each cluster
        cluster_scores = []
        for cluster_ids in clusters.values():
            cluster_embeddings = [embeddings[i] for i in cluster_ids]
            avg_sim = sum(
                self._cosine_sim(emb, query_embedding)
                for emb in cluster_embeddings
            ) / len(cluster_embeddings)
            cluster_scores.append(avg_sim)

        # Normalize scores
        max_score = max(cluster_scores) if cluster_scores else 1.0
        normalized_scores = [s / max_score for s in cluster_scores]

        # Use LLM to describe each cluster
        themes = []
        for cluster_idx, (cluster_id, paper_indices) in enumerate(clusters.items()):
            cluster_papers = [papers[i] for i in paper_indices]

            # Calculate avg relevance to query
            avg_relevance = sum(p.relevance_score or 0 for p in cluster_papers) / len(cluster_papers)

            # Use LLM to generate theme name and description
            theme = self._llm_describe_theme(cluster_papers, query)
            theme.relevance_score = normalized_scores[cluster_idx]
            theme.paper_ids = [p.id for p in cluster_papers]

            # Override with higher of clustering or embedding relevance
            theme.relevance_score = max(theme.relevance_score, avg_relevance)
            themes.append(theme)

        # Sort by relevance score
        themes.sort(key=lambda t: t.relevance_score, reverse=True)

        self.logger.info(f"Extracted {len(themes)} themes via clustering")
        return themes

    def _kmeans_cluster(self, embeddings: List[List[float]], n_clusters: int) -> dict:
        """Simple k-means clustering on embeddings."""
        n = len(embeddings)
        if n <= n_clusters:
            return {i: [i] for i in range(n)}

        # Initialize centroids using k-means++
        centroids = self._kmeans_init(embeddings, n_clusters)

        for _ in range(20):  # Max iterations
            # Assign to clusters
            clusters = {i: [] for i in range(n_clusters)}
            for idx, emb in enumerate(embeddings):
                distances = [self._euclidean(emb, c) for c in centroids]
                nearest = distances.index(min(distances))
                clusters[nearest].append(idx)

            # Update centroids
            new_centroids = []
            for cluster_id, indices in clusters.items():
                if indices:
                    new_centroid = [
                        sum(embeddings[i][d] for i in indices) / len(indices)
                        for d in range(len(embeddings[0]))
                    ]
                else:
                    new_centroid = centroids[cluster_id]
                new_centroids.append(new_centroid)

            # Check convergence
            if all(self._euclidean(c, nc) < 1e-6 for c, nc in zip(centroids, new_centroids)):
                break
            centroids = new_centroids

        return clusters

    def _kmeans_init(self, embeddings: List[List[float]], n_clusters: int) -> List[List[float]]:
        """K-means++ initialization."""
        import random
        random.seed(42)

        centroids = []
        # First centroid: random
        centroids.append(embeddings[random.randint(0, len(embeddings) - 1)].copy())

        for _ in range(1, n_clusters):
            # Compute distances to nearest centroid
            distances = []
            for emb in embeddings:
                min_dist = min(self._euclidean(emb, c) for c in centroids)
                distances.append(min_dist ** 2)

            # Select next centroid with probability proportional to distance
            total = sum(distances)
            r = random.random() * total
            cumsum = 0
            for i, d in enumerate(distances):
                cumsum += d
                if cumsum >= r:
                    centroids.append(embeddings[i].copy())
                    break

        return centroids

    def _euclidean(self, a: List[float], b: List[float]) -> float:
        """Compute Euclidean distance."""
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    def _cosine_sim(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity."""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

    def _llm_describe_theme(self, papers: List[Paper], query: str) -> Theme:
        """Use LLM to generate theme name and description from cluster papers."""
        papers_text = "\n\n".join([
            f"[{i+1}] {p.title}\nAbstract: {p.abstract[:250]}..."
            for i, p in enumerate(papers)
        ])

        prompt = f"""Analyze these {len(papers)} papers and identify the common theme.

Research Query: "{query}"

Papers:
{papers_text}

Return a JSON object with exactly this structure:
{{
    "name": "2-4 word theme name",
    "description": "1-2 sentence description of what unites these papers"
}}

Focus on what makes these papers similar (domain, methodology, application, etc.)."""

        try:
            result = self.llm.complete_structured(
                prompt=prompt,
                schema=Theme,
                temperature=0.3,
            )
            return result
        except Exception as e:
            self.logger.warning(f"LLM theme description failed: {e}")
            # Fallback based on content
            return Theme(
                name=f"Theme {len(papers)} Papers",
                description=f"Papers discussing related aspects of {query}",
                paper_ids=[p.id for p in papers],
                relevance_score=0.5
            )

    def _cosine_rank(
        self, papers: List[Paper], embeddings: List[List[float]],
        query_embedding: List[float], top_k: int,
    ) -> List[Paper]:
        """Fallback: rank papers by cosine similarity to query."""
        import math

        def cosine_sim(a: List[float], b: List[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_b = math.sqrt(sum(x * x for x in b))
            return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

        scored = []
        for paper, emb in zip(papers, embeddings):
            score = cosine_sim(emb, query_embedding)
            paper.relevance_score = score
            scored.append((score, paper))

        scored.sort(key=lambda x: x[0], reverse=True)
        ranked = [p for _, p in scored[:top_k]]
        self.logger.info(f"Cosine-ranked {len(ranked)} papers (top score: {scored[0][0]:.3f})")
        return ranked

    def _match_results_to_papers(
        self, results: list, papers: List[Paper], top_k: int
    ) -> List[Paper]:
        """Match Vespa search results back to Paper objects."""
        paper_map = {p.id: p for p in papers}
        matched = []
        for r in results[:top_k]:
            pid = r.get("paper_id", "")
            if pid in paper_map:
                paper = paper_map[pid]
                paper.relevance_score = r.get("_relevance", 0.0)
                matched.append(paper)
        return matched if matched else papers[:top_k]
