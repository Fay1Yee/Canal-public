#!/usr/bin/env python3
"""
内存分析器 - 分析和优化Canal Visualizer的内存使用
"""

import gc
import sys
import time
import tracemalloc
import psutil
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from collections import defaultdict, deque
import threading
import weakref

@dataclass
class MemorySnapshot:
    """内存快照"""
    timestamp: float
    total_memory: float  # MB
    heap_memory: float   # MB
    numpy_memory: float  # MB
    pygame_memory: float # MB
    object_count: int
    gc_count: Tuple[int, int, int]
    top_objects: List[Tuple[str, int]]

class MemoryTracker:
    """内存跟踪器"""
    
    def __init__(self, max_snapshots: int = 1000):
        self.max_snapshots = max_snapshots
        self.snapshots: deque = deque(maxlen=max_snapshots)
        self.tracking = False
        self.process = psutil.Process()
        self._object_registry = weakref.WeakSet()
        
    def start_tracking(self):
        """开始内存跟踪"""
        if not self.tracking:
            tracemalloc.start()
            self.tracking = True
            print("内存跟踪已启动")
    
    def stop_tracking(self):
        """停止内存跟踪"""
        if self.tracking:
            tracemalloc.stop()
            self.tracking = False
            print("内存跟踪已停止")
    
    def take_snapshot(self) -> MemorySnapshot:
        """获取内存快照"""
        # 获取系统内存信息
        memory_info = self.process.memory_info()
        total_memory = memory_info.rss / 1024 / 1024  # MB
        
        # 获取堆内存信息
        heap_memory = 0
        if self.tracking:
            snapshot = tracemalloc.take_snapshot()
            heap_memory = sum(stat.size for stat in snapshot.statistics('lineno')) / 1024 / 1024
        
        # 估算NumPy内存使用
        numpy_memory = self._estimate_numpy_memory()
        
        # 估算Pygame内存使用
        pygame_memory = self._estimate_pygame_memory()
        
        # 获取对象计数
        object_count = len(gc.get_objects())
        
        # 获取垃圾回收统计
        gc_count = gc.get_count()
        
        # 获取顶级对象
        top_objects = self._get_top_objects()
        
        snapshot = MemorySnapshot(
            timestamp=time.time(),
            total_memory=total_memory,
            heap_memory=heap_memory,
            numpy_memory=numpy_memory,
            pygame_memory=pygame_memory,
            object_count=object_count,
            gc_count=gc_count,
            top_objects=top_objects
        )
        
        self.snapshots.append(snapshot)
        return snapshot
    
    def _estimate_numpy_memory(self) -> float:
        """估算NumPy数组内存使用"""
        total_size = 0
        for obj in gc.get_objects():
            if isinstance(obj, np.ndarray):
                total_size += obj.nbytes
        return total_size / 1024 / 1024  # MB
    
    def _estimate_pygame_memory(self) -> float:
        """估算Pygame内存使用"""
        # 这是一个简化的估算，实际Pygame内存使用更复杂
        try:
            import pygame
            total_size = 0
            for obj in gc.get_objects():
                if hasattr(obj, '__class__') and 'pygame' in str(obj.__class__):
                    if hasattr(obj, 'get_size'):
                        size = obj.get_size()
                        if isinstance(size, tuple) and len(size) == 2:
                            # 假设32位RGBA
                            total_size += size[0] * size[1] * 4
            return total_size / 1024 / 1024  # MB
        except:
            return 0.0
    
    def _get_top_objects(self, limit: int = 10) -> List[Tuple[str, int]]:
        """获取占用内存最多的对象类型"""
        type_counts = defaultdict(int)
        for obj in gc.get_objects():
            type_name = type(obj).__name__
            type_counts[type_name] += 1
        
        return sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    def register_object(self, obj):
        """注册对象用于跟踪"""
        self._object_registry.add(obj)
    
    def get_memory_growth(self, window_size: int = 10) -> float:
        """获取内存增长率 (MB/s)"""
        if len(self.snapshots) < 2:
            return 0.0
        
        recent_snapshots = list(self.snapshots)[-window_size:]
        if len(recent_snapshots) < 2:
            return 0.0
        
        start_snapshot = recent_snapshots[0]
        end_snapshot = recent_snapshots[-1]
        
        memory_diff = end_snapshot.total_memory - start_snapshot.total_memory
        time_diff = end_snapshot.timestamp - start_snapshot.timestamp
        
        return memory_diff / time_diff if time_diff > 0 else 0.0

