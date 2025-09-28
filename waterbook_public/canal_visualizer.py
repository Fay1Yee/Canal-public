# 运河场景可视化器 - 清理版本
# 实现粒子点云效果替代色块显示，优化性能

import pygame
import numpy as np
import math
import time
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass

# 导入结构化点云生成器
from structured_pointcloud_generator import (
    StructuredPointCloudGenerator, 
    StructuredParticle, 
    StructureType
)

# 导入声音分类器
try:
    from enhanced_sound_classifier import EnhancedSoundClassifier
    SOUND_CLASSIFIER_ENABLED = True
except ImportError:
    SOUND_CLASSIFIER_ENABLED = False
    print("声音分类器模块未找到，将使用基础音频处理")

# 性能优化模块
try:
    from performance_optimizer import get_optimizer, profile_function
    PERFORMANCE_OPTIMIZATION_ENABLED = True
except ImportError:
    PERFORMANCE_OPTIMIZATION_ENABLED = False
    def profile_function(func):
        return func

# 内存分析模块
try:
    from memory_analyzer import MemoryProfiler
    MEMORY_ANALYSIS_ENABLED = True
except ImportError:
    MEMORY_ANALYSIS_ENABLED = False

class CanalColors:
    """运河场景颜色定义 - 水墨风格"""
    # 基础墨色 - 调整为更淡雅的古风配色
    INK_BLACK = (45, 45, 50)             # 浓墨（降低饱和度）
    INK_DARK = (65, 65, 70)              # 重墨（降低饱和度）
    INK_MEDIUM = (90, 90, 95)            # 中墨（降低饱和度）
    INK_GRAY = (120, 120, 125)           # 墨灰（降低饱和度）
    INK_LIGHT = (150, 150, 155)          # 淡墨（降低饱和度）
    INK_FAINT = (200, 200, 205)          # 极淡墨（降低饱和度）
    
    # 纸张色调 - E2场景专用纯白背景
    PAPER_WHITE = (255, 255, 255)        # 纯白背景（E2专用）
    PAPER_CREAM = (250, 250, 252)        # 淡雅米色
    PAPER_AGED = (248, 248, 250)         # 淡雅陈年色
    
    # 水墨替代色彩 - 调整为更淡雅的古风配色
    CANAL_BLUE_DEEP = (55, 55, 60)       # 深水墨（降低饱和度）
    CANAL_BLUE = (85, 85, 90)            # 中水墨（降低饱和度）
    CANAL_BLUE_LIGHT = (115, 115, 120)   # 浅水墨（降低饱和度）
    CANAL_BLUE_MIST = (165, 165, 170)    # 水雾墨（降低饱和度）
    
    # 自然元素墨色 - 调整为更淡雅的古风配色
    CANAL_GREEN_DEEP = (60, 60, 55)      # 深墨绿（降低饱和度）
    CANAL_GREEN = (90, 90, 85)           # 中墨绿（降低饱和度）
    CANAL_GREEN_LIGHT = (120, 120, 115)  # 浅墨绿（降低饱和度）
    CANAL_GREEN_MIST = (150, 150, 145)   # 绿雾墨（降低饱和度）
    
    # 建筑元素墨色 - 调整为更淡雅的古风配色
    BRIDGE_BROWN_DEEP = (70, 70, 65)     # 深墨棕（降低饱和度）
    BRIDGE_BROWN = (100, 100, 95)        # 中墨棕（降低饱和度）
    BRIDGE_BROWN_LIGHT = (130, 130, 125) # 浅墨棕（降低饱和度）
    
    # 特殊效果色 - 调整为更淡雅的古风配色
    WATER_FOAM = (245, 245, 250)         # 水花白（淡雅）
    SKY_MIST = (220, 220, 225)           # 天空雾（淡雅）
    SHORE_STONE = (110, 110, 115)        # 岸石灰（淡雅）
    TREE_SHADOW = (80, 80, 85)           # 树影墨（淡雅）
    
    # 传统色彩 - 调整为更淡雅的古风配色
    TRADITIONAL_BLACK = (50, 50, 55)     # 传统墨色（淡雅）
    TRADITIONAL_GRAY = (140, 140, 145)   # 传统灰（淡雅）
    SEAL_RED = (160, 65, 55)             # 印章红（降低饱和度，保持古风韵味）

@dataclass
class WavePoint:
    """水波点数据结构"""
    x: float
    y: float
    amplitude: float
    frequency: float
    phase: float
    speed: float

@dataclass
class Boat:
    """船只数据结构"""
    x: float
    y: float
    size: float
    speed: float
    direction: float
    boat_type: str  # "货船", "客船", "小船"
    color: Tuple[int, int, int]

@dataclass
class Bridge:
    """桥梁数据结构"""
    x: float
    y: float
    width: float
    height: float
    arch_count: int
    color: Tuple[int, int, int]
    style: str  # "石桥", "木桥", "现代桥"

@dataclass
class Particle:
    """粒子数据结构"""
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
    """粒子系统数据结构"""
    particles: List[Particle]
    max_particles: int
    emission_rate: float
    audio_responsiveness: float

