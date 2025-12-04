import pytest
from app.decision_mapper import DecisionMapper


class TestDecisionMapper:
    """Test decision mapper functionality"""

    @pytest.fixture
    def mapper(self, mock_provider):
        """Create decision mapper instance"""
        return DecisionMapper(mock_provider)

    def test_get_operation_valid(self, mapper):
        """Test getting valid operation"""
        operation = mapper.get_operation("ListLeagues")
        assert "validate" in operation
        assert "execute" in operation
        assert "normalize" in operation

    def test_get_operation_invalid(self, mapper):
        """Test getting invalid operation raises error"""
        with pytest.raises(ValueError, match="Unknown operationType"):
            mapper.get_operation("InvalidOperation")

    def test_validate_list_leagues(self, mapper):
        """Test ListLeagues validation"""
        is_valid, details = mapper._validate_list_leagues({})
        assert is_valid is True
        assert details is None

    def test_validate_get_league_matches_valid(self, mapper):
        """Test GetLeagueMatches validation with valid payload"""
        is_valid, details = mapper._validate_get_league_matches({"leagueId": "bl1"})
        assert is_valid is True
        assert details is None

    def test_validate_get_league_matches_invalid(self, mapper):
        """Test GetLeagueMatches validation with missing leagueId"""
        is_valid, details = mapper._validate_get_league_matches({})
        assert is_valid is False
        assert "leagueId" in details.get("reason", "")

    def test_validate_get_team_valid(self, mapper):
        """Test GetTeam validation with valid payload"""
        is_valid, details = mapper._validate_get_team({"teamId": "100"})
        assert is_valid is True

    def test_validate_get_team_invalid(self, mapper):
        """Test GetTeam validation with missing teamId"""
        is_valid, details = mapper._validate_get_team({})
        assert is_valid is False
        assert "teamId" in details.get("reason", "")

    def test_validate_get_match_valid(self, mapper):
        """Test GetMatch validation with valid payload"""
        is_valid, details = mapper._validate_get_match({"matchId": "123"})
        assert is_valid is True

    def test_validate_get_match_invalid(self, mapper):
        """Test GetMatch validation with missing matchId"""
        is_valid, details = mapper._validate_get_match({})
        assert is_valid is False
        assert "matchId" in details.get("reason", "")

    @pytest.mark.asyncio
    async def test_execute_list_leagues(self, mapper, mock_provider):
        """Test executing ListLeagues"""
        result = await mapper._execute_list_leagues({})
        assert result == [{"id": "1", "name": "League 1"}]
        mock_provider.list_leagues.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_get_league_matches(self, mapper, mock_provider):
        """Test executing GetLeagueMatches"""
        result = await mapper._execute_get_league_matches({"leagueId": "bl1"})
        assert result == [{"id": "m1", "league": "bl1"}]
        mock_provider.get_league_matches.assert_called_once_with("bl1")

    @pytest.mark.asyncio
    async def test_execute_get_team(self, mapper, mock_provider):
        """Test executing GetTeam"""
        result = await mapper._execute_get_team({"teamId": "100"})
        assert result == {"id": "t1", "name": "Team 1"}
        mock_provider.get_team.assert_called_once_with("100")

    @pytest.mark.asyncio
    async def test_execute_get_match(self, mapper, mock_provider):
        """Test executing GetMatch"""
        result = await mapper._execute_get_match({"matchId": "123"})
        assert result == {"id": "m1", "status": "finished"}
        mock_provider.get_match.assert_called_once_with("123")

    def test_normalize_list_leagues(self, mapper):
        """Test normalizing ListLeagues response"""
        data = [{"id": "1"}, {"id": "2"}]
        normalized = mapper._normalize_list_leagues(data)
        assert normalized["leagues"] == data
        assert normalized["count"] == 2

    def test_normalize_get_league_matches(self, mapper):
        """Test normalizing GetLeagueMatches response"""
        data = [{"id": "m1"}, {"id": "m2"}]
        normalized = mapper._normalize_get_league_matches(data)
        assert normalized["matches"] == data
        assert normalized["count"] == 2

    def test_normalize_get_team(self, mapper):
        """Test normalizing GetTeam response"""
        data = {"id": "t1", "name": "Team 1"}
        normalized = mapper._normalize_get_team(data)
        assert normalized["team"] == data

    def test_normalize_get_match(self, mapper):
        """Test normalizing GetMatch response"""
        data = {"id": "m1", "status": "finished"}
        normalized = mapper._normalize_get_match(data)
        assert normalized["match"] == data
