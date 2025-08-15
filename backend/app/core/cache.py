"""
Caching layer for frequently accessed data
Supports Redis and in-memory caching with automatic invalidation
"""

import json
import pickle
import hashlib
import logging
from typing import Any, Optional, Dict, List, Union, Callable
from datetime import datetime, timedelta
from functools import wraps
from dataclasses import dataclass
import redis
from redis.exceptions import ConnectionError as RedisConnectionError

logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    """Cache configuration"""
    redis_url: str = "redis://localhost:6379/1"
    default_ttl: int = 3600  # 1 hour
    max_memory_items: int = 1000
    enable_redis: bool = True
    enable_memory: bool = True

class MemoryCache:
    """In-memory cache with LRU eviction"""
    
    def __init__(self, max_items: int = 1000):
        self.max_items = max_items
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_order: List[str] = []
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        if key not in self.cache:
            return None
            
        item = self.cache[key]
        
        # Check expiration
        if item['expires_at'] and datetime.now() > item['expires_at']:
            self.delete(key)
            return None
        
        # Update access order (LRU)
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        
        return item['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set item in cache"""
        expires_at = None
        if ttl:
            expires_at = datetime.now() + timedelta(seconds=ttl)
        
        # Evict oldest items if at capacity
        while len(self.cache) >= self.max_items and key not in self.cache:
            oldest_key = self.access_order.pop(0)
            del self.cache[oldest_key]
        
        self.cache[key] = {
            'value': value,
            'expires_at': expires_at,
            'created_at': datetime.now()
        }
        
        # Update access order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        
        return True
    
    def delete(self, key: str) -> bool:
        """Delete item from cache"""
        if key in self.cache:
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)
            return True
        return False
    
    def clear(self):
        """Clear all cache items"""
        self.cache.clear()
        self.access_order.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_items = len(self.cache)
        expired_items = 0
        
        now = datetime.now()
        for item in self.cache.values():
            if item['expires_at'] and now > item['expires_at']:
                expired_items += 1
        
        return {
            'total_items': total_items,
            'expired_items': expired_items,
            'max_items': self.max_items,
            'utilization': total_items / self.max_items if self.max_items > 0 else 0
        }

class CacheManager:
    """Multi-tier cache manager with Redis and memory backends"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.memory_cache = MemoryCache(config.max_memory_items) if config.enable_memory else None
        self.redis_client = None
        
        if config.enable_redis:
            try:
                self.redis_client = redis.from_url(config.redis_url, decode_responses=True)
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache connected successfully")
            except (RedisConnectionError, Exception) as e:
                logger.warning(f"Redis connection failed, using memory cache only: {e}")
                self.redis_client = None
    
    def _serialize_value(self, value: Any) -> str:
        """Serialize value for storage"""
        try:
            # Try JSON first (faster and more readable)
            return json.dumps(value, default=str)
        except (TypeError, ValueError):
            # Fall back to pickle for complex objects
            return pickle.dumps(value).hex()
    
    def _deserialize_value(self, serialized: str) -> Any:
        """Deserialize value from storage"""
        try:
            # Try JSON first
            return json.loads(serialized)
        except (json.JSONDecodeError, ValueError):
            # Fall back to pickle
            return pickle.loads(bytes.fromhex(serialized))
    
    def _generate_key(self, namespace: str, key: str) -> str:
        """Generate cache key with namespace"""
        return f"{namespace}:{key}"
    
    async def get(self, namespace: str, key: str) -> Optional[Any]:
        """Get item from cache (tries Redis first, then memory)"""
        cache_key = self._generate_key(namespace, key)
        
        # Try Redis first
        if self.redis_client:
            try:
                value = self.redis_client.get(cache_key)
                if value is not None:
                    return self._deserialize_value(value)
            except Exception as e:
                logger.warning(f"Redis get error: {e}")
        
        # Try memory cache
        if self.memory_cache:
            return self.memory_cache.get(cache_key)
        
        return None
    
    async def set(self, namespace: str, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set item in cache (both Redis and memory)"""
        cache_key = self._generate_key(namespace, key)
        ttl = ttl or self.config.default_ttl
        success = False
        
        # Set in Redis
        if self.redis_client:
            try:
                serialized = self._serialize_value(value)
                self.redis_client.setex(cache_key, ttl, serialized)
                success = True
            except Exception as e:
                logger.warning(f"Redis set error: {e}")
        
        # Set in memory cache
        if self.memory_cache:
            self.memory_cache.set(cache_key, value, ttl)
            success = True
        
        return success
    
    async def delete(self, namespace: str, key: str) -> bool:
        """Delete item from cache"""
        cache_key = self._generate_key(namespace, key)
        success = False
        
        # Delete from Redis
        if self.redis_client:
            try:
                self.redis_client.delete(cache_key)
                success = True
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")
        
        # Delete from memory cache
        if self.memory_cache:
            self.memory_cache.delete(cache_key)
            success = True
        
        return success
    
    async def clear_namespace(self, namespace: str) -> bool:
        """Clear all items in a namespace"""
        success = False
        
        # Clear from Redis
        if self.redis_client:
            try:
                pattern = f"{namespace}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                success = True
            except Exception as e:
                logger.warning(f"Redis clear namespace error: {e}")
        
        # Clear from memory cache (partial - only exact matches)
        if self.memory_cache:
            keys_to_delete = [
                key for key in self.memory_cache.cache.keys() 
                if key.startswith(f"{namespace}:")
            ]
            for key in keys_to_delete:
                self.memory_cache.delete(key)
            success = True
        
        return success
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            'redis': None,
            'memory': None,
            'config': {
                'redis_enabled': self.redis_client is not None,
                'memory_enabled': self.memory_cache is not None,
                'default_ttl': self.config.default_ttl
            }
        }
        
        # Redis stats
        if self.redis_client:
            try:
                info = self.redis_client.info()
                stats['redis'] = {
                    'connected': True,
                    'used_memory': info.get('used_memory_human'),
                    'connected_clients': info.get('connected_clients'),
                    'total_commands_processed': info.get('total_commands_processed'),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0)
                }
                
                # Calculate hit rate
                hits = stats['redis']['keyspace_hits']
                misses = stats['redis']['keyspace_misses']
                if hits + misses > 0:
                    stats['redis']['hit_rate'] = hits / (hits + misses)
                else:
                    stats['redis']['hit_rate'] = 0
                    
            except Exception as e:
                stats['redis'] = {'connected': False, 'error': str(e)}
        
        # Memory cache stats
        if self.memory_cache:
            stats['memory'] = self.memory_cache.get_stats()
        
        return stats

