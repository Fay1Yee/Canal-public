#!/usr/bin/env python3
"""
水墨风格渲染引擎
使用PIL和数学算法生成真实的水墨书法艺术效果
支持行书、篆书、水墨晕染三种风格
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
import random
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class BrushStroke:
    """笔画数据"""
    points: List[Tuple[float, float]]  # 笔画路径点
    thickness: float                   # 粗细
    pressure: float                   # 压力
    speed: float                      # 速度
    ink_density: float               # 墨浓度

@dataclass
class InkEffect:
    """墨迹效果参数"""
    blur_radius: float               # 模糊半径
    spread_factor: float            # 扩散因子
    flywhite_intensity: float       # 飞白强度
    texture_strength: float         # 纹理强度

class InkWashRenderer:
    """水墨渲染引擎"""
    
    def __init__(self):
        """初始化渲染引擎"""
        self.canvas_size = (960, 540)  # 默认画布大小
        self.paper_color = (245, 245, 240)  # 宣纸色
        self.ink_color = (30, 30, 30)  # 墨色
        
        # 加载字体
        self._load_fonts()
        
        # 预生成纹理
        self._generate_paper_texture()
        
        print("水墨渲染引擎初始化完成")
    
    def _load_fonts(self):
        """加载字体"""
        self.fonts = {}
        
        # 优先级字体列表，包含项目中实际存在的字体
        font_candidates = [
            "墨趣古风体.ttf",  # 项目根目录的主字体
            "assets/fonts/NotoSansCJK-Regular.ttc",  # 项目中的中文字体
            "assets/fonts/Songti.ttc",  # 项目中的宋体
            "assets/fonts/SourceHanSansSC-Regular.otf",  # 项目中的思源黑体
            "/System/Library/Fonts/PingFang.ttc",  # macOS系统字体
            "/System/Library/Fonts/STHeiti Light.ttc",  # macOS中文字体
            "assets/fonts/NotoSansSC-Regular.otf",  # 备用字体
            "assets/fonts/SimSun.ttf",  # 备用字体
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"  # Linux字体
        ]
        
        for font_path in font_candidates:
            try:
                if Path(font_path).exists():
                    # 不同大小的字体
                    self.fonts['large'] = ImageFont.truetype(font_path, 200)
                    self.fonts['medium'] = ImageFont.truetype(font_path, 150)
                    self.fonts['small'] = ImageFont.truetype(font_path, 100)
                    print(f"水墨字体加载成功: {font_path}")
                    return
            except Exception as e:
                print(f"字体 {font_path} 加载失败: {e}")
                continue
        
        # 如果没有加载成功，使用默认字体
        try:
            self.fonts['large'] = ImageFont.load_default()
            self.fonts['medium'] = ImageFont.load_default()
            self.fonts['small'] = ImageFont.load_default()
            print("使用默认字体进行水墨渲染")
        except Exception as e:
            print(f"默认字体加载失败: {e}")
            # 创建空字体字典，避免后续错误
            self.fonts = {
                'large': None,
                'medium': None,
                'small': None
            }
    
    def _generate_paper_texture(self):
        """生成宣纸纹理"""
        width, height = self.canvas_size
        self.paper_texture = Image.new('L', (width, height), 255)
        
        # 生成纹理噪声
        pixels = np.array(self.paper_texture)
        
        # 添加细微的纹理变化
        noise = np.random.normal(0, 5, (height, width))
        pixels = np.clip(pixels + noise, 0, 255).astype(np.uint8)
        
        # 添加纤维纹理
        for _ in range(100):
            x1 = random.randint(0, width-1)
            y1 = random.randint(0, height-1)
            x2 = x1 + random.randint(-20, 20)
            y2 = y1 + random.randint(-5, 5)
            
            if 0 <= x2 < width and 0 <= y2 < height:
                # 绘制细纤维
                draw = ImageDraw.Draw(self.paper_texture)
                draw.line([(x1, y1), (x2, y2)], fill=250, width=1)
        
        self.paper_texture = Image.fromarray(pixels, 'L')
    
    def render_calligraphy(self, text: str, style: str = "行书", **kwargs) -> Image.Image:
        """渲染书法作品"""
        
        # 提取参数
        brush_thickness = kwargs.get('brush_thickness', 0.5)
        ink_density = kwargs.get('ink_density', 0.7)
        flywhite_intensity = kwargs.get('flywhite_intensity', 0.3)
        ink_blur = kwargs.get('ink_blur', 0.4)
        ink_spread = kwargs.get('ink_spread', 0.2)
        
        # 创建画布
        canvas = Image.new('RGB', self.canvas_size, self.paper_color)
        
        # 应用宣纸纹理
        self._apply_paper_texture(canvas)
        
        # 根据风格选择渲染方法
        if style == "行书":
            self._render_running_script(canvas, text, brush_thickness, ink_density, flywhite_intensity, ink_blur)
        elif style == "篆书":
            self._render_seal_script(canvas, text, brush_thickness, ink_density, flywhite_intensity, ink_blur)
        elif style == "水墨晕染":
            self._render_ink_wash(canvas, text, brush_thickness, ink_density, ink_spread, ink_blur)
        else:
            # 默认行书
            self._render_running_script(canvas, text, brush_thickness, ink_density, flywhite_intensity, ink_blur)
        
        return canvas
    
    def _apply_paper_texture(self, canvas: Image.Image):
        """应用宣纸纹理"""
        # 将纹理转换为RGB并混合到画布
        texture_rgb = Image.new('RGB', self.canvas_size, self.paper_color)
        texture_alpha = self.paper_texture.convert('L')
        
        # 创建带透明度的纹理
        texture_rgba = Image.new('RGBA', self.canvas_size)
        texture_rgba.paste(texture_rgb, (0, 0))
        texture_rgba.putalpha(texture_alpha)
        
        # 混合到画布
        canvas.paste(texture_rgba, (0, 0), texture_rgba)
    
    def _render_running_script(self, canvas: Image.Image, text: str, thickness: float, 
                              density: float, flywhite: float, blur: float):
        """渲染行书风格"""
        draw = ImageDraw.Draw(canvas)
        
        # 计算文字布局
        font = self.fonts.get('large', ImageFont.load_default())
        
        # 获取文字尺寸
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 居中位置
        x = (self.canvas_size[0] - text_width) // 2
        y = (self.canvas_size[1] - text_height) // 2
        
        # 创建文字蒙版
        text_mask = Image.new('L', self.canvas_size, 0)
        mask_draw = ImageDraw.Draw(text_mask)
        mask_draw.text((x, y), text, font=font, fill=255)
        
        # 应用行书效果
        self._apply_running_script_effects(canvas, text_mask, thickness, density, flywhite, blur)
    
    def _render_seal_script(self, canvas: Image.Image, text: str, thickness: float,
                           density: float, flywhite: float, blur: float):
        """渲染篆书风格"""
        draw = ImageDraw.Draw(canvas)
        
        # 篆书使用更规整的字体
        font = self.fonts.get('medium', ImageFont.load_default())
        
        # 计算布局
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (self.canvas_size[0] - text_width) // 2
        y = (self.canvas_size[1] - text_height) // 2
        
        # 创建文字蒙版
        text_mask = Image.new('L', self.canvas_size, 0)
        mask_draw = ImageDraw.Draw(text_mask)
        mask_draw.text((x, y), text, font=font, fill=255)
        
        # 应用篆书效果（更规整，飞白较少）
        self._apply_seal_script_effects(canvas, text_mask, thickness, density, flywhite * 0.5, blur)
    
    def _render_ink_wash(self, canvas: Image.Image, text: str, thickness: float,
                        density: float, spread: float, blur: float):
        """渲染水墨晕染风格"""
        draw = ImageDraw.Draw(canvas)
        
        # 水墨晕染使用较大的字体
        font = self.fonts.get('large', ImageFont.load_default())
        
        # 计算布局
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (self.canvas_size[0] - text_width) // 2
        y = (self.canvas_size[1] - text_height) // 2
        
        # 创建多层墨迹效果
        for i in range(3):
            # 每层有不同的偏移和透明度
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            alpha = int(255 * density * (0.8 - i * 0.2))
            
            # 创建当前层
            layer = Image.new('RGBA', self.canvas_size, (0, 0, 0, 0))
            layer_draw = ImageDraw.Draw(layer)
            
            # 绘制文字
            ink_color_alpha = (*self.ink_color, alpha)
            layer_draw.text((x + offset_x, y + offset_y), text, font=font, fill=ink_color_alpha)
            
            # 应用模糊和扩散
            if blur > 0:
                layer = layer.filter(ImageFilter.GaussianBlur(radius=blur * (i + 1)))
            
            # 合并到画布
            canvas.paste(layer, (0, 0), layer)
        
        # 添加水墨扩散效果
        self._apply_ink_diffusion(canvas, spread)
    
    def _apply_running_script_effects(self, canvas: Image.Image, text_mask: Image.Image,
                                     thickness: float, density: float, flywhite: float, blur: float):
        """应用行书效果"""
        
        # 创建墨迹层
        ink_layer = Image.new('RGBA', self.canvas_size, (0, 0, 0, 0))
        
        # 转换蒙版为numpy数组进行处理
        mask_array = np.array(text_mask)
        
        # 找到文字区域
        text_pixels = np.where(mask_array > 0)
        
        if len(text_pixels[0]) > 0:
            # 为每个文字像素添加墨迹效果
            ink_pixels = []
            
            for i in range(len(text_pixels[0])):
                y, x = text_pixels[0][i], text_pixels[1][i]
                
                # 基础墨迹强度
                base_intensity = mask_array[y, x] / 255.0
                
                # 添加随机变化（模拟笔触不均匀）
                variation = random.uniform(0.7, 1.3)
                intensity = base_intensity * density * variation
                
                # 飞白效果（随机跳过一些像素）
                if random.random() < flywhite:
                    intensity *= 0.3
                
                # 笔触粗细效果（扩展像素）
                brush_size = int(thickness * 3) + 1
                for dy in range(-brush_size, brush_size + 1):
                    for dx in range(-brush_size, brush_size + 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.canvas_size[0] and 0 <= ny < self.canvas_size[1]:
                            distance = math.sqrt(dx*dx + dy*dy)
                            if distance <= brush_size:
                                # 距离越远，强度越低
                                pixel_intensity = intensity * (1 - distance / brush_size)
                                alpha = int(pixel_intensity * 255)
                                if alpha > 0:
                                    ink_pixels.append((nx, ny, alpha))
            
            # 将墨迹像素绘制到层上
            ink_array = np.zeros((*self.canvas_size[::-1], 4), dtype=np.uint8)
            
            for x, y, alpha in ink_pixels:
                if 0 <= x < self.canvas_size[0] and 0 <= y < self.canvas_size[1]:
                    ink_array[y, x] = [*self.ink_color, min(alpha, 255)]
            
            ink_layer = Image.fromarray(ink_array, 'RGBA')
            
            # 应用模糊效果
            if blur > 0:
                ink_layer = ink_layer.filter(ImageFilter.GaussianBlur(radius=blur * 2))
            
            # 合并到画布
            canvas.paste(ink_layer, (0, 0), ink_layer)
    
    def _apply_seal_script_effects(self, canvas: Image.Image, text_mask: Image.Image,
                                  thickness: float, density: float, flywhite: float, blur: float):
        """应用篆书效果（更规整）"""
        
        # 篆书效果类似行书，但变化更小，更规整
        ink_layer = Image.new('RGBA', self.canvas_size, (0, 0, 0, 0))
        
        mask_array = np.array(text_mask)
        text_pixels = np.where(mask_array > 0)
        
        if len(text_pixels[0]) > 0:
            ink_pixels = []
            
            for i in range(len(text_pixels[0])):
                y, x = text_pixels[0][i], text_pixels[1][i]
                
                base_intensity = mask_array[y, x] / 255.0
                
                # 篆书变化较小
                variation = random.uniform(0.85, 1.15)
                intensity = base_intensity * density * variation
                
                # 飞白效果较少
                if random.random() < flywhite:
                    intensity *= 0.5
                
                # 笔触更均匀
                brush_size = int(thickness * 2) + 1
                for dy in range(-brush_size, brush_size + 1):
                    for dx in range(-brush_size, brush_size + 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.canvas_size[0] and 0 <= ny < self.canvas_size[1]:
                            distance = math.sqrt(dx*dx + dy*dy)
                            if distance <= brush_size:
                                pixel_intensity = intensity * (1 - distance / brush_size * 0.5)  # 更均匀
                                alpha = int(pixel_intensity * 255)
                                if alpha > 0:
                                    ink_pixels.append((nx, ny, alpha))
            
            # 绘制墨迹
            ink_array = np.zeros((*self.canvas_size[::-1], 4), dtype=np.uint8)
            
            for x, y, alpha in ink_pixels:
                if 0 <= x < self.canvas_size[0] and 0 <= y < self.canvas_size[1]:
                    ink_array[y, x] = [*self.ink_color, min(alpha, 255)]
            
            ink_layer = Image.fromarray(ink_array, 'RGBA')
            
            # 轻微模糊
            if blur > 0:
                ink_layer = ink_layer.filter(ImageFilter.GaussianBlur(radius=blur))
            
            canvas.paste(ink_layer, (0, 0), ink_layer)
    
    def _apply_ink_diffusion(self, canvas: Image.Image, spread: float):
        """应用水墨扩散效果"""
        if spread <= 0:
            return
        
        # 创建扩散效果
        diffusion_layer = Image.new('RGBA', self.canvas_size, (0, 0, 0, 0))
        
        # 在文字周围添加淡墨扩散
        canvas_array = np.array(canvas)
        
        # 找到有墨迹的区域
        gray = np.mean(canvas_array, axis=2)
        ink_regions = gray < 200  # 找到比宣纸色深的区域
        
        if np.any(ink_regions):
            # 创建扩散蒙版
            diffusion_mask = np.zeros(self.canvas_size[::-1], dtype=np.uint8)
            
            # 在墨迹周围添加扩散
            for _ in range(int(spread * 100)):
                # 随机选择墨迹点
                ink_points = np.where(ink_regions)
                if len(ink_points[0]) > 0:
                    idx = random.randint(0, len(ink_points[0]) - 1)
                    y, x = ink_points[0][idx], ink_points[1][idx]
                    
                    # 在周围添加扩散点
                    for _ in range(10):
                        dx = random.randint(-20, 20)
                        dy = random.randint(-20, 20)
                        nx, ny = x + dx, y + dy
                        
                        if 0 <= nx < self.canvas_size[0] and 0 <= ny < self.canvas_size[1]:
                            distance = math.sqrt(dx*dx + dy*dy)
                            if distance > 0:
                                alpha = int(50 * spread / distance * 10)
                                if alpha > 0:
                                    diffusion_mask[ny, nx] = min(alpha, 255)
            
            # 创建扩散层
            diffusion_array = np.zeros((*self.canvas_size[::-1], 4), dtype=np.uint8)
            diffusion_array[:, :, :3] = self.ink_color
            diffusion_array[:, :, 3] = diffusion_mask
            
            diffusion_layer = Image.fromarray(diffusion_array, 'RGBA')
            
            # 模糊扩散层
            diffusion_layer = diffusion_layer.filter(ImageFilter.GaussianBlur(radius=5))
            
            # 合并到画布
            canvas.paste(diffusion_layer, (0, 0), diffusion_layer)
    
    def render_animation_frames(self, text: str, style: str, parameters: Any, frame_count: int) -> List[str]:
        """渲染动画帧序列"""
        frames = []
        
        try:
            # 创建临时目录
            temp_dir = Path("temp_frames")
            temp_dir.mkdir(exist_ok=True)
            
            # 生成动画帧
            for i in range(frame_count):
                # 计算动画进度
                progress = i / max(frame_count - 1, 1)
                
                # 根据进度调整参数（模拟书写过程）
                animated_params = self._calculate_animation_parameters(parameters, progress)
                
                # 渲染当前帧
                frame_image = self.render_calligraphy(text, style, **animated_params)
                
                # 保存帧
                frame_path = temp_dir / f"frame_{i:04d}.png"
                frame_image.save(frame_path)
                frames.append(str(frame_path))
            
            return frames
            
        except Exception as e:
            print(f"动画帧生成错误: {e}")
            # 返回静态帧
            static_frame = self.render_calligraphy(text, style, 
                                                 brush_thickness=parameters.brush_thickness,
                                                 ink_density=parameters.ink_density,
                                                 flywhite_intensity=parameters.flywhite_intensity,
                                                 ink_blur=parameters.ink_blur,
                                                 ink_spread=parameters.ink_spread)
            
            frame_path = "temp_static_frame.png"
            static_frame.save(frame_path)
            return [frame_path] * frame_count
    
    def _calculate_animation_parameters(self, base_params: Any, progress: float) -> Dict[str, float]:
        """计算动画参数"""
        
        # 模拟书写过程：从淡到浓，从细到粗
        write_progress = min(progress * 1.5, 1.0)  # 前2/3时间用于书写
        
        return {
            'brush_thickness': base_params.brush_thickness * write_progress,
            'ink_density': base_params.ink_density * (0.3 + 0.7 * write_progress),
            'flywhite_intensity': base_params.flywhite_intensity * (1 - write_progress * 0.5),
            'ink_blur': base_params.ink_blur * (1 + progress * 0.5),
            'ink_spread': base_params.ink_spread * progress
        }

# 测试代码
if __name__ == "__main__":
    # 测试水墨渲染引擎
    renderer = InkWashRenderer()
    
    # 测试不同风格
    test_texts = ["水", "流", "静", "远"]
    styles = ["行书", "篆书", "水墨晕染"]
    
    print("开始测试水墨渲染...")
    
    for i, text in enumerate(test_texts):
        style = styles[i % len(styles)]
        
        print(f"渲染 '{text}' - {style}")
        
        # 渲染图像
        image = renderer.render_calligraphy(
            text=text,
            style=style,
            brush_thickness=0.6,
            ink_density=0.8,
            flywhite_intensity=0.4,
            ink_blur=0.3,
            ink_spread=0.2
        )
        
        # 保存测试图像
        output_path = f"test_{text}_{style}.png"
        image.save(output_path)
        print(f"保存: {output_path}")
    
    print("测试完成")