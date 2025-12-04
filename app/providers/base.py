from abc import ABC, abstractmethod
from typing import List, Dict, Any


class SportsProvider(ABC):
    """Abstract interface for sports data providers"""

    @abstractmethod
    async def list_leagues(self) -> List[Dict[str, Any]]:
        """List all available leagues"""
        pass

    @abstractmethod
    async def get_league_matches(self, league_id: str) -> List[Dict[str, Any]]:
        """Get matches for a specific league"""
        pass

    @abstractmethod
    async def get_team(self, team_id: str) -> Dict[str, Any]:
        """Get team information by ID"""
        pass

    @abstractmethod
    async def get_match(self, match_id: str) -> Dict[str, Any]:
        """Get match information by ID"""
        pass