# Global cache instance
cache_config = CacheConfig()
cache_manager = CacheManager(cache_config)

# Decorator for caching function results
def cached(namespace: str, ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """Decorator to cache function results"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            cached_result = await cache_manager.get(namespace, cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs) if hasattr(func, '__await__') else func(*args, **kwargs)
            await cache_manager.set(namespace, cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

# Specific cache functions for common use cases
class DocumentCache:
    """Document-specific caching utilities"""
    
    @staticmethod
    async def get_document(doc_id: str) -> Optional[Dict]:
        return await cache_manager.get("documents", doc_id)
    
    @staticmethod
    async def set_document(doc_id: str, document: Dict, ttl: int = 3600):
        return await cache_manager.set("documents", doc_id, document, ttl)
    
    @staticmethod
    async def invalidate_document(doc_id: str):
        # Invalidate document and related data
        await cache_manager.delete("documents", doc_id)
        await cache_manager.clear_namespace(f"chapters:{doc_id}")
        await cache_manager.clear_namespace(f"knowledge:{doc_id}")
        await cache_manager.clear_namespace(f"cards:{doc_id}")

class SearchCache:
    """Search result caching utilities"""
    
    @staticmethod
    async def get_search_results(query: str, filters: Dict) -> Optional[List]:
        key = hashlib.md5(f"{query}:{json.dumps(filters, sort_keys=True)}".encode()).hexdigest()
        return await cache_manager.get("search", key)
    
    @staticmethod
    async def set_search_results(query: str, filters: Dict, results: List, ttl: int = 1800):
        key = hashlib.md5(f"{query}:{json.dumps(filters, sort_keys=True)}".encode()).hexdigest()
        return await cache_manager.set("search", key, results, ttl)

class EmbeddingCache:
    """Embedding caching utilities"""
    
    @staticmethod
    async def get_embedding(text: str) -> Optional[List[float]]:
        key = hashlib.md5(text.encode()).hexdigest()
        return await cache_manager.get("embeddings", key)
    
    @staticmethod
    async def set_embedding(text: str, embedding: List[float], ttl: int = 86400):  # 24 hours
        key = hashlib.md5(text.encode()).hexdigest()
        return await cache_manager.set("embeddings", key, embedding, ttl)