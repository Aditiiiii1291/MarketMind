"""Dashboard service response dataclasses."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DashboardMetrics:
    """Structured metrics prepared for dashboard rendering."""

    review_count: Optional[int] = None
    average_rating: Optional[float] = None
    negative_percentage: Optional[float] = None
    health_score: Optional[float] = None
    health_label: Optional[str] = None
    launch_score: Optional[float] = None
    launch_label: Optional[str] = None
    similar_review_count: Optional[int] = None
    recommendations: List[str] = field(default_factory=list)
    simulation_note: Optional[str] = None
    error: Optional[str] = None


@dataclass
class DashboardTables:
    """Structured table inputs prepared for dashboard rendering."""

    sentiment_distribution: Dict[str, Any] = field(default_factory=dict)
    category_summary: Any = None
    matched_product_names: List[str] = field(default_factory=list)
    persona_simulations: List[Any] = field(default_factory=list)


@dataclass
class DashboardResponse:
    """Combined dashboard response containing service result, metrics, and tables."""

    result: Any
    metrics: DashboardMetrics
    tables: DashboardTables
    error: Optional[str] = None
