#!/usr/bin/env python3
"""
本地随机声音可视化映射书法艺术作品生成器
用于E5状态的左侧功能模块，替代原有的网页显示功能
实时生成基于声音特征的书法艺术作品
"""

import pygame
import numpy as np
import math
import time
import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import deque
import threading
from pathlib import Path

from canal_visualizer import CanalColors
from audio_rec import AudioFeatures
from generator import ArtParameters

@dataclass
class CalligraphyStroke:
    """书法笔画数据类"""
    points: List[Tuple[int, int]]
    thickness: float
    alpha: int
    color: Tuple[int, int, int]
    style: str  # 'flowing', 'bold', 'delicate'
    created_time: float
    duration: float

class LocalCalligraphyGenerator:
    """本地书法艺术生成器"""
    
    def __init__(self, width: int, height: int):
        """初始化生成器"""
        self.width = width
        self.height = height
        
        # 画布区域（左侧）
        self.canvas_width = width // 2 - 50
        self.canvas_height = height - 200
        self.canvas_x = 25
        self.canvas_y = 100
        
        # 声音可视化数据
        self.audio_energy = 0.0
        self.audio_spectrum = np.zeros(64)
        self.frequency_bands = {
            'low': 0.0,    # 低频 (0-250Hz) - 水流声
            'mid': 0.0,    # 中频 (250-2000Hz) - 人声、鸟鸣
            'high': 0.0    # 高频 (2000Hz+) - 风声、细节
        }
        
        # 书法笔画系统
        self.strokes = deque(maxlen=50)  # 最多保持50个笔画
        self.current_character = ""
        self.character_pool = [
            "水", "流", "波", "浪", "涛", "潮", "涌", "溅",
            "船", "舟", "帆", "桨", "航", "渡", "泊", "港", 
            "桥", "岸", "堤", "柳", "风", "云", "雨", "雾",
            "静", "幽", "深", "远", "清", "澈", "碧", "蓝",
            "鸟", "鸣", "啼", "飞", "翔", "栖", "息", "巢"
        ]
        
        # 风格映射
        self.style_mapping = {
            'water_dominant': 'flowing',    # 水声主导 - 流动风格
            'bird_dominant': 'delicate',    # 鸟鸣主导 - 精细风格  
            'engine_dominant': 'bold',      # 引擎声主导 - 粗犷风格
            'balanced': 'flowing'           # 平衡 - 流动风格
        }
        
        # 动画参数
        self.last_generation_time = 0
        self.generation_interval = 2.0  # 每2秒生成一次新笔画
        self.animation_time = 0
        
        # 字体加载
        self._load_fonts()
        
        # 背景纹理
        self._generate_paper_texture()
        
        print("本地书法艺术生成器初始化完成")
    
    def _load_fonts(self):
        """加载字体"""
        try:
            self.font_large = pygame.font.Font("墨趣古风体.ttf", 48)
            self.font_medium = pygame.font.Font("墨趣古风体.ttf", 32)
            self.font_small = pygame.font.Font("墨趣古风体.ttf", 24)
        except:
            self.font_large = pygame.font.Font(None, 48)
            self.font_medium = pygame.font.Font(None, 32)
            self.font_small = pygame.font.Font(None, 24)
    
    def _generate_paper_texture(self):
        """生成宣纸纹理背景"""
        self.paper_surface = pygame.Surface((self.canvas_width, self.canvas_height))
        self.paper_surface.fill(CanalColors.PAPER_WHITE)
        
        # 添加细微的纹理噪声
        for _ in range(200):
            x = random.randint(0, self.canvas_width-1)
            y = random.randint(0, self.canvas_height-1)
            color_variation = random.randint(-10, 10)
            color = (245 + color_variation, 245 + color_variation, 240 + color_variation)
            pygame.draw.circle(self.paper_surface, color, (x, y), 1)
    
    def update_audio_data(self, audio_data: np.ndarray, sample_rate: int = 32000):
        """更新音频数据"""
        if audio_data is None or len(audio_data) == 0:
            return
        
        try:
            # 计算音频能量
            self.audio_energy = np.mean(np.abs(audio_data))
            
            # 计算频谱
            if len(audio_data) >= 512:
                fft = np.fft.fft(audio_data[:512])
                spectrum = np.abs(fft[:256])
                
                # 分频段分析
                low_end = len(spectrum) // 8
                mid_end = len(spectrum) // 2
                
                self.frequency_bands['low'] = np.mean(spectrum[:low_end])
                self.frequency_bands['mid'] = np.mean(spectrum[low_end:mid_end])
                self.frequency_bands['high'] = np.mean(spectrum[mid_end:])
                
                # 更新频谱显示数据
                self.audio_spectrum = spectrum[:64]
        
        except Exception as e:
            print(f"音频数据更新错误: {e}")
    
    def _determine_style(self) -> str:
        """根据音频特征确定书法风格"""
        low, mid, high = self.frequency_bands['low'], self.frequency_bands['mid'], self.frequency_bands['high']
        
        # 归一化
        total = low + mid + high
        if total == 0:
            return 'flowing'
        
        low_ratio = low / total
        mid_ratio = mid / total
        high_ratio = high / total
        
        # 风格判断
        if low_ratio > 0.5:
            return 'flowing'  # 水声主导
        elif mid_ratio > 0.4:
            return 'delicate'  # 鸟鸣主导
        elif high_ratio > 0.3:
            return 'bold'  # 风声/引擎声主导
        else:
            return 'flowing'  # 默认流动风格
    
    def _select_character(self) -> str:
        """根据音频特征选择字符"""
        style = self._determine_style()
        
        # 根据风格选择相应的字符池
        if style == 'flowing':
            chars = ["水", "流", "波", "浪", "涛", "潮", "涌", "溅"]
        elif style == 'delicate':
            chars = ["鸟", "鸣", "啼", "飞", "翔", "栖", "息", "巢"]
        elif style == 'bold':
            chars = ["风", "云", "雨", "雾", "桥", "岸", "堤", "柳"]
        else:
            chars = self.character_pool
        
        # 根据音频能量影响选择
        energy_index = int(self.audio_energy * 100) % len(chars)
        return chars[energy_index]
    
    def _generate_stroke_points(self, character: str, style: str, center_x: int, center_y: int) -> List[Tuple[int, int]]:
        """生成笔画轨迹点"""
        points = []
        
        # 基础字符大小
        char_size = 60 + int(self.audio_energy * 40)
        
        if style == 'flowing':
            # 流动风格 - 曲线笔画
            for i in range(20):
                angle = i * 0.3 + self.animation_time
                radius = char_size * (0.5 + 0.3 * math.sin(angle))
                x = center_x + int(radius * math.cos(angle))
                y = center_y + int(radius * math.sin(angle) * 0.6)
                points.append((x, y))
                
        elif style == 'delicate':
            # 精细风格 - 细腻笔画
            for i in range(15):
                angle = i * 0.4
                radius = char_size * 0.4
                x = center_x + int(radius * math.cos(angle) + random.randint(-5, 5))
                y = center_y + int(radius * math.sin(angle) + random.randint(-5, 5))
                points.append((x, y))
                
        elif style == 'bold':
            # 粗犷风格 - 直线笔画
            for i in range(12):
                x = center_x + (i - 6) * 8 + random.randint(-3, 3)
                y = center_y + random.randint(-char_size//2, char_size//2)
                points.append((x, y))
        
        return points
    
    def _create_new_stroke(self):
        """创建新的书法笔画"""
        current_time = time.time()
        
        # 选择字符和风格
        character = self._select_character()
        style = self._determine_style()
        
        # 确定位置（在画布内随机分布）
        margin = 80
        center_x = random.randint(margin, self.canvas_width - margin)
        center_y = random.randint(margin, self.canvas_height - margin)
        
        # 生成笔画点
        points = self._generate_stroke_points(character, style, center_x, center_y)
        
        # 确定笔画属性
        thickness = 2 + self.audio_energy * 8
        alpha = int(150 + self.audio_energy * 100)
        
        # 根据频段确定颜色
        if self.frequency_bands['low'] > self.frequency_bands['mid']:
            color = CanalColors.INK_BLACK  # 低频用深墨
        elif self.frequency_bands['mid'] > self.frequency_bands['high']:
            color = CanalColors.INK_MEDIUM  # 中频用中墨
        else:
            color = CanalColors.INK_LIGHT  # 高频用淡墨
        
        # 创建笔画
        stroke = CalligraphyStroke(
            points=points,
            thickness=thickness,
            alpha=alpha,
            color=color,
            style=style,
            created_time=current_time,
            duration=5.0 + random.random() * 3.0
        )
        
        self.strokes.append(stroke)
        self.current_character = character
    
    def update(self, dt: float):
        """更新生成器状态"""
        self.animation_time += dt
        current_time = time.time()
        
        # 检查是否需要生成新笔画
        if current_time - self.last_generation_time > self.generation_interval:
            # 根据音频活动调整生成频率
            if self.audio_energy > 0.1:  # 有声音活动时才生成
                self._create_new_stroke()
                self.last_generation_time = current_time
                
                # 动态调整生成间隔
                self.generation_interval = 1.0 + random.random() * 2.0
        
        # 更新笔画透明度（淡出效果）
        for stroke in list(self.strokes):
            age = current_time - stroke.created_time
            if age > stroke.duration:
                self.strokes.remove(stroke)
            else:
                # 淡出效果
                fade_ratio = 1.0 - (age / stroke.duration)
                stroke.alpha = int(stroke.alpha * fade_ratio)
    
    def render(self, screen: pygame.Surface):
        """渲染书法艺术生成器"""
        # 绘制画布背景
        canvas_rect = pygame.Rect(self.canvas_x, self.canvas_y, self.canvas_width, self.canvas_height)
        screen.blit(self.paper_surface, (self.canvas_x, self.canvas_y))
        
        # 绘制画布边框
        pygame.draw.rect(screen, CanalColors.INK_MEDIUM, canvas_rect, 3)
        
        # 渲染所有笔画
        for stroke in self.strokes:
            if len(stroke.points) > 1 and stroke.alpha > 0:
                # 创建带透明度的表面
                stroke_surface = pygame.Surface((self.canvas_width, self.canvas_height), pygame.SRCALPHA)
                
                # 调整点坐标到相对画布的位置
                adjusted_points = [(x - self.canvas_x, y - self.canvas_y) for x, y in stroke.points]
                
                # 绘制笔画
                if len(adjusted_points) > 1:
                    color_with_alpha = (*stroke.color, stroke.alpha)
                    
                    # 根据风格绘制不同效果
                    if stroke.style == 'flowing':
                        # 流动风格 - 平滑曲线
                        pygame.draw.lines(stroke_surface, stroke.color, False, adjusted_points, int(stroke.thickness))
                    elif stroke.style == 'delicate':
                        # 精细风格 - 细线条
                        pygame.draw.lines(stroke_surface, stroke.color, False, adjusted_points, max(1, int(stroke.thickness * 0.7)))
                    elif stroke.style == 'bold':
                        # 粗犷风格 - 粗线条
                        pygame.draw.lines(stroke_surface, stroke.color, False, adjusted_points, int(stroke.thickness * 1.3))
                
                # 应用透明度
                stroke_surface.set_alpha(stroke.alpha)
                screen.blit(stroke_surface, (self.canvas_x, self.canvas_y))
        
        # 绘制当前字符提示
        if self.current_character:
            char_surface = self.font_large.render(self.current_character, True, CanalColors.INK_LIGHT)
            char_rect = char_surface.get_rect()
            char_rect.center = (self.canvas_x + self.canvas_width // 2, self.canvas_y - 30)
            screen.blit(char_surface, char_rect)
        
        # 绘制标题
        title_text = "声音映射书法"
        title_surface = self.font_medium.render(title_text, True, CanalColors.INK_BLACK)
        title_rect = title_surface.get_rect()
        title_rect.center = (self.canvas_x + self.canvas_width // 2, 50)
        screen.blit(title_surface, title_rect)
        
        # 绘制音频可视化信息
        self._render_audio_info(screen)
    
    def _render_audio_info(self, screen: pygame.Surface):
        """渲染音频信息面板"""
        info_x = self.canvas_x
        info_y = self.canvas_y + self.canvas_height + 20
        
        # 音频能量条
        energy_width = int(self.audio_energy * 200)
        energy_rect = pygame.Rect(info_x, info_y, energy_width, 10)
        pygame.draw.rect(screen, CanalColors.CANAL_BLUE, energy_rect)
        
        # 能量标签
        energy_text = f"音频强度: {self.audio_energy:.2f}"
        energy_surface = self.font_small.render(energy_text, True, CanalColors.INK_MEDIUM)
        screen.blit(energy_surface, (info_x, info_y + 15))
        
        # 频段信息
        freq_y = info_y + 40
        freq_labels = ["低频", "中频", "高频"]
        freq_values = [self.frequency_bands['low'], self.frequency_bands['mid'], self.frequency_bands['high']]
        
        for i, (label, value) in enumerate(zip(freq_labels, freq_values)):
            x = info_x + i * 80
            
            # 频段条
            bar_height = int(value * 30)
            bar_rect = pygame.Rect(x, freq_y - bar_height, 20, bar_height)
            
            # 根据频段使用不同颜色
            colors = [CanalColors.CANAL_BLUE, CanalColors.INK_MEDIUM, CanalColors.INK_LIGHT]
            pygame.draw.rect(screen, colors[i], bar_rect)
            
            # 标签
            label_surface = self.font_small.render(label, True, CanalColors.INK_MEDIUM)
            screen.blit(label_surface, (x, freq_y + 5))
        
        # 当前风格显示
        style = self._determine_style()
        style_names = {'flowing': '流动', 'delicate': '精细', 'bold': '粗犷'}
        style_text = f"当前风格: {style_names.get(style, style)}"
        style_surface = self.font_small.render(style_text, True, CanalColors.INK_BLACK)
        screen.blit(style_surface, (info_x, freq_y + 30))

if __name__ == "__main__":
    # 测试代码
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("本地书法艺术生成器测试")
    
    generator = LocalCalligraphyGenerator(800, 600)
    clock = pygame.time.Clock()
    
    print("本地书法艺术生成器测试启动")
    print("按ESC退出")
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # 模拟音频数据
        fake_audio = np.random.random(1024) * 0.1
        generator.update_audio_data(fake_audio)
        
        # 更新和渲染
        generator.update(dt)
        
        screen.fill(CanalColors.PAPER_WHITE)
        generator.render(screen)
        
        pygame.display.flip()
    
    pygame.quit()
    print("测试完成")