#!/usr/bin/env python3
"""
运河场景可视化模块
创建沉浸式的运河环境，包括动态水波、航行船只、传统桥梁、河岸环境等
结合音频特征实现实时响应的视觉效果
"""

import pygame
import numpy as np
import math
import time
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass
from moderngl_renderer import create_renderer
from realtime_audio_visualizer import RealtimeAudioVisualizer
from phoneme_visualizer import PhonemeVisualizer
from onomatopoeia_visualizer import OnomatopoeiaVisualizer

# 导入性能优化器
try:
    from performance_optimizer import get_optimizer, profile_function
    PERFORMANCE_OPTIMIZATION_ENABLED = True
except ImportError:
    PERFORMANCE_OPTIMIZATION_ENABLED = False
    def profile_function(func):
        return func

try:
    from memory_analyzer import MemoryProfiler
    MEMORY_ANALYSIS_ENABLED = True
except ImportError:
    MEMORY_ANALYSIS_ENABLED = False

# 运河主题配色 - 黑白水墨风格
class CanalColors:
    """运河主题配色方案 - 黑白水墨风格"""
    # 水墨黑色系 - 主要文字和线条
    INK_BLACK = (20, 20, 20)             # 浓墨
    INK_DARK = (40, 40, 40)              # 重墨
    INK_MEDIUM = (70, 70, 70)            # 中墨
    INK_GRAY = (100, 100, 100)           # 墨灰
    INK_LIGHT = (120, 120, 120)          # 淡墨
    INK_FAINT = (180, 180, 180)          # 极淡墨
    
    # 宣纸色系 - 背景和留白
    PAPER_WHITE = (252, 250, 245)        # 宣纸白
    PAPER_CREAM = (248, 246, 240)        # 宣纸米色
    PAPER_AGED = (245, 242, 235)         # 陈年宣纸
    
    # 运河水色系 - 黑白水墨风格的水
    CANAL_BLUE_DEEP = (30, 30, 30)       # 深水墨（替代蓝色）
    CANAL_BLUE = (60, 60, 60)            # 中水墨（替代蓝色）
    CANAL_BLUE_LIGHT = (90, 90, 90)      # 浅水墨（替代蓝色）
    CANAL_BLUE_MIST = (140, 140, 140)    # 水雾墨（替代蓝色）
    
    # 运河植物色系 - 黑白水墨风格的植物
    CANAL_GREEN_DEEP = (35, 35, 35)      # 深墨绿（替代绿色）
    CANAL_GREEN = (65, 65, 65)           # 中墨绿（替代绿色）
    CANAL_GREEN_LIGHT = (95, 95, 95)     # 浅墨绿（替代绿色）
    CANAL_GREEN_MIST = (125, 125, 125)   # 绿雾墨（替代绿色）
    
    # 桥梁色系 - 黑白水墨风格的建筑
    BRIDGE_BROWN_DEEP = (45, 45, 45)     # 深墨棕（替代棕色）
    BRIDGE_BROWN = (75, 75, 75)          # 中墨棕（替代棕色）
    BRIDGE_BROWN_LIGHT = (105, 105, 105) # 浅墨棕（替代棕色）
    
    # 特殊色彩 - 黑白水墨风格的点缀
    WATER_FOAM = (235, 235, 235)         # 水花白（纯净）
    SKY_MIST = (200, 200, 200)           # 天空雾（空灵）
    SHORE_STONE = (85, 85, 85)           # 岸石灰（沉稳）
    TREE_SHADOW = (55, 55, 55)           # 树影墨（深邃）
    
    # 传统水墨色 - 经典搭配
    TRADITIONAL_BLACK = (25, 25, 25)     # 传统墨色
    TRADITIONAL_GRAY = (128, 128, 128)   # 传统灰
    SEAL_RED = (180, 45, 35)             # 印章红（保留作为唯一彩色点缀）

@dataclass
class WavePoint:
    """水波点数据"""
    x: float
    y: float
    amplitude: float
    frequency: float
    phase: float
    speed: float

@dataclass
class Boat:
    """船只数据"""
    x: float
    y: float
    size: float
    speed: float
    direction: float
    boat_type: str  # "货船", "客船", "小船"
    color: Tuple[int, int, int]

@dataclass
class Bridge:
    """桥梁数据"""
    x: float
    y: float
    width: float
    height: float
    arch_count: int
    color: Tuple[int, int, int]
    style: str  # "石桥", "木桥", "现代桥"

