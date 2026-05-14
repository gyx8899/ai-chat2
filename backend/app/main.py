"""FastAPI 应用入口。

重构后采用 DDD 分层架构。
集成：
- 路由（chat/sessions/config）
- 中间件（CORS/TraceId/Metrics）
- 结构化日志（structlog）
- Prometheus 指标（/metrics）
- 统一异常处理
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.settings import get_settings
from app.db.database import init_db
from app.core.exceptions import AppException
from app.core.prompts.service import get_prompt_service
from app.observability.logging import configure_logging, get_logger
from app.observability.metrics import MetricsMiddleware, get_metrics_response
from app.observability.middleware import TraceIdMiddleware
from app.routers import chat, config, prompts, sessions

# 配置日志（应用启动前）
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理。"""
    logger.info("application_initializing")
    await init_db()
    # 初始化提示词服务（启动失败则 lifespan 抛出，FastAPI 拒绝启动）
    await get_prompt_service().init()
    logger.info("application_ready")
    yield
    logger.info("application_shutdown")


settings = get_settings()

app = FastAPI(
    title=settings.title,
    version=settings.version,
    description=settings.api.description,
    lifespan=lifespan,
)

# ============================================================================
# 中间件注册（顺序重要：外层 → 内层）
# ============================================================================

# 1. CORS（最外层）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Trace-Id"],
)

# 2. Metrics（采集 HTTP 指标）
app.add_middleware(MetricsMiddleware)

# 3. TraceId（注入 trace_id 到日志，最内层）
app.add_middleware(TraceIdMiddleware)


# ============================================================================
# 统一异常处理
# ============================================================================


@app.exception_handler(AppException)
async def app_exception_handler(
    request: Request, exc: AppException
) -> JSONResponse:
    """处理业务异常，返回统一错误格式。"""
    logger.warning(
        "app_exception",
        error_code=exc.code.value,
        error_message=exc.message,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=exc.http_status,
        content=exc.to_dict(),
    )


# ============================================================================
# 路由注册
# ============================================================================
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(config.router, prefix="/api/v1/config", tags=["config"])
app.include_router(prompts.router, prefix="/api/v1/config/prompts", tags=["prompts"])


# ============================================================================
# 系统端点
# ============================================================================


@app.get("/health")
async def health_check() -> dict[str, str]:
    """健康检查。"""
    return {"status": "ok"}


@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus 指标端点。"""
    return get_metrics_response()


@app.get("/")
async def root() -> dict[str, str]:
    """根路径。"""
    return {
        "name": settings.app_name,
        "version": settings.version,
    }