class CanalVisualizer:
    """运河场景可视化器 - 粒子点云版本"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.water_surface_y = height * 0.6
        
        # 初始化结构化点云生成器
        self.structured_pointcloud_generator = StructuredPointCloudGenerator(width, height)
        self.structured_particles = []
        
        # 生成初始结构化场景
        self._generate_structured_scene()
        
        # 初始化粒子系统（保留原有系统作为补充）
        self._init_particle_systems()
        
        # 初始化传统元素
        self._init_water_waves()
        self._init_boats()
        self._init_bridges()
        
        # 音频相关属性
        self.audio_energy = 0.0
        self.audio_peak = 0.0
        self.spectrum = None
        self.dominant_freq = 0
        
        # 场景活动参数
        self.water_activity = 0.5
        self.boat_activity = 0.3
        self.scene_activity = 0.4
        
        # 时间偏移
        self.time_offset = 0.0
        
        # 性能监控
        self.render_times = []
        self.last_update_time = 0.0
        
        # 初始化声音分类器
        self.sound_classifier = None
        self.current_classification = None
        self.classification_confidence = 0.0
        self.classification_history = []
        
        if SOUND_CLASSIFIER_ENABLED:
            try:
                self.sound_classifier = EnhancedSoundClassifier()
                print("声音分类器初始化成功")
            except Exception as e:
                print(f"声音分类器初始化失败: {e}")
                self.sound_classifier = None

    def _init_particle_systems(self):
        """初始化粒子系统"""
        self.particle_systems = {
            'buildings': ParticleSystem([], 200, 10.0, 1.0),
            'trees': ParticleSystem([], 150, 15.0, 1.5),
            'sky': ParticleSystem([], 100, 5.0, 0.8),
            'water_drops': ParticleSystem([], 80, 20.0, 2.0)
        }
        
        # 初始化各类粒子
        self._init_building_particles()
        self._init_tree_particles()
        self._init_sky_particles()
        self._init_water_drop_particles()
    
    def _generate_structured_scene(self):
        """生成结构化场景点云"""
        # 生成完整的运河场景结构化点云
        self.structured_particles = self.structured_pointcloud_generator.generate_canal_scene()
        print(f"生成了 {len(self.structured_particles)} 个结构化粒子")

    def _init_building_particles(self):
        """初始化建筑粒子"""
        building_system = self.particle_systems['buildings']
        
        # 左岸建筑群
        for i in range(60):
            x = np.random.uniform(0, self.width * 0.3)
            y = np.random.uniform(self.height * 0.2, self.height * 0.5)
            z = np.random.uniform(0.3, 0.8)  # 深度
            
            # 随机选择建筑颜色
            building_colors = [
                CanalColors.INK_DARK,
                CanalColors.INK_MEDIUM,
                CanalColors.BRIDGE_BROWN
            ]
            color = building_colors[np.random.randint(0, len(building_colors))]
            
            particle = Particle(
                x=x, y=y, z=z,
                size=np.random.uniform(2, 6),
                color=color,
                velocity_x=np.random.uniform(-0.1, 0.1),
                velocity_y=np.random.uniform(-0.05, 0.05),
                life=1.0,
                particle_type="building",
                intensity=0.0
            )
            building_system.particles.append(particle)
        
        # 右岸建筑群
        for i in range(60):
            x = np.random.uniform(self.width * 0.7, self.width * 0.95)
            y = np.random.uniform(self.height * 0.2, self.height * 0.5)
            z = np.random.uniform(0.3, 0.8)  # 深度
            
            # 随机选择建筑颜色
            building_colors = [
                CanalColors.INK_DARK,
                CanalColors.INK_MEDIUM,
                CanalColors.BRIDGE_BROWN
            ]
            color = building_colors[np.random.randint(0, len(building_colors))]
            
            particle = Particle(
                x=x, y=y, z=z,
                size=np.random.uniform(2, 6),
                color=color,
                velocity_x=np.random.uniform(-0.1, 0.1),
                velocity_y=np.random.uniform(-0.05, 0.05),
                life=1.0,
                particle_type="building",
                intensity=0.0
            )
            building_system.particles.append(particle)

    def _init_tree_particles(self):
        """初始化树木粒子"""
        tree_system = self.particle_systems['trees']
        
        # 沿岸树木
        tree_positions = [
            (self.width * 0.1, self.height * 0.4),
            (self.width * 0.25, self.height * 0.35),
            (self.width * 0.75, self.height * 0.38),
            (self.width * 0.9, self.height * 0.42)
        ]
        
        for tree_x, tree_y in tree_positions:
            # 每棵树用多个粒子表示
            for i in range(25):
                offset_x = np.random.normal(0, 15)
                offset_y = np.random.normal(0, 20)
                
                # 随机选择树木颜色
                tree_colors = [
                    CanalColors.CANAL_GREEN_DEEP,
                    CanalColors.CANAL_GREEN,
                    CanalColors.TREE_SHADOW
                ]
                color = tree_colors[np.random.randint(0, len(tree_colors))]
                
                particle = Particle(
                    x=tree_x + offset_x,
                    y=tree_y + offset_y,
                    z=np.random.uniform(0.4, 0.9),
                    size=np.random.uniform(1, 4),
                    color=color,
                    velocity_x=np.random.uniform(-0.2, 0.2),
                    velocity_y=np.random.uniform(-0.1, 0.1),
                    life=1.0,
                    particle_type="tree",
                    intensity=0.0
                )
                tree_system.particles.append(particle)

    def _init_sky_particles(self):
        """初始化天空粒子"""
        sky_system = self.particle_systems['sky']
        
        # 天空中的云雾粒子
        for i in range(50):
            particle = Particle(
                x=np.random.uniform(0, self.width),
                y=np.random.uniform(0, self.height * 0.3),
                z=np.random.uniform(0.1, 0.3),
                size=np.random.uniform(3, 8),
                color=CanalColors.SKY_MIST,
                velocity_x=np.random.uniform(-0.3, 0.3),
                velocity_y=np.random.uniform(-0.1, 0.1),
                life=1.0,
                particle_type="sky",
                intensity=0.0
            )
            sky_system.particles.append(particle)

    def _init_water_drop_particles(self):
        """初始化水滴粒子"""
        # 水滴粒子将在运行时根据音频动态生成
        pass

    def _update_particle_systems(self):
        """更新所有粒子系统"""
        for system_name, system in self.particle_systems.items():
            if system_name == 'buildings':
                self._update_building_particles()
            elif system_name == 'trees':
                self._update_tree_particles()
            elif system_name == 'sky':
                self._update_sky_particles()
            elif system_name == 'water_drops':
                self._update_water_drop_particles()

    def _update_building_particles(self):
        """更新建筑粒子"""
        building_system = self.particle_systems['buildings']
        
        for particle in building_system.particles:
            # 音频响应
            if hasattr(self, 'audio_energy'):
                particle.intensity = self.audio_energy * 5
                
                # 根据音频强度调整粒子大小和透明度
                base_size = 2 + particle.z * 4
                particle.size = base_size * (1 + particle.intensity * 0.3)
            
            # 轻微的随机移动
            particle.x += particle.velocity_x * (1 + particle.intensity * 0.5)
            particle.y += particle.velocity_y * (1 + particle.intensity * 0.5)

    def _update_tree_particles(self):
        """更新树木粒子"""
        tree_system = self.particle_systems['trees']
        
        for particle in tree_system.particles:
            # 风吹效果
            wind_strength = 0.1 + (self.audio_energy if hasattr(self, 'audio_energy') else 0) * 0.2
            particle.x += math.sin(time.time() * 2 + particle.y * 0.01) * wind_strength
            particle.y += math.cos(time.time() * 1.5 + particle.x * 0.01) * wind_strength * 0.5
            
            # 音频响应
            if hasattr(self, 'audio_energy'):
                particle.intensity = self.audio_energy * 3
                
                # 根据音频调整颜色深度
                base_color = CanalColors.CANAL_GREEN
                intensity_factor = 1 - particle.intensity * 0.3
                particle.color = tuple(int(c * intensity_factor) for c in base_color)

    def _update_sky_particles(self):
        """更新天空粒子"""
        sky_system = self.particle_systems['sky']
        
        for particle in sky_system.particles:
            # 缓慢漂移
            particle.x += particle.velocity_x
            particle.y += particle.velocity_y
            
            # 边界循环
            if particle.x > self.width + 20:
                particle.x = -20
            elif particle.x < -20:
                particle.x = self.width + 20
                
            # 音频响应 - 云雾密度变化
            if hasattr(self, 'audio_energy'):
                particle.intensity = self.audio_energy * 2
                base_alpha = 100
                alpha = int(base_alpha * (1 + particle.intensity * 0.5))
                particle.color = (*CanalColors.SKY_MIST[:3], min(alpha, 255))

    def _update_water_drop_particles(self):
        """更新水滴粒子"""
        water_system = self.particle_systems['water_drops']
        
        # 根据音频强度生成新的水滴
        if hasattr(self, 'audio_energy') and self.audio_energy > 0.1:
            if len(water_system.particles) < water_system.max_particles:
                # 生成新水滴
                for _ in range(int(self.audio_energy * 10)):
                    if len(water_system.particles) >= water_system.max_particles:
                        break
                        
                    particle = Particle(
                        x=np.random.uniform(0, self.width),
                        y=self.water_surface_y + np.random.uniform(-10, 5),
                        z=np.random.uniform(0.8, 1.0),
                        size=np.random.uniform(1, 3),
                        color=CanalColors.WATER_FOAM,
                        velocity_x=np.random.uniform(-1, 1),
                        velocity_y=np.random.uniform(-2, -0.5),
                        life=1.0,
                        particle_type="water_drop",
                        intensity=self.audio_energy
                    )
                    water_system.particles.append(particle)
        
        # 更新现有水滴
        particles_to_remove = []
        for i, particle in enumerate(water_system.particles):
            particle.x += particle.velocity_x
            particle.y += particle.velocity_y
            particle.life -= 0.02
            
            # 重力效果
            particle.velocity_y += 0.1
            
            # 移除生命周期结束的粒子
            if particle.life <= 0 or particle.y > self.height:
                particles_to_remove.append(i)
        
        # 移除过期粒子
        for i in reversed(particles_to_remove):
            water_system.particles.pop(i)

    def _render_particle_systems(self, screen: pygame.Surface):
        """渲染所有粒子系统"""
        # 按深度排序渲染
        all_particles = []
        for system in self.particle_systems.values():
            all_particles.extend(system.particles)
        
        # 按z值排序（远到近）
        all_particles.sort(key=lambda p: p.z)
        
        for particle in all_particles:
            self._render_particle(screen, particle)

    def _render_particle(self, screen: pygame.Surface, particle: Particle):
        """渲染单个粒子 - 增强E2场景的古风粒子效果"""
        try:
            # 深度调整
            depth_factor = particle.z
            adjusted_size = max(1, int(particle.size * depth_factor))
            
            # 颜色深度调整 - 增强古风效果
            color = particle.color
            if len(color) == 3:  # RGB
                depth_alpha = int(255 * depth_factor * particle.life * 0.7)  # 降低透明度，更加淡雅
                color = (*color, depth_alpha)
            
            # 创建带透明度的表面
            if adjusted_size > 0:
                particle_surface = pygame.Surface((adjusted_size * 2, adjusted_size * 2), pygame.SRCALPHA)
                
                # 根据粒子类型选择渲染方式 - 增强古风效果
                if particle.particle_type == "building":
                    # 建筑粒子 - 方形，带古风边缘模糊
                    pygame.draw.rect(particle_surface, color[:3], 
                                   (0, 0, adjusted_size * 2, adjusted_size * 2))
                    # 添加边缘模糊效果
                    for i in range(1, 3):
                        edge_alpha = int(color[3] * 0.3 / i) if len(color) > 3 else 30
                        edge_color = (*color[:3], edge_alpha)
                        pygame.draw.rect(particle_surface, edge_color[:3], 
                                       (-i, -i, adjusted_size * 2 + i*2, adjusted_size * 2 + i*2), 1)
                        
                elif particle.particle_type == "tree":
                    # 树木粒子 - 圆形，带古风晕染效果
                    pygame.draw.circle(particle_surface, color[:3], 
                                     (adjusted_size, adjusted_size), adjusted_size)
                    # 添加晕染效果
                    for r in range(adjusted_size + 1, adjusted_size + 3):
                        fade_alpha = int((color[3] if len(color) > 3 else 255) * 0.2)
                        fade_color = (*color[:3], fade_alpha)
                        pygame.draw.circle(particle_surface, fade_color[:3], 
                                         (adjusted_size, adjusted_size), r, 1)
                        
                elif particle.particle_type == "sky":
                    # 天空粒子 - 模糊圆形，增强古风云雾效果
                    for r in range(adjusted_size, 0, -1):
                        alpha = int((color[3] if len(color) > 3 else 255) * (r / adjusted_size) * 0.2)  # 更淡
                        fade_color = (*color[:3], alpha)
                        pygame.draw.circle(particle_surface, fade_color[:3], 
                                         (adjusted_size, adjusted_size), r)
                        
                elif particle.particle_type == "water_drop":
                    # 水滴粒子 - 增强古风水墨效果
                    pygame.draw.circle(particle_surface, color[:3], 
                                     (adjusted_size, adjusted_size), adjusted_size)
                    # 添加水墨晕染
                    for r in range(adjusted_size + 1, adjusted_size + 4):
                        ripple_alpha = int((color[3] if len(color) > 3 else 255) * 0.15)
                        ripple_color = (*CanalColors.CANAL_BLUE_MIST, ripple_alpha)
                        pygame.draw.circle(particle_surface, ripple_color[:3], 
                                         (adjusted_size, adjusted_size), r, 1)
                else:
                    # 默认 - 圆形，带古风效果
                    pygame.draw.circle(particle_surface, color[:3], 
                                     (adjusted_size, adjusted_size), adjusted_size)
                
                # 应用透明度
                if len(color) > 3:
                    particle_surface.set_alpha(color[3])
                
                # 绘制到屏幕
                screen.blit(particle_surface, 
                          (int(particle.x - adjusted_size), int(particle.y - adjusted_size)))
                
        except Exception as e:
            print(f"粒子渲染错误: {e}")

    def _render_sky(self, screen: pygame.Surface):
        """渲染天空 - E2场景使用纯白背景"""
        # E2场景使用纯白背景，营造淡雅古风氛围
        screen.fill(CanalColors.PAPER_WHITE)
        
        # 添加极淡的云雾效果，增强古风意境
        for i in range(3):
            cloud_alpha = 15 + i * 5  # 极淡的透明度
            cloud_y = self.height * (0.1 + i * 0.15)
            cloud_width = self.width * (0.3 + i * 0.2)
            cloud_height = 30 + i * 10
            
            # 创建半透明云雾表面
            cloud_surface = pygame.Surface((cloud_width, cloud_height), pygame.SRCALPHA)
            cloud_surface.fill((*CanalColors.SKY_MIST, cloud_alpha))
            
            # 绘制云雾
            cloud_x = self.width * (0.2 + i * 0.25)
            screen.blit(cloud_surface, (cloud_x, cloud_y))

    def _render_background(self, screen: pygame.Surface):
        """渲染背景（传统方式，作为粒子系统的备用）"""
        # 左岸建筑轮廓
        building_points = [
            (0, self.height * 0.4),
            (self.width * 0.1, self.height * 0.3),
            (self.width * 0.2, self.height * 0.35),
            (self.width * 0.3, self.height * 0.45),
            (self.width * 0.3, self.height)
        ]
        pygame.draw.polygon(screen, CanalColors.INK_DARK, building_points)
        
        # 右岸建筑轮廓
        building_points_right = [
            (self.width * 0.7, self.height * 0.4),
            (self.width * 0.8, self.height * 0.32),
            (self.width * 0.9, self.height * 0.38),
            (self.width, self.height * 0.42),
            (self.width, self.height),
            (self.width * 0.7, self.height)
        ]
        pygame.draw.polygon(screen, CanalColors.INK_DARK, building_points_right)

    def _render_bridges(self, screen: pygame.Surface):
        """渲染桥梁"""
        for bridge in self.bridges:
            if bridge.style == "石桥":
                self._render_stone_bridge(screen, bridge)
            else:
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
                arch_width // 1.5,
                bridge.height * 2 // 3
            )
            pygame.draw.ellipse(screen, CanalColors.PAPER_WHITE, arch_rect)
        
        # 桥墩
        for i in range(bridge.arch_count + 1):
            pier_x = bridge.x - bridge.width // 2 + i * arch_width
            pier_rect = pygame.Rect(
                pier_x - 5,
                bridge.y + bridge.height // 3,
                10,
                bridge.height * 2 // 3
            )
            pygame.draw.rect(screen, bridge.color, pier_rect)

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
        
        # 木桩支撑
        support_count = 5
        support_spacing = bridge.width // support_count
        for i in range(support_count):
            support_x = bridge.x - bridge.width // 2 + i * support_spacing
            pygame.draw.line(
                screen,
                bridge.color,
                (support_x, bridge.y + bridge.height // 4),
                (support_x, bridge.y + bridge.height),
                3
            )

    def _render_shore(self, screen: pygame.Surface):
        """渲染岸边"""
        # 左岸
        shore_points_left = [
            (0, self.water_surface_y),
            (self.width * 0.3, self.water_surface_y - 10),
            (self.width * 0.3, self.height),
            (0, self.height)
        ]
        pygame.draw.polygon(screen, CanalColors.SHORE_STONE, shore_points_left)
        
        # 右岸
        shore_points_right = [
            (self.width * 0.7, self.water_surface_y - 10),
            (self.width, self.water_surface_y),
            (self.width, self.height),
            (self.width * 0.7, self.height)
        ]
        pygame.draw.polygon(screen, CanalColors.SHORE_STONE, shore_points_right)

    def _render_water(self, screen: pygame.Surface):
        """渲染水面"""
        # 基础水面
        water_rect = pygame.Rect(
            0,
            self.water_surface_y,
            self.width,
            self.height - self.water_surface_y
        )
        pygame.draw.rect(screen, CanalColors.CANAL_BLUE, water_rect)
        
        # 水波纹理
        if hasattr(self, 'wave_points'):
            wave_points = []
            for wave in self.wave_points:
                wave_points.append((wave.x, wave.y))
            
            if len(wave_points) > 2:
                pygame.draw.lines(screen, CanalColors.CANAL_BLUE_LIGHT, False, wave_points, 2)
        
        # 渲染频谱反射（水面光影效果）
        self._render_spectrum_reflection(screen)

    def _render_spectrum_reflection(self, screen: pygame.Surface):
        """渲染频谱反射 - 全屏长度的水面光影效果"""
        if not hasattr(self, 'spectrum_data') or self.spectrum_data is None or len(self.spectrum_data) == 0:
            return
        
        # 在水面下方绘制频谱反射，覆盖全屏宽度
        reflection_y_start = self.water_surface_y + 15
        reflection_height = 40  # 增加高度以增强视觉效果
        
        # 确保频谱条覆盖全屏宽度
        bar_width = max(1, self.width / len(self.spectrum_data))
        
        for i, magnitude in enumerate(self.spectrum_data):
            # 归一化幅度
            normalized_mag = min(magnitude / (np.max(self.spectrum_data) + 1e-8), 1.0)
            
            # 只渲染有意义的频谱数据
            if normalized_mag < 0.08:  # 降低阈值以显示更多细节
                continue
            
            # 计算反射条高度
            bar_height = max(1, int(normalized_mag * reflection_height * 0.8))
            
            # 反射条位置 - 确保覆盖全屏宽度
            bar_x = int(i * bar_width)
            bar_y = reflection_y_start
            
            # 更柔和的透明度和颜色
            alpha = int(100 * (0.8 + normalized_mag * 0.4))  # 调整透明度
            
            # 使用水墨蓝色系
            base_color = CanalColors.CANAL_BLUE_MIST
            color = (*base_color, alpha)
            
            # 创建带透明度的表面
            bar_width_int = max(1, int(bar_width))
            reflection_surf = pygame.Surface((bar_width_int, bar_height), pygame.SRCALPHA)
            reflection_surf.fill(color)
            
            # 确保不超出屏幕边界
            if bar_x + bar_width_int <= self.width:
                screen.blit(reflection_surf, (bar_x, bar_y))

    def _render_boats(self, screen: pygame.Surface):
        """渲染船只"""
        for boat in self.boats:
            if boat.boat_type == "货船":
                self._render_cargo_boat(screen, boat)
            elif boat.boat_type == "客船":
                self._render_passenger_boat(screen, boat)
            else:
                self._render_small_boat(screen, boat)

    def _render_cargo_boat(self, screen: pygame.Surface, boat: Boat):
        """渲染货船"""
        # 船体
        boat_rect = pygame.Rect(
            boat.x - boat.size // 2,
            boat.y - boat.size // 4,
            boat.size,
            boat.size // 2
        )
        pygame.draw.rect(screen, boat.color, boat_rect)
        
        # 货物堆叠
        cargo_count = 3
        cargo_width = boat.size // cargo_count
        for i in range(cargo_count):
            cargo_rect = pygame.Rect(
                boat.x - boat.size // 2 + i * cargo_width,
                boat.y - boat.size // 2,
                cargo_width - 2,
                boat.size // 4
            )
            pygame.draw.rect(screen, CanalColors.INK_MEDIUM, cargo_rect)
        
        # 烟囱
        chimney_rect = pygame.Rect(
            boat.x + boat.size // 4,
            boat.y - boat.size // 2,
            boat.size // 8,
            boat.size // 3
        )
        pygame.draw.rect(screen, CanalColors.INK_BLACK, chimney_rect)

    def _render_passenger_boat(self, screen: pygame.Surface, boat: Boat):
        """渲染客船"""
        # 船体
        boat_points = [
            (boat.x - boat.size // 2, boat.y),
            (boat.x - boat.size // 3, boat.y - boat.size // 3),
            (boat.x + boat.size // 3, boat.y - boat.size // 3),
            (boat.x + boat.size // 2, boat.y),
            (boat.x + boat.size // 3, boat.y + boat.size // 4),
            (boat.x - boat.size // 3, boat.y + boat.size // 4)
        ]
        pygame.draw.polygon(screen, boat.color, boat_points)
        
        # 客舱窗户
        window_count = 4
        window_width = boat.size // (window_count + 1)
        for i in range(window_count):
            window_x = boat.x - boat.size // 3 + (i + 1) * window_width
            window_rect = pygame.Rect(
                window_x - window_width // 4,
                boat.y - boat.size // 6,
                window_width // 2,
                boat.size // 8
            )
            pygame.draw.rect(screen, CanalColors.PAPER_WHITE, window_rect)
        
        # 船帆
        sail_points = [
            (boat.x, boat.y - boat.size // 2),
            (boat.x - boat.size // 4, boat.y - boat.size // 4),
            (boat.x, boat.y - boat.size // 8),
            (boat.x + boat.size // 4, boat.y - boat.size // 4)
        ]
        pygame.draw.polygon(screen, CanalColors.PAPER_CREAM, sail_points)

    def _render_small_boat(self, screen: pygame.Surface, boat: Boat):
        """渲染小船"""
        # 简单的椭圆船体
        boat_rect = pygame.Rect(
            boat.x - boat.size // 2,
            boat.y - boat.size // 6,
            boat.size,
            boat.size // 3
        )
        pygame.draw.ellipse(screen, boat.color, boat_rect)
        
        # 船桨
        if boat.direction > 0:
            paddle_x = boat.x - boat.size // 3
        else:
            paddle_x = boat.x + boat.size // 3
            
        pygame.draw.line(
            screen,
            CanalColors.BRIDGE_BROWN,
            (paddle_x, boat.y),
            (paddle_x + boat.direction * boat.size // 4, boat.y - boat.size // 4),
            2
        )

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
        
        # 创建不同类型的船只
        boat_types = ["货船", "客船", "小船"]
        boat_colors = [CanalColors.BRIDGE_BROWN, CanalColors.INK_DARK, CanalColors.INK_MEDIUM]
        
        for i in range(3):
            boat = Boat(
                x=np.random.uniform(0, self.width),
                y=self.water_surface_y + np.random.uniform(-10, 10),
                size=np.random.uniform(30, 80),
                speed=np.random.uniform(0.5, 2.0),
                direction=np.random.choice([-1, 1]),
                boat_type=boat_types[np.random.randint(0, len(boat_types))],
                color=boat_colors[np.random.randint(0, len(boat_colors))]
            )
            self.boats.append(boat)

    def _init_bridges(self):
        """初始化桥梁"""
        self.bridges = []
        
        # 创建1-2座桥
        bridge_count = np.random.randint(1, 3)
        bridge_positions = np.linspace(self.width * 0.2, self.width * 0.8, bridge_count)
        
        for x in bridge_positions:
            # 随机选择桥梁样式
            bridge_styles = ["石桥", "木桥"]
            bridge_style = bridge_styles[np.random.randint(0, len(bridge_styles))]
            bridge_color = CanalColors.BRIDGE_BROWN if bridge_style == "木桥" else CanalColors.SHORE_STONE
            
            bridge = Bridge(
                x=x,
                y=self.water_surface_y - 50,
                width=np.random.uniform(120, 200),
                height=np.random.uniform(40, 80),
                arch_count=np.random.randint(1, 4),
                color=bridge_color,
                style=bridge_style
            )
            self.bridges.append(bridge)

    @profile_function
    def update(self, audio_data: Optional[np.ndarray] = None):
        """更新场景状态"""
        try:
            current_time = time.time()
            
            # 限制更新频率以提升性能
            if hasattr(self, 'last_update_time'):
                if current_time - self.last_update_time < 1.0 / 60:  # 限制为60FPS
                    return
            self.last_update_time = current_time
            
            # 处理音频数据
            if audio_data is not None:
                # 降采样音频数据以提升性能
                if len(audio_data) > 512:
                    audio_data = audio_data[::2]  # 简单降采样
                
                self._process_audio_data(audio_data)
            
            # 更新粒子系统（E2状态的核心功能）
            self._update_particle_systems()
            
            # 更新结构化粒子（新增）
            self._update_structured_particles(audio_data)
            
            # 更新水波（优化版本）
            self._update_water_waves_optimized()
            
            # 更新船只
            self._update_boats()
            
            # 更新时间相关的动画
            self.time_offset = current_time * 0.5
            
        except Exception as e:
            print(f"更新场景时出错: {e}")
    
    def _update_structured_particles(self, audio_data: Optional[np.ndarray] = None):
        """更新结构化粒子"""
        if audio_data is not None and len(self.structured_particles) > 0:
            # 计算音频能量
            audio_energy = np.mean(np.abs(audio_data))
            
            # 计算频段
            fft = np.fft.fft(audio_data)
            freqs = np.abs(fft[:len(fft)//2])
            
            # 分为低、中、高频段
            low_freq = np.mean(freqs[:len(freqs)//3])
            mid_freq = np.mean(freqs[len(freqs)//3:2*len(freqs)//3])
            high_freq = np.mean(freqs[2*len(freqs)//3:])
            
            frequency_bands = np.array([low_freq, mid_freq, high_freq])
            
            # 更新结构化粒子
            self.structured_pointcloud_generator.update_particles_with_audio(
                self.structured_particles, audio_energy, frequency_bands
            )

    def _update_water_waves_optimized(self):
        """优化的水波更新"""
        try:
            current_time = time.time()
            
            # 只更新可见的水波点
            for wave in self.wave_points:
                if 0 <= wave.x <= self.width:  # 只更新屏幕内的波点
                    wave.y = self.water_surface_y + wave.amplitude * math.sin(
                        current_time * wave.frequency + wave.phase
                    )
                    wave.x += wave.speed
                    
                    # 循环边界
                    if wave.x > self.width:
                        wave.x = -10
                        
        except Exception as e:
            print(f"水波更新错误: {e}")

    def _update_boats(self):
        """更新船只位置"""
        try:
            for boat in self.boats:
                boat.x += boat.speed * boat.direction
                
                # 边界处理
                if boat.x > self.width + 50:
                    boat.x = -50
                elif boat.x < -50:
                    boat.x = self.width + 50
                    
                # 轻微的垂直摆动
                boat.y = self.water_surface_y + 5 * math.sin(time.time() * 2 + boat.x * 0.01)
                
        except Exception as e:
            print(f"船只更新错误: {e}")

    @profile_function
    def render(self, screen: pygame.Surface):
        """渲染场景"""
        try:
            # 性能计时
            render_start = time.time()
            
            # 渲染天空
            self._render_sky(screen)
            
            # 渲染背景（使用粒子系统替代色块）
            if hasattr(self, 'particle_systems'):
                self._render_particle_systems(screen)
            else:
                # 回退到传统渲染
                self._render_background(screen)
            
            # 渲染结构化粒子（新增）
            self._render_structured_particles(screen)
            
            # 渲染桥梁
            self._render_bridges(screen)
            
            # 渲染岸边
            self._render_shore(screen)
            
            # 渲染水面
            self._render_water(screen)
            
            # 渲染船只
            self._render_boats(screen)
            
            # 渲染前景元素
            self._render_foreground(screen)
            
            # 性能监控
            if PERFORMANCE_OPTIMIZATION_ENABLED:
                render_time = time.time() - render_start
                if hasattr(self, 'render_times'):
                    self.render_times.append(render_time)
                    if len(self.render_times) > 60:  # 保持最近60帧的记录
                        self.render_times.pop(0)
                else:
                    self.render_times = [render_time]
                
                # 显示性能信息
                if len(self.render_times) > 10:
                    avg_render_time = sum(self.render_times) / len(self.render_times)
                    fps = 1.0 / avg_render_time if avg_render_time > 0 else 0
                    
                    # 在屏幕上显示FPS
                    font = pygame.font.Font(None, 24)
                    fps_text = font.render(f"FPS: {fps:.1f}", True, CanalColors.INK_DARK)
                    screen.blit(fps_text, (10, 10))
            
        except Exception as e:
            print(f"渲染场景时出错: {e}")

    def _render_structured_particles(self, screen: pygame.Surface):
        """渲染结构化粒子"""
        try:
            for particle in self.structured_particles:
                # 转换结构化粒子为pygame坐标
                screen_x = int(particle.x)
                screen_y = int(particle.y)
                
                # 确保在屏幕范围内
                if 0 <= screen_x < self.width and 0 <= screen_y < self.height:
                    # 根据深度调整颜色和大小
                    depth_factor = particle.z
                    adjusted_color = tuple(
                        int(c * (0.5 + depth_factor * 0.5)) for c in particle.color
                    )
                    adjusted_size = max(1, int(particle.size * (0.7 + depth_factor * 0.3)))
                    
                    # 音频响应效果
                    if hasattr(particle, 'intensity') and particle.intensity > 0:
                        intensity_factor = min(1.0, particle.intensity * 2)
                        adjusted_size = int(adjusted_size * (1 + intensity_factor * 0.5))
                        # 添加轻微的颜色变化
                        adjusted_color = tuple(
                            min(255, int(c * (1 + intensity_factor * 0.3))) for c in adjusted_color
                        )
                    
                    # 绘制粒子
                    if adjusted_size > 1:
                        pygame.draw.circle(screen, adjusted_color, (screen_x, screen_y), adjusted_size)
                    else:
                        screen.set_at((screen_x, screen_y), adjusted_color)
                        
        except Exception as e:
            print(f"渲染结构化粒子时出错: {e}")

    def _process_audio_data(self, audio_data: np.ndarray):
        """处理音频数据"""
        try:
            # 计算音频特征
            self.audio_energy = np.mean(np.abs(audio_data))
            self.audio_peak = np.max(np.abs(audio_data))
            
            # 频谱分析（简化版本以提升性能）
            if len(audio_data) >= 256:
                fft = np.fft.fft(audio_data[:256])  # 使用较小的FFT窗口
                self.spectrum = np.abs(fft[:128])
                self.dominant_freq = np.argmax(self.spectrum)
            
            # 计算频谱数据用于水面光影效果
            if len(audio_data) >= 512:
                # 使用FFT计算频谱
                fft_data = np.fft.fft(audio_data[:512])
                magnitude_spectrum = np.abs(fft_data[:256])  # 取前一半频率
                
                # 对数缩放以增强视觉效果
                self.spectrum_data = np.log1p(magnitude_spectrum)
                
                # 平滑处理
                if hasattr(self, 'prev_spectrum_data') and self.prev_spectrum_data is not None:
                    self.spectrum_data = 0.7 * self.spectrum_data + 0.3 * self.prev_spectrum_data
                
                self.prev_spectrum_data = self.spectrum_data.copy()
            else:
                # 如果音频数据不足，使用默认值
                self.spectrum_data = np.zeros(128)
            
            # 声音分类处理
            if self.sound_classifier is not None:
                try:
                    # 进行声音分类
                    classification_result = self.sound_classifier.classify_audio(audio_data)
                    
                    if classification_result and len(classification_result) > 0:
                        # classification_result 是 List[SoundClassification]
                        best_classification = classification_result[0]  # 取置信度最高的分类
                        self.current_classification = best_classification.class_name
                        self.classification_confidence = best_classification.confidence
                        
                        # 更新分类历史
                        self.classification_history.append({
                            'class': self.current_classification,
                            'confidence': self.classification_confidence,
                            'timestamp': time.time()
                        })
                        
                        # 保持历史记录在合理范围内
                        if len(self.classification_history) > 10:
                            self.classification_history = self.classification_history[-10:]
                        
                        # 根据分类结果调整场景
                        self._adjust_scene_by_classification(classification_result)
                        
                except Exception as e:
                    print(f"声音分类处理出错: {e}")
            
            # 更新粒子系统的音频响应性
            for system_name, system in self.particle_systems.items():
                if hasattr(system, 'audio_responsiveness'):
                    # 根据音频能量调整发射率
                    energy_factor = min(2.0, self.audio_energy * 10)
                    system.emission_rate = system.emission_rate * (1 + energy_factor * system.audio_responsiveness)
                        
        except Exception as e:
            print(f"处理音频数据时出错: {e}")
            # 设置默认值
            self.audio_energy = 0.0
            self.audio_peak = 0.0
            self.spectrum_data = np.zeros(128)
            
            # 更新粒子系统的音频响应
            if hasattr(self, 'particle_systems'):
                for system_name, system in self.particle_systems.items():
                    system.audio_responsiveness = self.audio_energy * 10
                    
        except Exception as e:
            print(f"音频处理错误: {e}")
            self.audio_energy = 0.0
            self.spectrum_data = np.zeros(128)

    def _render_foreground(self, screen: pygame.Surface):
        """渲染前景元素"""
        try:
            # 渲染水面涟漪
            if hasattr(self, 'audio_energy') and self.audio_energy > 0.05:
                ripple_count = int(self.audio_energy * 20)
                for i in range(ripple_count):
                    x = np.random.randint(0, self.width)
                    y = self.water_surface_y + np.random.randint(-5, 15)
                    radius = np.random.randint(5, 20)
                    
                    pygame.draw.circle(screen, CanalColors.WATER_FOAM, (x, y), radius, 1)
                    
        except Exception as e:
            print(f"前景渲染错误: {e}")

    def get_audio_visualization_data(self) -> Dict:
        """获取音频可视化数据"""
        return {
            'energy': getattr(self, 'audio_energy', 0.0),
            'peak': getattr(self, 'audio_peak', 0.0),
            'spectrum': getattr(self, 'spectrum', []),
            'dominant_freq': getattr(self, 'dominant_freq', 0),
            'particle_count': sum(len(system.particles) for system in self.particle_systems.values()) if hasattr(self, 'particle_systems') else 0
        }

    def _adjust_scene_by_classification(self, classifications):
        """根据声音分类调整场景"""
        try:
            if not classifications:
                return
                
            # 获取主导分类 - classifications 是 List[SoundClassification]
            dominant_class = max(classifications, key=lambda x: x.confidence)
            class_name = dominant_class.category  # 使用category字段
            confidence = dominant_class.confidence
            
            # 根据分类调整场景参数
            if class_name == 'water':
                # 增强水面效果
                self.water_activity = confidence
                if hasattr(self, 'particle_systems') and 'water_drops' in self.particle_systems:
                    self.particle_systems['water_drops'].emission_rate = confidence * 50
                    
            elif class_name in ['boat', 'traffic']:
                # 增加船只活动
                self.boat_activity = confidence
                for boat in self.boats:
                    boat.speed = boat.speed * (1 + confidence * 0.5)
                    
            elif class_name == 'nature':
                # 增强自然元素
                if hasattr(self, 'particle_systems'):
                    if 'trees' in self.particle_systems:
                        self.particle_systems['trees'].emission_rate = confidence * 30
                    if 'sky' in self.particle_systems:
                        self.particle_systems['sky'].audio_responsiveness = confidence * 5
                        
            elif class_name == 'human':
                # 增加场景活力
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
    pygame.display.set_caption("运河场景可视化测试 - 粒子点云版本")
    
    visualizer = CanalVisualizer(width, height)
    clock = pygame.time.Clock()
    
    print("运河场景可视化测试启动 - 粒子点云效果")
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