class CanalVisualizer:
    """运河场景可视化器"""
    
    def __init__(self, width: int, height: int):
        """初始化可视化器"""
        self.width = width
        self.height = height
        
        # 性能优化器
        self.performance_optimizer = None
        if PERFORMANCE_OPTIMIZATION_ENABLED:
            try:
                self.performance_optimizer = get_optimizer()
            except Exception as e:
                print(f"性能优化器初始化失败: {e}")
        
        # 内存分析器
        self.memory_profiler = None
        if MEMORY_ANALYSIS_ENABLED:
            try:
                self.memory_profiler = MemoryProfiler()
                self.memory_profiler.start_profiling(2.0)  # 每2秒采样一次
                print("内存分析器已启动")
            except Exception as e:
                print(f"内存分析器初始化失败: {e}")
        
        # 时间和动画
        self.time = 0.0
        self.animation_speed = 1.0
        
        # 音频响应参数
        self.audio_intensity = 0.0
        self.water_flow_strength = 0.0
        self.boat_activity = 0.0
        self.bird_activity = 0.0
        self.wind_strength = 0.0
        
        # 初始化场景元素
        self._init_water_waves()
        self._init_boats()
        self._init_bridges()
        self._init_shore_elements()
        
        # 频谱可视化
        self.spectrum_data = None
        self.spectrum_history = []
        
        # 初始化GPU渲染器（带异常处理）
        self.gpu_renderer = None
        self.particle_system = None
        try:
            self.gpu_renderer = create_renderer(width, height)
            if self.gpu_renderer:
                self.particle_system = self.gpu_renderer.create_particle_system(200)  # 200个粒子
                print("GPU加速渲染已启用")
        except Exception as e:
            print(f"GPU渲染器初始化失败，将使用CPU渲染: {e}")
            self.gpu_renderer = None
        
        # 初始化实时音频可视化器（带异常处理）
        self.audio_visualizer = None
        try:
            self.audio_visualizer = RealtimeAudioVisualizer(width, height)
            print("实时音频可视化已启用")
        except Exception as e:
            print(f"音频可视化器初始化失败: {e}")
            self.audio_visualizer = None
        
        # 初始化音素可视化器（带异常处理）
        self.phoneme_visualizer = None
        try:
            self.phoneme_visualizer = PhonemeVisualizer(width, height)
            print("运河音素可视化已启用")
        except Exception as e:
            print(f"音素可视化器初始化失败: {e}")
            self.phoneme_visualizer = None
        
        # 初始化拟声词生成器（带异常处理）
        self.onomatopoeia_generator = None
        try:
            from onomatopoeia_generator import CanalOnomatopoeiaGenerator
            self.onomatopoeia_generator = CanalOnomatopoeiaGenerator()
            print("运河拟声词生成器已启用")
        except Exception as e:
            print(f"拟声词生成器初始化失败: {e}")
            self.onomatopoeia_generator = None
        
        # 初始化拟声词可视化器（带异常处理）
        self.onomatopoeia_visualizer = None
        try:
            self.onomatopoeia_visualizer = OnomatopoeiaVisualizer(width, height)
            print("运河拟声词可视化已启用")
        except Exception as e:
            print(f"拟声词可视化器初始化失败: {e}")
            self.onomatopoeia_visualizer = None
        
        # 增强声音分类器
        try:
            from enhanced_sound_classifier import EnhancedSoundClassifier
            self.enhanced_classifier = EnhancedSoundClassifier(sample_rate=32000)
            print("运河可视化器：增强声音分类器已加载")
        except ImportError as e:
            print(f"运河可视化器：无法加载增强声音分类器: {e}")
            self.enhanced_classifier = None
        
        print("运河场景可视化器初始化完成 - {}x{}".format(width, height))
    
    def _init_water_waves(self):
        """初始化水波系统"""
        self.wave_points = []
        
        # 创建多层水波
        wave_count = 50
        for i in range(wave_count):
            wave = WavePoint(
                x=i * (self.width / wave_count),
                y=self.height * 0.6,  # 水面位置
                amplitude=np.random.uniform(5, 15),
                frequency=np.random.uniform(0.01, 0.03),
                phase=np.random.uniform(0, 2 * math.pi),
                speed=np.random.uniform(0.5, 1.5)
            )
            self.wave_points.append(wave)
        
        # 水面反射区域
        self.water_surface_y = self.height * 0.6
        self.water_depth = self.height - self.water_surface_y
    
    def _init_boats(self):
        """初始化船只"""
        self.boats = []
        
        # 大型货船
        cargo_boat = Boat(
            x=-100,
            y=self.water_surface_y - 20,
            size=80,
            speed=0.3,
            direction=1,
            boat_type="货船",
            color=CanalColors.BRIDGE_BROWN
        )
        self.boats.append(cargo_boat)
        
        # 客船
        passenger_boat = Boat(
            x=self.width + 50,
            y=self.water_surface_y - 15,
            size=60,
            speed=0.5,
            direction=-1,
            boat_type="客船",
            color=CanalColors.CANAL_BLUE_LIGHT
        )
        self.boats.append(passenger_boat)
        
        # 小船
        small_boat = Boat(
            x=self.width * 0.3,
            y=self.water_surface_y - 8,
            size=30,
            speed=0.2,
            direction=1,
            boat_type="小船",
            color=CanalColors.CANAL_GREEN
        )
        self.boats.append(small_boat)
    
    def _init_bridges(self):
        """初始化桥梁"""
        self.bridges = []
        
        # 主桥梁
        main_bridge = Bridge(
            x=self.width * 0.7,
            y=self.water_surface_y - 80,
            width=200,
            height=60,
            arch_count=3,
            color=CanalColors.BRIDGE_BROWN,
            style="石桥"
        )
        self.bridges.append(main_bridge)
        
        # 远景桥梁
        distant_bridge = Bridge(
            x=self.width * 0.2,
            y=self.water_surface_y - 40,
            width=120,
            height=30,
            arch_count=2,
            color=CanalColors.BRIDGE_BROWN_LIGHT,
            style="木桥"
        )
        self.bridges.append(distant_bridge)
    
    def _init_shore_elements(self):
        """初始化河岸元素"""
        # 河岸线
        self.shore_points = []
        for i in range(0, self.width + 10, 10):
            shore_y = self.water_surface_y + np.sin(i * 0.01) * 5
            self.shore_points.append((i, shore_y))
        
        # 建筑物
        self.buildings = []
        building_count = 8
        for i in range(building_count):
            x = i * (self.width / building_count) + np.random.uniform(-20, 20)
            height = np.random.uniform(40, 100)
            width = np.random.uniform(30, 60)
            self.buildings.append({
                'x': x,
                'y': self.water_surface_y - height,
                'width': width,
                'height': height,
                'color': CanalColors.SHORE_STONE
            })
        
        # 树木
        self.trees = []
        tree_count = 15
        for i in range(tree_count):
            x = np.random.uniform(0, self.width)
            y = self.water_surface_y + np.random.uniform(-10, 5)
            size = np.random.uniform(15, 30)
            self.trees.append({
                'x': x,
                'y': y,
                'size': size,
                'sway': np.random.uniform(0, 2 * math.pi)
            })
    
    @profile_function
    def update(self, audio_data: Optional[np.ndarray] = None):
        """更新场景状态（性能优化版本）"""
        try:
            # 性能计时开始
            if self.performance_optimizer:
                self.performance_optimizer.profiler.start_timer('update_total')
            
            # 限制更新频率
            current_time = time.time()
            if not hasattr(self, 'last_update_time'):
                self.last_update_time = 0
            
            # 每50ms更新一次（20fps）而不是60fps
            if current_time - self.last_update_time < 0.05:
                return
            
            self.last_update_time = current_time
            self.time += 0.05  # 调整为20fps
            
            # 处理音频数据（降采样）
            if audio_data is not None:
                try:
                    if self.performance_optimizer:
                        self.performance_optimizer.profiler.start_timer('audio_processing')
                    
                    # 降采样音频数据以提高性能
                    if len(audio_data) > 512:
                        step = len(audio_data) // 512
                        audio_data = audio_data[::step]
                    
                    self._process_audio_data(audio_data)
                    
                    # 更新可视化器（限制频率）
                    if hasattr(self, 'visualizer_update_counter'):
                        self.visualizer_update_counter += 1
                    else:
                        self.visualizer_update_counter = 0
                    
                    # 每3帧更新一次可视化器
                    if self.visualizer_update_counter % 3 == 0:
                        # 更新实时音频可视化器
                        if self.audio_visualizer:
                            self.audio_visualizer.update(audio_data)
                        # 更新音素可视化器
                        if self.phoneme_visualizer:
                            self.phoneme_visualizer.update(audio_data)
                        # 更新拟声词可视化器
                        if self.onomatopoeia_visualizer:
                            self.onomatopoeia_visualizer.update(audio_data)
                    
                    # 每5帧更新一次声音分类器
                    if self.visualizer_update_counter % 5 == 0:
                        # 更新增强声音分类器
                        if self.enhanced_classifier:
                            if self.performance_optimizer:
                                self.performance_optimizer.profiler.start_timer('classification')
                            classifications = self.enhanced_classifier.classify_audio(audio_data)
                            # 根据分类结果调整场景参数
                            self._adjust_scene_by_classification(classifications)
                            if self.performance_optimizer:
                                self.performance_optimizer.profiler.end_timer('classification')
                    
                    if self.performance_optimizer:
                        self.performance_optimizer.profiler.end_timer('audio_processing')
                        
                except Exception as e:
                    print(f"音频数据处理错误: {e}")
                    # 继续运行，使用默认值
            
            # 更新场景元素（简化版本）
            try:
                # 每帧都更新水波（但简化计算）
                self._update_water_waves_optimized()
                
                # 每2帧更新一次船只
                if self.visualizer_update_counter % 2 == 0:
                    self._update_boats()
                
                # 每4帧更新一次桥梁颜色
                if self.visualizer_update_counter % 4 == 0:
                    self._update_bridge_colors()
                
                # 每4帧更新一次树木
                if self.visualizer_update_counter % 4 == 0:
                    self._update_trees()
                    
            except Exception as e:
                print(f"场景元素更新错误: {e}")
            
            # 内存监控（降低频率）
            if self.memory_profiler and hasattr(self.memory_profiler, 'tracker'):
                if self.visualizer_update_counter % 10 == 0:  # 每10帧检查一次
                    try:
                        self.memory_profiler.tracker.take_snapshot()
                    except Exception as e:
                        pass  # 静默处理内存监控错误
            
            # 性能计时结束
            if self.performance_optimizer:
                self.performance_optimizer.profiler.end_timer('update_total')
                
        except Exception as e:
            print(f"运河场景更新错误: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_water_waves_optimized(self):
        """优化的水波更新方法"""
        # 只更新部分水波点以提高性能
        update_count = min(len(self.wave_points), 20)  # 最多更新20个点
        for i in range(0, len(self.wave_points), max(1, len(self.wave_points) // update_count)):
            wave = self.wave_points[i]
            # 基础波动
            wave.phase += wave.frequency * wave.speed
            
            # 音频响应（简化计算）
            audio_factor = 1 + self.water_flow_strength
            wave.amplitude = wave.amplitude * 0.9 + (5 + self.audio_intensity * 10) * 0.1
            
            # 计算波高（简化）
            wave_height = wave.amplitude * math.sin(wave.phase) * audio_factor
            wave.y = self.water_surface_y + wave_height
    
    def _update_boats(self):
        """更新船只位置和动画"""
        for boat in self.boats:
            # 基础移动
            boat.x += boat.speed * boat.direction
            
            # 音频响应 - 船只活动影响速度
            speed_factor = 1 + self.boat_activity * 0.5
            boat.x += boat.speed * boat.direction * speed_factor * 0.1
            
            # 水波影响船只摆动
            wave_offset = math.sin(self.time * 2 + boat.x * 0.01) * 3
            boat.y = self.water_surface_y - (boat.size * 0.3) + wave_offset
            
            # 边界处理 - 船只循环出现
            if boat.direction > 0 and boat.x > self.width + boat.size:
                boat.x = -boat.size
            elif boat.direction < 0 and boat.x < -boat.size:
                boat.x = self.width + boat.size
    
    def _update_bridge_colors(self):
        """根据音频特征更新桥梁颜色"""
        for bridge in self.bridges:
            # 基础颜色
            base_color = CanalColors.BRIDGE_BROWN
            
            # 音频响应调色
            intensity = min(self.audio_intensity * 2, 1.0)
            
            # 调整颜色亮度
            r = min(255, base_color[0] + int(intensity * 30))
            g = min(255, base_color[1] + int(intensity * 20))
            b = min(255, base_color[2] + int(intensity * 10))
            
            bridge.color = (r, g, b)
    
    def _update_trees(self):
        """更新树木摆动"""
        for tree in self.trees:
            # 风声影响树木摆动
            wind_factor = 1 + self.wind_strength * 2
            tree['sway'] += 0.02 * wind_factor
    
    @profile_function
    def render(self, screen: pygame.Surface):
        """渲染运河场景"""
        try:
            # 性能计时开始
            if self.performance_optimizer:
                self.performance_optimizer.profiler.start_timer('render')
            
            # 渲染天空背景
            try:
                self._render_sky(screen)
            except Exception as e:
                print(f"天空渲染错误: {e}")
            
            # 渲染远景背景
            try:
                self._render_background(screen)
            except Exception as e:
                print(f"背景渲染错误: {e}")
            
            # 渲染桥梁
            try:
                self._render_bridges(screen)
            except Exception as e:
                print(f"桥梁渲染错误: {e}")
            
            # 渲染河岸
            try:
                self._render_shore(screen)
            except Exception as e:
                print(f"河岸渲染错误: {e}")
            
            # 渲染水面
            try:
                if self.performance_optimizer:
                    self.performance_optimizer.profiler.start_timer('water_render')
                self._render_water(screen)
                if self.performance_optimizer:
                    self.performance_optimizer.profiler.end_timer('water_render')
            except Exception as e:
                print(f"水面渲染错误: {e}")
            
            # 渲染船只
            try:
                self._render_boats(screen)
            except Exception as e:
                print(f"船只渲染错误: {e}")
            
            # 渲染音频频谱反射
            try:
                self._render_spectrum_reflection(screen)
            except Exception as e:
                print(f"频谱反射渲染错误: {e}")
            
            # 渲染前景元素
            try:
                self._render_foreground(screen)
            except Exception as e:
                print(f"前景渲染错误: {e}")
            
            # 性能计时结束
            if self.performance_optimizer:
                self.performance_optimizer.profiler.end_timer('render')
                
        except Exception as e:
            print(f"运河场景渲染严重错误: {e}")
            import traceback
            traceback.print_exc()
            # 渲染简单的错误提示
            try:
                screen.fill((245, 245, 240))  # 宣纸色
                try:
                    font = pygame.font.Font("墨趣古风体.ttf", 36)
                except:
                    font = pygame.font.Font(None, 36)
                text = font.render("运河场景渲染异常", True, (50, 50, 50))
                text_rect = text.get_rect(center=(screen.get_width()//2, screen.get_height()//2))
                screen.blit(text, text_rect)
            except:
                pass  # 如果连错误提示都无法渲染，就保持静默
        
        # 渲染实时音频可视化覆盖层
        if self.audio_visualizer:
            try:
                if self.performance_optimizer:
                    self.performance_optimizer.profiler.start_timer('audio_visualization')
                self.audio_visualizer.render(screen)
                if self.performance_optimizer:
                    self.performance_optimizer.profiler.end_timer('audio_visualization')
            except Exception as e:
                print(f"音频可视化渲染错误: {e}")
        
        # 渲染音素可视化覆盖层
        if self.phoneme_visualizer:
            try:
                if self.performance_optimizer:
                    self.performance_optimizer.profiler.start_timer('phoneme_visualization')
                self.phoneme_visualizer.render(screen)
                if self.performance_optimizer:
                    self.performance_optimizer.profiler.end_timer('phoneme_visualization')
            except Exception as e:
                print(f"音素可视化渲染错误: {e}")
        
        # 渲染拟声词可视化覆盖层
        if self.onomatopoeia_visualizer:
            try:
                if self.performance_optimizer:
                    self.performance_optimizer.profiler.start_timer('onomatopoeia_visualization')
                self.onomatopoeia_visualizer.render(screen)
                if self.performance_optimizer:
                    self.performance_optimizer.profiler.end_timer('onomatopoeia_visualization')
            except Exception as e:
                print(f"拟声词可视化渲染错误: {e}")
    
    def _render_sky(self, screen: pygame.Surface):
        """渲染天空"""
        # 渐变天空
        for y in range(int(self.water_surface_y)):
            ratio = y / self.water_surface_y
            color = (
                int(CanalColors.SKY_MIST[0] * (1 - ratio) + CanalColors.PAPER_WHITE[0] * ratio),
                int(CanalColors.SKY_MIST[1] * (1 - ratio) + CanalColors.PAPER_WHITE[1] * ratio),
                int(CanalColors.SKY_MIST[2] * (1 - ratio) + CanalColors.PAPER_WHITE[2] * ratio)
            )
            pygame.draw.line(screen, color, (0, y), (self.width, y))
    
    def _render_background(self, screen: pygame.Surface):
        """渲染背景建筑"""
        for building in self.buildings:
            # 建筑主体
            rect = pygame.Rect(building['x'], building['y'], building['width'], building['height'])
            pygame.draw.rect(screen, building['color'], rect)
            
            # 建筑轮廓
            pygame.draw.rect(screen, CanalColors.INK_MEDIUM, rect, 2)
            
            # 窗户
            window_rows = int(building['height'] // 20)
            window_cols = int(building['width'] // 15)
            for row in range(window_rows):
                for col in range(window_cols):
                    if np.random.random() > 0.3:  # 70%概率有窗户
                        window_x = building['x'] + col * 15 + 3
                        window_y = building['y'] + row * 20 + 3
                        window_rect = pygame.Rect(window_x, window_y, 8, 12)
                        pygame.draw.rect(screen, CanalColors.SKY_MIST, window_rect)
    
    def _render_bridges(self, screen: pygame.Surface):
        """渲染桥梁"""
        for bridge in self.bridges:
            if bridge.style == "stone":
                self._render_stone_bridge(screen, bridge)
            elif bridge.style == "wood":
                self._render_wood_bridge(screen, bridge)
    
    def _render_stone_bridge(self, screen: pygame.Surface, bridge: Bridge):
        """渲染石桥"""
        # 桥面
        bridge_rect = pygame.Rect(
            bridge.x - bridge.width // 2,
            bridge.y,
            bridge.width,
            bridge.height // 3
        )
        pygame.draw.rect(screen, bridge.color, bridge_rect)
        
        # 桥拱
        arch_width = bridge.width // bridge.arch_count
        for i in range(bridge.arch_count):
            arch_x = bridge.x - bridge.width // 2 + i * arch_width + arch_width // 2
            arch_y = bridge.y + bridge.height // 3
            arch_rect = pygame.Rect(
                arch_x - arch_width // 3,
                arch_y,
                arch_width * 2 // 3,
                bridge.height * 2 // 3
            )
            
            # 拱形
            pygame.draw.ellipse(screen, bridge.color, arch_rect)
            pygame.draw.ellipse(screen, CanalColors.CANAL_BLUE, arch_rect.inflate(-10, -5))
        
        # 桥梁轮廓
        pygame.draw.rect(screen, CanalColors.INK_BLACK, bridge_rect, 3)
    
    def _render_wood_bridge(self, screen: pygame.Surface, bridge: Bridge):
        """渲染木桥"""
        # 桥面
        bridge_rect = pygame.Rect(
            bridge.x - bridge.width // 2,
            bridge.y,
            bridge.width,
            bridge.height // 4
        )
        pygame.draw.rect(screen, bridge.color, bridge_rect)
        
        # 木桩
        pile_count = 5
        for i in range(pile_count):
            pile_x = bridge.x - bridge.width // 2 + i * (bridge.width // (pile_count - 1))
            pile_rect = pygame.Rect(pile_x - 3, bridge.y + bridge.height // 4, 6, bridge.height * 3 // 4)
            pygame.draw.rect(screen, CanalColors.BRIDGE_BROWN_DEEP, pile_rect)
        
        # 桥梁轮廓
        pygame.draw.rect(screen, CanalColors.INK_BLACK, bridge_rect, 2)
    
    def _render_shore(self, screen: pygame.Surface):
        """渲染河岸"""
        # 河岸线
        if len(self.shore_points) > 1:
            pygame.draw.lines(screen, CanalColors.SHORE_STONE, False, self.shore_points, 3)
        
        # 树木
        for tree in self.trees:
            sway_offset = math.sin(tree['sway']) * 3
            
            # 树干
            trunk_start = (tree['x'] + sway_offset, tree['y'])
            trunk_end = (tree['x'] + sway_offset, tree['y'] - tree['size'])
            pygame.draw.line(screen, CanalColors.INK_DARK, trunk_start, trunk_end, 4)
            
            # 树冠（使用黑白水墨风格）
            crown_center = (tree['x'] + sway_offset, tree['y'] - tree['size'] * 0.8)
            crown_radius = tree['size'] * 0.4
            pygame.draw.circle(screen, CanalColors.INK_GRAY, crown_center, int(crown_radius))
            pygame.draw.circle(screen, CanalColors.TREE_SHADOW, crown_center, int(crown_radius), 2)
    
    def _render_water(self, screen: pygame.Surface):
        """渲染水面 - 使用GPU加速"""
        # 尝试使用GPU渲染水面
        audio_intensity = 0.0
        if self.spectrum_data is not None and len(self.spectrum_data) > 0:
            audio_intensity = np.mean(self.spectrum_data) / (np.max(self.spectrum_data) + 1e-8)
        
        # GPU水面渲染
        water_surface = self.gpu_renderer.render_water_surface(
            audio_intensity=audio_intensity,
            water_color=(0.137, 0.255, 0.373)  # 运河蓝色归一化
        )
        
        if water_surface:
            # 将GPU渲染的水面混合到屏幕
            water_rect = pygame.Rect(0, self.water_surface_y, self.width, self.height - self.water_surface_y)
            scaled_water = pygame.transform.scale(water_surface, water_rect.size)
            screen.blit(scaled_water, water_rect, special_flags=pygame.BLEND_ALPHA_SDL2)
        else:
            # 回退到CPU渲染
            self._render_water_cpu(screen)
        
        # GPU粒子效果（水花）
        particle_surface = self.gpu_renderer.render_particles(
            self.particle_system,
            particle_color=(0.922, 0.941, 0.961)  # 水花白色归一化
        )
        
        if particle_surface:
            screen.blit(particle_surface, (0, 0), special_flags=pygame.BLEND_ADD)
    
    def _render_water_cpu(self, screen: pygame.Surface):
        """CPU回退水面渲染 - 改进版本"""
        # 水面基色 - 使用渐变效果
        water_rect = pygame.Rect(0, int(self.water_surface_y), self.width, int(self.water_depth))
        
        # 创建渐变水面
        for y in range(int(self.water_depth)):
            depth_ratio = y / self.water_depth
            # 从浅蓝到深蓝的渐变
            color_r = int(CanalColors.CANAL_BLUE_LIGHT[0] * (1 - depth_ratio) + CanalColors.CANAL_BLUE_DEEP[0] * depth_ratio)
            color_g = int(CanalColors.CANAL_BLUE_LIGHT[1] * (1 - depth_ratio) + CanalColors.CANAL_BLUE_DEEP[1] * depth_ratio)
            color_b = int(CanalColors.CANAL_BLUE_LIGHT[2] * (1 - depth_ratio) + CanalColors.CANAL_BLUE_DEEP[2] * depth_ratio)
            
            pygame.draw.line(screen, (color_r, color_g, color_b), 
                           (0, int(self.water_surface_y + y)), 
                           (self.width, int(self.water_surface_y + y)))
        
        # 水波 - 改进的波浪效果
        if len(self.wave_points) > 1:
            # 创建平滑的水波表面
            wave_surface_points = []
            for point in self.wave_points:
                wave_surface_points.append((int(point.x), int(point.y)))
            
            # 添加边界点形成完整的多边形
            wave_surface_points.append((self.width, self.height))
            wave_surface_points.append((0, self.height))
            
            # 绘制水波表面
            if len(wave_surface_points) >= 3:
                pygame.draw.polygon(screen, CanalColors.CANAL_BLUE, wave_surface_points)
            
            # 水波线条 - 多层效果
            wave_line = [(int(point.x), int(point.y)) for point in self.wave_points]
            if len(wave_line) > 1:
                # 主水波线
                pygame.draw.lines(screen, CanalColors.CANAL_BLUE_LIGHT, False, wave_line, 3)
                
                # 次级水波线（偏移）
                offset_wave_line = [(int(point.x), int(point.y - 2)) for point in self.wave_points]
                pygame.draw.lines(screen, CanalColors.CANAL_BLUE_MIST, False, offset_wave_line, 1)
        
        # 添加水面反光效果
        current_time = time.time()
        for i in range(0, self.width, 30):
            reflection_intensity = (math.sin(i * 0.03 + current_time * 2) + 1) * 0.5
            if reflection_intensity > 0.6:
                reflection_y = self.water_surface_y + math.sin(i * 0.02 + current_time) * 5
                pygame.draw.circle(screen, CanalColors.WATER_FOAM, 
                                 (i, int(reflection_y)), 
                                 int(3 * reflection_intensity), 1)
    
    def _render_boats(self, screen: pygame.Surface):
        """渲染船只"""
        for boat in self.boats:
            if boat.boat_type == "cargo":
                self._render_cargo_boat(screen, boat)
            elif boat.boat_type == "passenger":
                self._render_passenger_boat(screen, boat)
            elif boat.boat_type == "small":
                self._render_small_boat(screen, boat)
    
    def _render_cargo_boat(self, screen: pygame.Surface, boat: Boat):
        """渲染货船"""
        # 船体
        hull_rect = pygame.Rect(
            int(boat.x - boat.size // 2),
            int(boat.y - boat.size // 4),
            int(boat.size),
            int(boat.size // 2)
        )
        pygame.draw.rect(screen, boat.color, hull_rect)
        
        # 货舱
        cargo_rect = pygame.Rect(
            int(boat.x - boat.size // 3),
            int(boat.y - boat.size // 2),
            int(boat.size * 2 // 3),
            int(boat.size // 4)
        )
        pygame.draw.rect(screen, CanalColors.BRIDGE_BROWN_LIGHT, cargo_rect)
        
        # 轮廓
        pygame.draw.rect(screen, CanalColors.INK_BLACK, hull_rect, 2)
        pygame.draw.rect(screen, CanalColors.INK_BLACK, cargo_rect, 1)
    
    def _render_passenger_boat(self, screen: pygame.Surface, boat: Boat):
        """渲染客船"""
        # 船体
        hull_rect = pygame.Rect(
            int(boat.x - boat.size // 2),
            int(boat.y - boat.size // 4),
            int(boat.size),
            int(boat.size // 2)
        )
        pygame.draw.rect(screen, boat.color, hull_rect)
        
        # 客舱
        cabin_rect = pygame.Rect(
            int(boat.x - boat.size // 3),
            int(boat.y - boat.size // 2),
            int(boat.size * 2 // 3),
            int(boat.size // 4)
        )
        pygame.draw.rect(screen, CanalColors.PAPER_WHITE, cabin_rect)
        
        # 窗户
        window_count = 4
        for i in range(window_count):
            window_x = cabin_rect.x + i * (cabin_rect.width // window_count) + 5
            window_y = cabin_rect.y + 3
            window_rect = pygame.Rect(window_x, window_y, 6, 8)
            pygame.draw.rect(screen, CanalColors.SKY_MIST, window_rect)
        
        # 轮廓
        pygame.draw.rect(screen, CanalColors.INK_BLACK, hull_rect, 2)
        pygame.draw.rect(screen, CanalColors.INK_BLACK, cabin_rect, 1)
    
    def _render_small_boat(self, screen: pygame.Surface, boat: Boat):
        """渲染小船"""
        # 船体（椭圆形）
        boat_rect = pygame.Rect(
            int(boat.x - boat.size // 2),
            int(boat.y - boat.size // 4),
            int(boat.size),
            int(boat.size // 2)
        )
        pygame.draw.ellipse(screen, boat.color, boat_rect)
        pygame.draw.ellipse(screen, CanalColors.INK_BLACK, boat_rect, 2)
        
        # 桅杆
        mast_start = (int(boat.x), int(boat.y - boat.size // 4))
        mast_end = (int(boat.x), int(boat.y - boat.size))
        pygame.draw.line(screen, CanalColors.BRIDGE_BROWN_DEEP, mast_start, mast_end, 2)
    
    def _render_spectrum_reflection(self, screen: pygame.Surface):
        """渲染频谱水面反射 - 使用GPU加速"""
        if self.spectrum_data is None or len(self.spectrum_data) == 0:
            return
        
        # 尝试GPU渲染
        reflection_surface = self.gpu_renderer.render_spectrum_reflection(self.spectrum_data)
        
        if reflection_surface:
            # 将GPU渲染的反射效果混合到屏幕
            reflection_rect = pygame.Rect(0, self.water_surface_y + 20, self.width, 60)
            scaled_reflection = pygame.transform.scale(reflection_surface, reflection_rect.size)
            screen.blit(scaled_reflection, reflection_rect, special_flags=pygame.BLEND_ADD)
        else:
            # 回退到CPU渲染
            self._render_spectrum_reflection_cpu(screen)
    
    def _render_spectrum_reflection_cpu(self, screen: pygame.Surface):
        """CPU回退频谱反射渲染 - 优化视觉效果"""
        if self.spectrum_data is None or len(self.spectrum_data) == 0:
            return
        
        # 在水面下方绘制频谱反射，位置更靠近水面
        reflection_y_start = self.water_surface_y + 10
        reflection_height = 30  # 减小高度，避免过于突兀
        
        bar_width = max(2, int(self.width / len(self.spectrum_data)))  # 增加条宽
        
        for i, magnitude in enumerate(self.spectrum_data):
            # 归一化幅度
            normalized_mag = min(magnitude / (np.max(self.spectrum_data) + 1e-8), 1.0)
            
            # 只渲染有意义的频谱数据
            if normalized_mag < 0.1:  # 过滤低幅度噪声
                continue
            
            # 计算反射条高度
            bar_height = max(1, int(normalized_mag * reflection_height * 0.6))  # 降低反射强度
            
            # 反射条位置
            bar_x = i * bar_width
            bar_y = reflection_y_start
            
            # 更柔和的透明度和颜色
            alpha = int(120 * (1 - normalized_mag * 0.3))  # 降低整体透明度
            
            # 使用更柔和的水墨蓝色
            base_color = CanalColors.CANAL_BLUE_MIST  # 使用雾蓝色替代亮蓝色
            color = (*base_color, alpha)
            
            # 创建带透明度的表面
            reflection_surf = pygame.Surface((bar_width, bar_height), pygame.SRCALPHA)
            reflection_surf.fill(color)
            screen.blit(reflection_surf, (bar_x, bar_y))
    
    def _render_foreground(self, screen: pygame.Surface):
        """渲染前景元素"""
        # 水花效果（基于音频强度）
        if self.audio_intensity > 0.1:
            foam_count = int(self.audio_intensity * 20)
            for _ in range(foam_count):
                foam_x = np.random.uniform(0, self.width)
                foam_y = np.random.uniform(self.water_surface_y - 10, self.water_surface_y + 10)
                foam_size = np.random.uniform(2, 6)
                pygame.draw.circle(screen, CanalColors.WATER_FOAM, (int(foam_x), int(foam_y)), int(foam_size))
    
    def get_audio_visualization_data(self) -> Dict:
        """获取音频可视化数据"""
        return {
            'water_flow_strength': self.water_flow_strength,
            'boat_activity': self.boat_activity,
            'bird_activity': self.bird_activity,
            'wind_strength': self.wind_strength,
            'audio_intensity': self.audio_intensity,
            'spectrum_data': self.spectrum_data
        }
    
    def _adjust_scene_by_classification(self, classifications):
        """根据声音分类结果调整场景参数"""
        if not classifications:
            return
        
        try:
            # 获取主要分类结果
            primary_classification = classifications[0]
            category = primary_classification.category
            confidence = primary_classification.confidence
            
            # 根据分类调整场景参数
            if category == 'water':
                # 水声：增强水波效果
                self.audio_intensity = min(1.0, self.audio_intensity + confidence * 0.3)
                for wave in self.water_waves:
                    wave.amplitude *= (1.0 + confidence * 0.2)
                    wave.frequency *= (1.0 + confidence * 0.1)
            
            elif category == 'boat':
                # 船只声：增加船只活动
                self.boat_activity = min(1.0, confidence * 1.2)
                for boat in self.boats:
                    boat.speed *= (1.0 + confidence * 0.3)
            
            elif category == 'bird':
                # 鸟鸣声：增强自然元素
                self.bird_activity = min(1.0, confidence * 1.1)
                # 可以在这里添加鸟类相关的视觉效果
            
            elif category == 'wind':
                # 风声：增强水面波动
                for wave in self.water_waves:
                    wave.speed *= (1.0 + confidence * 0.2)
            
            elif category == 'quiet':
                # 安静：减少所有动态效果
                self.audio_intensity *= (1.0 - confidence * 0.2)
                for wave in self.water_waves:
                    wave.amplitude *= (1.0 - confidence * 0.1)
            
            # 根据置信度调整整体场景活跃度
            if hasattr(self, 'scene_activity'):
                self.scene_activity = confidence
            
        except Exception as e:
            print(f"场景调整错误: {e}")

    def get_classification_summary(self):
        """获取分类摘要"""
        # 显示主导类别
        if hasattr(self, 'enhanced_classifier') and self.enhanced_classifier:
            summary = self.enhanced_classifier.get_classification_summary()
            if summary:
                # 使用统一的字体
                try:
                    font = pygame.font.Font("墨趣古风体.ttf", 36)
                except:
                    font = pygame.font.Font(None, 36)
                
                text = f"主导声音: {summary['dominant_class']} ({summary['confidence']:.2f})"
                text_surface = font.render(text, True, (255, 255, 255))
                screen.blit(text_surface, (20, 20))
        return None

# 测试代码
if __name__ == "__main__":
    # 测试运河可视化器
    pygame.init()
    
    width, height = 1280, 720
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("运河场景可视化测试")
    
    visualizer = CanalVisualizer(width, height)
    clock = pygame.time.Clock()
    
    print("运河场景可视化测试启动")
    print("按ESC退出")
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # 生成测试音频数据
        test_audio = np.random.normal(0, 0.1, 1024) * (1 + np.sin(time.time()) * 0.5)
        
        # 更新和渲染
        visualizer.update(test_audio)
        
        screen.fill(CanalColors.PAPER_WHITE)
        visualizer.render(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    print("测试完成")