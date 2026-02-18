"""
Prometheus metrics for Edge Gateway (FastAPI).
"""

from prometheus_client import Counter, Gauge, Histogram

# -------------------------
# Request Counter
# -------------------------

CHAT_REQUESTS_TOTAL = Counter(
    "chat_requests_total",
    "Total number of chat completion requests",
    ["model", "status"]
)

# -------------------------
# Token Counters
# -------------------------

CHAT_PROMPT_TOKENS_TOTAL = Counter(
    "chat_prompt_tokens_total",
    "Total prompt tokens processed",
)

CHAT_COMPLETION_TOKENS_TOTAL = Counter(
    "chat_completion_tokens_total",
    "Total completion tokens generated",
)

# -------------------------
# Active Requests Gauge
# -------------------------

ACTIVE_REQUESTS = Gauge(
    "chat_active_requests",
    "Number of active chat requests"
)

# -------------------------
# Latency Histogram
# -------------------------

REQUEST_LATENCY_SECONDS = Histogram(
    "chat_request_latency_seconds",
    "Chat completion request latency",
    buckets=[0.1, 0.3, 0.5, 1, 2, 5, 10]
)

# -------------------------
# Throughput Gauge
# -------------------------

TOKENS_PER_SECOND = Gauge(
    "chat_tokens_per_second",
    "Tokens generated per second (last request)"
)
