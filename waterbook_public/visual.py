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

class UIRenderer:
    """水墨风格UI渲染器"""
    
    def __init__(self, screen, width: int, height: int):
        """初始化UI渲染器"""
        self.screen = screen
        self.width = width
        self.height = height
        
        # 加载字体
        self._load_fonts()
        
        # 初始化颜色
        self.colors = CanalColors()
        
        # 二维码缓存
        self.qr_code_surface = None
        self.qr_code_url = None
        
        # 添加font_tiny字体
        try:
            font_path = "墨趣古风体.ttf"
            if Path(font_path).exists():
                self.font_tiny = pygame.font.Font(font_path, 16)
            else:
                self.font_tiny = pygame.font.Font(None, 16)
        except:
            self.font_tiny = pygame.font.Font(None, 16)
        
        # 动画状态
        self.animation_time = 0
        self.style_switch_animation = {
            'active': False,
            'progress': 0.0,
            'old_style': '',
            'new_style': '',
            'fade_out_progress': 0.0,
            'fade_in_progress': 0.0
        }
        self.loading_animation = {
            'active': False,
            'progress': 0.0,
            'rotation': 0.0,
            'pulse': 0.0,
            'dots_animation': [0.0, 0.0, 0.0]
        }
        
        # 性能优化：缓存常用表面
        self._surface_cache = {}
        self._last_render_state = None
        self._frame_skip_counter = 0
        
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
        """渲染E5展示状态界面"""
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
        
        # 加载并显示封面图像
        try:
            cover_image = pygame.image.load(generated_art.cover_image_path)
            # 缩放图像以适应屏幕
            cover_rect = cover_image.get_rect()
            max_width = self.width // 2
            max_height = self.height - 200
            
            scale = min(max_width / cover_rect.width, max_height / cover_rect.height)
            new_size = (int(cover_rect.width * scale), int(cover_rect.height * scale))
            cover_image = pygame.transform.scale(cover_image, new_size)
            
            # 居中显示
            cover_rect = cover_image.get_rect(center=(self.width // 4, self.height // 2))
            self.screen.blit(cover_image, cover_rect)
            
            # 图像边框
            pygame.draw.rect(self.screen, CanalColors.INK_MEDIUM, cover_rect, 3)
            
        except Exception as e:
            print(f"封面图像加载失败: {e}")
            # 绘制占位矩形
            placeholder_rect = pygame.Rect(self.width // 8, self.height // 4, self.width // 4, self.height // 2)
            pygame.draw.rect(self.screen, CanalColors.CANAL_BLUE_LIGHT, placeholder_rect)
            pygame.draw.rect(self.screen, CanalColors.INK_MEDIUM, placeholder_rect, 3)
            
            # 占位文字
            placeholder_text = "艺术作品"
            placeholder_surface = self.font_medium.render(placeholder_text, True, CanalColors.INK_BLACK)
            placeholder_text_rect = placeholder_surface.get_rect(center=placeholder_rect.center)
            self.screen.blit(placeholder_surface, placeholder_text_rect)
        
        # 作品信息面板
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
        
        # 二维码
        qr_y = y_offset + 20
        self._draw_qr_code(info_x + info_width // 2, qr_y)
        
        # 倒计时显示
        if remaining_time > 0:
            countdown_text = f"自动返回: {int(remaining_time)}秒"
            countdown_surface = self.font_small.render(countdown_text, True, CanalColors.INK_MEDIUM)
            countdown_rect = countdown_surface.get_rect(center=(self.width // 2, self.height - 80))
            self.screen.blit(countdown_surface, countdown_rect)
        
        # 提示文字
        hint_text = "长按返回主界面"
        hint_surface = self.font_small.render(hint_text, True, CanalColors.INK_LIGHT)
        hint_rect = hint_surface.get_rect(center=(self.width // 2, self.height - 50))
        self.screen.blit(hint_surface, hint_rect)
        
        # 装饰元素
        self._draw_ink_wash_decorations()
    
    def render_reset_screen(self):
        """渲染E6重置状态界面"""
        # 清屏
        self.screen.fill(CanalColors.PAPER_WHITE)
        self._draw_paper_texture()
        
        # 重置提示
        reset_text = "正在重置..."
        reset_surface = self.font_large.render(reset_text, True, CanalColors.INK_BLACK)
        reset_rect = reset_surface.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(reset_surface, reset_rect)
        
        # 旋转的水墨圆圈
        self._draw_reset_animation()
        
        # 感谢文字
        thanks_text = "感谢您的体验"
        thanks_surface = self.font_medium.render(thanks_text, True, CanalColors.INK_GRAY)
        thanks_rect = thanks_surface.get_rect(center=(self.width // 2, self.height // 2 + 80))
        self.screen.blit(thanks_surface, thanks_rect)
    
    def render_error_screen(self, error_message: str):
        """渲染错误界面"""
        # 清屏
        self.screen.fill(CanalColors.PAPER_WHITE)
        self._draw_ink_wash_background()
        
        # 错误标题
        title_text = "系统提示"
        title_surface = self.font_large.render(title_text, True, CanalColors.INK_BLACK)
        title_rect = title_surface.get_rect(center=(self.width // 2, self.height // 3))
        
        # 添加标题阴影
        shadow_surface = self.font_large.render(title_text, True, CanalColors.INK_FAINT)
        shadow_rect = shadow_surface.get_rect(center=(self.width // 2 + 2, self.height // 3 + 2))
        self.screen.blit(shadow_surface, shadow_rect)
        self.screen.blit(title_surface, title_rect)
        
        # 错误信息
        error_surface = self.font_medium.render(error_message, True, CanalColors.INK_MEDIUM)
        error_rect = error_surface.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(error_surface, error_rect)
        
        # 提示信息
        hint_text = "系统将自动重试..."
        hint_surface = self.font_small.render(hint_text, True, CanalColors.INK_LIGHT)
        hint_rect = hint_surface.get_rect(center=(self.width // 2, self.height // 2 + 60))
        self.screen.blit(hint_surface, hint_rect)
        
        # 装饰元素
        self._draw_ink_wash_decorations()
    
    def _draw_ink_wash_background(self):
        """绘制水墨背景纹理效果"""
        # 尝试使用生成的宣纸纹理
        try:
            from assets.rice_paper_texture import create_waterbook_ui_background
            import pygame
            
            # 创建宣纸背景纹理
            paper_texture = create_waterbook_ui_background(self.width, self.height, "main")
            
            # 转换为pygame surface
            mode = paper_texture.mode
            size = paper_texture.size
            data = paper_texture.tobytes()
            
            paper_surface = pygame.image.fromstring(data, size, mode)
            
            # 直接绘制到屏幕
            self.screen.blit(paper_surface, (0, 0))
            
        except Exception as e:
            print(f"使用生成纹理失败，回退到程序化纹理: {e}")
            # 回退到原有的程序化纹理
            self._draw_procedural_background()
    
    def _draw_procedural_background(self):
        """绘制程序化水墨背景纹理（回退方案）"""
        # 创建宣纸纹理基础
        for _ in range(30):
            x = np.random.randint(0, self.width)
            y = np.random.randint(0, self.height)
            size = np.random.randint(1, 3)
            alpha = np.random.randint(10, 30)
            color = (*CanalColors.INK_FAINT, alpha)
            
            # 创建带透明度的一个小点
            dot_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(dot_surface, color, (size, size), size)
            self.screen.blit(dot_surface, (x - size, y - size))
        
        # 添加淡淡的 waterbook 背景纹理
        for i in range(5):
            x = np.random.randint(self.width // 4, 3 * self.width // 4)
            y = np.random.randint(self.height // 4, 3 * self.height // 4)
            radius = np.random.randint(50, 150)
            alpha = np.random.randint(5, 15)
            
            # 创建渐变圆形
            gradient_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            for r in range(radius, 0, -5):
                circle_alpha = int(alpha * (radius - r) / radius)
                color = (*CanalColors.INK_FAINT, circle_alpha)
                pygame.draw.circle(gradient_surface, color, (radius, radius), r)
            
            self.screen.blit(gradient_surface, (x - radius, y - radius))
    
    def _draw_ink_wash_decorations(self):
        """绘制水墨风装饰元素"""
        # 左上角印章效果
        self._draw_traditional_seal(100, 100)
        
        # 右下角题跋线条
        self._draw_inscription_lines()
        
        # 边框装饰线条
        self._draw_border_lines()
    
    def _draw_traditional_seal(self, x: int, y: int):
        """绘制传统印章"""
        seal_size = 80
        
        # 印章背景（方形）
        seal_rect = pygame.Rect(x - seal_size//2, y - seal_size//2, seal_size, seal_size)
        
        # 绘制印章边框
        pygame.draw.rect(self.screen, CanalColors.SEAL_RED, seal_rect, 3)
        
        # 印章内容 - 简化的"运河"字样
        inner_rect = pygame.Rect(x - seal_size//3, y - seal_size//3, seal_size*2//3, seal_size*2//3)
        pygame.draw.rect(self.screen, CanalColors.SEAL_RED, inner_rect)
        
        # 印章文字
        seal_text = "水上"
        try:
            seal_surface = self.font_tiny.render(seal_text, True, CanalColors.PAPER_WHITE)
            seal_text_rect = seal_surface.get_rect(center=(x, y))
            self.screen.blit(seal_surface, seal_text_rect)
        except:
            # 如果字体不支持中文，绘制简单图案
            pygame.draw.circle(self.screen, CanalColors.PAPER_WHITE, (x, y), 15)
    
    def _draw_inscription_lines(self):
        """绘制题跋线条"""
        # 右下角的装饰线条
        start_x = self.width - 200
        start_y = self.height - 150
        
        # 绘制几条平行的细线
        for i in range(4):
            line_start = (start_x, start_y + i * 25)
            line_end = (self.width - 50, start_y + i * 25)
            pygame.draw.line(self.screen, CanalColors.INK_LIGHT, line_start, line_end, 1)
        
        # 添加一些装饰性的短线
        for i in range(3):
            short_start = (start_x + 20, start_y + i * 25 + 10)
            short_end = (start_x + 80, start_y + i * 25 + 10)
            pygame.draw.line(self.screen, CanalColors.INK_FAINT, short_start, short_end, 1)
    
    def _draw_border_lines(self):
        """绘制边框装饰线条"""
        margin = 30
        
        # 四角的装饰线条
        corner_length = 60
        
        # 左上角
        pygame.draw.line(self.screen, CanalColors.INK_FAINT, 
                        (margin, margin), (margin + corner_length, margin), 2)
        pygame.draw.line(self.screen, CanalColors.INK_FAINT, 
                        (margin, margin), (margin, margin + corner_length), 2)
        
        # 右上角
        pygame.draw.line(self.screen, CanalColors.INK_FAINT, 
                        (self.width - margin - corner_length, margin), (self.width - margin, margin), 2)
        pygame.draw.line(self.screen, CanalColors.INK_FAINT, 
                        (self.width - margin, margin), (self.width - margin, margin + corner_length), 2)
        
        # 左下角
        pygame.draw.line(self.screen, CanalColors.INK_FAINT, 
                        (margin, self.height - margin), (margin + corner_length, self.height - margin), 2)
        pygame.draw.line(self.screen, CanalColors.INK_FAINT, 
                        (margin, self.height - margin - corner_length), (margin, self.height - margin), 2)
        
        # 右下角
        pygame.draw.line(self.screen, CanalColors.INK_FAINT, 
                        (self.width - margin - corner_length, self.height - margin), 
                        (self.width - margin, self.height - margin), 2)
        pygame.draw.line(self.screen, CanalColors.INK_FAINT, 
                        (self.width - margin, self.height - margin - corner_length), 
                        (self.width - margin, self.height - margin), 2)
    
    def _draw_progress_circle(self, center_x: int, center_y: int, radius: int, progress: float):
        """绘制进度圆环 - 水墨风格"""
        # 背景圆环 - 使用淡墨色
        pygame.draw.circle(self.screen, CanalColors.INK_FAINT, (center_x, center_y), radius, 3)
        
        # 进度弧
        if progress > 0:
            start_angle = -math.pi / 2  # 从顶部开始
            end_angle = start_angle + 2 * math.pi * progress
            
            # 绘制进度弧（使用多个小线段模拟）
            points = []
            segments = max(int(progress * 100), 1)  # 确保至少有1个段
            for i in range(segments + 1):
                angle = start_angle + (end_angle - start_angle) * i / segments
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                points.append((x, y))
            
            if len(points) > 1:
                # 使用渐变效果的进度弧
                pygame.draw.lines(self.screen, CanalColors.CANAL_BLUE, False, points, 6)
                # 添加内层细线增强效果
                pygame.draw.lines(self.screen, CanalColors.CANAL_BLUE_LIGHT, False, points, 2)
    
    def _draw_progress_bar(self, x: int, y: int, width: int, height: int, progress: float):
        """绘制进度条"""
        # 背景
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, CanalColors.INK_GRAY, bg_rect, 0, height//2)
        
        # 进度填充
        fill_width = int(width * progress)
        fill_rect = pygame.Rect(x, y, fill_width, height)
        pygame.draw.rect(self.screen, CanalColors.CANAL_BLUE, fill_rect, 0, height//2)
    
    def _draw_ink_wash_waves(self):
        """绘制水墨风格的波纹效果"""
        center_x, center_y = self.width // 2, self.height // 2
        
        # 多层波纹 - 使用水墨色调
        for i in range(4):
            radius = 180 + i * 60 + math.sin(self.animation_time * 1.5 + i) * 25
            alpha = max(0, int(80 - i * 20))
            
            # 创建带透明度的表面
            wave_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            
            # 使用不同的水墨色调
            if i % 2 == 0:
                color = (*CanalColors.CANAL_BLUE_MIST, alpha)
            else:
                color = (*CanalColors.INK_FAINT, alpha)
            
            pygame.draw.circle(wave_surface, color, (radius, radius), int(radius), 3)
            
            wave_rect = wave_surface.get_rect(center=(center_x, center_y))
            self.screen.blit(wave_surface, wave_rect)
    
    def _draw_ink_generation_animation(self):
        """绘制水墨生成动画"""
        # 在屏幕底部绘制流动的水墨效果
        y = self.height - 150
        
        for i in range(10):
            x = (i * 100 + self.animation_time * 50) % (self.width + 100) - 50
            size = 5 + math.sin(self.animation_time * 3 + i) * 3
            alpha = int(100 + math.sin(self.animation_time * 2 + i) * 50)
            
            ink_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(ink_surface, (*CanalColors.INK_BLACK, alpha), (size, size), int(size))
            
            self.screen.blit(ink_surface, (x - size, y - size))
    
    def _draw_reset_animation(self):
        """绘制重置动画"""
        center_x, center_y = self.width // 2, self.height // 2 - 50
        
        # 旋转的水墨圆圈
        for i in range(8):
            angle = self.animation_time * 2 + i * math.pi / 4
            radius = 80
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            
            size = 8 + math.sin(self.animation_time * 4 + i) * 4
            pygame.draw.circle(self.screen, CanalColors.INK_BLACK, (int(x), int(y)), int(size))
    
    def _draw_qr_code(self, x: int, y: int):
        """绘制二维码"""
        try:
            # 获取本机IP地址
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            url = f"http://{local_ip}:8000"
            
            # 如果URL变化或没有缓存，重新生成二维码
            if self.qr_code_url != url or self.qr_code_surface is None:
                qr = qrcode.QRCode(version=1, box_size=3, border=1)
                qr.add_data(url)
                qr.make(fit=True)
                
                # 生成PIL图像
                qr_img = qr.make_image(fill_color="black", back_color="white")
                
                # 转换为pygame表面
                qr_size = 120
                qr_img = qr_img.resize((qr_size, qr_size))
                
                # PIL转pygame - 修复转换问题
                qr_img_rgb = qr_img.convert('RGB')
                mode = qr_img_rgb.mode
                size = qr_img_rgb.size
                data = qr_img_rgb.tobytes()
                
                self.qr_code_surface = pygame.image.fromstring(data, size, mode)
                self.qr_code_url = url
                print(f"二维码生成成功: {url}")
            
            # 绘制二维码
            if self.qr_code_surface:
                # 调整二维码位置，确保在右下角显示
                qr_x = x - 60  # 居中显示
                qr_y = y
                self.screen.blit(self.qr_code_surface, (qr_x, qr_y))
                
                # 二维码边框
                qr_rect = pygame.Rect(qr_x, qr_y, 120, 120)
                pygame.draw.rect(self.screen, CanalColors.INK_GRAY, qr_rect, 2)
                
                # URL文字
                url_surface = self.font_tiny.render(self.qr_code_url, True, CanalColors.INK_GRAY)
                url_rect = url_surface.get_rect(center=(qr_x + 60, qr_y - 15))
                self.screen.blit(url_surface, url_rect)
        
        except Exception as e:
            print(f"二维码生成失败: {e}")
            # 绘制占位矩形
            qr_x = x - 60
            placeholder_rect = pygame.Rect(qr_x, y, 120, 120)
            pygame.draw.rect(self.screen, CanalColors.CANAL_BLUE_LIGHT, placeholder_rect)
            pygame.draw.rect(self.screen, CanalColors.INK_GRAY, placeholder_rect, 2)
            
            # 占位文字
            placeholder_text = "二维码"
            placeholder_surface = self.font_small.render(placeholder_text, True, CanalColors.INK_GRAY)
            placeholder_rect = placeholder_surface.get_rect(center=(qr_x + 60, y + 60))
            self.screen.blit(placeholder_surface, placeholder_rect)
    
    def _render_style_switch_animation(self):
        """渲染风格切换动画"""
        # 获取动画进度
        fade_out_progress = self.style_switch_animation['fade_out_progress']
        fade_in_progress = self.style_switch_animation['fade_in_progress']
        
        # 创建半透明表面
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(int(255 * fade_out_progress))
        overlay.fill(CanalColors.INK_BLACK)
        
        # 绘制切换提示
        if fade_out_progress > 0.3:
            switch_text = f"切换至 {self.style_switch_animation['new_style']}"
            text_surface = self.font_large.render(switch_text, True, CanalColors.PAPER_WHITE)
            text_rect = text_surface.get_rect(center=(self.width // 2, self.height // 2))
            
            # 文字淡入效果
            text_alpha = int(255 * min(1.0, (fade_out_progress - 0.3) / 0.4))
            text_surface.set_alpha(text_alpha)
            overlay.blit(text_surface, text_rect)
        
        self.screen.blit(overlay, (0, 0))
    
    def _render_loading_animation(self):
        """渲染加载动画"""
        # 半透明背景
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(200)
        overlay.fill(CanalColors.INK_BLACK)
        self.screen.blit(overlay, (0, 0))
        
        center_x, center_y = self.width // 2, self.height // 2
        
        # 旋转的水墨圆环
        rotation = self.loading_animation['rotation']
        for i in range(8):
            angle = rotation + i * math.pi / 4
            radius = 60
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            
            # 脉冲效果
            pulse = self.loading_animation['pulse']
            size = 8 + pulse * 4
            alpha = int(128 + pulse * 127)
            
            # 绘制圆点
            color = (*CanalColors.CANAL_BLUE, alpha)
            pygame.draw.circle(self.screen, color[:3], (int(x), int(y)), int(size))
        
        # 加载文字
        loading_text = "正在生成艺术作品..."
        text_surface = self.font_medium.render(loading_text, True, CanalColors.PAPER_WHITE)
        text_rect = text_surface.get_rect(center=(center_x, center_y + 120))
        self.screen.blit(text_surface, text_rect)
        
        # 动态点点点效果
        dots_text = ""
        for i, dot_progress in enumerate(self.loading_animation['dots_animation']):
            if dot_progress > 0.5:
                dots_text += "●"
            else:
                dots_text += "○"
        
        dots_surface = self.font_small.render(dots_text, True, CanalColors.CANAL_BLUE_LIGHT)
        dots_rect = dots_surface.get_rect(center=(center_x, center_y + 160))
        self.screen.blit(dots_surface, dots_rect)

# 测试代码
if __name__ == "__main__":
    # 测试UI渲染器
    pygame.init()
    
    width, height = 1280, 720
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("运河水墨UI测试")
    
    config = {
        'font': '墨趣古风体.ttf'
    }
    
    renderer = UIRenderer(screen, config)
    clock = pygame.time.Clock()
    
    # 测试不同状态
    test_states = [
        "吸引",
        "聆听", 
        "生成",
        "选择",
        "重置"
    ]
    
    current_state = 0
    state_time = 0
    
    print("UI渲染器测试启动")
    print("按空格键切换状态，ESC退出")
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        renderer.update_animation(dt)
        state_time += dt
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    current_state = (current_state + 1) % len(test_states)
                    state_time = 0
        
        # 渲染当前状态
        state = test_states[current_state]
        
        if state == "吸引":
            renderer.render_attract_screen()
        elif state == "聆听":
            remaining_time = max(0, 8 - state_time)
            renderer.render_listen_screen(remaining_time)
        elif state == "生成":
            progress = min(state_time / 5.0, 1.0)  # 5秒完成
            renderer.render_generate_screen(progress)
        elif state == "选择":
            remaining_time = max(0, 8 - state_time)
            styles = ["行书", "篆书", "水墨晕染"]
            selected = styles[int(state_time) % len(styles)]
            renderer.render_select_screen(selected, remaining_time)
        elif state == "重置":
            renderer.render_reset_screen()
        
        # 状态提示
        state_text = f"当前状态: {state} (按空格切换)"
        state_surface = renderer.font_tiny.render(state_text, True, CanalColors.INK_GRAY)
        screen.blit(state_surface, (10, 10))
        
        pygame.display.flip()
    
    pygame.quit()
    print("测试完成")