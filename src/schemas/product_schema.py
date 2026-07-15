"""Product service response dataclasses."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProductHealth:
    """Structured response for one product health analysis."""

    product_query: Optional[str]
    matched_product_names: List[str] = field(default_factory=list)
    product_reviews: Any = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    sentiment_distribution: Dict[str, Any] = field(default_factory=dict)
    health_score: Optional[float] = None
    health_label: Optional[str] = None
    negative_reviews: Any = None
    category_summary: Any = None
    recommendations: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class ProductSummary:
    """Compact product summary returned by product services."""

    product_query: Optional[str]
    matched_product_names: List[str] = field(default_factory=list)
    review_count: Optional[int] = None
    average_rating: Optional[float] = None
    health_score: Optional[float] = None
    health_label: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ProductComparison:
    """Structured response for product comparison workflows."""

    comparison: Any
    ranked_products: Any
    insight: str
