#!/usr/bin/env python3
"""
拟声词可视化模块 - 水墨线条风格
实现拟声词的动态显示和视觉效果，以水墨书法方式呈现
"""

import pygame
import numpy as np
import math
import time
from typing import List, Dict, Tuple, Optional
from collections import deque
from onomatopoeia_generator import CanalOnomatopoeiaGenerator, OnomatopoeiaFeature

class InkBrushStroke:
    """水墨笔画类"""
    
    def __init__(self, word: str, x: float, y: float, color: Tuple[int, int, int], 
                 intensity: float, duration: float, style: str = 'flowing'):
        self.word = word
        self.x = x
        self.y = y
        self.color = color
        self.intensity = intensity
        self.duration = duration
        self.style = style  # 'flowing', 'bold', 'delicate', 'splash'
        
        # 笔画参数
        self.created_time = time.time()
        self.alpha = int(255 * min(intensity, 1.0))
        self.thickness = max(2, int(intensity * 12))
        self.length = int(len(word) * 40 + intensity * 60)
        
        # 水墨效果参数
        self.ink_density = intensity
        self.brush_pressure = min(1.0, intensity * 1.2)
        self.stroke_points = self._generate_stroke_points()
        self.ink_drops = self._generate_ink_drops()
        
        # 动画参数
        self.animation_progress = 0.0
        self.fade_start_time = self.created_time + duration * 0.7
        
    def _generate_stroke_points(self) -> List[Tuple[int, int]]:
        """生成笔画轨迹点"""
        points = []
        char_width = 35
        
        for i, char in enumerate(self.word):
            char_x = self.x + i * char_width
            char_y = self.y
            
            # 根据字符和风格生成笔画
            if self.style == 'flowing':
                # 流动笔画 - 适合水流相关拟声词
                for j in range(20):
                    x = char_x + j * 2
                    y = char_y + math.sin(j * 0.3 + i) * self.intensity * 8
                    points.append((int(x), int(y)))
                    
            elif self.style == 'bold':
                # 粗犷笔画 - 适合引擎、撞击声
                for j in range(15):
                    x = char_x + j * 3
                    y = char_y + (j % 3 - 1) * self.intensity * 5
                    points.append((int(x), int(y)))
                    
            elif self.style == 'delicate':
                # 精细笔画 - 适合鸟鸣、细微声音
                for j in range(25):
                    x = char_x + j * 1.5
                    y = char_y + math.sin(j * 0.5) * self.intensity * 3
                    points.append((int(x), int(y)))
                    
            elif self.style == 'splash':
                # 飞溅笔画 - 适合水花、爆裂声
                center_x, center_y = char_x + 15, char_y
                for angle in np.linspace(0, 2*math.pi, 12):
                    radius = self.intensity * 20
                    x = center_x + radius * math.cos(angle)
                    y = center_y + radius * math.sin(angle)
                    points.append((int(x), int(y)))
        
        return points
    
    def _generate_ink_drops(self) -> List[Dict]:
        """生成墨滴效果"""
        drops = []
        drop_count = int(self.intensity * 8)
        
        for _ in range(drop_count):
            drop = {
                'x': self.x + np.random.uniform(-20, self.length + 20),
                'y': self.y + np.random.uniform(-15, 15),
                'size': np.random.uniform(1, 4) * self.intensity,
                'alpha': int(self.alpha * np.random.uniform(0.3, 0.8)),
                'vx': np.random.uniform(-1, 1),
                'vy': np.random.uniform(0.5, 2),
                'life': np.random.uniform(1.0, 2.5)
            }
            drops.append(drop)
        
        return drops

