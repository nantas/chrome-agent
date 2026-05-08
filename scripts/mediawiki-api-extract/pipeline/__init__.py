"""Pipeline sub-package — orchestration, phases, and rate limiting."""

from .orchestrate import (
    run_pipeline,
    build_pipeline,
    parse_strategy,
    validate_api_config,
    PipelineStrategies,
    RateLimitConfig,
    # Exit codes
    EXIT_SUCCESS,
    EXIT_PARTIAL_SUCCESS,
    EXIT_API_UNREACHABLE,
    EXIT_PHASE_A_FAILURE,
    EXIT_PHASE_B_FAILURE,
    EXIT_PHASE_C_FAILURE,
    EXIT_STRATEGY_ERROR,
    EXIT_INVALID_ARGS,
    EXIT_VALIDATION_FAILURE,
)
from .rate_limit import RateLimitConfig as _RateLimitConfig, resolve_rate_limit_config

# Use the RateLimitConfig from rate_limit.py as canonical
RateLimitConfig = _RateLimitConfig

__all__ = [
    "run_pipeline",
    "build_pipeline",
    "parse_strategy",
    "validate_api_config",
    "resolve_rate_limit_config",
    "PipelineStrategies",
    "RateLimitConfig",
    "EXIT_SUCCESS",
    "EXIT_PARTIAL_SUCCESS",
    "EXIT_API_UNREACHABLE",
    "EXIT_PHASE_A_FAILURE",
    "EXIT_PHASE_B_FAILURE",
    "EXIT_PHASE_C_FAILURE",
    "EXIT_STRATEGY_ERROR",
    "EXIT_INVALID_ARGS",
    "EXIT_VALIDATION_FAILURE",
]
