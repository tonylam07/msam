# MSAM Performance Optimization Modules

## Overview

This repository contains performance optimization modules for MSAM (Multi-Stream Adaptive Memory). The modules provide:

- Redis-based query caching
- Local embedding generation with ONNX support
- Asynchronous retrieval for high concurrency
- Batch embedding optimization
- JWT authentication and rate limiting
- Enhanced security with SOC2/GDPR compliance
- Multi-backend embedding support
- Prometheus metrics export

## Modules

### 1. redis_cache.py
Redis-based query caching system.
- Query result caching with configurable TTL
- Cache hit/miss tracking
- Statistics monitoring
- Graceful fallback when Redis is unavailable

### 2. local_embeddings.py
Local embedding generation module.
- Supports sentence-transformers/all-MiniLM-L6-v2
- Optional ONNX runtime acceleration
- Fallback to API-based embeddings
- Automatic model loading and caching

### 3. async_retrieval.py
Asynchronous retrieval system.
- Non-blocking I/O operations
- Thread pool management (50 concurrent queries)
- Performance metrics collection
- Timeout handling

### 4. batch_embeddings.py
Batch embedding optimization.
- Automatic batching of embedding requests
- Configurable batch size (default: 50)
- API call reduction through batching
- Performance tracking

### 5. security.py
Basic authentication and rate limiting.
- JWT token generation and validation
- User permission management
- IP-based rate limiting
- 20-byte encryption keys
- Request throttling

### 6. enterprise_security.py
Enhanced security features.
- JWT with automatic key rotation (24h)
- Token refresh mechanism (7-day expiry)
- OAuth2 support (Google, Azure, Okta)
- SSO support (SAML 2.0, OIDC)
- Audit logging with encryption
- 365-day audit retention
- SOC2 compliance features
- Role-based access control (RBAC)
- GDPR compliance option
- HIPAA compliance option

### 7. multi_strategy_embeddings.py
Multi-backend embedding support.
- Supports multiple embedding backends
- Auto-selection based on query type
- Performance tracking per strategy
- Graceful fallback between backends

### 8. metrics_exporter.py
Prometheus metrics exporter.
- Real-time performance monitoring
- Query latency metrics
- Cache hit ratio tracking
- API efficiency metrics
- Cost tracking
- Exports to port 9090
- Prometheus-compatible metrics format

### 9. optimization_suite.py
Unified optimization manager.
- Integrates all optimization modules
- Centralized configuration
- Orchestration of optimizations
- Easy deployment and configuration

## Installation

### Prerequisites

- Python 3.11+
- Redis server (optional but recommended)

### Dependencies

```bash
pip install redis pyjwt sentence-transformers
```

### Optional Dependencies

```bash
# For ONNX runtime acceleration
pip install onnxruntime
```

## Configuration

### JWT Settings

- Token expiry: 60 minutes
- Key rotation: 24 hours
- Refresh tokens: 7-day expiry
- Encryption: 20-byte keys

### Embedding Configuration

- Primary model: all-MiniLM-L6-v2
- Supports ONNX runtime for acceleration
- Fallback to API-based embeddings
- Auto-selection based on query context

### Security Features

- SOC2 compliance enabled
- GDPR compliance option
- HIPAA compliance option
- Event encryption
- Audit logging with encryption

## Usage

### Basic Usage

```python
from optimization_suite import MSAMOptimizationSuite

# Initialize the optimization suite
suite = MSAMOptimizationSuite()

# Execute optimized query
result = await suite.optimized_query("Your query here")
```

### Redis Caching

```python
from redis_cache import RedisCache

cache = RedisCache(host="localhost", port=6379)
cache.set("query_key", "result", ttl=3600)
result = cache.get("query_key")
```

### Local Embeddings

```python
from local_embeddings import LocalEmbeddings

embeddings = LocalEmbeddings(model="all-MiniLM-L6-v2")
result = embeddings.generate("text to embed")
```

### Async Retrieval

```python
from async_retrieval import AsyncRetrieval

retriever = AsyncRetrieval(max_concurrent=50)
results = await retriever.query("search query")
```

## Metrics

Metrics are available at `http://localhost:9090/metrics`.

### Available Metrics

- `msam_query_latency_seconds` - Query latency histogram
- `msam_cache_hits_total` - Cache hit count
- `msam_cache_misses_total` - Cache miss count
- `msam_api_calls_total` - API call count
- `msam_local_embeddings_enabled_total` - Local embedding status
- `msam_tokens_total` - Token usage
- `msam_errors_total` - Error count

### Example Prometheus Configuration

```yaml
scrape_configs:
  - job_name: 'msam'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'
```

## Testing

All modules have been validated:

- ✅ Module import: All 9 modules load successfully
- ✅ Authentication: JWT generation/validation working
- ✅ Rate limiting: IP-based limiting functional
- ✅ Async retrieval: 50 concurrent queries supported
- ✅ Batch optimization: Batching working
- ✅ Fallback mechanisms: Active and tested

### Run Tests

```bash
# Validate modules
python validate_modules.py

# Performance testing
python performance_test_suite.py

# Comprehensive testing
python comprehensive_test.py
```

## Cross-Platform Support

All modules work on:

- Windows (10/11, Server 2019/2022)
- Linux (Ubuntu 22.04+, RHEL 8+, Debian 11+)
- macOS (Intel + Apple Silicon)
- Docker/Kubernetes

## Security Considerations

- All sensitive data is encrypted at rest
- Audit logs are encrypted and retained for 365 days
- JWT keys rotate automatically every 24 hours
- Rate limiting prevents abuse
- SOC2 compliant audit trails
- GDPR compliant data handling

## File Structure

```
msam/
├── redis_cache.py              # Redis caching module
├── local_embeddings.py         # Local embedding generation
├── async_retrieval.py          # Async retrieval system
├── batch_embeddings.py         # Batch optimization
├── security.py                 # Basic auth & rate limiting
├── enterprise_security.py      # Enhanced security
├── multi_strategy_embeddings.py # Multi-backend support
├── metrics_exporter.py         # Prometheus metrics
├── optimization_suite.py       # Unified manager
├── validate_modules.py         # Module validation
├── performance_test_suite.py   # Performance tests
└── comprehensive_test.py       # Comprehensive tests
```

## License

This project is licensed under the same license as the MSAM project.

## Support

For issues and questions, please open an issue on the MSAM repository or contact the maintainers.

## Status

All optimizations are production-ready and tested.
