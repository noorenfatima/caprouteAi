"""Configuration-driven route generation for CapRoute AI.

The generator returns validated route candidates only. It does not calculate
costs, score routes, or rank them; existing optimizer code remains responsible
for those behaviors.
"""

from typing import Any, Dict, Iterable, List, Mapping, Set

from backend.models import CorridorCandidate, CorridorHop


class ConfigRouteGenerator:
    def __init__(self, source_to_destination_zone: Mapping[str, Mapping[str, Dict[str, Any]]]):
        self.source_to_destination_zone = {
            source.upper(): {
                destination.upper(): {
                    "zone": entry["zone"],
                    "logic": entry["logic"],
                }
                for destination, entry in destinations.items()
            }
            for source, destinations in source_to_destination_zone.items()
        }

    def generate(self, source: str, destination: str, max_hops: int = 1) -> List[CorridorCandidate]:
        """Generate all valid direct and one-hop corridors from configuration."""
        if max_hops != 1:
            raise ValueError("ConfigRouteGenerator currently supports direct and one-hop corridors only")

        source_upper = source.upper()
        destination_upper = destination.upper()
        candidates: List[CorridorCandidate] = []

        direct = self._build_candidate([source_upper, destination_upper])
        if direct:
            candidates.append(direct)

        for hub in self._candidate_hubs(source_upper, destination_upper):
            candidate = self._build_candidate([source_upper, hub, destination_upper])
            if candidate:
                candidates.append(candidate)

        return candidates

    def _candidate_hubs(self, source: str, destination: str) -> Iterable[str]:
        configured_sources: Set[str] = set(self.source_to_destination_zone.keys())
        source_destinations = self.source_to_destination_zone.get(source, {})

        for country in source_destinations.keys():
            hub = country.upper()
            if hub in {source, destination}:
                continue
            if hub not in configured_sources:
                continue
            yield hub

    def _build_candidate(self, path: List[str]) -> CorridorCandidate | None:
        if self._has_loop(path):
            return None

        hops: List[CorridorHop] = []
        for index in range(len(path) - 1):
            source = path[index]
            destination = path[index + 1]
            zone_entry = self.source_to_destination_zone.get(source, {}).get(destination)
            if not zone_entry:
                return None
            hops.append(
                CorridorHop(
                    source=source,
                    destination=destination,
                    zone_name=zone_entry["zone"],
                    zone_logic=zone_entry["logic"],
                )
            )

        return CorridorCandidate(path=path, hops=hops)

    @staticmethod
    def _has_loop(path: List[str]) -> bool:
        return len(path) != len(set(path))

