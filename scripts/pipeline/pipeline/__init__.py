"""Pipeline sub-package — orchestration, phases, and rate limiting."""

# --- Exit codes (from orchestrate.py) ---
from .orchestrate import (
    run_pipeline,
    validate_api_config,
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

# --- Registry (from registry.py) ---
from .registry import (
    PipelineStrategies,
    build_pipeline,
    STRATEGY_REGISTRY,
    PROFILE_KEY_MAP,
    derive_capabilities,
)

# --- Re-exported from lib/ for backward compatibility ---
from ...lib.strategy_loader import parse_strategy
from ...lib.config_resolver import RateLimitConfig, resolve_rate_limit_config

__all__ = [
    "run_pipeline",
    "build_pipeline",
    "parse_strategy",
    "validate_api_config",
    "resolve_rate_limit_config",
    "PipelineStrategies",
    "RateLimitConfig",
    "STRATEGY_REGISTRY",
    "PROFILE_KEY_MAP",
    "derive_capabilities",
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
