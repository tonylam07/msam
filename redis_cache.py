"""
MSAM Redis Caching Layer
Provides high-speed caching for frequently accessed memory atoms
"""

import redis
import json
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class CachedQuery:
    """Represents a cached query result"""
    query_id: str
    query_text: str
    results: Dict[str, Any]
    timestamp: float
    confidence: float
    hit_count: int = 0


class MSAMCache:
    """Redis-based caching layer for MSAM"""
    
    def __init__(self, host='localhost', port=6379, db=0):
        """Initialize Redis connection"""
        self.redis = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.prefix = 'msam:'
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def cache_query(self, query_id: str, query_text: str, 
                   results: Dict[str, Any], ttl: int = 3600) -> bool:
        """Cache a query result with TTL"""
        try:
            cached_query = CachedQuery(
                query_id=query_id,
                query_text=query_text,
                results=results,
                timestamp=time.time()
            )
            
            key = f"{self.prefix}query:{query_id}"
            self.redis.setex(
                key, 
                ttl,
                json.dumps(asdict(cached_query))
            )
            
            # Track in query history
            self.redis.lpush(f"{self.prefix}query_history", query_id)
            self.redis.expire(f"{self.prefix}query_history", 86400)
            
            return True
            
        except redis.RedisError as e:
            print(f"Cache error: {e}")
            return False
    
    def get_cached_query(self, query_id: str) -> Optional[CachedQuery]:
        """Retrieve cached query if available"""
        try:
            key = f"{self.prefix}query:{query_id}"
            data = self.redis.get(key)
            
            if data:
                self.stats['hits'] += 1
                cached_data = json.loads(data)
                return CachedQuery(**cached_data)
            
            self.stats['misses'] += 1
            return None
            
        except redis.RedisError as e:
            print(f"Cache retrieval error: {e}")
            return None
    
    def get_cached_by_query(self, query_text: str, threshold: float = 0.8) -> Optional[CachedQuery]:
        """Find cached query similar to current query"""
        # In production, use embeddings for similarity search
        # For now, use approximate string matching
        try:
            history = self.redis.lrange(f"{self.prefix}query_history", 0, 100)
            
            for query_id in history:
                cached = self.get_cached_query(query_id)
                if cached and query_text.lower() in cached.query_text.lower():
                    cached.hit_count += 1
                    self.cache_query(
                        cached.query_id,
                        cached.query_text,
                        cached.results,
                        ttl=3600
                    )
                    return cached
            
            return None
            
        except Exception as e:
            print(f"Query search error: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            keys_count = self.redis.keys(f"{self.prefix}*")
            
            return {
                **self.stats,
                'total_cached_queries': len(keys_count),
                'memory_usage': self.redis.info('memory').get('used_memory_human', 'N/A'),
                'hit_ratio': self._calculate_hit_ratio()
            }
        except Exception as e:
            print(f"Stats error: {e}")
            return self.stats
    
    def _calculate_hit_ratio(self) -> float:
        """Calculate cache hit ratio"""
        total = self.stats['hits'] + self.stats['misses']
        if total == 0:
            return 0.0
        return round(self.stats['hits'] / total, 2)
    
    def invalidate_query(self, query_id: str) -> bool:
        """Invalidate a specific cached query"""
        try:
            key = f"{self.prefix}query:{query_id}"
            self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Invalidate error: {e}")
            return False
    
    def invalidate_all(self) -> bool:
        """Clear all cached queries"""
        try:
            keys = self.redis.keys(f"{self.prefix}query:*")
            if keys:
                self.redis.delete(*keys)
            self.stats['evictions'] += 1
            return True
        except Exception as e:
            print(f"Clear all error: {e}")
            return False
    
    def cleanup_old_queries(self, max_age_hours: int = 24) -> int:
        """Remove queries older than specified hours"""
        try:
            cutoff_time = time.time() - (max_age_hours * 3600)
            keys_to_delete = []
            
            for key in self.redis.keys(f"{self.prefix}query:*"):
                data = self.redis.get(key)
                if data:
                    cached = json.loads(data)
                    if cached.get('timestamp', 0) < cutoff_time:
                        keys_to_delete.append(key)
            
            if keys_to_delete:
                self.redis.delete(*keys_to_delete)
            
            return len(keys_to_delete)
            
        except Exception as e:
            print(f"Cleanup error: {e}")
            return 0


class CachingDecorator:
    """Decorator for adding caching to MSAM methods"""
    
    def __init__(self, cache: MSAMCache):
        self.cache = cache
        self.query_cache = {}
    
    def cache_query(self, query_func):
        """Decorator to cache query results"""
        import hashlib
        
        def wrapper(*args, **kwargs):
            # Generate query hash from arguments
            query_str = str(args) + str(kwargs)
            query_hash = hashlib.md5(query_str.encode()).hexdigest()
            
            # Check cache first
            cached = self.cache.get_cached_query(query_hash)
            if cached:
                return cached.results
            
            # Execute query
            result = query_func(*args, **kwargs)
            
            # Cache result
            self.cache.cache_query(query_hash, query_str, result)
            
            return result
        
        return wrapper


# Example usage:
if __name__ == "__main__":
    # Initialize cache
    cache = MSAMCache(host='localhost', port=6379)
    
    # Test basic caching
    print("Testing MSAM Cache...")
    
    # Cache a query
    query_id = "test_001"
    results = {
        "atoms": [{"id": "1", "text": "Test atom"}],
        "confidence": 0.95
    }
    
    cache.cache_query(query_id, "test query", results)
    
    # Retrieve cached query
    cached = cache.get_cached_query(query_id)
    if cached:
        print(f"Retrieved cached query: {cached.results}")
    
    # Check stats
    print(f"Cache stats: {cache.get_stats()}")
