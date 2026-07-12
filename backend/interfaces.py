"""Interfaces for the target CapRoute AI production architecture.

These protocols make future modules explicit while Phase 1 keeps runtime
behavior unchanged.
"""

from typing import Any, Dict, List, Protocol, Tuple

from backend.models import CorridorCandidate, FeatureVector, MLDecision, Route


class RouteGenerator(Protocol):
    def generate(self, source: str, destination: str) -> List[CorridorCandidate]:
        ...


class FeatureEngineering(Protocol):
    def build_for_candidate(self, candidate: CorridorCandidate, context: Dict[str, Any]) -> List[FeatureVector]:
        ...


class DecisionEngine(Protocol):
    def predict_compliance(self, **kwargs: Any) -> MLDecision:
        ...


class PriorityOptimizer(Protocol):
    def rank(self, routes: List[Route], priority: str) -> Tuple[Route, Route, Route]:
        ...


class DataProvider(Protocol):
    def get(self, key: str, fallback: Any = None) -> Any:
        ...


class SimulationEngine(Protocol):
    def simulate(self, route: CorridorCandidate, context: Dict[str, Any]) -> Dict[str, Any]:
        ...


class HistoryEngine(Protocol):
    def record_optimization(self, payload: Dict[str, Any]) -> None:
        ...


class AnalyticsEngine(Protocol):
    def dashboard(self) -> Dict[str, Any]:
        ...

    def insights(self) -> Dict[str, Any]:
        ...

