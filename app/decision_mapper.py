from typing import Dict, Any, Tuple, Callable, Optional
from .providers.base import SportsProvider


class ValidationError(Exception):
    """Raised when payload validation fails"""

    def __init__(self, message: str, details: Dict[str, Any] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DecisionMapper:
    """Maps operationType to validation, provider method, and normalization"""

    def __init__(self, provider: SportsProvider):
        self.provider = provider
        self.operations = {
            "ListLeagues": {
                "validate": self._validate_list_leagues,
                "execute": self._execute_list_leagues,
                "normalize": self._normalize_list_leagues,
            },
            "GetLeagueMatches": {
                "validate": self._validate_get_league_matches,
                "execute": self._execute_get_league_matches,
                "normalize": self._normalize_get_league_matches,
            },
            "GetTeam": {
                "validate": self._validate_get_team,
                "execute": self._execute_get_team,
                "normalize": self._normalize_get_team,
            },
            "GetMatch": {
                "validate": self._validate_get_match,
                "execute": self._execute_get_match,
                "normalize": self._normalize_get_match,
            },
        }

    def get_operation(self, operation_type: str) -> Dict[str, Callable]:
        """Get operation handlers for a given operationType"""
        if operation_type not in self.operations:
            raise ValueError(f"Unknown operationType: {operation_type}")
        return self.operations[operation_type]

    @staticmethod
    def _validate_list_leagues(payload: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate ListLeagues payload (no fields required)"""
        return True, None

    @staticmethod
    def _validate_get_league_matches(payload: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate GetLeagueMatches payload"""
        if "leagueId" not in payload or not payload["leagueId"]:
            return False, {"missing_field": "leagueId", "reason": "leagueId is required"}
        return True, None

    @staticmethod
    def _validate_get_team(payload: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate GetTeam payload"""
        if "teamId" not in payload or not payload["teamId"]:
            return False, {"missing_field": "teamId", "reason": "teamId is required"}
        return True, None

    @staticmethod
    def _validate_get_match(payload: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate GetMatch payload"""
        if "matchId" not in payload or not payload["matchId"]:
            return False, {"missing_field": "matchId", "reason": "matchId is required"}
        return True, None

    async def _execute_list_leagues(self, payload: Dict[str, Any]) -> Any:
        """Execute ListLeagues operation"""
        return await self.provider.list_leagues()

    async def _execute_get_league_matches(self, payload: Dict[str, Any]) -> Any:
        """Execute GetLeagueMatches operation"""
        return await self.provider.get_league_matches(payload["leagueId"])

    async def _execute_get_team(self, payload: Dict[str, Any]) -> Any:
        """Execute GetTeam operation"""
        return await self.provider.get_team(payload["teamId"])

    async def _execute_get_match(self, payload: Dict[str, Any]) -> Any:
        """Execute GetMatch operation"""
        return await self.provider.get_match(payload["matchId"])

    @staticmethod
    def _normalize_list_leagues(data: Any) -> Dict[str, Any]:
        """Normalize ListLeagues response"""
        return {
            "leagues": data if isinstance(data, list) else [],
            "count": len(data) if isinstance(data, list) else 0
        }

    @staticmethod
    def _normalize_get_league_matches(data: Any) -> Dict[str, Any]:
        """Normalize GetLeagueMatches response"""
        return {
            "matches": data if isinstance(data, list) else [],
            "count": len(data) if isinstance(data, list) else 0
        }

    @staticmethod
    def _normalize_get_team(data: Any) -> Dict[str, Any]:
        """Normalize GetTeam response"""
        return {
            "team": data if isinstance(data, dict) else {}
        }

    @staticmethod
    def _normalize_get_match(data: Any) -> Dict[str, Any]:
        """Normalize GetMatch response"""
        return {
            "match": data if isinstance(data, dict) else {}
        }