class OnomatopoeiaVisualizer:
    """拟声词可视化器 - 水墨线条风格"""
    
    def __init__(self, width: int, height: int):
        """初始化拟声词可视化器"""
        self.width = width
        self.height = height
        
        # 性能优化参数
        self.update_interval = 0.1  # 100ms更新一次
        self.last_update_time = 0
        
        # 字体加载（优先使用墨趣古风体）
        self.font_size = 48
        self.font = None
        font_paths = [
            "墨趣古风体.ttf",
            "fonts/墨趣古风体.ttf",
            "assets/fonts/墨趣古风体.ttf",
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc"
        ]
        
        for font_path in font_paths:
            try:
                self.font = pygame.font.Font(font_path, self.font_size)
                print(f"成功加载字体: {font_path}")
                break
            except:
                continue
        
        if self.font is None:
            try:
                self.font = pygame.font.Font("墨趣古风体.ttf", self.font_size)
            except:
                self.font = pygame.font.Font(None, self.font_size)
            print("使用默认字体")
        
        # 拟声词生成器
        self.generator = CanalOnomatopoeiaGenerator()
        
        # 当前显示的拟声词
        self.current_onomatopoeia = ""
        self.display_time = 0
        self.fade_duration = 2.0  # 淡出持续时间
        self.text_alpha = 0
        self.text_scale = 1.0
        
        # 动画参数
        self.animation_time = 0
        
        # 简化的笔画系统
        self.ink_strokes = []
        self.max_strokes = 5  # 限制最大笔画数量
        
        # 颜色定义
        self.colors = {
            'water': (70, 130, 180),
            'splash': (100, 149, 237),
            'boat': (139, 69, 19),
            'bird': (34, 139, 34),
            'wind': (176, 196, 222)
        }
        
        # 初始化pygame字体
        pygame.font.init()
        
        # 优先使用墨趣古风体，与其他组件保持一致
        font_paths = [
            "墨趣古风体.ttf",
            "assets/fonts/墨趣古风体.ttf",
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc"
        ]
        
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        
        for font_path in font_paths:
            try:
                if Path(font_path).exists():
                    self.font_large = pygame.font.Font(font_path, 48)
                    self.font_medium = pygame.font.Font(font_path, 32)
                    self.font_small = pygame.font.Font(font_path, 24)
                    print(f"拟声词可视化字体加载成功: {font_path}")
                    break
            except Exception as e:
                continue
        
        # 如果没有加载成功，使用系统字体
        if not self.font_large:
            try:
                chinese_fonts = ['PingFang SC', 'STHeiti', 'SimHei', 'Microsoft YaHei']
                for font_name in chinese_fonts:
                    try:
                        self.font_large = pygame.font.SysFont(font_name, 48)
                        self.font_medium = pygame.font.SysFont(font_name, 32)
                        self.font_small = pygame.font.SysFont(font_name, 24)
                        print(f"拟声词可视化使用系统字体: {font_name}")
                        break
                    except:
                        continue
                
                if not self.font_large:
                    try:
                        self.font_large = pygame.font.Font("墨趣古风体.ttf", 48)
                        self.font_medium = pygame.font.Font("墨趣古风体.ttf", 32)
                        self.font_small = pygame.font.Font("墨趣古风体.ttf", 24)
                    except:
                        self.font_large = pygame.font.Font(None, 48)
                        self.font_medium = pygame.font.Font(None, 32)
                        self.font_small = pygame.font.Font(None, 24)
                    print("拟声词可视化使用默认字体")
            except Exception as e:
                print(f"拟声词字体初始化失败: {e}")
                try:
                    self.font_large = pygame.font.Font("墨趣古风体.ttf", 48)
                    self.font_medium = pygame.font.Font("墨趣古风体.ttf", 32)
                    self.font_small = pygame.font.Font("墨趣古风体.ttf", 24)
                except:
                    self.font_large = pygame.font.Font(None, 48)
                    self.font_medium = pygame.font.Font(None, 32)
                    self.font_small = pygame.font.Font(None, 24)
        
        # 当前显示的拟声词
        self.current_onomatopoeia = ""
        self.display_time = 0
        self.fade_duration = 2.0  # 淡出持续时间
        
        # 水墨效果参数
        self.ink_particles = []
        self.brush_strokes = []
        
        # 性能优化：减少更新频率
        self.last_update_time = 0
        self.update_interval = 0.05  # 每50ms更新一次
        
        # 动画参数
        self.animation_time = 0
        self.text_scale = 1.0
        self.text_alpha = 255
    
    def _init_fonts(self):
        """初始化字体 - 优先使用中文字体"""
        try:
            pygame.font.init()
            
            # 尝试使用中文字体
            chinese_fonts = ['SimHei', 'Microsoft YaHei', 'PingFang SC', 'Hiragino Sans GB']
            
            for font_name in chinese_fonts:
                try:
                    self.fonts = {
                        'small': pygame.font.SysFont(font_name, 20),
                        'medium': pygame.font.SysFont(font_name, 28),
                        'large': pygame.font.SysFont(font_name, 40),
                        'calligraphy': pygame.font.SysFont(font_name, 48)  # 书法风格大字
                    }
                    break
                except:
                    continue
            
            # 如果中文字体不可用，使用默认字体
            if not self.fonts:
                self.fonts = {
                    'small': pygame.font.Font("墨趣古风体.ttf", 20) if self._try_load_font("墨趣古风体.ttf", 20) else pygame.font.Font(None, 20),
                    'medium': pygame.font.Font("墨趣古风体.ttf", 28) if self._try_load_font("墨趣古风体.ttf", 28) else pygame.font.Font(None, 28),
                    'large': pygame.font.Font("墨趣古风体.ttf", 40) if self._try_load_font("墨趣古风体.ttf", 40) else pygame.font.Font(None, 40),
                    'calligraphy': pygame.font.Font("墨趣古风体.ttf", 48) if self._try_load_font("墨趣古风体.ttf", 48) else pygame.font.Font(None, 48)
                }
                
        except Exception as e:
            print(f"字体初始化失败: {e}")
            self.fonts = {
                'small': None, 'medium': None, 'large': None, 'calligraphy': None
            }

    def _try_load_font(self, font_path: str, size: int) -> bool:
        """尝试加载字体，返回是否成功"""
        try:
            pygame.font.Font(font_path, size)
            return True
        except:
            return False

    def update(self, audio_data: np.ndarray):
        """更新拟声词可视化（性能优化版本）"""
        if audio_data is None or len(audio_data) == 0:
            return
        
        current_time = time.time()
        
        # 性能优化：限制更新频率
        if current_time - self.last_update_time < self.update_interval:
            return
        
        self.last_update_time = current_time
        
        # 性能优化：降采样音频数据
        if len(audio_data) > 800:  # 如果数据太长，进行降采样
            step = len(audio_data) // 800
            audio_data = audio_data[::step]
        
        # 简化的拟声词生成逻辑
        try:
            # 计算基本音频特征
            rms = np.sqrt(np.mean(audio_data**2))
            
            # 根据音频强度选择拟声词
            if rms > 0.1:
                # 计算频谱特征（简化版本）
                fft = np.fft.fft(audio_data)
                freqs = np.fft.fftfreq(len(audio_data), 1/32000)
                magnitude = np.abs(fft)
                
                # 找到主要频率
                dominant_freq_idx = np.argmax(magnitude[:len(magnitude)//2])
                dominant_freq = abs(freqs[dominant_freq_idx])
                
                # 根据频率范围选择拟声词
                if dominant_freq < 300:
                    onomatopoeia = random.choice(['突突', '轰轰', '嗡嗡'])
                elif dominant_freq < 1000:
                    onomatopoeia = random.choice(['潺潺', '汩汩', '淙淙'])
                elif dominant_freq < 3000:
                    onomatopoeia = random.choice(['哗啦', '溅溅'])
                else:
                    onomatopoeia = random.choice(['啾啾', '唧唧'])
                
                # 更新当前拟声词
                if onomatopoeia != self.current_onomatopoeia:
                    self.current_onomatopoeia = onomatopoeia
                    self.display_time = current_time
                    self.text_alpha = 255
                    self.text_scale = 1.2  # 初始放大效果
        
        except Exception as e:
            print(f"拟声词更新错误: {e}")
        
        # 更新动画参数
        self.animation_time += self.update_interval
        
        # 更新文字效果
        if self.current_onomatopoeia:
            elapsed = current_time - self.display_time
            if elapsed < self.fade_duration:
                # 淡出效果
                fade_progress = elapsed / self.fade_duration
                self.text_alpha = int(255 * (1 - fade_progress))
                self.text_scale = 1.2 - 0.2 * fade_progress  # 缩放效果
            else:
                self.current_onomatopoeia = ""
                self.text_alpha = 0

    def _create_ink_strokes(self, onomatopoeia_list: List[OnomatopoeiaFeature]):
        """创建水墨笔画"""
        for feature in onomatopoeia_list:
            if feature.confidence > 0.3:  # 只为高置信度的拟声词创建笔画
                # 确定笔画位置
                x, y = self._get_ink_position(feature)
                
                # 确定笔画风格
                style = self.word_styles.get(feature.word, 'flowing')
                
                # 确定墨色深浅
                ink_color = self._get_ink_color(feature.intensity)
                
                # 创建笔画
                stroke = InkBrushStroke(
                    word=feature.word,
                    x=x, y=y,
                    color=ink_color,
                    intensity=feature.intensity,
                    duration=feature.duration,
                    style=style
                )
                
                self.ink_strokes.append(stroke)
    
    def _get_ink_position(self, feature: OnomatopoeiaFeature) -> Tuple[float, float]:
        """根据拟声词特征确定笔画位置"""
        # 根据音频特征分布位置
        base_y = self.height * 0.6  # 基准线
        
        # 根据频率范围调整垂直位置
        if hasattr(feature, 'frequency_range'):
            freq_ratio = feature.frequency_range[0] / 8000 if feature.frequency_range[0] > 0 else 0.5
        else:
            freq_ratio = 0.5
        
        y_offset = (0.5 - freq_ratio) * self.height * 0.3
        
        # 水平位置 - 避免重叠
        x = np.random.uniform(50, self.width - 200)
        y = base_y + y_offset + np.random.uniform(-30, 30)
        
        return x, y
    
    def _get_ink_color(self, intensity: float) -> Tuple[int, int, int]:
        """根据强度确定墨色深浅"""
        if intensity > 0.8:
            return self.ink_colors['deep_ink']
        elif intensity > 0.6:
            return self.ink_colors['medium_ink']
        elif intensity > 0.4:
            return self.ink_colors['light_ink']
        else:
            return self.ink_colors['pale_ink']
    
    def _update_ink_strokes(self):
        """更新水墨笔画状态"""
        current_time = time.time()
        
        # 更新笔画动画进度
        for stroke in self.ink_strokes:
            age = current_time - stroke.created_time
            stroke.animation_progress = min(1.0, age / (stroke.duration * 0.3))
            
            # 更新墨滴位置
            for drop in stroke.ink_drops:
                drop['x'] += drop['vx']
                drop['y'] += drop['vy']
                drop['vy'] += 0.1  # 重力
                drop['life'] -= 0.016
        
        # 清理过期的笔画
        self.ink_strokes = [stroke for stroke in self.ink_strokes 
                           if current_time - stroke.created_time < 4.0]

    def render(self, surface: pygame.Surface):
        """渲染拟声词可视化（性能优化版本）"""
        try:
            # 渲染当前拟声词
            if self.current_onomatopoeia and self.text_alpha > 0:
                # 创建文字表面
                text_surface = self.font.render(self.current_onomatopoeia, True, (50, 50, 50))
                
                # 应用透明度
                if self.text_alpha < 255:
                    text_surface.set_alpha(self.text_alpha)
                
                # 计算位置（居中显示）
                text_rect = text_surface.get_rect()
                if self.text_scale != 1.0:
                    # 缩放文字
                    scaled_width = int(text_rect.width * self.text_scale)
                    scaled_height = int(text_rect.height * self.text_scale)
                    text_surface = pygame.transform.scale(text_surface, (scaled_width, scaled_height))
                    text_rect = text_surface.get_rect()
                
                text_rect.center = (self.width // 2, self.height // 2)
                
                # 绘制文字
                surface.blit(text_surface, text_rect)
            
            # 简化的装饰效果
            if self.current_onomatopoeia and len(self.ink_strokes) < self.max_strokes:
                # 添加简单的装饰笔画
                stroke_color = (100, 100, 100, 100)
                for i in range(min(2, self.max_strokes - len(self.ink_strokes))):
                    x = random.randint(50, self.width - 50)
                    y = random.randint(50, self.height - 50)
                    end_x = x + random.randint(-30, 30)
                    end_y = y + random.randint(-30, 30)
                    
                    # 绘制简单线条
                    pygame.draw.line(surface, stroke_color[:3], (x, y), (end_x, end_y), 2)
        
        except Exception as e:
            print(f"拟声词渲染错误: {e}")
    
    def _render_paper_texture(self, screen: pygame.Surface):
        """渲染宣纸纹理背景"""
        # 创建宣纸质感
        paper_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # 基础宣纸色
        paper_surface.fill(self.ink_colors['paper'])
        
        # 添加细微的纹理效果
        for i in range(0, self.height, 3):
            alpha = int(10 + 5 * math.sin(i * 0.1 + self.paper_texture_offset))
            color = (240, 238, 230, alpha)
            pygame.draw.line(paper_surface, color, (0, i), (self.width, i))
        
        screen.blit(paper_surface, (0, 0))
    
    def _render_ink_strokes(self, screen: pygame.Surface):
        """渲染水墨笔画"""
        current_time = time.time()
        
        for stroke in self.ink_strokes:
            age = current_time - stroke.created_time
            
            # 计算透明度（随时间淡化）
            if age > stroke.fade_start_time - stroke.created_time:
                fade_progress = (age - (stroke.fade_start_time - stroke.created_time)) / (stroke.duration * 0.3)
                alpha = max(0, int(stroke.alpha * (1 - fade_progress)))
            else:
                alpha = stroke.alpha
            
            if alpha > 0:
                # 渲染主笔画
                self._render_single_stroke(screen, stroke, alpha)
                
                # 渲染墨滴效果
                self._render_ink_drops(screen, stroke, alpha)
    
    def _render_single_stroke(self, screen: pygame.Surface, stroke: InkBrushStroke, alpha: int):
        """渲染单个笔画"""
        if not self.fonts['calligraphy']:
            return
            
        try:
            # 创建笔画表面
            stroke_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            
            # 渲染文字 - 书法风格
            text_surface = self.fonts['calligraphy'].render(
                stroke.word, True, (*stroke.color, alpha)
            )
            
            # 添加笔画效果
            if stroke.style == 'flowing':
                # 流动效果 - 轻微的位置偏移
                for i in range(3):
                    offset_x = int(math.sin(self.animation_time + i) * 2)
                    offset_y = int(math.cos(self.animation_time + i) * 1)
                    temp_alpha = max(0, alpha - i * 30)
                    if temp_alpha > 0:
                        temp_surface = self.fonts['calligraphy'].render(
                            stroke.word, True, (*stroke.color, temp_alpha)
                        )
                        stroke_surface.blit(temp_surface, 
                                          (stroke.x + offset_x, stroke.y + offset_y))
            
            elif stroke.style == 'bold':
                # 粗犷效果 - 多层叠加
                for i in range(2):
                    temp_surface = self.fonts['calligraphy'].render(
                        stroke.word, True, (*stroke.color, alpha // (i + 1))
                    )
                    stroke_surface.blit(temp_surface, (stroke.x + i, stroke.y + i))
            
            elif stroke.style == 'splash':
                # 飞溅效果 - 随机位置偏移
                for i in range(5):
                    offset_x = int(np.random.uniform(-3, 3))
                    offset_y = int(np.random.uniform(-3, 3))
                    temp_alpha = max(0, alpha - i * 20)
                    if temp_alpha > 0:
                        temp_surface = self.fonts['calligraphy'].render(
                            stroke.word, True, (*stroke.color, temp_alpha)
                        )
                        stroke_surface.blit(temp_surface, 
                                          (stroke.x + offset_x, stroke.y + offset_y))
            
            else:  # delicate
                # 精细效果 - 清晰渲染
                stroke_surface.blit(text_surface, (stroke.x, stroke.y))
            
            screen.blit(stroke_surface, (0, 0))
            
        except Exception as e:
            print(f"笔画渲染错误: {e}")
    
    def _render_ink_drops(self, screen: pygame.Surface, stroke: InkBrushStroke, base_alpha: int):
        """渲染墨滴效果"""
        for drop in stroke.ink_drops:
            if drop['life'] > 0:
                drop_alpha = min(base_alpha, int(drop['alpha'] * (drop['life'] / 2.5)))
                if drop_alpha > 0:
                    drop_surface = pygame.Surface((drop['size'] * 2, drop['size'] * 2), pygame.SRCALPHA)
                    pygame.draw.circle(drop_surface, 
                                     (*stroke.color, drop_alpha),
                                     (int(drop['size']), int(drop['size'])), 
                                     int(drop['size']))
                    
                    screen.blit(drop_surface, 
                              (int(drop['x'] - drop['size']), 
                               int(drop['y'] - drop['size'])))
    
    def _render_ink_panel(self, screen: pygame.Surface):
        """渲染水墨风格信息面板"""
        if not self.fonts['medium']:
            return
            
        try:
            # 调整位置避免与E2录制覆盖层重叠
            panel_x = self.width - 300
            panel_y = 180  # 从20调整到180，避免与上方内容重叠
            panel_width = 280
            panel_height = 120
            
            # 创建水墨风格面板背景
            panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
            
            # 渐变背景模拟宣纸
            for i in range(panel_height):
                alpha = int(100 * (1 - i / panel_height * 0.2))
                pygame.draw.line(panel_surface, (250, 248, 240, alpha), 
                               (0, i), (panel_width, i))
            
            # 墨色边框
            pygame.draw.rect(panel_surface, (40, 40, 40, 120), 
                           (0, 0, panel_width, panel_height), 2)
            
            screen.blit(panel_surface, (panel_x, panel_y))
            
            # 标题
            title_text = self.fonts['medium'].render("运河拟声", True, self.ink_colors['deep_ink'])
            screen.blit(title_text, (panel_x + 10, panel_y + 10))
            
            # 显示最近的拟声词
            recent_words = list(self.word_history)[-6:] if self.word_history else []
            y_offset = 40
            
            for i, word in enumerate(recent_words):
                # 根据新旧程度调整墨色深浅
                age_factor = (i + 1) / len(recent_words)
                if age_factor > 0.8:
                    color = self.ink_colors['deep_ink']
                elif age_factor > 0.6:
                    color = self.ink_colors['medium_ink']
                else:
                    color = self.ink_colors['light_ink']
                
                word_text = self.fonts['small'].render(f"「{word}」", True, color)
                screen.blit(word_text, (panel_x + 10 + (i % 3) * 80, panel_y + y_offset + (i // 3) * 25))
                
        except Exception as e:
            print(f"面板渲染错误: {e}")

if __name__ == "__main__":
    # 测试代码
    pygame.init()
    
    width, height = 1280, 720
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("拟声词可视化测试")
    
    visualizer = OnomatopoeiaVisualizer(width, height)
    clock = pygame.time.Clock()
    
    print("拟声词可视化测试启动")
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
        t = np.linspace(0, 0.1, 3200)  # 100ms, 32kHz
        
        # 模拟不同类型的运河声音
        test_audio = np.zeros_like(t)
        
        # 根据时间变化模拟不同声音
        current_time = time.time()
        
        if current_time % 10 < 3:  # 水流声
            test_audio += 0.3 * np.sin(2 * np.pi * 200 * t) * (1 + 0.2 * np.sin(2 * np.pi * 5 * t))
        elif current_time % 10 < 5:  # 船只引擎
            test_audio += 0.4 * np.sin(2 * np.pi * 120 * t) + 0.2 * np.sin(2 * np.pi * 240 * t)
        elif current_time % 10 < 7:  # 鸟鸣声
            bird_freq = 3000 + 1000 * np.sin(2 * np.pi * 10 * t)
            test_audio += 0.3 * np.sin(2 * np.pi * bird_freq * t)
        elif current_time % 10 < 8:  # 水花声
            test_audio += 0.5 * np.random.normal(0, 1, len(t)) * np.exp(-t * 20)
        else:  # 风声
            test_audio += 0.2 * np.random.normal(0, 1, len(t))
        
        # 添加背景噪声
        test_audio += 0.05 * np.random.normal(0, 1, len(test_audio))
        
        # 更新可视化
        visualizer.update(test_audio)
        
        # 渲染
        screen.fill((245, 245, 240))  # 宣纸色背景
        visualizer.render(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    print("测试完成")