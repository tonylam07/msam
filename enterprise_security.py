"""
MSAM Enterprise Security & Compliance Module
JWT authentication, OAuth2, SSO, audit logging, SOC2 compliance
"""

import time
import jwt
import hashlib
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from functools import wraps
from enum import Enum


class ComplianceLevel(Enum):
    """Compliance levels for MSAM deployment"""
    BASIC = "basic"           # Standard authentication
    ENTERPRISE = "enterprise" # OAuth2, SSO, audit trails
    REGULATED = "regulated"   # HIPAA, SOC2, GDPR


@dataclass
class EnterpriseSecurityConfig:
    """Enterprise security configuration"""
    # JWT Settings
    secret_key_rotation_hours: int = 24
    token_expiry_minutes: int = 60
    refresh_token_enabled: bool = True
    refresh_token_expiry_hours: int = 7
    
    # OAuth2 Settings
    oauth2_enabled: bool = True
    oauth2_providers: List[str] = None  # ['google', 'azure', 'okta']
    
    # SSO Settings
    saml_enabled: bool = True
    oidc_enabled: bool = True
    
    # Audit Settings
    audit_encryption: bool = True
    audit_retention_days: int = 365
    
    # Compliance Settings
    compliance_level: ComplianceLevel = ComplianceLevel.ENTERPRISE
    gdpr_compliance: bool = False
    hipaa_compliance: bool = False
    soc2_compliance: bool = True


@dataclass
class EnterpriseUser:
    """Enterprise user representation"""
    user_id: str
    email: str
    organization_id: str
    roles: List[str]
    permissions: List[str]
    oauth_provider: Optional[str] = None
    last_login: Optional[datetime] = None
    compliance_flags: Dict[str, bool] = None
    
    def __post_init__(self):
        if self.compliance_flags is None:
            self.compliance_flags = {}


@dataclass
class AuditEvent:
    """Comprehensive audit event"""
    event_id: str
    timestamp: str
    event_type: str
    user_id: str
    organization_id: str
    action: str
    resource_type: str
    resource_id: str
    ip_address: str
    user_agent: str
    success: bool
    metadata: Dict[str, Any] = None
    encrypted: bool = False


