from abc import ABC, abstractmethod
from typing import List
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class BaseEmbedder(ABC):
    """Abstract interface for text embedding and similarity calculations."""

    @abstractmethod
    def embed(self, texts: List[str]) -> np.ndarray:
        """Vectorize a list of input texts into numeric embeddings."""
        pass

    @abstractmethod
    def similarity(self, text1: str, text2: str) -> float:
        """Compute semantic cosine similarity score in range [0.0, 1.0]."""
        pass


class TfidfCharNgramEmbedder(BaseEmbedder):
    """
    Default character n-gram TF-IDF embedder.
    Robust against typos, punctuation differences, and partial invoice/vendor strings.
    """

    def __init__(self, ngram_range: tuple = (2, 4)):
        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=ngram_range,
            lowercase=True,
        )
        self._fitted = False

    def embed(self, texts: List[str]) -> np.ndarray:
        cleaned = [str(t).strip() for t in texts if t is not None]
        if not cleaned:
            return np.zeros((len(texts), 0))
        return self.vectorizer.fit_transform(cleaned).toarray()

    def similarity(self, text1: str, text2: str) -> float:
        s1 = str(text1 or "").strip()
        s2 = str(text2 or "").strip()
        if not s1 or not s2:
            return 0.0
        if s1.lower() == s2.lower():
            return 1.0

        try:
            vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), lowercase=True)
            matrix = vec.fit_transform([s1, s2])
            sim = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
            return float(max(0.0, min(1.0, sim)))
        except Exception:
            # Fallback simple Jaccard on char n-grams
            set1 = set([s1[i : i + 3] for i in range(len(s1) - 2)])
            set2 = set([s2[i : i + 3] for i in range(len(s2) - 2)])
            if not set1 or not set2:
                return 0.0
            return float(len(set1 & set2) / len(set1 | set2))

