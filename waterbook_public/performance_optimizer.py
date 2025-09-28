#!/usr/bin/env python3
"""
运河可视化器性能优化器
分析和优化性能、内存使用、渲染效率
"""

import time
import psutil
import gc
import numpy as np
from typing import Dict, List, Any, Optional
import threading
import queue
from dataclasses import dataclass
from collections import deque

@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    timestamp: float
    fps: float
    cpu_usage: float
    memory_usage: float  # MB
    gpu_memory: float = 0.0  # MB
    render_time: float = 0.0  # ms
    audio_processing_time: float = 0.0  # ms
    classification_time: float = 0.0  # ms
    visualization_time: float = 0.0  # ms

class MemoryPool:
    """内存池管理器"""
    
    def __init__(self, initial_size: int = 1024):
        self.pools = {}
        self.initial_size = initial_size
        self.usage_stats = {}
    
    def get_buffer(self, size: int, dtype=np.float32) -> np.ndarray:
        """获取指定大小的缓冲区"""
        key = (size, dtype)
        
        if key not in self.pools:
            self.pools[key] = deque()
            self.usage_stats[key] = {'allocated': 0, 'reused': 0}
        
        pool = self.pools[key]
        
        if pool:
            self.usage_stats[key]['reused'] += 1
            return pool.popleft()
        else:
            self.usage_stats[key]['allocated'] += 1
            return np.zeros(size, dtype=dtype)
    
    def return_buffer(self, buffer: np.ndarray):
        """归还缓冲区到池中"""
        key = (buffer.size, buffer.dtype)
        if key in self.pools:
            # 清零缓冲区
            buffer.fill(0)
            self.pools[key].append(buffer)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取内存池统计信息"""
        total_allocated = sum(stats['allocated'] for stats in self.usage_stats.values())
        total_reused = sum(stats['reused'] for stats in self.usage_stats.values())
        
        return {
            'total_allocated': total_allocated,
            'total_reused': total_reused,
            'reuse_ratio': total_reused / max(total_allocated, 1),
            'pool_details': dict(self.usage_stats)
        }

class PerformanceProfiler:
    """性能分析器"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history = deque(maxlen=max_history)
        self.current_metrics = None
        self.start_time = time.time()
        
        # 性能计时器
        self.timers = {}
        self.timer_stack = []
        
        # 内存监控
        self.process = psutil.Process()
        self.baseline_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
    def start_timer(self, name: str):
        """开始计时"""
        self.timers[name] = time.perf_counter()
        self.timer_stack.append(name)
    
    def end_timer(self, name: str) -> float:
        """结束计时并返回耗时（毫秒）"""
        if name in self.timers:
            elapsed = (time.perf_counter() - self.timers[name]) * 1000
            if self.timer_stack and self.timer_stack[-1] == name:
                self.timer_stack.pop()
            return elapsed
        return 0.0
    
    def record_frame(self, fps: float):
        """记录帧性能数据"""
        current_time = time.time()
        
        # CPU使用率
        cpu_usage = psutil.cpu_percent(interval=None)
        
        # 内存使用
        memory_info = self.process.memory_info()
        memory_usage = memory_info.rss / 1024 / 1024  # MB
        
        # 创建性能指标
        metrics = PerformanceMetrics(
            timestamp=current_time,
            fps=fps,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            render_time=self.timers.get('render', 0.0),
            audio_processing_time=self.timers.get('audio_processing', 0.0),
            classification_time=self.timers.get('classification', 0.0),
            visualization_time=self.timers.get('visualization', 0.0)
        )
        
        self.metrics_history.append(metrics)
        self.current_metrics = metrics
        
        # 清理计时器
        self.timers.clear()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.metrics_history:
            return {}
        
        recent_metrics = list(self.metrics_history)[-60:]  # 最近60帧
        
        fps_values = [m.fps for m in recent_metrics]
        cpu_values = [m.cpu_usage for m in recent_metrics]
        memory_values = [m.memory_usage for m in recent_metrics]
        render_times = [m.render_time for m in recent_metrics if m.render_time > 0]
        
        return {
            'fps': {
                'current': fps_values[-1] if fps_values else 0,
                'average': np.mean(fps_values) if fps_values else 0,
                'min': np.min(fps_values) if fps_values else 0,
                'max': np.max(fps_values) if fps_values else 0
            },
            'cpu_usage': {
                'current': cpu_values[-1] if cpu_values else 0,
                'average': np.mean(cpu_values) if cpu_values else 0,
                'max': np.max(cpu_values) if cpu_values else 0
            },
            'memory': {
                'current': memory_values[-1] if memory_values else 0,
                'baseline': self.baseline_memory,
                'peak': np.max(memory_values) if memory_values else 0,
                'growth': memory_values[-1] - self.baseline_memory if memory_values else 0
            },
            'render_time': {
                'average': np.mean(render_times) if render_times else 0,
                'max': np.max(render_times) if render_times else 0
            },
            'uptime': time.time() - self.start_time
        }

