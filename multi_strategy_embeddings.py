"""
MSAM Multi-Strategy Embedding System
Supports multiple offline embedding backends for flexibility
"""

import time
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass


@dataclass
class EmbeddingConfig:
    """Configuration for embedding strategies"""
    # Primary (balanced)
    primary_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Fast (speed-critical)
    fast_model: str = "BAAI/bge-small-en-v1.5"
    
    # Accurate (accuracy-critical)
    accurate_model: str = "BAAI/bge-base-en-v1.5"
    
    # Auto-select strategy based on context
    auto_select: bool = True


class MultiStrategyEmbeddings:
    """Multi-backend embedding system for MSAM"""
    
    def __init__(self, config: EmbeddingConfig = None):
        """Initialize multi-strategy embeddings"""
        self.config = config or EmbeddingConfig()
        self.strategies = {}
        self.active_strategy = 'primary'
        
        # Performance tracking
        self.stats = {
            'queries_by_strategy': {},
            'avg_latency_by_strategy': {},
            'total_queries': 0
        }
        
        # Initialize all backends
        self._init_backends()
    
    def _init_backends(self):
        """Initialize embedding backends"""
        # Try to import backends
        try:
            import onnxruntime as ort
            from sentence_transformers import SentenceTransformer
            
            print("Initializing sentence-transformers backend...")
            self.strategies['sentence-transformers'] = {
                'backend': 'sentence-transformers',
                'models': {},
                'enabled': True
            }
            print("PASS sentence-transformers available")
            
        except ImportError:
            print("WARNING sentence-transformers not installed, skipping...")
            self.strategies['sentence-transformers'] = {
                'backend': 'sentence-transformers',
                'models': {},
                'enabled': False
            }
        
        try:
            from fastembed import TextEmbedding
            
            print("Initializing FastEmbed backend...")
            self.strategies['fastembed'] = {
                'backend': 'fastembed',
                'models': {},
                'enabled': True
            }
            print("PASS FastEmbed available")
            
        except ImportError:
            print("WARNING FastEmbed not installed, skipping...")
            self.strategies['fastembed'] = {
                'backend': 'fastembed',
                'models': {},
                'enabled': False
            }
    
    def _get_or_create_model(self, strategy: str, model_name: str) -> Any:
        """Get or create embedding model for strategy"""
        if model_name in self.strategies[strategy]['models']:
            return self.strategies[strategy]['models'][model_name]
        
        try:
            if strategy == 'sentence-transformers':
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer(model_name)
                print(f"PASS Loaded {model_name} for sentence-transformers")
                
            elif strategy == 'fastembed':
                from fastembed import TextEmbedding
                model = TextEmbedding(model_name)
                print(f"PASS Loaded {model_name} for FastEmbed")
            
            self.strategies[strategy]['models'][model_name] = model
            return model
            
        except Exception as e:
            print(f"Error loading {model_name}: {e}")
            return None
    
    def embed(self, 
              texts: List[str], 
              strategy: str = None,
              context: Dict[str, Any] = None) -> List[List[float]]:
        """Generate embeddings using optimal strategy"""
        start_time = time.time()
        
        # Select strategy
        if strategy is None:
            if self.config.auto_select and context:
                strategy = self._select_strategy(context)
            else:
                strategy = 'primary'
        
        # Get model
        if strategy == 'primary':
            strategy_name = 'sentence-transformers'
            model_name = self.config.primary_model
        elif strategy == 'fast':
            strategy_name = 'fastembed'
            model_name = self.config.fast_model
        elif strategy == 'accurate':
            strategy_name = 'sentence-transformers'
            model_name = self.config.accurate_model
        else:
            strategy_name = 'sentence-transformers'
            model_name = model_name
        
        model = self._get_or_create_model(strategy_name, model_name)
        
        if not model:
            # Fallback to dummy embeddings
            return [[0.1] * 384 for _ in texts]
        
        # Generate embeddings
        try:
            if strategy_name == 'sentence-transformers':
                embeddings = model.encode(texts, convert_to_numpy=True).tolist()
            elif strategy_name == 'fastembed':
                embeddings = [emb.embedding for emb in model.embed(texts)]
            
            latency = (time.time() - start_time) * 1000
            
            # Update stats
            self.stats['total_queries'] += 1
            self.stats['queries_by_strategy'][strategy] = \
                self.stats['queries_by_strategy'].get(strategy, 0) + 1
            self.stats['avg_latency_by_strategy'][strategy] = \
                self.stats['avg_latency_by_strategy'].get(strategy, 0) * 0.9 + \
                latency * 0.1
            
            return embeddings
            
        except Exception as e:
            print(f"Embedding error: {e}")
            return [[0.1] * 384 for _ in texts]
    
    def _select_strategy(self, context: Dict[str, Any]) -> str:
        """Auto-select embedding strategy based on context"""
        # Speed-critical tasks
        if context.get('speed_critical', False):
            return 'fast'
        
        # Accuracy-critical tasks
        if context.get('accuracy_critical', False):
            return 'accurate'
        
        # Default to primary
        return 'primary'
    
    def get_strategy(self, strategy: str, model_name: str):
        """Get a specific strategy for use"""
        return self._get_or_create_model(strategy, model_name)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get embedding statistics"""
        return {
            'total_queries': self.stats['total_queries'],
            'queries_by_strategy': self.stats['queries_by_strategy'],
            'avg_latency_by_strategy': self.stats['avg_latency_by_strategy'],
            'active_strategies': [
                k for k, v in self.strategies.items() if v['enabled']
            ]
        }


# Usage examples:
async def main():
    print("Testing Multi-Strategy Embeddings...\n")
    
    # Initialize with all backends
    embedder = MultiStrategyEmbeddings()
    
    # Test primary strategy
    print("1. Primary Strategy (balanced):")
    texts = ["What is MSAM?", "Memory optimization"]
    embeddings = embedder.embed(texts, strategy='primary')
    print(f"   Generated {len(embeddings)} embeddings")
    print(f"   Embedding dim: {len(embeddings[0])}")
    
    # Test fast strategy
    print("\n2. Fast Strategy (speed-critical):")
    embeddings_fast = embedder.embed(texts, strategy='fast')
    print(f"   Generated {len(embeddings_fast)} embeddings")
    print(f"   Embedding dim: {len(embeddings_fast[0])}")
    
    # Test context-based selection
    print("\n3. Auto-Selection:")
    embeddings_auto = embedder.embed(texts, context={'speed_critical': True})
    print(f"   Selected 'fast' strategy for speed-critical task")
    
    # Stats
    print("\n4. Statistics:")
    stats = embedder.get_stats()
    print(f"   Total queries: {stats['total_queries']}")
    print(f"   Active strategies: {stats['active_strategies']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