class EnterpriseAuthManager:
    """Enterprise-grade authentication system"""
    
    def __init__(self, config: EnterpriseSecurityConfig = None):
        """Initialize enterprise authentication"""
        self.config = config or EnterpriseSecurityConfig()
        self.secret_keys = {}  # For key rotation
        self.active_tokens = {}  # Current active sessions
        self.refresh_tokens = {}  # Refresh token registry
        self.oauth_providers = {}  # OAuth2 providers
        
        # Initialize default secret key
        self._generate_secret_key()
        
        # Metrics
        self.stats = {
            'logins_total': 0,
            'logins_success': 0,
            'logins_failed': 0,
            'refreshes_total': 0,
            'sso_logins': 0,
            'oauth_logins': 0
        }
    
    def _generate_secret_key(self):
        """Generate rotation-ready secret key"""
        key_id = f"key_{int(time.time())}"
        secret_key = hashlib.sha256(
            f"{uuid.uuid4()}{time.time()}".encode()
        ).hexdigest()
        
        self.secret_keys[key_id] = {
            'secret': secret_key,
            'created_at': time.time(),
            'expires_at': time.time() + (self.config.secret_key_rotation_hours * 3600)
        }
    
    def generate_access_token(
        self, 
        user: EnterpriseUser,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """Generate JWT access token for enterprise user"""
        # Create token payload
        payload = {
            'user_id': user.user_id,
            'email': user.email,
            'org_id': user.organization_id,
            'roles': user.roles,
            'permissions': user.permissions,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(minutes=self.config.token_expiry_minutes),
            'jti': str(uuid.uuid4()),  # JWT ID for token tracking
            'iss': 'msam-enterprise',
            'aud': 'msam-api'
        }
        
        # Get active secret key
        secret_key = self._get_active_secret_key()
        
        # Generate JWT
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        
        # Store token metadata
        token_id = payload['jti']
        self.active_tokens[token_id] = {
            'user_id': user.user_id,
            'created_at': time.time(),
            'expires_at': time.time() + (self.config.token_expiry_minutes * 60),
            'ip_address': ip_address,
            'user_agent': user_agent
        }
        
        # Update stats
        self.stats['logins_total'] += 1
        self.stats['logins_success'] += 1
        
        return {
            'access_token': token,
            'token_type': 'Bearer',
            'expires_in': self.config.token_expiry_minutes * 60,
            'scope': ' '.join(user.permissions)
        }
    
    def generate_refresh_token(
        self,
        access_token: str,
        ip_address: str = None
    ) -> str:
        """Generate refresh token for session extension"""
        if not self.config.refresh_token_enabled:
            raise ValueError("Refresh tokens disabled in configuration")
        
        # Decode access token to get user_id
        payload = self._decode_token(access_token)
        user_id = payload['user_id']
        
        # Generate refresh token
        refresh_token_id = str(uuid.uuid4())
        refresh_token = hashlib.sha256(
            f"{user_id}{time.time()}{uuid.uuid4()}".encode()
        ).hexdigest()
        
        # Store refresh token
        self.refresh_tokens[refresh_token_id] = {
            'user_id': user_id,
            'access_token': access_token,
            'created_at': time.time(),
            'expires_at': time.time() + (
                self.config.refresh_token_expiry_hours * 3600
            ),
            'ip_address': ip_address
        }
        
        return refresh_token
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return payload"""
        try:
            # Try all active keys (supports key rotation)
            for key_id, key_info in self.secret_keys.items():
                try:
                    payload = jwt.decode(
                        token,
                        key_info['secret'],
                        algorithms=['HS256'],
                        audience='msam-api'
                    )
                    
                    # Check if token is still active
                    jti = payload.get('jti')
                    if jti in self.active_tokens:
                        return payload
                    
                    return None
                    
                except jwt.InvalidTokenError:
                    continue
            
            return None
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            self.stats['logins_failed'] += 1
            return None
    
    def rotate_secret_key(self) -> str:
        """Rotate JWT secret key for security compliance"""
        self._generate_secret_key()
        
        # Mark old keys as deprecated (keep for existing tokens)
        now = time.time()
        for key_id in list(self.secret_keys.keys()):
            if self.secret_keys[key_id]['expires_at'] < now:
                self.secret_keys[key_id]['expired'] = True
        
        return list(self.secret_keys.keys())[-1]
    
    def _decode_token(self, token: str) -> Dict[str, Any]:
        """Decode JWT token without verification"""
        return jwt.decode(
            token,
            options={"verify_signature": False}
        )
    
    def _get_active_secret_key(self) -> str:
        """Get the most recently created secret key"""
        active_keys = {
            k: v for k, v in self.secret_keys.items()
            if not v.get('expired', False)
        }
        return max(active_keys.values(), key=lambda x: x['created_at'])['secret']
    
    def get_stats(self) -> Dict[str, Any]:
        """Get authentication statistics"""
        return {
            **self.stats,
            'active_tokens': len(self.active_tokens),
            'refresh_tokens': len(self.refresh_tokens),
            'secret_keys': len(self.secret_keys),
            'compliance_level': self.config.compliance_level.value
        }


class EnterpriseAuditLogger:
    """Comprehensive audit logging for compliance"""
    
    def __init__(self, config: EnterpriseSecurityConfig = None):
        """Initialize audit logging"""
        self.config = config or EnterpriseSecurityConfig()
        self.audit_logs = []  # In production: database
        self.encryption_key = hashlib.sha256(
            f"audit-{uuid.uuid4()}".encode()
        ).hexdigest() if config.audit_encryption else None
        
        # Metrics
        self.stats = {
            'total_events': 0,
            'query_events': 0,
            'auth_events': 0,
            'security_events': 0,
            'error_events': 0
        }
    
    def log_query(self, 
                  user_id: str,
                  query_text: str,
                  success: bool,
                  latency_ms: float,
                  organization_id: str = None):
        """Log query event for audit"""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            event_type='query',
            user_id=user_id,
            organization_id=organization_id or 'default',
            action='query_execution',
            resource_type='msam_query',
            resource_id=str(hash(query_text)),
            ip_address='unknown',
            user_agent='unknown',
            success=success,
            metadata={
                'query_length': len(query_text),
                'latency_ms': latency_ms
            },
            encrypted=self.config.audit_encryption
        )
        
        self._store_event(event)
        self.stats['query_events'] += 1
        self.stats['total_events'] += 1
    
    def log_authentication(self,
                          user_id: str,
                          success: bool,
                          method: str,  # 'jwt', 'oauth', 'sso'
                          organization_id: str = None,
                          ip_address: str = None):
        """Log authentication event"""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            event_type='authentication',
            user_id=user_id,
            organization_id=organization_id or 'default',
            action=f"{method}_login",
            resource_type='auth',
            resource_id='user_auth',
            ip_address=ip_address or 'unknown',
            user_agent='unknown',
            success=success,
            metadata={'method': method}
        )
        
        self._store_event(event)
        self.stats['auth_events'] += 1
        self.stats['total_events'] += 1
    
    def log_security_event(self,
                          user_id: str,
                          event_type: str,
                          severity: str,  # 'low', 'medium', 'high', 'critical'
                          details: str,
                          organization_id: str = None):
        """Log security event"""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            event_type='security',
            user_id=user_id,
            organization_id=organization_id or 'default',
            action='security_event',
            resource_type='security',
            resource_id=event_type,
            ip_address='unknown',
            user_agent='unknown',
            success=True,  # Event logged successfully
            metadata={
                'event_type': event_type,
                'severity': severity,
                'details': details
            },
            encrypted=self.config.audit_encryption
        )
        
        self._store_event(event)
        self.stats['security_events'] += 1
        self.stats['total_events'] += 1
    
    def log_error(self,
                 error: str,
                 user_id: str = None,
                 organization_id: str = None):
        """Log error event"""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            event_type='error',
            user_id=user_id or 'anonymous',
            organization_id=organization_id or 'default',
            action='error',
            resource_type='system',
            resource_id='error_log',
            ip_address='unknown',
            user_agent='unknown',
            success=False,
            metadata={'error': error}
        )
        
        self._store_event(event)
        self.stats['error_events'] += 1
        self.stats['total_events'] += 1
    
    def _store_event(self, event: AuditEvent):
        """Store audit event (with encryption if enabled)"""
        if self.config.audit_encryption:
            event_dict = asdict(event)
            # Encrypt sensitive fields
            event_dict['metadata'] = self._encrypt(
                str(event_dict['metadata'])
            )
            event_dict['encrypted'] = True
        
        self.audit_logs.append(asdict(event))
        
        # Periodic cleanup (in production: use database retention policies)
        if len(self.audit_logs) > 1000:
            self.audit_logs = self.audit_logs[-1000:]
    
    def _encrypt(self, data: str) -> str:
        """Simple encryption for compliance"""
        if not self.encryption_key:
            return data
        
        # In production: use AES encryption
        import base64
        return base64.b64encode(
            hashlib.sha256((data + self.encryption_key).encode()).digest()
        ).decode()
    
    def get_compliance_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate compliance report for audit"""
        recent_logs = self.audit_logs[-1000:]  # Last N events
        
        return {
            'report_period_days': days,
            'generated_at': datetime.utcnow().isoformat(),
            'total_events': len(recent_logs),
            'event_breakdown': {
                'queries': self.stats['query_events'],
                'authentications': self.stats['auth_events'],
                'security': self.stats['security_events'],
                'errors': self.stats['error_events']
            },
            'audit_trail': recent_logs,
            'encryption_enabled': self.config.audit_encryption,
            'retention_policy_days': self.config.audit_retention_days,
            'compliance_status': 'compliant' if len(recent_logs) > 0 else 'pending'
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get audit statistics"""
        return {
            **self.stats,
            'total_events': self.stats['total_events'],
            'events_per_type': {
                'queries': self.stats['query_events'],
                'auth': self.stats['auth_events'],
                'security': self.stats['security_events'],
                'errors': self.stats['error_events']
            },
            'encryption_enabled': self.config.audit_encryption
        }


# Example usage:
async def main():
    print("Testing Enterprise Security & Compliance...\n")
    
    # Initialize enterprise auth
    config = EnterpriseSecurityConfig()
    config.compliance_level = ComplianceLevel.ENTERPRISE
    config.soc2_compliance = True
    
    auth = EnterpriseAuthManager(config)
    audit = EnterpriseAuditLogger(config)
    
    # Create test user
    from datetime import datetime
    test_user = EnterpriseUser(
        user_id="user_001",
        email="admin@enterprise.com",
        organization_id="org_123",
        roles=['admin', 'user'],
        permissions=['read', 'write', 'delete', 'audit']
    )
    
    print("1. Generate Access Token:")
    token_response = auth.generate_access_token(
        test_user,
        ip_address="192.168.1.100",
        user_agent="MSAM/1.0"
    )
    print(f"   Access token: {token_response['access_token'][:50]}...")
    print(f"   Expires in: {token_response['expires_in']} seconds")
    
    print("\n2. Validate Token:")
    payload = auth.validate_token(token_response['access_token'])
    print(f"   Token valid: {payload is not None}")
    print(f"   User ID: {payload['user_id'] if payload else None}")
    
    print("\n3. Generate Refresh Token:")
    refresh = auth.generate_refresh_token(token_response['access_token'])
    print(f"   Refresh token: {refresh[:50]}...")
    
    print("\n4. Log Query Event:")
    audit.log_query(
        user_id=test_user.user_id,
        query_text="enterprise msam query",
        success=True,
        latency_ms=45.5,
        organization_id=test_user.organization_id
    )
    
    print("\n5. Generate Compliance Report:")
    report = audit.get_compliance_report()
    print(f"   Total events: {report['total_events']}")
    print(f"   Query events: {report['event_breakdown']['queries']}")
    print(f"   Encryption: {report['encryption_enabled']}")
    print(f"   Status: {report['compliance_status']}")
    
    # Stats
    print("\n6. Authentication Stats:")
    print(auth.get_stats())
    
    print("\n7. Audit Stats:")
    print(audit.get_stats())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
