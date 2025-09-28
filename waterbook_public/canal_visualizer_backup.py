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

@dataclass
class Particle:
    """粒子数据类"""
    x: float
    y: float
    z: float  # 深度信息
    size: float
    color: Tuple[int, int, int]
    velocity_x: float
    velocity_y: float
    life: float  # 生命周期 (0-1)
    particle_type: str  # "building", "tree", "sky", "water_drop"
    intensity: float  # 音频响应强度

@dataclass
class ParticleSystem:
    """粒子系统"""
    particles: List[Particle]
    max_particles: int
    emission_rate: float
    audio_responsiveness: float

class CanalVisualizer:
    """运河场景可视化器 - 粒子点云版本"""
    
    def __init__(self, width: int, height: int):
        """初始化可视化器"""
        self.width = width
        self.height = height
        self.water_surface_y = height * 0.7
        
        # 音频数据
        self.audio_data = None
        self.audio_intensity = 0.0
        self.frequency_bands = np.zeros(8)
        
        # 粒子系统
        self.particle_systems = {
            'buildings': ParticleSystem([], 2000, 50.0, 0.8),
            'trees': ParticleSystem([], 1500, 30.0, 0.6),
            'sky': ParticleSystem([], 800, 20.0, 0.4),
            'water_drops': ParticleSystem([], 500, 100.0, 1.0)
        }
        
        # 初始化粒子系统
        self._init_particle_systems()
        
        # 保留原有的水面和船只系统
        self._init_water_waves()
        self._init_boats()
        self._init_bridges()
        
        # 性能优化
        try:
            self.performance_optimizer = get_optimizer()
        except:
            self.performance_optimizer = None
        
        # 音频可视化器
        try:
            self.audio_visualizer = RealtimeAudioVisualizer(width, height)
        except Exception as e:
            print(f"音频可视化器初始化失败: {e}")
            self.audio_visualizer = None
        
        # 风力和环境参数
        self.wind_strength = 0.0
        self.scene_activity = 0.5
        
        print("运河粒子点云可视化器初始化完成")

    def _init_particle_systems(self):
        """初始化粒子系统"""
        # 初始化建筑粒子
        self._init_building_particles()
        
        # 初始化树木粒子
        self._init_tree_particles()
        
        # 初始化天空粒子
        self._init_sky_particles()
        
        # 初始化水滴粒子
        self._init_water_drop_particles()
    
    def _init_building_particles(self):
        """初始化建筑粒子点云"""
        building_system = self.particle_systems['buildings']
        
        # 创建多个建筑群的粒子点云
        building_count = 8
        for building_idx in range(building_count):
            building_x = building_idx * (self.width / building_count) + np.random.uniform(-20, 20)
            building_height = np.random.uniform(80, 150)
            building_width = np.random.uniform(40, 80)
            building_depth = np.random.uniform(30, 60)
            
            # 为每个建筑生成粒子点云
            particles_per_building = 200 + int(building_height * 2)
            
            for _ in range(particles_per_building):
                # 在建筑体积内随机分布粒子
                x = building_x + np.random.uniform(-building_width/2, building_width/2)
                y = self.water_surface_y - np.random.uniform(0, building_height)
                z = np.random.uniform(0, building_depth)
                
                # 粒子大小根据深度变化
                size = np.random.uniform(1, 3) * (1 + z / building_depth * 0.5)
                
                # 建筑粒子颜色 - 水墨风格
                base_gray = np.random.randint(60, 120)
                color = (base_gray, base_gray, base_gray)
                
                particle = Particle(
                    x=x, y=y, z=z,
                    size=size,
                    color=color,
                    velocity_x=np.random.uniform(-0.1, 0.1),
                    velocity_y=np.random.uniform(-0.05, 0.05),
                    life=1.0,
                    particle_type="building",
                    intensity=np.random.uniform(0.3, 0.8)
                )
                
                building_system.particles.append(particle)
    
    def _init_tree_particles(self):
        """初始化树木粒子点云"""
        tree_system = self.particle_systems['trees']
        
        # 创建多棵树的粒子点云
        tree_count = 15
        for tree_idx in range(tree_count):
            tree_x = np.random.uniform(0, self.width)
            tree_y = self.water_surface_y + np.random.uniform(-10, 5)
            tree_height = np.random.uniform(40, 80)
            crown_radius = np.random.uniform(20, 35)
            
            # 树干粒子
            trunk_particles = 50
            for _ in range(trunk_particles):
                x = tree_x + np.random.uniform(-3, 3)
                y = tree_y - np.random.uniform(0, tree_height * 0.7)
                z = np.random.uniform(0, 6)
                
                particle = Particle(
                    x=x, y=y, z=z,
                    size=np.random.uniform(1, 2),
                    color=(40, 40, 40),  # 深墨色树干
                    velocity_x=np.random.uniform(-0.05, 0.05),
                    velocity_y=np.random.uniform(-0.02, 0.02),
                    life=1.0,
                    particle_type="tree",
                    intensity=np.random.uniform(0.4, 0.7)
                )
                
                tree_system.particles.append(particle)
            
            # 树冠粒子
            crown_particles = 150
            for _ in range(crown_particles):
                # 在球形树冠内随机分布
                angle = np.random.uniform(0, 2 * np.pi)
                radius = np.random.uniform(0, crown_radius)
                height_offset = np.random.uniform(-crown_radius/2, crown_radius/2)
                
                x = tree_x + radius * np.cos(angle)
                y = tree_y - tree_height * 0.7 + height_offset
                z = radius * np.sin(angle) + crown_radius/2
                
                # 树叶粒子颜色变化
                gray_value = np.random.randint(80, 140)
                color = (gray_value, gray_value, gray_value)
                
                particle = Particle(
                    x=x, y=y, z=z,
                    size=np.random.uniform(0.8, 2.5),
                    color=color,
                    velocity_x=np.random.uniform(-0.2, 0.2),
                    velocity_y=np.random.uniform(-0.1, 0.1),
                    life=1.0,
                    particle_type="tree",
                    intensity=np.random.uniform(0.5, 0.9)
                )
                
                tree_system.particles.append(particle)
    
    def _init_sky_particles(self):
        """初始化天空粒子点云"""
        sky_system = self.particle_systems['sky']
        
        # 创建天空中的云雾粒子
        for _ in range(800):
            x = np.random.uniform(0, self.width)
            y = np.random.uniform(0, self.water_surface_y * 0.6)
            z = np.random.uniform(50, 200)
            
            # 天空粒子大小和颜色
            size = np.random.uniform(2, 6) * (1 + z / 200)
            gray_value = np.random.randint(180, 230)
            color = (gray_value, gray_value, gray_value)
            
            particle = Particle(
                x=x, y=y, z=z,
                size=size,
                color=color,
                velocity_x=np.random.uniform(-0.3, 0.3),
                velocity_y=np.random.uniform(-0.1, 0.1),
                life=1.0,
                particle_type="sky",
                intensity=np.random.uniform(0.2, 0.6)
            )
            
            sky_system.particles.append(particle)
    
    def _init_water_drop_particles(self):
        """初始化水滴粒子系统"""
        # 水滴粒子在运行时动态生成，这里只初始化空系统
        pass

    def _update_particle_systems(self):
        """更新所有粒子系统"""
        # 更新建筑粒子
        self._update_building_particles()
        
        # 更新树木粒子
        self._update_tree_particles()
        
        # 更新天空粒子
        self._update_sky_particles()
        
        # 更新水滴粒子
        self._update_water_drop_particles()
    
    def _update_building_particles(self):
        """更新建筑粒子"""
        building_system = self.particle_systems['buildings']
        
        for particle in building_system.particles:
            # 音频响应 - 建筑粒子根据低频能量轻微震动
            if self.audio_intensity > 0.3:
                shake_intensity = self.audio_intensity * particle.intensity * 0.5
                particle.x += np.random.uniform(-shake_intensity, shake_intensity)
                particle.y += np.random.uniform(-shake_intensity/2, shake_intensity/2)
            
            # 颜色根据音频强度变化
            base_intensity = int(60 + self.audio_intensity * particle.intensity * 40)
            particle.color = (base_intensity, base_intensity, base_intensity)
    
    def _update_tree_particles(self):
        """更新树木粒子"""
        tree_system = self.particle_systems['trees']
        
        for particle in tree_system.particles:
            # 风力影响 - 树木粒子摆动
            wind_factor = self.wind_strength * particle.intensity
            particle.x += particle.velocity_x * wind_factor
            particle.y += particle.velocity_y * wind_factor * 0.5
            
            # 音频响应 - 高频影响树叶颤动
            if len(self.frequency_bands) > 4 and self.frequency_bands[4] > 0.2:
                tremor = self.frequency_bands[4] * particle.intensity * 0.3
                particle.x += np.random.uniform(-tremor, tremor)
                particle.y += np.random.uniform(-tremor, tremor)
            
            # 边界检查和重置
            if particle.x < -50 or particle.x > self.width + 50:
                particle.velocity_x *= -0.8
    
    def _update_sky_particles(self):
        """更新天空粒子"""
        sky_system = self.particle_systems['sky']
        
        for particle in sky_system.particles:
            # 缓慢漂移
            particle.x += particle.velocity_x
            particle.y += particle.velocity_y
            
            # 音频响应 - 中频影响云雾密度
            if len(self.frequency_bands) > 2:
                density_factor = self.frequency_bands[2] * particle.intensity
                new_alpha = int(180 + density_factor * 50)
                particle.color = (new_alpha, new_alpha, new_alpha)
            
            # 边界循环
            if particle.x < -20:
                particle.x = self.width + 20
            elif particle.x > self.width + 20:
                particle.x = -20
    
    def _update_water_drop_particles(self):
        """更新水滴粒子"""
        water_system = self.particle_systems['water_drops']
        
        # 根据音频强度动态生成水滴粒子
        if self.audio_intensity > 0.4:
            drops_to_add = int(self.audio_intensity * 20)
            
            for _ in range(drops_to_add):
                if len(water_system.particles) < water_system.max_particles:
                    x = np.random.uniform(0, self.width)
                    y = self.water_surface_y + np.random.uniform(-20, 10)
                    
                    particle = Particle(
                        x=x, y=y, z=0,
                        size=np.random.uniform(1, 3),
                        color=(220, 220, 220),
                        velocity_x=np.random.uniform(-1, 1),
                        velocity_y=np.random.uniform(-2, -0.5),
                        life=1.0,
                        particle_type="water_drop",
                        intensity=self.audio_intensity
                    )
                    
                    water_system.particles.append(particle)
        
        # 更新现有水滴
        particles_to_remove = []
        for i, particle in enumerate(water_system.particles):
            particle.x += particle.velocity_x
            particle.y += particle.velocity_y
            particle.life -= 0.02
            
            # 重力影响
            particle.velocity_y += 0.1
            
            # 移除生命周期结束的粒子
            if particle.life <= 0 or particle.y > self.height:
                particles_to_remove.append(i)
        
        # 移除过期粒子
        for i in reversed(particles_to_remove):
            water_system.particles.pop(i)

    def _render_particle_systems(self, screen: pygame.Surface):
        """渲染所有粒子系统"""
        # 按深度排序渲染（远到近）
        all_particles = []
        
        for system_name, system in self.particle_systems.items():
            for particle in system.particles:
                all_particles.append(particle)
        
        # 按z坐标排序（远的先渲染）
        all_particles.sort(key=lambda p: p.z, reverse=True)
        
        # 渲染粒子
        for particle in all_particles:
            self._render_particle(screen, particle)
    
    def _render_particle(self, screen: pygame.Surface, particle: Particle):
        """渲染单个粒子"""
        try:
            # 计算屏幕坐标
            screen_x = int(particle.x)
            screen_y = int(particle.y)
            
            # 边界检查
            if (screen_x < -10 or screen_x > self.width + 10 or 
                screen_y < -10 or screen_y > self.height + 10):
                return
            
            # 根据深度调整大小和透明度
            depth_factor = max(0.3, 1.0 - particle.z / 200.0)
            adjusted_size = max(1, int(particle.size * depth_factor))
            
            # 调整颜色透明度
            color = particle.color
            if particle.particle_type == "sky":
                # 天空粒子使用半透明效果
                alpha = int(color[0] * depth_factor * particle.life)
                color = (alpha, alpha, alpha)
            
            # 渲染粒子
            if adjusted_size == 1:
                # 单像素粒子
                if 0 <= screen_x < self.width and 0 <= screen_y < self.height:
                    screen.set_at((screen_x, screen_y), color)
            else:
                # 多像素粒子
                pygame.draw.circle(screen, color, (screen_x, screen_y), adjusted_size)
                
                # 为建筑和树木粒子添加水墨晕染效果
                if particle.particle_type in ["building", "tree"] and adjusted_size > 2:
                    # 外围晕染
                    fade_color = tuple(min(255, c + 20) for c in color)
                    pygame.draw.circle(screen, fade_color, (screen_x, screen_y), adjusted_size + 1, 1)
        
        except Exception as e:
            # 静默处理渲染错误，避免影响整体性能
            pass

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
        self.water_depth = self.height - self.water_surface_y

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

    @profile_function
    def update(self, audio_data: Optional[np.ndarray] = None):
        """更新场景状态（粒子点云优化版本）"""
        try:
            # 性能计时开始
            if self.performance_optimizer:
                self.performance_optimizer.profiler.start_timer('update_total')
            
            # 限制更新频率
            current_time = time.time()
            if not hasattr(self, 'last_update_time'):
                self.last_update_time = 0
            
            # 每33ms更新一次（30fps）优化性能
            if current_time - self.last_update_time < 0.033:
                return
            
            self.last_update_time = current_time
            self.time = getattr(self, 'time', 0) + 0.033
            
            # 处理音频数据
            if audio_data is not None:
                try:
                    if self.performance_optimizer:
                        self.performance_optimizer.profiler.start_timer('audio_processing')
                    
                    # 降采样音频数据以提高性能
                    if len(audio_data) > 512:
                        step = len(audio_data) // 512
                        audio_data = audio_data[::step]
                    
                    self._process_audio_data(audio_data)
                    
                    # 更新音频可视化器
                    if self.audio_visualizer:
                        self.audio_visualizer.update(audio_data)
                    
                    if self.performance_optimizer:
                        self.performance_optimizer.profiler.end_timer('audio_processing')
                        
                except Exception as e:
                    print(f"音频数据处理错误: {e}")
            
            # 更新粒子系统
            try:
                if self.performance_optimizer:
                    self.performance_optimizer.profiler.start_timer('particle_update')
                self._update_particle_systems()
                if self.performance_optimizer:
                    self.performance_optimizer.profiler.end_timer('particle_update')
            except Exception as e:
                print(f"粒子系统更新错误: {e}")
            
            # 更新传统场景元素（简化版本）
            try:
                # 水波更新
                self._update_water_waves_optimized()
                
                # 船只更新
                self._update_boats()
                
            except Exception as e:
                print(f"场景元素更新错误: {e}")
            
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
        update_count = min(len(self.wave_points), 15)  # 最多更新15个点
        for i in range(0, len(self.wave_points), max(1, len(self.wave_points) // update_count)):
            wave = self.wave_points[i]
            # 基础波动
            wave.phase += wave.frequency * wave.speed
            
            # 音频响应（简化计算）
            audio_factor = 1 + self.audio_intensity * 0.5
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
            speed_factor = 1 + self.audio_intensity * 0.3
            boat.x += boat.speed * boat.direction * speed_factor * 0.1
            
            # 水波影响船只摆动
            wave_offset = math.sin(self.time * 2 + boat.x * 0.01) * 3
            boat.y = self.water_surface_y - (boat.size * 0.3) + wave_offset
            
            # 边界处理 - 船只循环出现
            if boat.direction > 0 and boat.x > self.width + boat.size:
                boat.x = -boat.size
            elif boat.direction < 0 and boat.x < -boat.size:
                boat.x = self.width + boat.size

    @profile_function
    def render(self, screen: pygame.Surface):
        """渲染运河场景（粒子点云版本）"""
        try:
            # 性能计时开始
            if self.performance_optimizer:
                self.performance_optimizer.profiler.start_timer('render')
            
            # 渲染天空背景
            try:
                self._render_sky(screen)
            except Exception as e:
                print(f"天空渲染错误: {e}")
            
            # 渲染粒子系统（替代原有的色块建筑和树木）
            try:
                if self.performance_optimizer:
                    self.performance_optimizer.profiler.start_timer('particle_render')
                self._render_particle_systems(screen)
                if self.performance_optimizer:
                    self.performance_optimizer.profiler.end_timer('particle_render')
            except Exception as e:
                print(f"粒子系统渲染错误: {e}")
            
            # 渲染桥梁
            try:
                self._render_bridges(screen)
            except Exception as e:
                print(f"桥梁渲染错误: {e}")
            
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

    def _process_audio_data(self, audio_data: np.ndarray):
        """处理音频数据，提取特征用于场景响应"""
        try:
            # 计算音频强度
            self.audio_intensity = np.mean(np.abs(audio_data))
            
            # 计算频谱
            if len(audio_data) >= 256:
                fft = np.fft.fft(audio_data[:256])
                self.audio_spectrum = np.abs(fft[:128])
                
                # 提取频段特征
                low_freq = np.mean(self.audio_spectrum[:32])    # 低频
                mid_freq = np.mean(self.audio_spectrum[32:96])  # 中频
                high_freq = np.mean(self.audio_spectrum[96:])   # 高频
                
                # 更新场景参数
                self.low_freq_intensity = low_freq
                self.mid_freq_intensity = mid_freq
                self.high_freq_intensity = high_freq
            else:
                # 音频数据不足时使用默认值
                self.audio_spectrum = np.zeros(128)
                self.low_freq_intensity = 0
                self.mid_freq_intensity = 0
                self.high_freq_intensity = 0
                
        except Exception as e:
            print(f"音频数据处理错误: {e}")
            # 设置默认值
            self.audio_intensity = 0
            self.audio_spectrum = np.zeros(128)
            self.low_freq_intensity = 0
            self.mid_freq_intensity = 0
            self.high_freq_intensity = 0

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