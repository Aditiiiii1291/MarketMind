"""AI-readiness dataclasses for deterministic analysis outputs."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AIContext:
    """Aggregated analytics context prepared for future AI analysis."""

    product_query: Optional[str] = None
    product_health: Any = None
    sentiment_distribution: Dict[str, Any] = field(default_factory=dict)
    complaint_summary: Any = None
    strengths: List[str] = field(default_factory=list)
    personas: List[Any] = field(default_factory=list)
    launch_score: Optional[float] = None
    launch_label: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)
    comparison: Any = None
    concept: Any = None
    error: Optional[str] = None


@dataclass
class ProductInsight:
    """Deterministic product insight prepared from AIContext."""

    product_query: Optional[str]
    health_score: Optional[float]
    health_label: Optional[str]
    review_count: Optional[int]
    average_rating: Optional[float]
    strengths: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    prompt: str = ""
    error: Optional[str] = None


@dataclass
class LaunchAnalysis:
    """Deterministic launch-readiness analysis prepared from AIContext."""

    product_name: Optional[str]
    launch_score: Optional[float]
    launch_label: Optional[str]
    similar_review_count: Optional[int]
    recommendations: List[str] = field(default_factory=list)
    prompt: str = ""
    error: Optional[str] = None


@dataclass
class PersonaSummary:
    """Deterministic persona summary prepared from AIContext."""

    personas: List[Any] = field(default_factory=list)
    prompt: str = ""
    error: Optional[str] = None


@dataclass
class BusinessReport:
    """Deterministic business report prepared from AIContext."""

    product_insight: Optional[ProductInsight] = None
    launch_analysis: Optional[LaunchAnalysis] = None
    persona_summary: Optional[PersonaSummary] = None
    comparison_summary: Optional[str] = None
    prompt: str = ""
    error: Optional[str] = None
