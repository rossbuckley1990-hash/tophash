"""
TopHash — Distance & Similarity utilities
"""
import numpy as np
from typing import Union


def euclidean(x: np.ndarray, y: np.ndarray) -> float:
    """Euclidean distance between two fingerprints."""
    return float(np.linalg.norm(x - y))


def cosine_similarity(x: np.ndarray, y: np.ndarray) -> float:
    """Cosine similarity in [-1, 1]."""
    nx = np.linalg.norm(x)
    ny = np.linalg.norm(y)
    if nx < 1e-12 or ny < 1e-12:
        return 0.0
    return float(np.dot(x, y) / (nx * ny))


def cosine_distance(x: np.ndarray, y: np.ndarray) -> float:
    """Cosine distance in [0, 2]."""
    return 1.0 - cosine_similarity(x, y)


def manhattan(x: np.ndarray, y: np.ndarray) -> float:
    """L1 / Manhattan distance."""
    return float(np.sum(np.abs(x - y)))


def hamming(x: np.ndarray, y: np.ndarray, threshold: float = 0.0) -> float:
    """Fraction of dimensions that differ (by more than threshold)."""
    return float(np.mean(np.abs(x - y) > threshold))


# Default distance for TopHash v3
DEFAULT_DISTANCE = euclidean

# Default similarity for ANN retrieval
DEFAULT_SIMILARITY = cosine_similarity
