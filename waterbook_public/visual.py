#!/usr/bin/env python3
"""
水上书艺术生成器 - UI渲染器
提供各种状态下的用户界面渲染功能
"""

import pygame
import numpy as np
import math
import time
import random
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import qrcode
from PIL import Image, ImageDraw, ImageFont
import socket

from canal_visualizer import CanalColors
from generator import GeneratedArt
from local_calligraphy_generator import LocalCalligraphyGenerator

class UIRenderer:
    """水墨风格UI渲染器"""
    
    def __init__(self, screen, width: int, height: int):
        """初始化UI渲染器"""
        self.screen = screen
        self.width = width
        self.height = height
        
        # 表面缓存
        self._surface_cache = {}
        
        # 加载字体
        self._load_fonts()
        
        # 动画状态
        self.animation_time = 0
        
        # 风格切换动画
        self.style_switch_animation = {
            'active': False,
            'progress': 0.0,
            'old_style': '',
            'new_style': '',
            'duration': 1.0
        }
        
        # 加载动画
        self.loading_animation = {
            'active': False,
            'progress': 0.0,
            'duration': 2.0
        }
        
        # 初始化本地书法艺术生成器
        self.local_calligraphy_generator = LocalCalligraphyGenerator(width, height)
        
        print("UI渲染器初始化完成")
    
    def _load_fonts(self):
        """加载字体"""
        try:
            # 尝试加载中文字体
            font_path = "墨趣古风体.ttf"
            if Path(font_path).exists():
                self.font_title = pygame.font.Font(font_path, 72)
                self.font_large = pygame.font.Font(font_path, 48)
                self.font_medium = pygame.font.Font(font_path, 32)
                self.font_small = pygame.font.Font(font_path, 24)
                print(f"中文字体加载成功: {font_path}")
            else:
                raise FileNotFoundError("中文字体文件不存在")
        except Exception as e:
            print(f"中文字体加载失败: {e}")
            # 使用系统默认字体
            self.font_title = pygame.font.Font(None, 72)
            self.font_large = pygame.font.Font(None, 48)
            self.font_medium = pygame.font.Font(None, 32)
            self.font_small = pygame.font.Font(None, 24)
            print("使用系统默认字体")
    
    def update_animation(self, dt: float):
        """更新动画状态"""
        self.animation_time += dt
        
        # 更新风格切换动画
        if self.style_switch_animation['active']:
            self.style_switch_animation['progress'] += dt / self.style_switch_animation['duration']
            
            # 计算淡出和淡入进度
            if self.style_switch_animation['progress'] <= 0.5:
                # 前半段：淡出旧风格
                self.style_switch_animation['fade_out_progress'] = self.style_switch_animation['progress'] * 2
                self.style_switch_animation['fade_in_progress'] = 0.0
            else:
                # 后半段：淡入新风格
                self.style_switch_animation['fade_out_progress'] = 1.0
                self.style_switch_animation['fade_in_progress'] = (self.style_switch_animation['progress'] - 0.5) * 2
            
            # 动画完成
            if self.style_switch_animation['progress'] >= 1.0:
                self.style_switch_animation['active'] = False
                self.style_switch_animation['progress'] = 0.0
        
        # 更新加载动画
        if self.loading_animation['active']:
            self.loading_animation['progress'] += dt
            self.loading_animation['rotation'] += dt * 180  # 每秒旋转180度
            self.loading_animation['pulse'] = (math.sin(self.loading_animation['progress'] * 4) + 1) / 2
            
            # 更新点动画
            for i in range(self.loading_animation['dots_count']):
                offset = i * 0.3  # 每个点延迟0.3秒
                self.loading_animation['dots_animation'][i] = max(0, 
                    (math.sin((self.loading_animation['progress'] - offset) * 6) + 1) / 2)
    
    def start_style_switch_animation(self, old_style: str, new_style: str):
        """开始风格切换动画"""
        self.style_switch_animation['active'] = True
        self.style_switch_animation['progress'] = 0.0
        self.style_switch_animation['old_style'] = old_style
        self.style_switch_animation['new_style'] = new_style
        self.style_switch_animation['fade_out_progress'] = 0.0
        self.style_switch_animation['fade_in_progress'] = 0.0
    
    def start_loading_animation(self):
        """开始加载动画"""
        self.loading_animation['active'] = True
        self.loading_animation['progress'] = 0.0
        self.loading_animation['rotation'] = 0.0
        self.loading_animation['pulse'] = 0.0
        self.loading_animation['dots_animation'] = [0.0, 0.0, 0.0]
    
    def stop_loading_animation(self):
        """停止加载动画"""
        self.loading_animation['active'] = False
    
    def is_style_switching(self) -> bool:
        """检查是否正在进行风格切换动画"""
        return self.style_switch_animation['active']
    
    def render_attract_screen(self):
        """渲染E0吸引状态界面"""
        # 清屏 - 移除跳帧渲染以解决频闪问题
        self.screen.fill(CanalColors.PAPER_WHITE)
        
        # 绘制背景纹理（缓存）- 使用rice_paper_texture
        if 'attract_bg' not in self._surface_cache:
            try:
                from assets.rice_paper_texture import create_waterbook_ui_background
                
                # 创建宣纸背景纹理
                paper_texture = create_waterbook_ui_background(self.width, self.height, "main")
                
                # 转换为pygame surface
                mode = paper_texture.mode
                size = paper_texture.size
                data = paper_texture.tobytes()
                
                bg_surface = pygame.image.fromstring(data, size, mode)
                self._surface_cache['attract_bg'] = bg_surface
                
            except Exception as e:
                print(f"使用rice_paper_texture失败，回退到简单背景: {e}")
                # 回退到简单背景
                bg_surface = pygame.Surface((self.width, self.height))
                bg_surface.fill(CanalColors.PAPER_WHITE)
                self._surface_cache['attract_bg'] = bg_surface
        
        self.screen.blit(self._surface_cache['attract_bg'], (0, 0))
        
        # 标题
        title_text = "水上书"
        title_surface = self.font_title.render(title_text, True, CanalColors.INK_BLACK)
        title_rect = title_surface.get_rect(center=(self.width // 2, self.height // 3))
        
        # 标题阴影
        shadow_surface = self.font_title.render(title_text, True, CanalColors.INK_FAINT)
        shadow_rect = shadow_surface.get_rect(center=(self.width // 2 + 3, self.height // 3 + 3))
        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(title_surface, title_rect)
        
        # 副标题
        subtitle_text = "运河环境声音艺术生成器"
        subtitle_surface = self.font_large.render(subtitle_text, True, CanalColors.INK_MEDIUM)
        subtitle_rect = subtitle_surface.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(subtitle_surface, subtitle_rect)
        
        # 提示文字
        hint_text = "按任意键开始体验"
        hint_surface = self.font_medium.render(hint_text, True, CanalColors.INK_LIGHT)
        hint_rect = hint_surface.get_rect(center=(self.width // 2, self.height // 2 + 80))
        self.screen.blit(hint_surface, hint_rect)
        
        # 动态装饰元素（简化）
        self._draw_simple_decorations()
    
    def _draw_paper_texture_on_surface(self, surface):
        """在指定表面上绘制纸张纹理"""
        # 简化的纸张纹理效果
        for i in range(0, self.width, 20):
            for j in range(0, self.height, 20):
                alpha = random.randint(5, 15)
                color = (250 - alpha, 248 - alpha, 240 - alpha)
                pygame.draw.circle(surface, color, (i, j), 2)
    
    def _draw_ink_wash_background(self):
        """绘制水墨风格背景"""
        # 创建渐变背景效果
        for y in range(0, self.height, 10):
            alpha = int(20 + 10 * math.sin(y * 0.01))
            color = (240 - alpha, 245 - alpha, 250 - alpha)
            pygame.draw.rect(self.screen, color, (0, y, self.width, 10))
        
        # 添加水墨晕染效果
        time_factor = time.time() * 0.3
        for i in range(5):
            x = random.randint(50, self.width - 50)
            y = random.randint(50, self.height - 50)
            radius = 30 + 20 * math.sin(time_factor + i)
            alpha = int(30 + 20 * math.sin(time_factor * 2 + i))
            
            # 创建水墨晕染圆
            ink_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(ink_surface, (*CanalColors.INK_FAINT, alpha), (radius, radius), radius)
            self.screen.blit(ink_surface, (x - radius, y - radius))

    def _draw_ink_wash_waves(self):
        """绘制水墨风格波纹效果"""
        time_factor = time.time() * 0.5
        
        # 绘制多层波纹
        for wave_layer in range(3):
            # 每层波纹有不同的频率和振幅
            frequency = 0.02 + wave_layer * 0.01
            amplitude = 20 + wave_layer * 10
            phase_offset = wave_layer * math.pi / 3
            
            # 波纹颜色和透明度
            alpha = int(40 - wave_layer * 10)
            color = (*CanalColors.CANAL_BLUE_LIGHT, alpha)
            
            # 创建波纹表面
            wave_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            
            # 绘制水平波纹
            for y in range(0, self.height, 8):
                wave_points = []
                for x in range(0, self.width, 4):
                    wave_y = y + amplitude * math.sin(x * frequency + time_factor + phase_offset)
                    wave_points.append((x, wave_y))
                
                if len(wave_points) > 1:
                    try:
                        pygame.draw.lines(wave_surface, color, False, wave_points, 2)
                    except ValueError:
                        # 如果点坐标超出范围，跳过这条线
                        pass
            
            # 绘制垂直波纹（较少）
            if wave_layer == 0:  # 只在第一层绘制垂直波纹
                for x in range(0, self.width, 40):
                    wave_points = []
                    for y in range(0, self.height, 4):
                        wave_x = x + amplitude * 0.5 * math.sin(y * frequency * 2 + time_factor + phase_offset)
                        if 0 <= wave_x < self.width:
                            wave_points.append((wave_x, y))
                    
                    if len(wave_points) > 1:
                        try:
                            pygame.draw.lines(wave_surface, color, False, wave_points, 1)
                        except ValueError:
                            pass
            
            # 将波纹层混合到屏幕
            self.screen.blit(wave_surface, (0, 0))

    def _draw_progress_circle(self, x: int, y: int, radius: int, progress: float):
        """绘制进度圆环"""
        # 背景圆环
        pygame.draw.circle(self.screen, CanalColors.INK_FAINT, (x, y), radius, 3)
        
        # 进度圆弧
        if progress > 0:
            # 计算角度 (从顶部开始，顺时针)
            start_angle = -math.pi / 2  # 从顶部开始
            end_angle = start_angle + (2 * math.pi * progress)
            
            # 绘制进度弧线
            points = []
            for i in range(int(progress * 360) + 1):
                angle = start_angle + (i * math.pi / 180)
                px = x + radius * math.cos(angle)
                py = y + radius * math.sin(angle)
                points.append((px, py))
            
            if len(points) > 1:
                pygame.draw.lines(self.screen, CanalColors.CANAL_BLUE, False, points, 4)

    def _draw_simple_decorations(self):
        """绘制简化的装饰元素"""
        # 减少装饰元素的复杂度以提高性能
        time_factor = time.time() * 0.5
        
        # 简单的浮动圆点
        for i in range(3):  # 减少到3个
            x = self.width // 4 + i * self.width // 4
            y = self.height // 4 + math.sin(time_factor + i) * 20
            radius = 3 + math.sin(time_factor * 2 + i) * 2
            alpha = int(100 + math.sin(time_factor + i) * 50)
            color = (*CanalColors.CANAL_BLUE_LIGHT, alpha)
            
            # 创建带透明度的表面
            circle_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(circle_surface, color, (radius, radius), radius)
            self.screen.blit(circle_surface, (x - radius, y - radius))
    
    def render_listen_screen(self, remaining_time: float):
        """渲染E1聆听状态界面 - 水墨风格"""
        # 清屏
        self.screen.fill(CanalColors.PAPER_WHITE)
        self._draw_ink_wash_background()
        
        # 标题 - 使用传统墨色
        title_text = "聆听水上环境"
        title_surface = self.font_large.render(title_text, True, CanalColors.INK_BLACK)
        title_rect = title_surface.get_rect(center=(self.width // 2, self.height // 4))
        
        # 添加标题阴影
        shadow_surface = self.font_large.render(title_text, True, CanalColors.INK_FAINT)
        shadow_rect = shadow_surface.get_rect(center=(self.width // 2 + 2, self.height // 4 + 2))
        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(title_surface, title_rect)
        
        # 倒计时 - 使用运河蓝
        countdown = int(remaining_time) + 1
        countdown_text = f"{countdown}"
        countdown_surface = self.font_large.render(countdown_text, True, CanalColors.CANAL_BLUE)
        countdown_rect = countdown_surface.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(countdown_surface, countdown_rect)
        
        # 进度圆环 - 增大半径，增加留白
        progress = 1 - (remaining_time / 8.0)  # 假设总时长8秒
        self._draw_progress_circle(self.width // 2, self.height // 2, 120, progress)
        
        # 指导文字 - 增加行间距
        guide_lines = [
            "请保持安静",
            "让设备感受水上的声音",
            "",
            "长按可跳过倒计时"
        ]
        
        y_offset = self.height // 2 + 180  # 增加留白
        line_spacing = 45  # 增加行间距
        for line in guide_lines:
            if line:
                text_surface = self.font_small.render(line, True, CanalColors.INK_LIGHT)
                text_rect = text_surface.get_rect(center=(self.width // 2, y_offset))
                self.screen.blit(text_surface, text_rect)
            y_offset += line_spacing
        
        # 波纹效果 - 使用水墨色调
        self._draw_ink_wash_waves()
    
    def render_record_overlay(self, progress: float):
        """渲染E2录制状态的覆盖层"""
        # 创建半透明覆盖层
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # 录制状态指示
        record_text = "正在采集运河环境声音..."
        record_surface = self.font_medium.render(record_text, True, CanalColors.INK_BLACK)
        record_rect = record_surface.get_rect(center=(self.width // 2, self.height // 4))
        
        # 添加背景框
        padding = 20
        bg_rect = pygame.Rect(
            record_rect.left - padding,
            record_rect.top - padding,
            record_rect.width + padding * 2,
            record_rect.height + padding * 2
        )
        pygame.draw.rect(overlay, (*CanalColors.PAPER_WHITE, 200), bg_rect, 0, 10)
        pygame.draw.rect(overlay, CanalColors.INK_FAINT, bg_rect, 2, 10)
        
        overlay.blit(record_surface, record_rect)
        
        # 进度条
        progress_width = 300
        progress_height = 8
        progress_x = (self.width - progress_width) // 2
        progress_y = record_rect.bottom + 30
        
        # 进度条背景
        progress_bg = pygame.Rect(progress_x, progress_y, progress_width, progress_height)
        pygame.draw.rect(overlay, CanalColors.INK_FAINT, progress_bg, 0, 4)
        
        # 进度条填充
        if progress > 0:
            fill_width = int(progress * progress_width)
            progress_fill = pygame.Rect(progress_x, progress_y, fill_width, progress_height)
            pygame.draw.rect(overlay, CanalColors.CANAL_BLUE, progress_fill, 0, 4)
        
        # 时间显示
        remaining_time = max(0, 35 - int(progress * 35))
        time_text = f"剩余时间: {remaining_time}秒"
        time_surface = self.font_small.render(time_text, True, CanalColors.INK_MEDIUM)
        time_rect = time_surface.get_rect(center=(self.width // 2, progress_y + 30))
        overlay.blit(time_surface, time_rect)
        
        # 录制指示灯（闪烁效果）
        pulse = (math.sin(self.animation_time * 4) + 1) / 2
        indicator_alpha = int(100 + pulse * 155)
        indicator_color = (*CanalColors.SEAL_RED, indicator_alpha)
        
        indicator_radius = 8
        indicator_pos = (record_rect.right + 20, record_rect.centery)
        
        indicator_surface = pygame.Surface((indicator_radius * 2, indicator_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(indicator_surface, indicator_color, (indicator_radius, indicator_radius), indicator_radius)
        overlay.blit(indicator_surface, (indicator_pos[0] - indicator_radius, indicator_pos[1] - indicator_radius))
        
        # 混合到主屏幕
        self.screen.blit(overlay, (0, 0))
    
    def render_generate_screen(self, progress: float):
        """渲染E3生成状态界面 - 水墨风格进度指示器"""
        # 清屏并绘制背景
        self.screen.fill(CanalColors.PAPER_WHITE)
        self._draw_ink_wash_background()
        
        # 主标题
        title_text = "正在采集运河环境声音"
        title_surface = self.font_large.render(title_text, True, CanalColors.INK_BLACK)
        title_rect = title_surface.get_rect(center=(self.width // 2, self.height // 6))
        
        # 添加标题阴影效果
        shadow_surface = self.font_large.render(title_text, True, CanalColors.INK_FAINT)
        shadow_rect = shadow_surface.get_rect(center=(self.width // 2 + 3, self.height // 6 + 3))
        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(title_surface, title_rect)
        
        # 进度条区域
        progress_y = self.height // 2 - 50
        progress_width = self.width // 2
        progress_height = 20
        progress_x = (self.width - progress_width) // 2
        
        # 进度条背景（宣纸色）
        progress_bg = pygame.Rect(progress_x, progress_y, progress_width, progress_height)
        pygame.draw.rect(self.screen, CanalColors.PAPER_CREAM, progress_bg, 0, 10)
        pygame.draw.rect(self.screen, CanalColors.INK_FAINT, progress_bg, 2, 10)
        
        # 进度条填充（运河蓝）
        if progress > 0:
            fill_width = int(progress * progress_width)
            progress_fill = pygame.Rect(progress_x, progress_y, fill_width, progress_height)
            pygame.draw.rect(self.screen, CanalColors.CANAL_BLUE, progress_fill, 0, 10)
        
        # 进度百分比
        progress_percent = int(progress * 100)
        percent_text = f"{progress_percent}%"
        percent_surface = self.font_medium.render(percent_text, True, CanalColors.INK_BLACK)
        percent_rect = percent_surface.get_rect(center=(self.width // 2, progress_y + 50))
        self.screen.blit(percent_surface, percent_rect)
        
        # 生成步骤指示器
        steps = [
            "分析音频特征",
            "提取环境元素", 
            "生成水墨构图",
            "渲染艺术作品",
            "完成创作"
        ]
        
        current_step = min(int(progress * len(steps)), len(steps) - 1)
        
        # 步骤列表
        step_y_start = progress_y + 100
        step_spacing = 40
        
        for i, step in enumerate(steps):
            step_y = step_y_start + i * step_spacing
            
            # 步骤圆圈
            circle_x = self.width // 2 - 150
            circle_radius = 12
            
            if i <= current_step:
                # 已完成或当前步骤
                circle_color = CanalColors.CANAL_BLUE if i < current_step else CanalColors.INK_MEDIUM
                pygame.draw.circle(self.screen, circle_color, (circle_x, step_y), circle_radius)
                
                # 完成标记
                if i < current_step:
                    check_text = "完"
                    check_surface = self.font_small.render(check_text, True, CanalColors.PAPER_WHITE)
                    check_rect = check_surface.get_rect(center=(circle_x, step_y))
                    self.screen.blit(check_surface, check_rect)
                else:
                    # 当前步骤的动画点
                    pulse = (math.sin(self.animation_time * 6) + 1) / 2
                    inner_radius = int(circle_radius * 0.3 + pulse * circle_radius * 0.3)
                    pygame.draw.circle(self.screen, CanalColors.PAPER_WHITE, (circle_x, step_y), inner_radius)
            else:
                # 未完成步骤
                pygame.draw.circle(self.screen, CanalColors.INK_FAINT, (circle_x, step_y), circle_radius, 2)
            
            # 连接线
            if i < len(steps) - 1:
                line_start = (circle_x, step_y + circle_radius)
                line_end = (circle_x, step_y + step_spacing - circle_radius)
                line_color = CanalColors.CANAL_BLUE if i < current_step else CanalColors.INK_FAINT
                pygame.draw.line(self.screen, line_color, line_start, line_end, 3)
            
            # 步骤文字
            text_color = CanalColors.INK_BLACK if i <= current_step else CanalColors.INK_LIGHT
            step_surface = self.font_small.render(step, True, text_color)
            step_rect = step_surface.get_rect(left=circle_x + 30, centery=step_y)
            self.screen.blit(step_surface, step_rect)
        
        # 动态提示信息
        hints = [
            "聆听水流的韵律...",
            "捕捉鸟鸣的灵动...", 
            "感受微风的轻柔...",
            "融合自然的和谐...",
            "创造独特的水墨..."
        ]
        
        hint_text = hints[current_step] if current_step < len(hints) else "即将完成..."
        hint_surface = self.font_small.render(hint_text, True, CanalColors.INK_MEDIUM)
        hint_rect = hint_surface.get_rect(center=(self.width // 2, self.height - 100))
        
        # 提示文字的呼吸效果
        pulse = (math.sin(self.animation_time * 3) + 1) / 2
        alpha = int(128 + pulse * 127)
        hint_surface.set_alpha(alpha)
        self.screen.blit(hint_surface, hint_rect)
        
        # 装饰性水墨元素
        self._draw_ink_wash_decorations()
    
    def render_select_screen(self, selected_style: str, remaining_time: float):
        """渲染E4选择状态界面"""
        # 清屏
        self.screen.fill(CanalColors.PAPER_WHITE)
        self._draw_ink_wash_background()
        
        # 如果正在进行风格切换动画，渲染动画效果
        if self.style_switch_animation['active']:
            self._render_style_switch_animation()
            return
        
        # 如果正在加载，渲染加载动画
        if self.loading_animation['active']:
            self._render_loading_animation()
            return
        
        # 标题
        title_text = "选择水墨风格"
        title_surface = self.font_large.render(title_text, True, CanalColors.INK_BLACK)
        title_rect = title_surface.get_rect(center=(self.width // 2, self.height // 6))
        
        # 添加标题阴影
        shadow_surface = self.font_large.render(title_text, True, CanalColors.INK_FAINT)
        shadow_rect = shadow_surface.get_rect(center=(self.width // 2 + 2, self.height // 6 + 2))
        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(title_surface, title_rect)
        
        # 风格选项
        styles = ["行书", "篆书", "水墨晕染"]
        style_descriptions = {
            "行书": "流畅自然，适合水流声主导的环境",
            "篆书": "古朴庄重，适合宁静的水上环境", 
            "水墨晕染": "艺术表现，适合丰富的环境声音"
        }
        
        # 绘制风格选项
        y_start = self.height // 3
        option_height = 120
        
        for i, style in enumerate(styles):
            y = y_start + i * option_height
            
            # 选中状态高亮
            if style == selected_style:
                # 高亮背景
                highlight_rect = pygame.Rect(self.width // 4, y - 40, self.width // 2, 80)
                pygame.draw.rect(self.screen, CanalColors.CANAL_BLUE_LIGHT, highlight_rect, 0, 10)
                pygame.draw.rect(self.screen, CanalColors.CANAL_BLUE, highlight_rect, 3, 10)
                
                # 选中标记
                mark_text = "●"
                mark_surface = self.font_medium.render(mark_text, True, CanalColors.CANAL_BLUE)
                mark_rect = mark_surface.get_rect(center=(self.width // 4 - 30, y))
                self.screen.blit(mark_surface, mark_rect)
            
            # 风格名称
            style_surface = self.font_medium.render(style, True, CanalColors.INK_BLACK)
            style_rect = style_surface.get_rect(center=(self.width // 2, y - 15))
            self.screen.blit(style_surface, style_rect)
            
            # 风格描述
            desc_surface = self.font_small.render(style_descriptions[style], True, CanalColors.INK_MEDIUM)
            desc_rect = desc_surface.get_rect(center=(self.width // 2, y + 15))
            self.screen.blit(desc_surface, desc_rect)
        
        # 倒计时
        countdown = int(remaining_time) + 1
        countdown_text = f"自动确认: {countdown}s"
        countdown_surface = self.font_small.render(countdown_text, True, CanalColors.INK_LIGHT)
        countdown_rect = countdown_surface.get_rect(center=(self.width // 2, self.height - 120))
        self.screen.blit(countdown_surface, countdown_rect)
        
        # 操作提示
        hint_lines = [
            "短按切换风格，长按确认选择"
        ]
        
        y_offset = self.height - 80
        for line in hint_lines:
            hint_surface = self.font_small.render(line, True, CanalColors.INK_LIGHT)
            hint_rect = hint_surface.get_rect(center=(self.width // 2, y_offset))
            self.screen.blit(hint_surface, hint_rect)
            y_offset += 35
        
        # 装饰元素
        self._draw_ink_wash_decorations()
    
    def render_display_screen(self, generated_art: GeneratedArt, remaining_time: float = 0):
        """渲染E5展示状态界面 - 集成本地书法艺术生成器"""
        # 清屏
        self.screen.fill(CanalColors.PAPER_WHITE)
        self._draw_ink_wash_background()
        
        # 标题
        title_text = "水墨艺术作品"
        title_surface = self.font_large.render(title_text, True, CanalColors.INK_BLACK)
        title_rect = title_surface.get_rect(center=(self.width // 2, 60))
        
        # 添加标题阴影
        shadow_surface = self.font_large.render(title_text, True, CanalColors.INK_FAINT)
        shadow_rect = shadow_surface.get_rect(center=(self.width // 2 + 2, 62))
        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(title_surface, title_rect)
        
        # 左侧：本地书法艺术生成器（替代原有的封面图像显示）
        self.local_calligraphy_generator.render(self.screen)
        
        # 右侧：作品信息面板
        info_x = self.width // 2 + 50
        info_y = 150
        info_width = self.width // 2 - 100
        
        # 信息背景
        info_bg = pygame.Rect(info_x, info_y, info_width, self.height - 300)
        pygame.draw.rect(self.screen, (*CanalColors.PAPER_CREAM, 180), info_bg, 0, 10)
        pygame.draw.rect(self.screen, CanalColors.INK_FAINT, info_bg, 2, 10)
        
        # 作品信息
        info_items = [
            ("风格", generated_art.parameters.style),
            ("内容", generated_art.parameters.content_text),
            ("创作时间", generated_art.creation_time.strftime('%Y年%m月%d日 %H:%M')),
            ("笔触粗细", f"{generated_art.parameters.brush_thickness:.1f}"),
            ("墨浓度", f"{generated_art.parameters.ink_density:.1f}"),
            ("飞白强度", f"{generated_art.parameters.flywhite_intensity:.1f}"),
        ]
        
        y_offset = info_y + 30
        for label, value in info_items:
            # 标签
            label_surface = self.font_small.render(f"{label}:", True, CanalColors.INK_MEDIUM)
            self.screen.blit(label_surface, (info_x + 20, y_offset))
            
            # 值
            value_surface = self.font_small.render(str(value), True, CanalColors.INK_BLACK)
            self.screen.blit(value_surface, (info_x + 120, y_offset))
            
            y_offset += 40
        
        # 实时声音映射信息
        mapping_y = y_offset + 20
        mapping_title = self.font_small.render("实时声音映射:", True, CanalColors.INK_MEDIUM)
        self.screen.blit(mapping_title, (info_x + 20, mapping_y))
        
        # 显示当前音频特征
        audio_info = [
            f"音频强度: {self.local_calligraphy_generator.audio_energy:.2f}",
            f"低频: {self.local_calligraphy_generator.frequency_bands['low']:.2f}",
            f"中频: {self.local_calligraphy_generator.frequency_bands['mid']:.2f}",
            f"高频: {self.local_calligraphy_generator.frequency_bands['high']:.2f}",
            f"当前字符: {self.local_calligraphy_generator.current_character}",
            f"笔画数量: {len(self.local_calligraphy_generator.strokes)}"
        ]
        
        for i, info in enumerate(audio_info):
            info_surface = self.font_small.render(info, True, CanalColors.INK_LIGHT)
            self.screen.blit(info_surface, (info_x + 30, mapping_y + 25 + i * 20))
        
        # 二维码（保持原有功能）
        qr_y = mapping_y + 180
        self._draw_qr_code(info_x + info_width // 2, qr_y)
        
        # 倒计时显示
        if remaining_time > 0:
            countdown_text = f"自动返回: {int(remaining_time)}秒"
            countdown_surface = self.font_small.render(countdown_text, True, CanalColors.INK_MEDIUM)
            countdown_rect = countdown_surface.get_rect(center=(self.width // 2, self.height - 80))
            self.screen.blit(countdown_surface, countdown_rect)
        
        # 提示文字
        hint_text = "长按返回主界面 | 实时声音映射书法生成中..."
        hint_surface = self.font_small.render(hint_text, True, CanalColors.INK_LIGHT)
        hint_rect = hint_surface.get_rect(center=(self.width // 2, self.height - 50))
        self.screen.blit(hint_surface, hint_rect)
        
        # 装饰元素
        self._draw_ink_wash_decorations()
    
    def update_local_calligraphy_audio(self, audio_data: np.ndarray, sample_rate: int = 32000):
        """更新本地书法生成器的音频数据"""
        if hasattr(self, 'local_calligraphy_generator'):
            self.local_calligraphy_generator.update_audio_data(audio_data, sample_rate)
    
    def update_local_calligraphy_animation(self, dt: float):
        """更新本地书法生成器的动画"""
        if hasattr(self, 'local_calligraphy_generator'):
            self.local_calligraphy_generator.update(dt)

    def _draw_paper_texture_on_surface(self, surface):
        """在指定表面上绘制纸张纹理"""
        # 简化的纸张纹理效果
        for i in range(0, self.width, 20):
            for j in range(0, self.height, 20):
                alpha = random.randint(5, 15)
                color = (250 - alpha, 248 - alpha, 240 - alpha)
                pygame.draw.circle(surface, color, (i, j), 2)
    
    def _draw_simple_decorations(self):
        """绘制简化的装饰元素"""
        # 减少装饰元素的复杂度以提高性能
        time_factor = time.time() * 0.5
        
        # 简单的浮动圆点
        for i in range(3):  # 减少到3个
            x = self.width // 4 + i * self.width // 4
            y = self.height // 4 + math.sin(time_factor + i) * 20
            radius = 3 + math.sin(time_factor * 2 + i) * 2
            alpha = int(100 + math.sin(time_factor + i) * 50)
            color = (*CanalColors.CANAL_BLUE_LIGHT, alpha)
            
            # 创建带透明度的表面
            circle_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(circle_surface, color, (radius, radius), radius)
            self.screen.blit(circle_surface, (x - radius, y - radius))
    
    def render_listen_screen(self, remaining_time: float):
        """渲染E1聆听状态界面 - 水墨风格"""
        # 清屏
        self.screen.fill(CanalColors.PAPER_WHITE)
        self._draw_ink_wash_background()
        
        # 标题 - 使用传统墨色
        title_text = "聆听水上环境"
        title_surface = self.font_large.render(title_text, True, CanalColors.INK_BLACK)
        title_rect = title_surface.get_rect(center=(self.width // 2, self.height // 4))
        
        # 添加标题阴影
        shadow_surface = self.font_large.render(title_text, True, CanalColors.INK_FAINT)
        shadow_rect = shadow_surface.get_rect(center=(self.width // 2 + 2, self.height // 4 + 2))
        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(title_surface, title_rect)
        
        # 倒计时 - 使用运河蓝
        countdown = int(remaining_time) + 1
        countdown_text = f"{countdown}"
        countdown_surface = self.font_large.render(countdown_text, True, CanalColors.CANAL_BLUE)
        countdown_rect = countdown_surface.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(countdown_surface, countdown_rect)
        
        # 进度圆环 - 增大半径，增加留白
        progress = 1 - (remaining_time / 8.0)  # 假设总时长8秒
        self._draw_progress_circle(self.width // 2, self.height // 2, 120, progress)
        
        # 指导文字 - 增加行间距
        guide_lines = [
            "请保持安静",
            "让设备感受水上的声音",
            "",
            "长按可跳过倒计时"
        ]
        
        y_offset = self.height // 2 + 180  # 增加留白
        line_spacing = 45  # 增加行间距
        for line in guide_lines:
            if line:
                text_surface = self.font_small.render(line, True, CanalColors.INK_LIGHT)
                text_rect = text_surface.get_rect(center=(self.width // 2, y_offset))
                self.screen.blit(text_surface, text_rect)
            y_offset += line_spacing
        
        # 波纹效果 - 使用水墨色调
        self._draw_ink_wash_waves()
    
    def render_record_overlay(self, progress: float):
        """渲染E2录制状态的覆盖层"""
        # 创建半透明覆盖层
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # 录制状态指示
        record_text = "正在采集运河环境声音..."
        record_surface = self.font_medium.render(record_text, True, CanalColors.INK_BLACK)
        record_rect = record_surface.get_rect(center=(self.width // 2, self.height // 4))
        
        # 添加背景框
        padding = 20
        bg_rect = pygame.Rect(
            record_rect.left - padding,
            record_rect.top - padding,
            record_rect.width + padding * 2,
            record_rect.height + padding * 2
        )
        pygame.draw.rect(overlay, (*CanalColors.PAPER_WHITE, 200), bg_rect, 0, 10)
        pygame.draw.rect(overlay, CanalColors.INK_FAINT, bg_rect, 2, 10)
        
        overlay.blit(record_surface, record_rect)
        
        # 进度条
        progress_width = 300
        progress_height = 8
        progress_x = (self.width - progress_width) // 2
        progress_y = record_rect.bottom + 30
        
        # 进度条背景
        progress_bg = pygame.Rect(progress_x, progress_y, progress_width, progress_height)
        pygame.draw.rect(overlay, CanalColors.INK_FAINT, progress_bg, 0, 4)
        
        # 进度条填充
        if progress > 0:
            fill_width = int(progress * progress_width)
            progress_fill = pygame.Rect(progress_x, progress_y, fill_width, progress_height)
            pygame.draw.rect(overlay, CanalColors.CANAL_BLUE, progress_fill, 0, 4)
        
        # 时间显示
        remaining_time = max(0, 35 - int(progress * 35))
        time_text = f"剩余时间: {remaining_time}秒"
        time_surface = self.font_small.render(time_text, True, CanalColors.INK_MEDIUM)
        time_rect = time_surface.get_rect(center=(self.width // 2, progress_y + 30))
        overlay.blit(time_surface, time_rect)
        
        # 录制指示灯（闪烁效果）
        pulse = (math.sin(self.animation_time * 4) + 1) / 2
        indicator_alpha = int(100 + pulse * 155)
        indicator_color = (*CanalColors.SEAL_RED, indicator_alpha)
        
        indicator_radius = 8
        indicator_pos = (record_rect.right + 20, record_rect.centery)
        
        indicator_surface = pygame.Surface((indicator_radius * 2, indicator_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(indicator_surface, indicator_color, (indicator_radius, indicator_radius), indicator_radius)
        overlay.blit(indicator_surface, (indicator_pos[0] - indicator_radius, indicator_pos[1] - indicator_radius))
        
        # 混合到主屏幕
        self.screen.blit(overlay, (0, 0))
    
    def render_generate_screen(self, progress: float):
        """渲染E3生成状态界面 - 水墨风格进度指示器"""
        # 清屏并绘制背景
        self.screen.fill(CanalColors.PAPER_WHITE)
        self._draw_ink_wash_background()
        
        # 主标题
        title_text = "正在采集运河环境声音"
        title_surface = self.font_large.render(title_text, True, CanalColors.INK_BLACK)
        title_rect = title_surface.get_rect(center=(self.width // 2, self.height // 6))
        
        # 添加标题阴影效果
        shadow_surface = self.font_large.render(title_text, True, CanalColors.INK_FAINT)
        shadow_rect = shadow_surface.get_rect(center=(self.width // 2 + 3, self.height // 6 + 3))
        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(title_surface, title_rect)
        
        # 进度条区域
        progress_y = self.height // 2 - 50
        progress_width = self.width // 2
        progress_height = 20
        progress_x = (self.width - progress_width) // 2
        
        # 进度条背景（宣纸色）
        progress_bg = pygame.Rect(progress_x, progress_y, progress_width, progress_height)
        pygame.draw.rect(self.screen, CanalColors.PAPER_CREAM, progress_bg, 0, 10)
        pygame.draw.rect(self.screen, CanalColors.INK_FAINT, progress_bg, 2, 10)
        
        # 进度条填充（运河蓝）
        if progress > 0:
            fill_width = int(progress * progress_width)
            progress_fill = pygame.Rect(progress_x, progress_y, fill_width, progress_height)
            pygame.draw.rect(self.screen, CanalColors.CANAL_BLUE, progress_fill, 0, 10)
        
        # 进度百分比
        progress_percent = int(progress * 100)
        percent_text = f"{progress_percent}%"
        percent_surface = self.font_medium.render(percent_text, True, CanalColors.INK_BLACK)
        percent_rect = percent_surface.get_rect(center=(self.width // 2, progress_y + 50))
        self.screen.blit(percent_surface, percent_rect)
        
        # 生成步骤指示器
        steps = [
            "分析音频特征",
            "提取环境元素", 
            "生成水墨构图",
            "渲染艺术作品",
            "完成创作"
        ]
        
        current_step = min(int(progress * len(steps)), len(steps) - 1)
        
        # 步骤列表
        step_y_start = progress_y + 100
        step_spacing = 40
        
        for i, step in enumerate(steps):
            step_y = step_y_start + i * step_spacing
            
            # 步骤圆圈
            circle_x = self.width // 2 - 150
            circle_radius = 12
            
            if i <= current_step:
                # 已完成或当前步骤
                circle_color = CanalColors.CANAL_BLUE if i < current_step else CanalColors.INK_MEDIUM
                pygame.draw.circle(self.screen, circle_color, (circle_x, step_y), circle_radius)
                
                # 完成标记
                if i < current_step:
                    check_text = "完"
                    check_surface = self.font_small.render(check_text, True, CanalColors.PAPER_WHITE)
                    check_rect = check_surface.get_rect(center=(circle_x, step_y))
                    self.screen.blit(check_surface, check_rect)
                else:
                    # 当前步骤的动画点
                    pulse = (math.sin(self.animation_time * 6) + 1) / 2
                    inner_radius = int(circle_radius * 0.3 + pulse * circle_radius * 0.3)
                    pygame.draw.circle(self.screen, CanalColors.PAPER_WHITE, (circle_x, step_y), inner_radius)
            else:
                # 未完成步骤
                pygame.draw.circle(self.screen, CanalColors.INK_FAINT, (circle_x, step_y), circle_radius, 2)
            
            # 连接线
            if i < len(steps) - 1:
                line_start = (circle_x, step_y + circle_radius)
                line_end = (circle_x, step_y + step_spacing - circle_radius)
                line_color = CanalColors.CANAL_BLUE if i < current_step else CanalColors.INK_FAINT
                pygame.draw.line(self.screen, line_color, line_start, line_end, 3)
            
            # 步骤文字
            text_color = CanalColors.INK_BLACK if i <= current_step else CanalColors.INK_LIGHT
            step_surface = self.font_small.render(step, True, text_color)
            step_rect = step_surface.get_rect(left=circle_x + 30, centery=step_y)
            self.screen.blit(step_surface, step_rect)
        
        # 动态提示信息
        hints = [
            "聆听水流的韵律...",
            "捕捉鸟鸣的灵动...", 
            "感受微风的轻柔...",
            "融合自然的和谐...",
            "创造独特的水墨..."
        ]
        
        hint_text = hints[current_step] if current_step < len(hints) else "即将完成..."
        hint_surface = self.font_small.render(hint_text, True, CanalColors.INK_MEDIUM)
        hint_rect = hint_surface.get_rect(center=(self.width // 2, self.height - 100))
        
        # 提示文字的呼吸效果
        pulse = (math.sin(self.animation_time * 3) + 1) / 2
        alpha = int(128 + pulse * 127)
        hint_surface.set_alpha(alpha)
        self.screen.blit(hint_surface, hint_rect)
        
        # 装饰性水墨元素
        self._draw_ink_wash_decorations()
    
    def render_select_screen(self, selected_style: str, remaining_time: float):
        """渲染E4选择状态界面"""
        # 清屏
        self.screen.fill(CanalColors.PAPER_WHITE)
        self._draw_ink_wash_background()
        
        # 如果正在进行风格切换动画，渲染动画效果
        if self.style_switch_animation['active']:
            self._render_style_switch_animation()
            return
        
        # 如果正在加载，渲染加载动画
        if self.loading_animation['active']:
            self._render_loading_animation()
            return
        
        # 标题
        title_text = "选择水墨风格"
        title_surface = self.font_large.render(title_text, True, CanalColors.INK_BLACK)
        title_rect = title_surface.get_rect(center=(self.width // 2, self.height // 6))
        
        # 添加标题阴影
        shadow_surface = self.font_large.render(title_text, True, CanalColors.INK_FAINT)
        shadow_rect = shadow_surface.get_rect(center=(self.width // 2 + 2, self.height // 6 + 2))
        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(title_surface, title_rect)
        
        # 风格选项
        styles = ["行书", "篆书", "水墨晕染"]
        style_descriptions = {
            "行书": "流畅自然，适合水流声主导的环境",
            "篆书": "古朴庄重，适合宁静的水上环境", 
            "水墨晕染": "艺术表现，适合丰富的环境声音"
        }
        
        # 绘制风格选项
        y_start = self.height // 3
        option_height = 120
        
        for i, style in enumerate(styles):
            y = y_start + i * option_height
            
            # 选中状态高亮
            if style == selected_style:
                # 高亮背景
                highlight_rect = pygame.Rect(self.width // 4, y - 40, self.width // 2, 80)
                pygame.draw.rect(self.screen, CanalColors.CANAL_BLUE_LIGHT, highlight_rect, 0, 10)
                pygame.draw.rect(self.screen, CanalColors.CANAL_BLUE, highlight_rect, 3, 10)
                
                # 选中标记
                mark_text = "●"
                mark_surface = self.font_medium.render(mark_text, True, CanalColors.CANAL_BLUE)
                mark_rect = mark_surface.get_rect(center=(self.width // 4 - 30, y))
                self.screen.blit(mark_surface, mark_rect)
            
            # 风格名称
            style_surface = self.font_medium.render(style, True, CanalColors.INK_BLACK)
            style_rect = style_surface.get_rect(center=(self.width // 2, y - 15))
            self.screen.blit(style_surface, style_rect)
            
            # 风格描述
            desc_surface = self.font_small.render(style_descriptions[style], True, CanalColors.INK_MEDIUM)
            desc_rect = desc_surface.get_rect(center=(self.width // 2, y + 15))
            self.screen.blit(desc_surface, desc_rect)
        
        # 倒计时
        countdown = int(remaining_time) + 1
        countdown_text = f"自动确认: {countdown}s"
        countdown_surface = self.font_small.render(countdown_text, True, CanalColors.INK_LIGHT)
        countdown_rect = countdown_surface.get_rect(center=(self.width // 2, self.height - 120))
        self.screen.blit(countdown_surface, countdown_rect)
        
        # 操作提示
        hint_lines = [
            "短按切换风格，长按确认选择"
        ]
        
        y_offset = self.height - 80
        for line in hint_lines:
            hint_surface = self.font_small.render(line, True, CanalColors.INK_LIGHT)
            hint_rect = hint_surface.get_rect(center=(self.width // 2, y_offset))
            self.screen.blit(hint_surface, hint_rect)
            y_offset += 35
        
        # 装饰元素
        self._draw_ink_wash_decorations()
    
    def render_display_screen(self, generated_art: GeneratedArt, remaining_time: float = 0):
        """渲染E5展示状态界面 - 集成本地书法艺术生成器"""
        # 清屏
        self.screen.fill(CanalColors.PAPER_WHITE)
        self._draw_ink_wash_background()
        
        # 标题
        title_text = "水墨艺术作品"
        title_surface = self.font_large.render(title_text, True, CanalColors.INK_BLACK)
        title_rect = title_surface.get_rect(center=(self.width // 2, 60))
        
        # 添加标题阴影
        shadow_surface = self.font_large.render(title_text, True, CanalColors.INK_FAINT)
        shadow_rect = shadow_surface.get_rect(center=(self.width // 2 + 2, 62))
        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(title_surface, title_rect)
        
        # 左侧：本地书法艺术生成器（替代原有的封面图像显示）
        self.local_calligraphy_generator.render(self.screen)
        
        # 右侧：作品信息面板
        info_x = self.width // 2 + 50
        info_y = 150
        info_width = self.width // 2 - 100
        
        # 信息背景
        info_bg = pygame.Rect(info_x, info_y, info_width, self.height - 300)
        pygame.draw.rect(self.screen, (*CanalColors.PAPER_CREAM, 180), info_bg, 0, 10)
        pygame.draw.rect(self.screen, CanalColors.INK_FAINT, info_bg, 2, 10)
        
        # 作品信息
        info_items = [
            ("风格", generated_art.parameters.style),
            ("内容", generated_art.parameters.content_text),
            ("创作时间", generated_art.creation_time.strftime('%Y年%m月%d日 %H:%M')),
            ("笔触粗细", f"{generated_art.parameters.brush_thickness:.1f}"),
            ("墨浓度", f"{generated_art.parameters.ink_density:.1f}"),
            ("飞白强度", f"{generated_art.parameters.flywhite_intensity:.1f}"),
        ]
        
        y_offset = info_y + 30
        for label, value in info_items:
            # 标签
            label_surface = self.font_small.render(f"{label}:", True, CanalColors.INK_MEDIUM)
            self.screen.blit(label_surface, (info_x + 20, y_offset))
            
            # 值
            value_surface = self.font_small.render(str(value), True, CanalColors.INK_BLACK)
            self.screen.blit(value_surface, (info_x + 120, y_offset))
            
            y_offset += 40
        
        # 实时声音映射信息
        mapping_y = y_offset + 20
        mapping_title = self.font_small.render("实时声音映射:", True, CanalColors.INK_MEDIUM)
        self.screen.blit(mapping_title, (info_x + 20, mapping_y))
        
        # 显示当前音频特征
        audio_info = [
            f"音频强度: {self.local_calligraphy_generator.audio_energy:.2f}",
            f"低频: {self.local_calligraphy_generator.frequency_bands['low']:.2f}",
            f"中频: {self.local_calligraphy_generator.frequency_bands['mid']:.2f}",
            f"高频: {self.local_calligraphy_generator.frequency_bands['high']:.2f}",
            f"当前字符: {self.local_calligraphy_generator.current_character}",
            f"笔画数量: {len(self.local_calligraphy_generator.strokes)}"
        ]
        
        for i, info in enumerate(audio_info):
            info_surface = self.font_small.render(info, True, CanalColors.INK_LIGHT)
            self.screen.blit(info_surface, (info_x + 30, mapping_y + 25 + i * 20))
        
        # 二维码（保持原有功能）
        qr_y = mapping_y + 180
        self._draw_qr_code(info_x + info_width // 2, qr_y)
        
        # 倒计时显示
        if remaining_time > 0:
            countdown_text = f"自动返回: {int(remaining_time)}秒"
            countdown_surface = self.font_small.render(countdown_text, True, CanalColors.INK_MEDIUM)
            countdown_rect = countdown_surface.get_rect(center=(self.width // 2, self.height - 80))
            self.screen.blit(countdown_surface, countdown_rect)
        
        # 提示文字
        hint_text = "长按返回主界面 | 实时声音映射书法生成中..."
        hint_surface = self.font_small.render(hint_text, True, CanalColors.INK_LIGHT)
        hint_rect = hint_surface.get_rect(center=(self.width // 2, self.height - 50))
        self.screen.blit(hint_surface, hint_rect)
        
        # 装饰元素
        self._draw_ink_wash_decorations()
    
    def update_local_calligraphy_audio(self, audio_data: np.ndarray, sample_rate: int = 32000):
        """更新本地书法生成器的音频数据"""
        if hasattr(self, 'local_calligraphy_generator'):
            self.local_calligraphy_generator.update_audio_data(audio_data, sample_rate)
    
    def update_local_calligraphy_animation(self, dt: float):
        """更新本地书法生成器的动画"""
        if hasattr(self, 'local_calligraphy_generator'):
            self.local_calligraphy_generator.update(dt)

    def _draw_paper_texture_on_surface(self, surface):
        """在指定表面上绘制纸张纹理"""
        # 简化的纸张纹理效果
        for i in range(0, self.width, 20):
            for j in range(0, self.height, 20):
                alpha = random.randint(5, 15)
                color = (250 - alpha, 248 - alpha, 240 - alpha)
                pygame.draw.circle(surface, color, (i, j), 2)
    
    def _draw_simple_decorations(self):
        """绘制简化的装饰元素"""
        # 减少装饰元素的复杂度以提高性能
        time_factor = time.time() * 0.5
        
        # 简单的浮动圆点
        for i in range(3):  # 减少到3个
            x = self.width // 4 + i * self.width // 4
            y = self.height // 4 + math.sin(time_factor + i) * 20
            radius = 3 + math.sin(time_factor * 2 + i) * 2
            alpha = int(100 + math.sin(time_factor + i) * 50)
            color = (*CanalColors.CANAL_BLUE_LIGHT, alpha)
            
            # 创建带透明度的表面
            circle_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(circle_surface, color, (radius, radius), radius)
            self.screen.blit(circle_surface, (x - radius, y - radius))
    
    def render_listen_screen(self, remaining_time: float):
        """渲染E1聆听状态界面 - 水墨风格"""
        # 清屏
        self.screen.fill(CanalColors.PAPER_WHITE)
        self._draw_ink_wash_background()
        
        # 标题 - 使用传统墨色
        title_text = "聆听水上环境"
        title_surface = self.font_large.render(title_text, True, CanalColors.INK_BLACK)
        title_rect = title_surface.get_rect(center=(self.width // 2, self.height // 4))
        
        # 添加标题阴影
        shadow_surface = self.font_large.render(title_text, True, CanalColors.INK_FAINT)
        shadow_rect = shadow_surface.get_rect(center=(self.width // 2 + 2, self.height // 4 + 2))
        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(title_surface, title_rect)
        
        # 倒计时 - 使用运河蓝
        countdown = int(remaining_time) + 1
        countdown_text = f"{countdown}"
        countdown_surface = self.font_large.render(countdown_text, True, CanalColors.CANAL_BLUE)
        countdown_rect = countdown_surface.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(countdown_surface, countdown_rect)
        
        # 进度圆环 - 增大半径，增加留白
        progress = 1 - (remaining_time / 8.0)  # 假设总时长8秒
        self._draw_progress_circle(self.width // 2, self.height // 2, 120, progress)
        
        # 指导文字 - 增加行间距
        guide_lines = [
            "请保持安静",
            "让设备感受水上的声音",
            "",
            "长按可跳过倒计时"
        ]
        
        y_offset = self.height // 2 + 180  # 增加留白
        line_spacing = 45  # 增加行间距
        for line in guide_lines:
            if line:
                text_surface = self.font_small.render(line, True, CanalColors.INK_LIGHT)
                text_rect = text_surface.get_rect(center=(self.width // 2, y_offset))
                self.screen.blit(text_surface, text_rect)
            y_offset += line_spacing
        
        # 波纹效果 - 使用水墨色调
        self._draw_ink_wash_waves()
    
    def render_record_overlay(self, progress: float):
        """渲染E2录制状态的覆盖层"""
        # 创建半透明覆盖层
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # 录制状态指示
        record_text = "正在采集运河环境声音..."
        record_surface = self.font_medium.render(record_text, True, CanalColors.INK_BLACK)
        record_rect = record_surface.get_rect(center=(self.width // 2, self.height // 4))
        
        # 添加背景框
        padding = 20
        bg_rect = pygame.Rect(
            record_rect.left - padding,
            record_rect.top - padding,
            record_rect.width + padding * 2,
            record_rect.height + padding * 2
        )
        pygame.draw.rect(overlay, (*CanalColors.PAPER_WHITE, 200), bg_rect, 0, 10)
        pygame.draw.rect(overlay, CanalColors.INK_FAINT, bg_rect, 2, 10)
        
        overlay.blit(record_surface, record_rect)
        
        # 进度条
        progress_width = 300
        progress_height = 8
        progress_x = (self.width - progress_width) // 2
        progress_y = record_rect.bottom + 30
        
        # 进度条背景
        progress_bg = pygame.Rect(progress_x, progress_y, progress_width, progress_height)
        pygame.draw.rect(overlay, CanalColors.INK_FAINT, progress_bg, 0, 4)
        
        # 进度条填充
        if progress > 0:
            fill_width = int(progress * progress_width)
            progress_fill = pygame.Rect(progress_x, progress_y, fill_width, progress_height)
            pygame.draw.rect(overlay, CanalColors.CANAL_BLUE, progress_fill, 0, 4)
        
        # 时间显示
        remaining_time = max(0, 35 - int(progress * 35))
        time_text = f"剩余时间: {remaining_time}秒"
        time_surface = self.font_small.render(time_text, True, CanalColors.INK_MEDIUM)
        time_rect = time_surface.get_rect(center=(self.width // 2, progress_y + 30))
        overlay.blit(time_surface, time_rect)
        
        # 录制指示灯（闪烁效果）
        pulse = (math.sin(self.animation_time * 4) + 1) / 2
        indicator_alpha = int(100 + pulse * 155)
        indicator_color = (*CanalColors.SEAL_RED, indicator_alpha)
        
        indicator_radius = 8
        indicator_pos = (record_rect.right + 20, record_rect.centery)
        
        indicator_surface = pygame.Surface((indicator_radius * 2, indicator_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(indicator_surface, indicator_color, (indicator_radius, indicator_radius), indicator_radius)
        overlay.blit(indicator_surface, (indicator_pos[0] - indicator_radius, indicator_pos[1] - indicator_radius))
        
        # 混合到主屏幕
        self.screen.blit(overlay, (0, 0))
    
    def render_generate_screen(self, progress: float):
        """渲染E3生成状态界面 - 水墨风格进度指示器"""
        # 清屏并绘制背景
        self.screen.fill(CanalColors.PAPER_WHITE)
        self._draw_ink_wash_background()
        
        # 主标题
        title_text = "正在采集运河环境声音"
        title_surface = self.font_large.render(title_text, True, CanalColors.INK_BLACK)
        title_rect = title_surface.get_rect(center=(self.width // 2, self.height // 6))
        
        # 添加标题阴影效果
        shadow_surface = self.font_large.render(title_text, True, CanalColors.INK_FAINT)
        shadow_rect = shadow_surface.get_rect(center=(self.width // 2 + 3, self.height // 6 + 3))
        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(title_surface, title_rect)
        
        # 进度条区域
        progress_y = self.height // 2 - 50
        progress_width = self.width // 2
        progress_height = 20
        progress_x = (self.width - progress_width) // 2
        
        # 进度条背景（宣纸色）
        progress_bg = pygame.Rect(progress_x, progress_y, progress_width, progress_height)
        pygame.draw.rect(self.screen, CanalColors.PAPER_CREAM, progress_bg, 0, 10)
        pygame.draw.rect(self.screen, CanalColors.INK_FAINT, progress_bg, 2, 10)
        
        # 进度条填充（运河蓝）
        if progress > 0:
            fill_width = int(progress * progress_width)
            progress_fill = pygame.Rect(progress_x, progress_y, fill_width, progress_height)
            pygame.draw.rect(self.screen, CanalColors.CANAL_BLUE, progress_fill, 0, 10)
        
        # 进度百分比
        progress_percent = int(progress * 100)
        percent_text = f"{progress_percent}%"
        percent_surface = self.font_medium.render(percent_text, True, CanalColors.INK_BLACK)
        percent_rect = percent_surface.get_rect(center=(self.width // 2, progress_y + 50))
        self.screen.blit(percent_surface, percent_rect)
        
        # 生成步骤指示器
        steps = [
            "分析音频特征",
            "提取环境元素", 
            "生成水墨构图",
            "渲染艺术作品",
            "完成创作"
        ]
        
        current_step = min(int(progress * len(steps)), len(steps) - 1)
        
        # 步骤列表
        step_y_start = progress_y + 100
        step_spacing = 40
        
        for i, step in enumerate(steps):
            step_y = step_y_start + i * step_spacing
            
            # 步骤圆圈
            circle_x = self.width // 2 - 150
            circle_radius = 12
            
            if i <= current_step:
                # 已完成或当前步骤
                circle_color = CanalColors.CANAL_BLUE if i < current_step else CanalColors.INK_MEDIUM
                pygame.draw.circle(self.screen, circle_color, (circle_x, step_y), circle_radius)
                
                # 完成标记
                if i < current_step:
                    check_text = "完"
                    check_surface = self.font_small.render(check_text, True, CanalColors.PAPER_WHITE)
                    check_rect = check_surface.get_rect(center=(circle_x, step_y))
                    self.screen.blit(check_surface, check_rect)
                else:
                    # 当前步骤的动画点
                    pulse = (math.sin(self.animation_time * 6) + 1) / 2
                    inner_radius = int(circle_radius * 0.3 + pulse * circle_radius * 0.3)
                    pygame.draw.circle(self.screen, CanalColors.PAPER_WHITE, (circle_x, step_y), inner_radius)
            else:
                # 未完成步骤
                pygame.draw.circle(self.screen, CanalColors.INK_FAINT, (circle_x, step_y), circle_radius, 2)
            
            # 连接线
            if i < len(steps) - 1:
                line_start = (circle_x, step_y + circle_radius)
                line_end = (circle_x, step_y + step_spacing - circle_radius)
                line_color = CanalColors.CANAL_BLUE if i < current_step else CanalColors.INK_FAINT
                pygame.draw.line(self.screen, line_color, line_start, line_end, 3)
            
            # 步骤文字
            text_color = CanalColors.INK_BLACK if i <= current_step else CanalColors.INK_LIGHT
            step_surface = self.font_small.render(step, True, text_color)
            step_rect = step_surface.get_rect(left=circle_x + 30, centery=step_y)
            self.screen.blit(step_surface, step_rect)
        
        # 动态提示信息
        hints = [
            "聆听水流的韵律...",
            "捕捉鸟鸣的灵动...", 
            "感受微风的轻柔...",
            "融合自然的和谐...",
            "创造独特的水墨..."
        ]
        
        hint_text = hints[current_step] if current_step < len(hints) else "即将完成..."
        hint_surface = self.font_small.render(hint_text, True, CanalColors.INK_MEDIUM)
        hint_rect = hint_surface.get_rect(center=(self.width // 2, self.height - 100))
        
        # 提示文字的呼吸效果
        pulse = (math.sin(self.animation_time * 3) + 1) / 2
        alpha = int(128 + pulse * 127)
        hint_surface.set_alpha(alpha)
        self.screen.blit(hint_surface, hint_rect)
        
        # 装饰性水墨元素
        self._draw_ink_wash_decorations()
    
    def render_select_screen(self, selected_style: str, remaining_time: float):
        """渲染E4选择状态界面"""
        # 清屏
        self.screen.fill(CanalColors.PAPER_WHITE)
        self._draw_ink_wash_background()
        
        # 如果正在进行风格切换动画，渲染动画效果
        if self.style_switch_animation['active']:
            self._render_style_switch_animation()
            return
        
        # 如果正在加载，渲染加载动画
        if self.loading_animation['active']:
            self._render_loading_animation()
            return
        
        # 标题
        title_text = "选择水墨风格"
        title_surface = self.font_large.render(title_text, True, CanalColors.INK_BLACK)
        title_rect = title_surface.get_rect(center=(self.width // 2, self.height // 6))
        
        # 添加标题阴影
        shadow_surface = self.font_large.render(title_text, True, CanalColors.INK_FAINT)
        shadow_rect = shadow_surface.get_rect(center=(self.width // 2 + 2, self.height // 6 + 2))
        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(title_surface, title_rect)
        
        # 风格选项
        styles = ["行书", "篆书", "水墨晕染"]
        style_descriptions = {
            "行书": "流畅自然，适合水流声主导的环境",
            "篆书": "古朴庄重，适合宁静的水上环境", 
            "水墨晕染": "艺术表现，适合丰富的环境声音"
        }
        
        # 绘制风格选项
        y_start = self.height // 3
        option_height = 120
        
        for i, style in enumerate(styles):
            y = y_start + i * option_height
            
            # 选中状态高亮
            if style == selected_style:
                # 高亮背景
                highlight_rect = pygame.Rect(self.width // 4, y - 40, self.width // 2, 80)
                pygame.draw.rect(self.screen, CanalColors.CANAL_BLUE_LIGHT, highlight_rect, 0, 10)
                pygame.draw.rect(self.screen, CanalColors.CANAL_BLUE, highlight_rect, 3, 10)
                
                # 选中标记
                mark_text = "●"
                mark_surface = self.font_medium.render(mark_text, True, CanalColors.CANAL_BLUE)
                mark_rect = mark_surface.get_rect(center=(self.width // 4 - 30, y))
                self.screen.blit(mark_surface, mark_rect)
            
            # 风格名称
            style_surface = self.font_medium.render(style, True, CanalColors.INK_BLACK)
            style_rect = style_surface.get_rect(center=(self.width // 2, y - 15))
            self.screen.blit(style_surface, style_rect)
            
            # 风格描述
            desc_surface = self.font_small.render(style_descriptions[style], True, CanalColors.INK_MEDIUM)
            desc_rect = desc_surface.get_rect(center=(self.width // 2, y + 15))
            self.screen.blit(desc_surface, desc_rect)
        
        # 倒计时
        countdown = int(remaining_time) + 1
        countdown_text = f"自动确认: {countdown}s"
        countdown_surface = self.font_small.render(countdown_text, True, CanalColors.INK_LIGHT)
        countdown_rect = countdown_surface.get_rect(center=(self.width // 2, self.height - 120))
        self.screen.blit(countdown_surface, countdown_rect)