"""
缓存模块
提供查询结果缓存功能，提高系统响应速度
"""

import time
import hashlib
import json
from typing import Any, Optional, Dict
from dataclasses import dataclass
import threading

@dataclass
class CacheEntry:
    """缓存条目"""
    value: Any
    timestamp: float
    ttl: int
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() - self.timestamp > self.ttl

class LRUCache:
    """LRU缓存实现"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order = []
        self.lock = threading.RLock()
    
    def _generate_key(self, query: str, params: Dict = None) -> str:
        """生成缓存键"""
        key_data = query
        if params:
            key_data += json.dumps(params, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, query: str, params: Dict = None) -> Optional[Any]:
        """获取缓存值"""
        key = self._generate_key(query, params)
        
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if not entry.is_expired():
                    # 更新访问顺序
                    self.access_order.remove(key)
                    self.access_order.append(key)
                    return entry.value
                else:
                    # 删除过期条目
                    del self.cache[key]
                    self.access_order.remove(key)
        
        return None
    
    def put(self, query: str, value: Any, ttl: int = 3600, params: Dict = None):
        """存储缓存值"""
        key = self._generate_key(query, params)
        
        with self.lock:
            # 如果缓存已满，删除最久未访问的条目
            if len(self.cache) >= self.max_size and key not in self.cache:
                oldest_key = self.access_order.pop(0)
                del self.cache[oldest_key]
            
            # 添加或更新条目
            self.cache[key] = CacheEntry(
                value=value,
                timestamp=time.time(),
                ttl=ttl
            )
            
            # 更新访问顺序
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
    
    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.access_order.clear()
    
    def size(self) -> int:
        """获取缓存大小"""
        return len(self.cache)
    
    def cleanup_expired(self):
        """清理过期条目"""
        current_time = time.time()
        
        with self.lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if current_time - entry.timestamp > entry.ttl
            ]
            
            for key in expired_keys:
                del self.cache[key]
                self.access_order.remove(key)
        
        return len(expired_keys)

class QueryCache:
    """查询结果缓存"""
    
    def __init__(self, max_size: int = 500, default_ttl: int = 3600):
        self.cache = LRUCache(max_size)
        self.default_ttl = default_ttl
        self.hit_count = 0
        self.miss_count = 0
        self.lock = threading.RLock()
    
    def get_query_result(self, question: str) -> Optional[Dict]:
        """获取查询结果"""
        result = self.cache.get(question)
        
        with self.lock:
            if result is not None:
                self.hit_count += 1
                return result
            else:
                self.miss_count += 1
                return None
    
    def cache_query_result(self, question: str, result: Dict, ttl: int = None):
        """缓存查询结果"""
        if ttl is None:
            ttl = self.default_ttl
        
        self.cache.put(question, result, ttl)
    
    def get_graph_data(self, query_type: str, params: Dict) -> Optional[Any]:
        """获取图数据"""
        key = f"graph_{query_type}"
        result = self.cache.get(key, params)
        
        with self.lock:
            if result is not None:
                self.hit_count += 1
                return result
            else:
                self.miss_count += 1
                return None
    
    def cache_graph_data(self, query_type: str, data: Any, ttl: int = None, params: Dict = None):
        """缓存图数据"""
        if ttl is None:
            ttl = self.default_ttl
        
        key = f"graph_{query_type}"
        self.cache.put(key, data, ttl, params)
    
    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        with self.lock:
            total_requests = self.hit_count + self.miss_count
            hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
            
            return {
                "cache_size": self.cache.size(),
                "hit_count": self.hit_count,
                "miss_count": self.miss_count,
                "hit_rate": hit_rate,
                "total_requests": total_requests
            }
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        with self.lock:
            self.hit_count = 0
            self.miss_count = 0
    
    def cleanup(self):
        """清理过期缓存"""
        return self.cache.cleanup_expired()

# 全局缓存实例
query_cache = QueryCache()