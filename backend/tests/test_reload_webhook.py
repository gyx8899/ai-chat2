"""Tests for reload webhook (httpx revalidate notification)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestNotifyFrontendRevalidate:
    """Test _notify_frontend_revalidate with mocked httpx."""

    @pytest.mark.asyncio
    async def test_notify_success(self) -> None:
        """Successful httpx POST triggers revalidate."""
        from app.routers.prompts import _notify_frontend_revalidate

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_aclient = AsyncMock()
        mock_aclient.post.return_value = mock_response
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_aclient
        mock_context.__aexit__.return_value = None
        mock_aclient.__aenter__.return_value = mock_aclient
        mock_aclient.__aexit__.return_value = None

        with patch("app.routers.prompts.httpx.AsyncClient", return_value=mock_context):
            await _notify_frontend_revalidate()
            mock_aclient.post.assert_called_once()
            call_url = mock_aclient.post.call_args[0][0]
            assert "api/revalidate-prompts" in call_url
            assert "secret=" in call_url

    @pytest.mark.asyncio
    async def test_notify_http_error_does_not_raise(self) -> None:
        """HTTP error does NOT raise, just warns."""
        from app.routers.prompts import _notify_frontend_revalidate

        mock_aclient = AsyncMock()
        mock_aclient.post.side_effect = Exception("HTTP 401")
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_aclient

        with patch("app.routers.prompts.httpx.AsyncClient", return_value=mock_context):
            # Should NOT raise
            try:
                await _notify_frontend_revalidate()
            except Exception as e:
                pytest.fail(f"Expected no exception, got: {e}")

    @pytest.mark.asyncio
    async def test_notify_timeout_does_not_raise(self) -> None:
        """Timeout does NOT raise, just warns."""
        from app.routers.prompts import _notify_frontend_revalidate

        mock_aclient = AsyncMock()
        mock_aclient.post.side_effect = TimeoutError("Connection timeout")
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_aclient

        with patch("app.routers.prompts.httpx.AsyncClient", return_value=mock_context):
            try:
                await _notify_frontend_revalidate()
            except Exception as e:
                pytest.fail(f"Expected no exception, got: {e}")

    @pytest.mark.asyncio
    async def test_notify_skipped_when_no_config(self) -> None:
        """Skipped when frontend_url or revalidate_secret is missing."""
        from app.routers.prompts import _notify_frontend_revalidate

        with patch("app.routers.prompts.get_settings") as mock_settings:
            mock_s = MagicMock()
            mock_s.prompts.frontend_url = None
            mock_s.prompts.revalidate_secret = "secret"
            mock_settings.return_value = mock_s

            with patch("app.routers.prompts.httpx.AsyncClient") as mock_async_client:
                await _notify_frontend_revalidate()
                mock_async_client.assert_not_called()