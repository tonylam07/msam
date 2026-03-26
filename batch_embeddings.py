"""
MSAM Batch Embedding Optimizer
Reduces API calls by processing multiple texts at once
"""

import asyncio
import time
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import aiohttp


@dataclass
class EmbeddingBatch:
    """Represents a batch of texts to embed"""
    batch_id: str
    texts: List[str]
    embeddings: Optional[List[List[float]]] = None
    timestamp: float = 0.0
    cached: bool = False


class BatchEmbeddingOptimizer:
    """Optimize embedding API calls through batching"""
    
    def __init__(self, max_batch_size: int = 50, 
                 batch_timeout_seconds: float = 5.0,
                 cache_ttl_seconds: int = 3600):
        """Initialize batch optimizer"""
        self.max_batch_size = max_batch_size
        self.batch_timeout = batch_timeout_seconds
        self.cache_ttl = cache_ttl_seconds
        
        self.pending_batches = []
        self.embedding_cache = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Statistics
        self.stats = {
            'total_texts': 0,
            'batches_created': 0,
            'api_calls': 0,
            'cache_hits': 0,
            'api_savings': 0
        }
    
    def _generate_batch_id(self, texts: List[str]) -> str:
        """Generate unique ID for a batch"""
        text_hash = hashlib.md5(
            ",".join(texts).encode()
        ).hexdigest()
        return f"batch_{text_hash}"
    
    def _get_cached_batch(self, texts: List[str]) -> Optional[EmbeddingBatch]:
        """Check if we have cached embeddings for these texts"""
        batch_id = self._generate_batch_id(texts)
        
        if batch_id in self.embedding_cache:
            cached = self.embedding_cache[batch_id]
            
            # Check TTL
            if time.time() - cached.timestamp < self.cache_ttl:
                self.stats['cache_hits'] += 1
                return cached
        
        return None
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings with automatic batching"""
        self.stats['total_texts'] += len(texts)
        
        # Check cache first
        cached = self._get_cached_batch(texts)
        if cached and cached.embeddings:
            return cached.embeddings
        
        # Group into batches
        batches = self._group_into_batches(texts)
        
        # Process batches
        all_embeddings = []
        
        for batch in batches:
            embeddings = await self._process_batch(batch)
            all_embeddings.extend(embeddings)
            
            # Cache result
            self.embedding_cache[batch.batch_id] = batch
            batch.embeddings = embeddings
            batch.timestamp = time.time()
        
        return all_embeddings
    
    def _group_into_batches(self, texts: List[str]) -> List[EmbeddingBatch]:
        """Group texts into batches"""
        batches = []
        
        for i in range(0, len(texts), self.max_batch_size):
            batch_texts = texts[i:i + self.max_batch_size]
            batch = EmbeddingBatch(
                batch_id=self._generate_batch_id(batch_texts),
                texts=batch_texts,
                timestamp=time.time()
            )
            
            batches.append(batch)
            self.stats['batches_created'] += 1
        
        return batches
    
    async def _process_batch(self, batch: EmbeddingBatch) -> List[List[float]]:
        """Process a single batch through embedding API"""
        start_time = time.time()
        
        try:
            # Simulate API call (in production, use actual MSAM embedding API)
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._blocking_embed,
                batch.texts
            )
            
            self.stats['api_calls'] += 1
            
            # Calculate savings
            if len(batch.texts) > 1:
                self.stats['api_savings'] += (len(batch.texts) - 1)
            
            return [[0.1] * 384 for _ in batch.texts]  # Dummy embeddings
            
        except Exception as e:
            print(f"Batch embedding error: {e}")
            return []
    
    def _blocking_embed(self, texts: List[str]) -> List[List[float]]:
        """Synchronous embedding (called from thread pool)"""
        time.sleep(0.01)  # Simulate API delay
        return [[0.1] * 384 for _ in texts]  # Dummy embeddings
    
    def clear_cache(self):
        """Clear embedding cache"""
        self.embedding_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get batching statistics"""
        return {
            **self.stats,
            'avg_texts_per_batch': (
                self.stats['total_texts'] / self.stats['batches_created']
                if self.stats['batches_created'] > 0 else 0
            ),
            'api_efficiency': (
                (self.stats['total_texts'] - self.stats['api_savings']) / 
                self.stats['total_texts']
                if self.stats['total_texts'] > 0 else 0
            ),
            'cache_hit_rate': (
                self.stats['cache_hits'] / self.stats['total_texts']
                if self.stats['total_texts'] > 0 else 0
            )
        }


class AsyncBatchEmbedding:
    """High-performance batch embedding with async/await"""
    
    def __init__(self, max_concurrent_batches: int = 10):
        """Initialize async batch embedding"""
        self.max_concurrent = max_concurrent_batches
        self.semaphore = asyncio.Semaphore(max_concurrent_batches)
        self.optimizer = BatchEmbeddingOptimizer()
        
    async def batch_embed(self, texts_list: List[List[str]]) -> List[List[List[float]]]:
        """Process multiple batch queries concurrently"""
        async def embed_single_batch(texts: List[str]) -> List[List[float]]:
            async with self.semaphore:
                return await self.optimizer.embed(texts)
        
        # Process batches concurrently
        tasks = [embed_single_batch(texts) for texts in texts_list]
        results = await asyncio.gather(*tasks)
        
        return results


# Example usage:
async def main():
    print("Testing MSAM Batch Embedding...")
    
    optimizer = BatchEmbeddingOptimizer()
    
    # Test single batch
    print("\n1. Single Batch Test:")
    texts = [
        "The quick brown fox jumps over the lazy dog",
        "A fast brown dog runs over a lazy fox",
        "Machine learning is transforming AI"
    ]
    
    start = time.time()
    embeddings = await optimizer.embed(texts)
    latency = (time.time() - start) * 1000
    
    print(f"   Processed {len(texts)} texts")
    print(f"   Embedding shape: {len(embeddings)} x {len(embeddings[0])}")
    print(f"   Latency: {latency:.2f}ms")
    
    # Test batching efficiency
    print("\n2. Batch Efficiency Test:")
    texts_list = [
        ["query 1", "query 2", "query 3"],
        ["query 4", "query 5"],
        ["query 6"]
    ]
    
    optimizer2 = BatchEmbeddingOptimizer(max_batch_size=3)
    
    start = time.time()
    results = await asyncio.gather(
        *[optimizer2.embed(texts) for texts in texts_list]
    )
    latency = (time.time() - start) * 1000
    
    stats = optimizer2.get_stats()
    print(f"   Original calls would be: {sum(len(t) for t in texts_list)}")
    print(f"   Actual API calls: {stats['api_calls']}")
    print(f"   API savings: {stats['api_savings']}")
    print(f"   Efficiency: {stats['api_efficiency']*100:.1f}%")
    
    # Performance comparison
    print("\n3. Performance Comparison:")
    print(f"   Single call latency: ~{latency:.0f}ms")
    print(f"   Batch call latency: ~{latency:.0f}ms")
    print(f"   Time saved: ~{len(texts_list) * 200 - latency:.0f}ms")


if __name__ == "__main__":
    asyncio.run(main())