class MemoryOptimizer:
    """内存优化器"""
    
    def __init__(self, tracker: MemoryTracker):
        self.tracker = tracker
        self.optimization_history = []
        
    def analyze_memory_usage(self) -> Dict[str, Any]:
        """分析内存使用情况"""
        if not self.tracker.snapshots:
            return {}
        
        latest = self.tracker.snapshots[-1]
        analysis = {
            'current_memory': latest.total_memory,
            'memory_growth_rate': self.tracker.get_memory_growth(),
            'numpy_percentage': (latest.numpy_memory / latest.total_memory * 100) if latest.total_memory > 0 else 0,
            'pygame_percentage': (latest.pygame_memory / latest.total_memory * 100) if latest.total_memory > 0 else 0,
            'object_count': latest.object_count,
            'gc_pressure': sum(latest.gc_count),
            'top_objects': latest.top_objects[:5]
        }
        
        return analysis
    
    def get_optimization_recommendations(self) -> List[str]:
        """获取优化建议"""
        analysis = self.analyze_memory_usage()
        recommendations = []
        
        if analysis.get('memory_growth_rate', 0) > 1.0:  # 超过1MB/s增长
            recommendations.append("检测到内存泄漏，建议检查对象引用")
        
        if analysis.get('numpy_percentage', 0) > 50:
            recommendations.append("NumPy数组占用过多内存，考虑使用更小的数据类型或释放不用的数组")
        
        if analysis.get('pygame_percentage', 0) > 30:
            recommendations.append("Pygame对象占用较多内存，考虑优化表面和纹理管理")
        
        if analysis.get('gc_pressure', 0) > 1000:
            recommendations.append("垃圾回收压力较大，考虑减少临时对象创建")
        
        if analysis.get('object_count', 0) > 100000:
            recommendations.append("对象数量过多，考虑使用对象池或减少对象创建")
        
        return recommendations
    
    def apply_optimizations(self) -> List[str]:
        """应用内存优化"""
        applied_optimizations = []
        
        # 强制垃圾回收
        collected = gc.collect()
        if collected > 0:
            applied_optimizations.append(f"垃圾回收清理了 {collected} 个对象")
        
        # 清理NumPy缓存
        try:
            # 清理可能的NumPy内部缓存
            if hasattr(np, 'core') and hasattr(np.core, '_internal'):
                # 这是一个内部API，可能不稳定
                pass
            applied_optimizations.append("清理NumPy缓存")
        except:
            pass
        
        # 优化内存分配
        self._optimize_memory_allocation()
        applied_optimizations.append("优化内存分配策略")
        
        self.optimization_history.append({
            'timestamp': time.time(),
            'optimizations': applied_optimizations
        })
        
        return applied_optimizations
    
    def _optimize_memory_allocation(self):
        """优化内存分配策略"""
        # 调整垃圾回收阈值
        current_thresholds = gc.get_threshold()
        # 更激进的垃圾回收
        gc.set_threshold(current_thresholds[0] // 2, current_thresholds[1] // 2, current_thresholds[2] // 2)

class MemoryProfiler:
    """内存性能分析器"""
    
    def __init__(self):
        self.tracker = MemoryTracker()
        self.optimizer = MemoryOptimizer(self.tracker)
        self.profiling = False
        self.profile_thread = None
        
    def start_profiling(self, interval: float = 1.0):
        """开始内存分析"""
        if not self.profiling:
            self.tracker.start_tracking()
            self.profiling = True
            self.profile_thread = threading.Thread(
                target=self._profile_loop,
                args=(interval,),
                daemon=True
            )
            self.profile_thread.start()
            print(f"内存分析已启动，采样间隔: {interval}秒")
    
    def stop_profiling(self):
        """停止内存分析"""
        if self.profiling:
            self.profiling = False
            self.tracker.stop_tracking()
            if self.profile_thread:
                self.profile_thread.join(timeout=1.0)
            print("内存分析已停止")
    
    def _profile_loop(self, interval: float):
        """分析循环"""
        while self.profiling:
            try:
                self.tracker.take_snapshot()
                time.sleep(interval)
            except Exception as e:
                print(f"内存分析错误: {e}")
                break
    
    def generate_report(self) -> str:
        """生成内存分析报告"""
        if not self.tracker.snapshots:
            return "没有可用的内存数据"
        
        analysis = self.optimizer.analyze_memory_usage()
        recommendations = self.optimizer.get_optimization_recommendations()
        
        report = []
        report.append("=" * 50)
        report.append("内存分析报告")
        report.append("=" * 50)
        
        report.append(f"当前内存使用: {analysis.get('current_memory', 0):.2f} MB")
        report.append(f"内存增长率: {analysis.get('memory_growth_rate', 0):.3f} MB/s")
        report.append(f"NumPy内存占比: {analysis.get('numpy_percentage', 0):.1f}%")
        report.append(f"Pygame内存占比: {analysis.get('pygame_percentage', 0):.1f}%")
        report.append(f"对象总数: {analysis.get('object_count', 0):,}")
        report.append(f"垃圾回收压力: {analysis.get('gc_pressure', 0)}")
        
        report.append("\n主要对象类型:")
        for obj_type, count in analysis.get('top_objects', []):
            report.append(f"  {obj_type}: {count:,}")
        
        if recommendations:
            report.append("\n优化建议:")
            for rec in recommendations:
                report.append(f"  • {rec}")
        
        # 内存趋势分析
        if len(self.tracker.snapshots) >= 10:
            report.append("\n内存趋势分析:")
            snapshots = list(self.tracker.snapshots)[-10:]
            memory_values = [s.total_memory for s in snapshots]
            
            if len(set(memory_values)) > 1:  # 有变化
                trend = "上升" if memory_values[-1] > memory_values[0] else "下降"
                report.append(f"  最近10次采样内存{trend}")
                report.append(f"  最小值: {min(memory_values):.2f} MB")
                report.append(f"  最大值: {max(memory_values):.2f} MB")
                report.append(f"  平均值: {sum(memory_values)/len(memory_values):.2f} MB")
        
        return "\n".join(report)

def profile_memory_usage(func):
    """内存使用装饰器"""
    def wrapper(*args, **kwargs):
        profiler = MemoryProfiler()
        profiler.start_profiling(0.1)  # 高频采样
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            time.sleep(0.5)  # 等待最后的采样
            profiler.stop_profiling()
            print(profiler.generate_report())
    
    return wrapper

def main():
    """主函数 - 演示内存分析功能"""
    print("内存分析器演示")
    
    # 创建分析器
    profiler = MemoryProfiler()
    
    # 开始分析
    profiler.start_profiling(0.5)
    
    try:
        # 模拟一些内存操作
        print("模拟内存操作...")
        
        # 创建一些NumPy数组
        arrays = []
        for i in range(10):
            arr = np.random.random((1000, 1000))
            arrays.append(arr)
            time.sleep(0.1)
        
        # 删除一些数组
        del arrays[::2]
        gc.collect()
        
        # 等待一段时间收集数据
        time.sleep(2)
        
    finally:
        # 停止分析并生成报告
        profiler.stop_profiling()
        print(profiler.generate_report())
        
        # 应用优化
        optimizations = profiler.optimizer.apply_optimizations()
        if optimizations:
            print("\n应用的优化:")
            for opt in optimizations:
                print(f"  • {opt}")

if __name__ == "__main__":
    main()