class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self):
        self.profiler = PerformanceProfiler()
        self.memory_pool = MemoryPool()
        self.optimization_enabled = True
        
        # 优化参数
        self.target_fps = 60
        self.max_memory_growth = 100  # MB
        self.gc_threshold = 50  # MB内存增长触发GC
        
        # 自适应参数
        self.adaptive_quality = True
        self.quality_level = 1.0  # 0.5-1.0
        self.frame_skip_count = 0
        self.max_frame_skip = 2
        
    def optimize_frame_rate(self, current_fps: float) -> Dict[str, Any]:
        """优化帧率"""
        optimizations = {}
        
        if current_fps < self.target_fps * 0.8:  # 低于目标FPS的80%
            if self.adaptive_quality:
                # 降低质量
                self.quality_level = max(0.5, self.quality_level - 0.1)
                optimizations['quality_reduced'] = self.quality_level
                
                # 启用帧跳过
                if current_fps < self.target_fps * 0.6:
                    self.frame_skip_count = min(self.max_frame_skip, self.frame_skip_count + 1)
                    optimizations['frame_skip'] = self.frame_skip_count
        
        elif current_fps > self.target_fps * 1.1:  # 高于目标FPS的110%
            # 提高质量
            if self.quality_level < 1.0:
                self.quality_level = min(1.0, self.quality_level + 0.05)
                optimizations['quality_increased'] = self.quality_level
            
            # 减少帧跳过
            if self.frame_skip_count > 0:
                self.frame_skip_count = max(0, self.frame_skip_count - 1)
                optimizations['frame_skip_reduced'] = self.frame_skip_count
        
        return optimizations
    
    def optimize_memory(self) -> Dict[str, Any]:
        """优化内存使用"""
        optimizations = {}
        summary = self.profiler.get_performance_summary()
        
        if 'memory' in summary:
            memory_growth = summary['memory']['growth']
            
            if memory_growth > self.gc_threshold:
                # 强制垃圾回收
                collected = gc.collect()
                optimizations['gc_collected'] = collected
                
                # 清理内存池
                if memory_growth > self.max_memory_growth:
                    self.memory_pool = MemoryPool()  # 重置内存池
                    optimizations['memory_pool_reset'] = True
        
        return optimizations
    
    def get_optimization_recommendations(self) -> List[str]:
        """获取优化建议"""
        recommendations = []
        summary = self.profiler.get_performance_summary()
        
        if not summary:
            return recommendations
        
        # FPS建议
        if summary['fps']['average'] < 30:
            recommendations.append("FPS过低，建议降低渲染质量或分辨率")
        elif summary['fps']['average'] < 45:
            recommendations.append("FPS偏低，可考虑优化渲染算法")
        
        # CPU建议
        if summary['cpu_usage']['average'] > 80:
            recommendations.append("CPU使用率过高，建议优化音频处理算法")
        elif summary['cpu_usage']['average'] > 60:
            recommendations.append("CPU使用率较高，可考虑使用多线程处理")
        
        # 内存建议
        if summary['memory']['growth'] > 100:
            recommendations.append("内存增长过多，可能存在内存泄漏")
        elif summary['memory']['growth'] > 50:
            recommendations.append("内存使用较高，建议定期清理缓存")
        
        # 渲染建议
        if summary['render_time']['average'] > 16:  # 超过16ms（60FPS）
            recommendations.append("渲染时间过长，建议优化绘制算法")
        
        return recommendations
    
    def apply_optimizations(self, fps: float) -> Dict[str, Any]:
        """应用优化策略"""
        if not self.optimization_enabled:
            return {}
        
        optimizations = {}
        
        # 记录性能数据
        self.profiler.record_frame(fps)
        
        # 帧率优化
        fps_opts = self.optimize_frame_rate(fps)
        if fps_opts:
            optimizations['fps'] = fps_opts
        
        # 内存优化
        memory_opts = self.optimize_memory()
        if memory_opts:
            optimizations['memory'] = memory_opts
        
        return optimizations
    
    def get_current_settings(self) -> Dict[str, Any]:
        """获取当前优化设置"""
        return {
            'optimization_enabled': self.optimization_enabled,
            'adaptive_quality': self.adaptive_quality,
            'quality_level': self.quality_level,
            'frame_skip_count': self.frame_skip_count,
            'target_fps': self.target_fps,
            'memory_pool_stats': self.memory_pool.get_stats()
        }

# 全局性能优化器实例
global_optimizer = PerformanceOptimizer()

def get_optimizer() -> PerformanceOptimizer:
    """获取全局优化器实例"""
    return global_optimizer

def optimize_numpy_operations():
    """优化NumPy操作"""
    # 设置NumPy线程数
    import os
    os.environ['OMP_NUM_THREADS'] = '4'
    os.environ['MKL_NUM_THREADS'] = '4'
    
    # 启用快速数学模式
    np.seterr(all='ignore')

def profile_function(func):
    """函数性能分析装饰器"""
    def wrapper(*args, **kwargs):
        profiler = global_optimizer.profiler
        func_name = func.__name__
        
        profiler.start_timer(func_name)
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            profiler.end_timer(func_name)
    
    return wrapper

# 初始化优化
optimize_numpy_operations()

if __name__ == "__main__":
    # 性能优化器测试
    optimizer = PerformanceOptimizer()
    
    print("性能优化器测试")
    print("=" * 40)
    
    # 模拟一些帧
    for i in range(100):
        fps = 60 - (i % 20)  # 模拟FPS波动
        optimizations = optimizer.apply_optimizations(fps)
        
        if optimizations:
            print(f"帧 {i}: FPS={fps}, 优化={optimizations}")
        
        time.sleep(0.01)
    
    # 显示性能摘要
    summary = optimizer.profiler.get_performance_summary()
    print("\n性能摘要:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # 显示优化建议
    recommendations = optimizer.get_optimization_recommendations()
    print("\n优化建议:")
    for rec in recommendations:
        print(f"  • {rec}")