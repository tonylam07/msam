# MSAM Optimization Alerting Rules
Production-grade alerting for monitoring system health

## Alert Definitions

### 🔴 Latency Spike
**Threshold:** Query latency > 500ms for > 1 minute  
**Impact:** Degraded user experience  
**Action:** Investigate query performance, check cache hits

```yaml
- alert: MSAM_HighLatency
  expr: msam_query_latency_seconds_p95 > 0.5
  for: 1m
  labels:
    severity: warning
  annotations:
    summary: "MSAM query latency is high"
    description: "P95 latency {{ $value | humanizeDuration }} exceeds threshold"
```

### 🟠 High Error Rate
**Threshold:** Error rate > 5% for > 5 minutes  
**Impact:** System reliability issues  
**Action:** Check query logs, validate authentication

```yaml
- alert: MSAM_HighErrorRate
  expr: |
    (rate(msam_queries_error_total[5m]) / 
     (rate(msam_queries_error_total[5m]) + 
      rate(msam_queries_success_total[5m]))) * 100 > 5
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "MSAM error rate is high"
    description: "Error rate {{ $value | humanize | humanizePercent }} exceeds 5%"
```

### 🟡 Cache Degradation
**Threshold:** Cache hit ratio < 50% for > 10 minutes  
**Impact:** Increased API calls, higher latency  
**Action:** Investigate caching patterns, check cache size

```yaml
- alert: MSAM_CacheDegradation
  expr: msam_cache_hit_ratio < 0.5
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "MSAM cache hit ratio is low"
    description: "Cache hit ratio {{ $value | humanizePercent }} below optimal"
```

### 🟠 API Efficiency Drop
**Threshold:** API calls not being batched efficiently  
**Impact:** Increased API costs, slower performance  
**Action:** Review batch embedding patterns

```yaml
- alert: MSAM_LowAPIEfficiency
  expr: msam_batch_api_calls_saved_total / msam_api_calls_total < 0.3
  for: 15m
  labels:
    severity: warning
  annotations:
    summary: "MSAM API efficiency is low"
    description: "Only {{ $value | humanizePercent }} of API calls are batched"
```

### 🔴 Security Alerts

#### Auth Failures
**Threshold:** > 10 authentication failures in 1 minute  
**Action:** Check for brute force attacks, review user credentials

```yaml
- alert: MSAM_AuthFailures
  expr: rate(msam_auth_failures_total[1m]) > 0.167
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "High authentication failure rate"
    description: "{{ $value | humanizeRate }} auth failures per second"
```

#### Rate Limiting
**Threshold:** > 5% requests rate limited  
**Action:** Check if legitimate users are being blocked

```yaml
- alert: MSAM_HighRateLimiting
  expr: |
    (rate(msam_rate_limited_requests_total[5m]) / 
     (rate(msam_queries_total[5m]) + 
      rate(msam_queries_error_total[5m]))) * 100 > 5
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High rate limiting frequency"
    description: "{{ $value | humanizePercent }} of requests being rate limited"
```

### 🔵 Concurrent Queries
**Threshold:** Concurrent queries > 40 (approaching limit)  
**Action:** Prepare for increased load, scale if needed

```yaml
- alert: MSAM_HighConcurrency
  expr: msam_concurrent_queries_current > 40
  for: 2m
  labels:
    severity: info
  annotations:
    summary: "MSAM high concurrent query count"
    description: "{{ $value }} concurrent queries (max: {{ $labels.max }})"
```

## Alert Routing

### Critical Alerts (🔴)
- **Latency Spike:** > 500ms
- **High Error Rate:** > 5%
- **Auth Failures:** > 10/min

**Notification:** Email + Slack + PagerDuty

### Warning Alerts (🟠/🟡)
- **Cache Degradation:** < 50% hit ratio
- **API Efficiency:** < 30% batched
- **Rate Limiting:** > 5% blocked
- **High Concurrency:** > 40 queries

**Notification:** Email + Slack

### Info Alerts (🔵)
- **Concurrent Queries:** > 40 (just monitoring)

**Notification:** Slack only

## Response Procedures

### For Latency Spike:
1. Check cache hit ratio
2. Review query patterns
3. Verify local embeddings status
4. Check async queue depth

### For High Error Rate:
1. Examine query logs
2. Validate authentication tokens
3. Check rate limiting settings
4. Review recent deployments

### For Cache Degradation:
1. Increase cache TTL if appropriate
2. Review query patterns for caching opportunities
3. Check Redis connection status
4. Consider cache warming

### For API Efficiency:
1. Review batch embedding patterns
2. Check query deduplication
3. Verify batch optimizer settings
4. Consider increasing batch size

---

**Alerting Rules Active:** ✅  
**Monitoring Dashboard:** ✅  
**Alert Notification:** Configured
