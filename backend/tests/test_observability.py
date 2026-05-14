"""指标和日志测试。"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.observability.metrics import _normalize_path


class TestMetricsEndpoint:
    """Prometheus 指标端点测试。"""

    @pytest.fixture
    async def client(self):
        """异步 HTTP 客户端。"""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_metrics_endpoint_accessible(self, client: AsyncClient) -> None:
        """/metrics 端点可访问，返回 Prometheus 格式。"""
        response = await client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_metrics_contains_expected_counters(self, client: AsyncClient) -> None:
        """指标包含预期的计数器。"""
        # 先发一些请求生成指标
        await client.get("/health")
        await client.get("/")

        response = await client.get("/metrics")
        body = response.text

        # 验证关键指标存在
        assert "http_requests_total" in body
        assert "http_request_duration_seconds" in body
        assert "llm_requests_total" in body


class TestTraceIdHeader:
    """TraceId 中间件测试。"""

    @pytest.fixture
    async def client(self):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_trace_id_in_response(self, client: AsyncClient) -> None:
        """响应头包含 X-Trace-Id。"""
        response = await client.get("/health")
        assert "X-Trace-Id" in response.headers
        assert len(response.headers["X-Trace-Id"]) > 0

    @pytest.mark.asyncio
    async def test_custom_trace_id_passed_through(self, client: AsyncClient) -> None:
        """客户端传入的 X-Trace-Id 被保留。"""
        custom_id = "custom-trace-123"
        response = await client.get("/health", headers={"X-Trace-Id": custom_id})
        assert response.headers["X-Trace-Id"] == custom_id


class TestPathNormalization:
    """路径归一化测试。"""

    def test_normalize_uuid_path(self) -> None:
        """UUID 路径归一化。"""
        path = "/api/v1/sessions/abc12345-1234-1234-1234-123456789abc/messages"
        assert _normalize_path(path) == "/api/v1/sessions/:id/messages"

    def test_normalize_numeric_path(self) -> None:
        """数字 ID 路径归一化。"""
        path = "/api/v1/users/123/profile"
        assert _normalize_path(path) == "/api/v1/users/:id/profile"

    def test_normalize_no_id_path(self) -> None:
        """无 ID 路径不变。"""
        path = "/api/v1/health"
        assert _normalize_path(path) == path