"""
Tests for AIuth - Vibe-Based Authentication Library

Note: These tests verify the API works correctly. They do not verify
security properties because AIuth operates on the Presumption of Honesty.
"""

import json
import os
import tempfile
import pytest
from aiuth import AIuth, create_aiuth, OllamaBackend


class TestAIuthRegistration:
    """Test user registration functionality."""

    def test_register_basic(self, tmp_path):
        """Test basic user registration."""
        db_file = tmp_path / "test_db.txt"
        auth = AIuth(db_file=str(db_file))
        
        result = auth.register("alice")
        assert result is True
        
        users = auth.list_users()
        assert "alice" in users

    def test_register_with_profile(self, tmp_path):
        """Test registration with profile data."""
        db_file = tmp_path / "test_db.txt"
        auth = AIuth(db_file=str(db_file))
        
        auth.register(
            "bob",
            name="Bob Jones",
            vibe="chill",
            role="developer",
            favorite_color="blue"
        )
        
        profile = auth.get_user("bob")
        assert profile["name"] == "Bob Jones"
        assert profile["vibe"] == "chill"
        assert profile["role"] == "developer"
        assert profile["favorite_color"] == "blue"

    def test_register_duplicate_user(self, tmp_path):
        """Test registering a duplicate user updates the profile (last write wins)."""
        db_file = tmp_path / "test_db.txt"
        auth = AIuth(db_file=str(db_file))
        
        auth.register("alice", name="Alice v1")
        auth.register("alice", name="Alice v2")
        
        # Latest entry wins (vibes evolve)
        users = auth.list_users()
        assert "alice" in users
        assert len(users) == 1  # Latest registration wins
        
        profile = auth.get_user("alice")
        assert profile["name"] == "Alice v2"


class TestAIuthDatabase:
    """Test database operations."""

    def test_list_users_empty(self, tmp_path):
        """Test listing users from empty database."""
        db_file = tmp_path / "test_db.txt"
        auth = AIuth(db_file=str(db_file))
        
        users = auth.list_users()
        assert users == []

    def test_get_user_not_found(self, tmp_path):
        """Test getting a non-existent user."""
        db_file = tmp_path / "test_db.txt"
        auth = AIuth(db_file=str(db_file))
        
        profile = auth.get_user("nonexistent")
        assert profile is None

    def test_clear_database(self, tmp_path):
        """Test clearing the database."""
        db_file = tmp_path / "test_db.txt"
        auth = AIuth(db_file=str(db_file))
        
        auth.register("alice")
        auth.register("bob")
        assert len(auth.list_users()) == 2
        
        result = auth.clear_database()
        assert result is True
        assert auth.list_users() == []


class TestAIuthAuthentication:
    """Test authentication functionality."""

    def test_authenticate_returns_bool(self, tmp_path):
        """Test that authenticate returns a boolean."""
        db_file = tmp_path / "test_db.txt"
        auth = AIuth(db_file=str(db_file))
        
        auth.register("alice")
        result = auth.authenticate("alice", "it's me, alice")
        
        # Should return True or False (or True on LLM failure)
        assert isinstance(result, bool)

    def test_authenticate_nonexistent_user(self, tmp_path):
        """Test authenticating a non-existent user."""
        db_file = tmp_path / "test_db.txt"
        auth = AIuth(db_file=str(db_file))
        
        # Should not raise, should return bool (True on LLM failure)
        result = auth.authenticate("nobody", "it's me")
        assert isinstance(result, bool)


class TestAIuthAuthorization:
    """Test authorization functionality."""

    def test_authorize_returns_bool(self, tmp_path):
        """Test that authorize returns a boolean."""
        db_file = tmp_path / "test_db.txt"
        auth = AIuth(db_file=str(db_file))
        
        auth.register("alice", role="admin")
        result = auth.authorize("alice", "delete_database")
        
        assert isinstance(result, bool)


class TestAIuthWhoami:
    """Test whoami functionality."""

    def test_whoami_returns_string_or_none(self, tmp_path):
        """Test that whoami returns a string or None."""
        db_file = tmp_path / "test_db.txt"
        auth = AIuth(db_file=str(db_file))
        
        auth.register("alice", name="Alice Smith", role="admin")
        result = auth.whoami("the admin")
        
        # Should return string or None
        assert result is None or isinstance(result, str)

    def test_whoami_empty_database(self, tmp_path):
        """Test whoami with empty database."""
        db_file = tmp_path / "test_db.txt"
        auth = AIuth(db_file=str(db_file))
        
        result = auth.whoami("anyone")
        assert result is None


class TestAIuthSecurityLevel:
    """Test security level configuration."""

    def test_security_level_stored(self, tmp_path):
        """Test that security level is stored."""
        db_file = tmp_path / "test_db.txt"
        db_file2 = tmp_path / "test_db2.txt"
        
        auth_paranoid = AIuth(db_file=str(db_file), security_level="paranoid")
        auth_trusting = AIuth(db_file=str(db_file2), security_level="trusting")
        
        assert auth_paranoid.security_level == "paranoid"
        assert auth_trusting.security_level == "trusting"


class TestCreateAIuth:
    """Test the create_aiuth convenience function."""

    def test_create_aiuth(self, tmp_path):
        """Test create_aiuth creates an AIuth instance."""
        db_file = tmp_path / "test_db.txt"
        
        auth = create_aiuth(db_file=str(db_file))
        
        assert isinstance(auth, AIuth)
        assert auth.list_users() == []


class TestBackendConfiguration:
    """Test backend configuration."""

    def test_ollama_backend_default(self, tmp_path):
        """Test Ollama backend is default."""
        db_file = tmp_path / "test_db.txt"
        auth = AIuth(db_file=str(db_file))
        
        assert isinstance(auth._backend, OllamaBackend)

    def test_unknown_backend_raises(self, tmp_path):
        """Test unknown backend raises ValueError."""
        db_file = tmp_path / "test_db.txt"
        
        with pytest.raises(ValueError, match="Unknown backend"):
            AIuth(db_file=str(db_file), backend="nonexistent")


class TestPresumptionOfHonesty:
    """Test the Presumption of Honesty principle."""

    def test_no_exceptions_raised(self, tmp_path):
        """Test that AIuth never raises exceptions."""
        db_file = tmp_path / "test_db.txt"
        auth = AIuth(db_file=str(db_file))
        
        # All these should return values, not raise
        assert isinstance(auth.register("alice"), bool)
        assert isinstance(auth.authenticate("alice", "claim"), bool)
        assert isinstance(auth.authorize("alice", "action"), bool)
        assert auth.whoami("description") is None or isinstance(auth.whoami("description"), str)
