#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rice Paper Texture Generator for Waterbook Ink Wash Style
水上书宣纸纹理生成器，用于水墨风格的背景
采用传统水墨配色方案和视觉美学
"""

import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw
import random
import math

# 水上书传统水墨配色方案
class WaterbookColors:
    """水上书主题配色方案 - 传统水墨风格"""
    # 水墨黑色系 - 主要文字和线条
    INK_BLACK = (20, 20, 20)             # 浓墨
    INK_DARK = (40, 40, 40)              # 重墨
    INK_MEDIUM = (70, 70, 70)            # 中墨
    INK_LIGHT = (120, 120, 120)          # 淡墨
    INK_FAINT = (180, 180, 180)          # 极淡墨
    
    # 宣纸色系 - 背景和留白
    PAPER_WHITE = (252, 250, 245)        # 宣纸白
    PAPER_CREAM = (248, 246, 240)        # 宣纸米色
    PAPER_AGED = (245, 242, 235)         # 陈年宣纸
    
    # 水上蓝色系 - 水的表现
    WATER_BLUE_DEEP = (35, 65, 95)       # 深水蓝（偏墨色）
    WATER_BLUE = (55, 85, 115)           # 水上蓝（中性）
    WATER_BLUE_LIGHT = (85, 115, 145)    # 浅水蓝（透明感）
    WATER_BLUE_MIST = (135, 155, 175)    # 水雾蓝（朦胧感）
    
    # 传统水墨色 - 经典搭配
    TRADITIONAL_BLACK = (25, 25, 25)     # 传统墨色
    SEAL_RED = (180, 45, 35)             # 印章红（点缀用）

def create_waterbook_rice_paper(width: int, height: int, 
                               base_color: tuple = None,
                               noise_intensity: float = 0.12,
                               fiber_density: float = 0.25,
                               ink_wash_spots: int = 3) -> Image.Image:
    """
    创建水上书风格的宣纸纹理
    
    Args:
        width: 图像宽度
        height: 图像高度
        base_color: 基础颜色，默认使用宣纸白
        noise_intensity: 噪点强度
        fiber_density: 纤维密度
        ink_wash_spots: 水墨渍数量
    
    Returns:
        PIL Image对象
    """
    if base_color is None:
        base_color = WaterbookColors.PAPER_WHITE
    
    # 创建基础画布
    img = Image.new('RGB', (width, height), base_color)
    pixels = np.array(img)
    
    # 添加细腻的宣纸纹理噪点
    noise = np.random.normal(0, noise_intensity * 255, (height, width, 3))
    # 使用更自然的噪点分布
    noise = noise * (0.8 + 0.4 * np.random.random((height, width, 3)))
    pixels = pixels.astype(np.float32) + noise
    pixels = np.clip(pixels, 0, 255).astype(np.uint8)
    
    # 创建纤维纹理层
    fiber_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    fiber_draw = ImageDraw.Draw(fiber_img)
    
    # 添加更自然的纤维线条
    num_fibers = int(width * height * fiber_density / 8000)
    for _ in range(num_fibers):
        # 随机起点和方向
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        length = random.randint(8, 40)
        angle = random.uniform(0, 2 * np.pi)
        thickness = random.uniform(0.5, 1.5)
        
        # 计算终点
        end_x = x + length * math.cos(angle)
        end_y = y + length * math.sin(angle)
        
        # 纤维颜色 - 使用淡墨色
        fiber_alpha = random.randint(10, 30)
        fiber_color = (*WaterbookColors.INK_FAINT, fiber_alpha)
        
        # 绘制纤维线
        fiber_draw.line([(x, y), (end_x, end_y)], 
                       fill=fiber_color, width=int(thickness))
    
    # 应用高斯模糊使纤维更自然
    fiber_img = fiber_img.filter(ImageFilter.GaussianBlur(radius=0.3))
    
    # 将纤维纹理混合到主图像
    img = Image.fromarray(pixels).convert('RGBA')
    img = Image.alpha_composite(img, fiber_img)
    
    # 添加水墨渍效果
    if ink_wash_spots > 0:
        img = _add_ink_wash_spots(img, ink_wash_spots)
    
    # 添加传统宣纸的微妙色彩变化
    img = _enhance_paper_texture(img)
    
    return img.convert('RGB')

def _add_ink_wash_spots(img: Image.Image, num_spots: int) -> Image.Image:
    """添加淡淡的水墨渍效果"""
    width, height = img.size
    ink_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    
    for _ in range(num_spots):
        # 随机位置和大小
        x = random.randint(int(width * 0.1), int(width * 0.9))
        y = random.randint(int(height * 0.1), int(height * 0.9))
        radius = random.randint(30, 120)
        
        # 创建单个墨渍
        spot_size = radius * 2
        spot = Image.new('RGBA', (spot_size, spot_size), (0, 0, 0, 0))
        spot_draw = ImageDraw.Draw(spot)
        
        # 使用传统墨色
        ink_color = random.choice([
            WaterbookColors.INK_FAINT,
            WaterbookColors.INK_LIGHT,
            WaterbookColors.WATER_BLUE_MIST
        ])
        
        # 创建径向渐变效果
        center = radius
        for r in range(radius, 0, -2):
            alpha = int((radius - r) / radius * 15)  # 很淡的透明度
            color = (*ink_color, alpha)
            spot_draw.ellipse([center - r, center - r, center + r, center + r], 
                            fill=color)
        
        # 添加不规则边缘
        spot = spot.filter(ImageFilter.GaussianBlur(radius=radius * 0.2))
        
        # 粘贴到墨渍层
        paste_x = max(0, min(width - spot_size, x - radius))
        paste_y = max(0, min(height - spot_size, y - radius))
        ink_layer.paste(spot, (paste_x, paste_y), spot)
    
    # 混合墨渍层
    result = Image.alpha_composite(img.convert('RGBA'), ink_layer)
    return result

def _enhance_paper_texture(img: Image.Image) -> Image.Image:
    """增强宣纸纹理效果"""
    # 轻微降低饱和度，模拟宣纸的自然色调
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(0.92)
    
    # 增加一点对比度，突出纹理
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.05)
    
    # 添加非常轻微的模糊，模拟纸张的柔和质感
    img = img.filter(ImageFilter.GaussianBlur(radius=0.2))
    
    return img

def create_waterbook_ink_background(width: int, height: int,
                                  style: str = "elegant",
                                  ink_intensity: float = 0.08) -> Image.Image:
    """
    创建水上书风格的水墨背景
    
    Args:
        width: 图像宽度
        height: 图像高度
        style: 风格类型 ("elegant", "traditional", "modern")
        ink_intensity: 墨渍强度
    
    Returns:
        PIL Image对象
    """
    # 先创建基础宣纸纹理
    if style == "elegant":
        paper = create_waterbook_rice_paper(width, height, 
                                          WaterbookColors.PAPER_WHITE,
                                          noise_intensity=0.1,
                                          fiber_density=0.2,
                                          ink_wash_spots=2)
    elif style == "traditional":
        paper = create_waterbook_rice_paper(width, height,
                                          WaterbookColors.PAPER_CREAM,
                                          noise_intensity=0.15,
                                          fiber_density=0.3,
                                          ink_wash_spots=4)
    else:  # modern
        paper = create_waterbook_rice_paper(width, height,
                                          WaterbookColors.PAPER_AGED,
                                          noise_intensity=0.08,
                                          fiber_density=0.15,
                                          ink_wash_spots=1)
    
    # 添加装饰性水墨元素
    paper = _add_decorative_elements(paper, style)
    
    return paper

def _add_decorative_elements(img: Image.Image, style: str) -> Image.Image:
    """添加装饰性水墨元素"""
    width, height = img.size
    decoration_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(decoration_layer)
    
    if style == "traditional":
        # 添加传统印章效果
        _draw_traditional_seal(draw, width, height)
        
        # 添加题跋线条
        _draw_inscription_lines(draw, width, height)
    
    elif style == "elegant":
        # 添加优雅的边框装饰
        _draw_elegant_borders(draw, width, height)
    
    # 混合装饰层
    result = Image.alpha_composite(img.convert('RGBA'), decoration_layer)
    return result.convert('RGB')

def _draw_traditional_seal(draw: ImageDraw.Draw, width: int, height: int):
    """绘制传统印章"""
    seal_size = min(width, height) // 15
    x = width // 20
    y = height // 20
    
    # 印章边框
    seal_color = (*WaterbookColors.SEAL_RED, 120)
    draw.rectangle([x, y, x + seal_size, y + seal_size], 
                  outline=seal_color, width=2)
    
    # 印章内容
    inner_margin = seal_size // 4
    draw.rectangle([x + inner_margin, y + inner_margin, 
                   x + seal_size - inner_margin, y + seal_size - inner_margin],
                  fill=(*WaterbookColors.SEAL_RED, 80))

def _draw_inscription_lines(draw: ImageDraw.Draw, width: int, height: int):
    """绘制题跋线条"""
    start_x = width - width // 6
    start_y = height - height // 4
    line_color = (*WaterbookColors.INK_FAINT, 60)
    
    # 绘制几条平行线
    for i in range(4):
        y_pos = start_y + i * (height // 40)
        draw.line([(start_x, y_pos), (width - width // 20, y_pos)], 
                 fill=line_color, width=1)

def _draw_elegant_borders(draw: ImageDraw.Draw, width: int, height: int):
    """绘制优雅的边框装饰"""
    margin = min(width, height) // 30
    corner_length = min(width, height) // 20
    border_color = (*WaterbookColors.INK_FAINT, 80)
    
    # 四角装饰线
    # 左上角
    draw.line([(margin, margin), (margin + corner_length, margin)], 
             fill=border_color, width=2)
    draw.line([(margin, margin), (margin, margin + corner_length)], 
             fill=border_color, width=2)
    
    # 右上角
    draw.line([(width - margin - corner_length, margin), (width - margin, margin)], 
             fill=border_color, width=2)
    draw.line([(width - margin, margin), (width - margin, margin + corner_length)], 
             fill=border_color, width=2)
    
    # 左下角
    draw.line([(margin, height - margin), (margin + corner_length, height - margin)], 
             fill=border_color, width=2)
    draw.line([(margin, height - margin - corner_length), (margin, height - margin)], 
             fill=border_color, width=2)
    
    # 右下角
    draw.line([(width - margin - corner_length, height - margin), 
              (width - margin, height - margin)], fill=border_color, width=2)
    draw.line([(width - margin, height - margin - corner_length), 
              (width - margin, height - margin)], fill=border_color, width=2)

def create_waterbook_ui_background(width: int, height: int, 
                                 ui_type: str = "main") -> Image.Image:
    """
    为水上书UI创建专用背景
    
    Args:
        width: 图像宽度
        height: 图像高度
        ui_type: UI类型 ("main", "dialog", "overlay")
    
    Returns:
        PIL Image对象
    """
    if ui_type == "main":
        return create_waterbook_ink_background(width, height, "elegant", 0.05)
    elif ui_type == "dialog":
        return create_waterbook_rice_paper(width, height,
                                         WaterbookColors.PAPER_WHITE,
                                         noise_intensity=0.08,
                                         fiber_density=0.15,
                                         ink_wash_spots=1)
    else:  # overlay
        return create_waterbook_rice_paper(width, height,
                                         WaterbookColors.PAPER_CREAM,
                                         noise_intensity=0.06,
                                         fiber_density=0.1,
                                         ink_wash_spots=0)

if __name__ == "__main__":
    # 测试生成不同风格的纹理
    print("生成水上书风格宣纸纹理...")
    
    # 优雅风格
    elegant_texture = create_waterbook_ink_background(800, 600, "elegant")
    elegant_texture.save("waterbook_elegant_paper.png")
    print("优雅风格纹理已保存: waterbook_elegant_paper.png")
    
    # 传统风格
    traditional_texture = create_waterbook_ink_background(800, 600, "traditional")
    traditional_texture.save("waterbook_traditional_paper.png")
    print("传统风格纹理已保存: waterbook_traditional_paper.png")
    
    # 现代风格
    modern_texture = create_waterbook_ink_background(800, 600, "modern")
    modern_texture.save("waterbook_modern_paper.png")
    print("现代风格纹理已保存: waterbook_modern_paper.png")
    
    # UI专用背景
    ui_bg = create_waterbook_ui_background(1280, 720, "main")
    ui_bg.save("waterbook_ui_background.png")
    print("UI背景已保存: waterbook_ui_background.png")
    
    print("所有纹理生成完成！")