"""Concept service response dataclasses."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PersonaSimulation:
    """Structured response for one simulated persona result."""

    cluster: int
    persona_name: str
    review_count_used: int
    evidence_review_count: int
    evidence_average_rating: Optional[float]
    evidence_sentiment_score: Optional[float]
    simulated_rating: float
    likely_concern: str
    confidence: str
    simulation_note: str
    persona_response: str


@dataclass
class LaunchSummary:
    """Compact launch-readiness summary for a concept simulation."""

    launch_score: Optional[float] = None
    launch_label: Optional[str] = None
    similar_review_count: Optional[int] = None
    recommendations: List[str] = field(default_factory=list)
    simulation_note: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ConceptSimulation:
    """Structured response for a full concept simulation."""

    product_name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[str] = None
    features: Optional[str] = None
    description: Optional[str] = None
    concept_text: Optional[str] = None
    persona_simulations: List[PersonaSimulation] = field(default_factory=list)
    launch_score: Optional[float] = None
    launch_label: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)
    similar_review_count: int = 0
    simulation_note: Optional[str] = None
    error: Optional[str] = None
