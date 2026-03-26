"""
MSAM Security Hardening
JWT authentication, rate limiting, and audit logging
"""

import time
import jwt
import hashlib
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from functools import wraps


@dataclass
class JWTToken:
    """JWT token representation"""
    token: str
    expires_at: float
    user_id: str
    permissions: List[str]


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int = 60
    burst_limit: int = 10
    burst_window_seconds: int = 5


class JWTAuthManager:
    """JWT-based authentication system"""
    
    def __init__(self, secret_key: str = "msam-secret-key-2026"):
        """Initialize JWT auth manager"""
        self.secret_key = secret_key
        self.tokens = {}  # In production, use secure storage
        self.token_expiry_minutes = 60
        
        # Security metrics
        self.stats = {
            'tokens_issued': 0,
            'tokens_validated': 0,
            'tokens_expired': 0,
            'auth_failures': 0
        }
    
    def generate_token(self, user_id: str, permissions: List[str] = None) -> JWTToken:
        """Generate JWT token for user"""
        permissions = permissions or ['read', 'write']
        
        payload = {
            'user_id': user_id,
            'permissions': permissions,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(minutes=self.token_expiry_minutes)
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        
        token_data = JWTToken(
            token=token,
            expires_at=time.time() + (self.token_expiry_minutes * 60),
            user_id=user_id,
            permissions=permissions
        )
        
        self.tokens[token] = token_data
        self.stats['tokens_issued'] += 1
        
        return token_data
    
    def validate_token(self, token: str) -> Optional[JWTToken]:
        """Validate JWT token and return token data"""
        try:
            # Check if token exists in our storage
            if token not in self.tokens:
                self.stats['auth_failures'] += 1
                return None
            
            token_data = self.tokens[token]
            
            # Check expiration
            if time.time() > token_data.expires_at:
                del self.tokens[token]
                self.stats['tokens_expired'] += 1
                return None
            
            # Decode and verify
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            self.stats['tokens_validated'] += 1
            
            return token_data
            
        except jwt.ExpiredSignatureError:
            self.stats['tokens_expired'] += 1
            return None
        except jwt.InvalidTokenError:
            self.stats['auth_failures'] += 1
            return None
    
    def rotate_token(self, old_token: str) -> Optional[JWTToken]:
        """Rotate expired token to new one"""
        token_data = self.validate_token(old_token)
        if token_data:
            new_token = self.generate_token(token_data.user_id, token_data.permissions)
            # Keep old token for smooth transition
            return new_token
        return None
    
    def get_user_permissions(self, token: str) -> Optional[List[str]]:
        """Get permissions for authenticated user"""
        token_data = self.validate_token(token)
        if token_data:
            return token_data.permissions
        return None
    
    def check_permission(self, token: str, required_permission: str) -> bool:
        """Check if user has required permission"""
        permissions = self.get_user_permissions(token)
        if permissions:
            return required_permission in permissions
        return False
    
    def delete_token(self, token: str) -> bool:
        """Invalidate token (logout)"""
        if token in self.tokens:
            del self.tokens[token]
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get authentication statistics"""
        return {
            **self.stats,
            'active_tokens': len(self.tokens),
            'total_issued': self.stats['tokens_issued'],
            'total_validated': self.stats['tokens_validated'],
            'failure_rate': (
                self.stats['auth_failures'] / self.stats['tokens_validated']
                if self.stats['tokens_validated'] > 0 else 0
            )
        }


class RateLimiter:
    """Rate limiting middleware"""
    
    def __init__(self, config: RateLimitConfig = None):
        """Initialize rate limiter"""
        self.config = config or RateLimitConfig()
        self.request_history = {}  # user_id -> list of timestamps
        
        # Security metrics
        self.stats = {
            'total_requests': 0,
            'blocked_requests': 0,
            'rate_limited_users': 0
        }
    
    def is_allowed(self, user_id: str) -> bool:
        """Check if user is allowed to make request"""
        current_time = time.time()
        user_id = user_id or "anonymous"
        
        self.stats['total_requests'] += 1
        
        # Clean old requests (older than window)
        if user_id not in self.request_history:
            self.request_history[user_id] = []
        
        self.request_history[user_id] = [
            t for t in self.request_history[user_id]
            if current_time - t < self.config.burst_window_seconds
        ]
        
        # Check burst limit
        if len(self.request_history[user_id]) >= self.config.burst_limit:
            self.stats['blocked_requests'] += 1
            return False
        
        # Check minute-based limit
        minute_ago = current_time - 60
        recent_requests = [
            t for t in self.request_history[user_id]
            if t > minute_ago
        ]
        
        if len(recent_requests) >= self.config.requests_per_minute:
            self.stats['blocked_requests'] += 1
            self.stats['rate_limited_users'] += 1
            return False
        
        # Allow request
        self.request_history[user_id].append(current_time)
        return True
    
    def get_remaining_requests(self, user_id: str) -> int:
        """Get remaining requests for user"""
        user_id = user_id or "anonymous"
        
        if user_id not in self.request_history:
            return self.config.requests_per_minute
        
        minute_ago = time.time() - 60
        recent_requests = len([
            t for t in self.request_history[user_id]
            if t > minute_ago
        ])
        
        return max(0, self.config.requests_per_minute - recent_requests)
    
    def get_reset_time(self, user_id: str) -> float:
        """Get time until rate limit resets"""
        user_id = user_id or "anonymous"
        
        if user_id not in self.request_history:
            return 0
        
        oldest_request = min(self.request_history[user_id])
        return oldest_request + 60 - time.time()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        return {
            **self.stats,
            'total_allowed': (
                self.stats['total_requests'] - self.stats['blocked_requests']
            ),
            'block_rate': (
                self.stats['blocked_requests'] / self.stats['total_requests']
                if self.stats['total_requests'] > 0 else 0
            )
        }


class AuditLogger:
    """Security audit logging system"""
    
    def __init__(self, log_file: str = "msam-audit.log"):
        """Initialize audit logger"""
        self.log_file = log_file
        self.log_buffer = []
        
        # Security metrics
        self.stats = {
            'queries_logged': 0,
            'auth_events': 0,
            'security_events': 0,
            'error_events': 0
        }
    
    def log_query(self, user_id: str, query_text: str, success: bool, latency_ms: float):
        """Log API query"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'query',
            'user_id': user_id,
            'query_text': query_text[:100],  # Truncate for security
            'success': success,
            'latency_ms': latency_ms
        }
        
        self._log_event(event)
        self.stats['queries_logged'] += 1
    
    def log_auth(self, user_id: str, event_type: str, success: bool):
        """Log authentication event"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'auth',
            'sub_type': event_type,
            'user_id': user_id,
            'success': success
        }
        
        self._log_event(event)
        self.stats['auth_events'] += 1
    
    def log_security_event(self, user_id: str, event: str, severity: str = 'info'):
        """Log security event"""
        event_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'security',
            'user_id': user_id,
            'event': event,
            'severity': severity
        }
        
        self._log_event(event_data)
        self.stats['security_events'] += 1
    
    def log_error(self, error: str, user_id: str = None):
        """Log error event"""
        event_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'error',
            'user_id': user_id or 'unknown',
            'error': error[:200]  # Truncate
        }
        
        self._log_event(event_data)
        self.stats['error_events'] += 1
    
    def _log_event(self, event: Dict[str, Any]):
        """Write event to log"""
        self.log_buffer.append(event)
        
        # Periodically flush to file
        if len(self.log_buffer) >= 100:
            self._flush_log()
    
    def _flush_log(self):
        """Flush log buffer to file"""
        try:
            with open(self.log_file, 'a') as f:
                for event in self.log_buffer:
                    f.write(f"{event['timestamp']} - {event['event_type']} - {event}\n")
            self.log_buffer = []
        except Exception as e:
            print(f"Log flush error: {e}")
    
    def get_recent_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent audit events"""
        return self.log_buffer[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get audit statistics"""
        return {
            **self.stats,
            'buffer_size': len(self.log_buffer),
            'total_events': (
                self.stats['queries_logged'] +
                self.stats['auth_events'] +
                self.stats['security_events'] +
                self.stats['error_events']
            )
        }


# Example usage:
async def main():
    print("Testing MSAM Security Hardening...\n")
    
    # Test JWT Auth
    print("1. JWT Authentication Test:")
    jwt_mgr = JWTAuthManager()
    
    token_data = jwt_mgr.generate_token("user_001", ['read', 'write', 'admin'])
    print(f"   Generated token: {token_data.token[:50]}...")
    print(f"   Expires: {datetime.fromtimestamp(token_data.expires_at)}")
    print(f"   Permissions: {token_data.permissions}")
    
    # Validate token
    validated = jwt_mgr.validate_token(token_data.token)
    print(f"   Validated: {validated is not None}")
    
    # Check permission
    has_admin = jwt_mgr.check_permission(token_data.token, 'admin')
    print(f"   Has admin permission: {has_admin}")
    
    # Test rate limiting
    print("\n2. Rate Limiting Test:")
    limiter = RateLimiter()
    
    # Simulate requests
    for i in range(5):
        allowed = limiter.is_allowed("user_001")
        remaining = limiter.get_remaining_requests("user_001")
        print(f"   Request {i+1}: {allowed} (remaining: {remaining})")
    
    # Test audit logging
    print("\n3. Audit Logging Test:")
    logger = AuditLogger()
    
    logger.log_query("user_001", "test query", True, 25.5)
    logger.log_auth("user_001", "login", True)
    logger.log_security_event("user_001", "login attempt", "info")
    
    print(f"   Logged {len(logger.log_buffer)} events")
    print(f"   Stats: {logger.get_stats()}")
    
    # Print stats
    print("\n4. Security Statistics:")
    print(f"   JWT tokens issued: {jwt_mgr.stats['tokens_issued']}")
    print(f"   Rate limit blocks: {limiter.stats['blocked_requests']}")
    print(f"   Audit events: {logger.stats['total_events']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
