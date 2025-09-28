#!/usr/bin/env python3
"""
运河水墨艺术生成器
将环境声音特征映射为水墨艺术参数，生成独特的书法艺术作品
支持行书、篆书、水墨晕染三种风格
"""

import json
import numpy as np
import threading
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import random

# 可选依赖
try:
    from moviepy import ImageClip, ImageSequenceClip
    HAS_MOVIEPY = True
except ImportError:
    print("警告: moviepy不可用，视频生成将被禁用")
    HAS_MOVIEPY = False

from audio_rec import AudioFeatures
from ink_wash_pygame import InkWashRenderer

@dataclass
class ArtParameters:
    """艺术参数数据类"""
    # 基础参数
    style: str                    # 风格：行书、篆书、水墨晕染
    content_text: str            # 生成的文字内容
    
    # 笔触参数
    brush_thickness: float       # 笔触粗细 (0-1)
    brush_speed: float          # 笔速 (0-1)
    brush_pressure: float       # 笔压 (0-1)
    
    # 墨迹效果
    ink_density: float          # 墨浓度 (0-1)
    ink_blur: float            # 墨迹模糊度 (0-1)
    flywhite_intensity: float  # 飞白强度 (0-1)
    ink_spread: float          # 墨晕扩散 (0-1)
    
    # 节奏参数
    pause_intensity: float      # 停顿强度 (0-1)
    rhythm_variation: float     # 节奏变化 (0-1)
    
    # 情感参数
    tranquility: float         # 宁静度 (0-1)
    vitality: float           # 活力度 (0-1)
    elegance: float           # 雅致度 (0-1)
    
    # 环境映射
    water_influence: float     # 水流影响 (0-1)
    boat_influence: float     # 船只影响 (0-1)
    bird_influence: float     # 鸟鸣影响 (0-1)
    wind_influence: float     # 风声影响 (0-1)

@dataclass
class GeneratedArt:
    """生成的艺术作品数据"""
    parameters: ArtParameters
    cover_image_path: str
    animation_video_path: str
    metadata: Dict[str, Any]
    creation_time: datetime
    
    # 音频相关
    audio_file_path: Optional[str] = None
    audio_features: Optional[AudioFeatures] = None

class ArtGenerator:
    """水上书艺术生成器"""
    
    def __init__(self, config: Dict):
        """初始化生成器"""
        self.config = config
        self.is_generating = False
        self.generation_complete = False
        self.generation_progress = 0.0
        self.generated_art = None
        
        # 加载象声词词典
        self.words_dict = self._load_words_dictionary()
        
        # 初始化水墨渲染器
        self.ink_renderer = InkWashRenderer()
        
        # 运河主题词汇
        self.canal_words = [
            "水", "流", "波", "浪", "涛", "潮", "涌", "溅",
            "船", "舟", "帆", "桨", "航", "渡", "泊", "港",
            "桥", "岸", "堤", "柳", "风", "云", "雨", "雾",
            "静", "幽", "深", "远", "清", "澈", "碧", "蓝",
            "鸟", "鸣", "啼", "飞", "翔", "栖", "息", "巢"
        ]
        
        # 风格配置
        self.style_configs = {
            "行书": {
                "brush_thickness_range": (0.3, 0.8),
                "brush_speed_range": (0.6, 0.9),
                "ink_density_range": (0.6, 0.9),
                "flywhite_range": (0.2, 0.6),
                "rhythm_variation_range": (0.4, 0.8)
            },
            "篆书": {
                "brush_thickness_range": (0.4, 0.7),
                "brush_speed_range": (0.3, 0.6),
                "ink_density_range": (0.7, 0.95),
                "flywhite_range": (0.1, 0.3),
                "rhythm_variation_range": (0.2, 0.4)
            },
            "水墨晕染": {
                "brush_thickness_range": (0.5, 1.0),
                "brush_speed_range": (0.2, 0.5),
                "ink_density_range": (0.3, 0.7),
                "flywhite_range": (0.0, 0.2),
                "rhythm_variation_range": (0.6, 1.0)
            }
        }
        
        print("艺术生成器初始化完成")
    
    def _load_words_dictionary(self) -> Dict:
        """加载象声词词典"""
        try:
            words_path = Path("assets/words.json")
            with open(words_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"词典加载失败: {e}")
            return {
                "low_freq_dominant": [],
                "mid_freq_dominant": [],
                "high_freq_dominant": [],
                "onset_dense": []
            }
    
    def start_generation(self, audio_features: AudioFeatures):
        """开始生成艺术作品"""
        if self.is_generating:
            return
        
        self.is_generating = True
        self.generation_complete = False
        self.generation_progress = 0.0
        
        # 启动生成线程
        self.generation_thread = threading.Thread(
            target=self._generate_art_async,
            args=(audio_features,),
            daemon=True
        )
        self.generation_thread.start()
        
        print("开始生成艺术作品...")
    
    def _generate_art_async(self, audio_features: AudioFeatures):
        """异步生成艺术作品（高度优化版本）"""
        try:
            print("开始异步生成艺术作品...")
            
            # 步骤1: 快速分析音频特征 (20%)
            print("步骤1: 分析音频特征...")
            self.generation_progress = 0.2
            art_params = self._map_audio_to_art_parameters_fast(audio_features)
            print(f"音频特征分析完成，生成参数: {art_params.style}")
            
            # 步骤2: 快速生成文字内容 (40%)
            print("步骤2: 生成文字内容...")
            self.generation_progress = 0.4
            content_text = self._generate_content_text_fast(audio_features, art_params)
            art_params.content_text = content_text
            print(f"文字内容生成完成: {content_text}")
            
            # 步骤3: 超快速渲染封面图像 (70%)
            print("步骤3: 渲染封面图像...")
            self.generation_progress = 0.7
            cover_path = self._render_cover_image_ultra_fast(art_params)
            print(f"封面图像渲染完成: {cover_path}")
            
            # 步骤4: 跳过视频生成或使用极简版本 (90%)
            print("步骤4: 生成动画视频...")
            self.generation_progress = 0.9
            video_path = self._render_animation_video_minimal(art_params)
            print(f"动画视频生成完成: {video_path}")
            
            # 步骤5: 快速生成元数据 (100%)
            print("步骤5: 生成元数据...")
            self.generation_progress = 1.0
            metadata = self._generate_metadata_fast(art_params, audio_features)
            print("元数据生成完成")
            
            # 创建最终艺术作品
            self.generated_art = GeneratedArt(
                parameters=art_params,
                cover_image_path=cover_path,
                animation_video_path=video_path,
                metadata=metadata,
                creation_time=datetime.now(),
                audio_features=audio_features
            )
            
            self.generation_complete = True
            print("艺术作品生成完成")
            
        except Exception as e:
            print(f"艺术生成错误: {e}")
            import traceback
            traceback.print_exc()
            
            # 创建错误时的占位作品
            try:
                print("创建占位作品...")
                placeholder_params = ArtParameters(
                    style="行书",
                    content_text="水",
                    brush_thickness=0.5,
                    brush_speed=0.5,
                    brush_pressure=0.5,
                    ink_density=0.7,
                    ink_blur=0.3,
                    flywhite_intensity=0.4,
                    ink_spread=0.2,
                    pause_intensity=0.3,
                    rhythm_variation=0.4,
                    tranquility=0.6,
                    vitality=0.4,
                    elegance=0.7,
                    water_influence=0.5,
                    boat_influence=0.3,
                    bird_influence=0.4,
                    wind_influence=0.2
                )
                
                # 创建简单的占位图像和视频
                placeholder_cover = self._create_placeholder_cover()
                placeholder_video = self._create_placeholder_video()
                
                self.generated_art = GeneratedArt(
                    parameters=placeholder_params,
                    cover_image_path=placeholder_cover,
                    animation_video_path=placeholder_video,
                    metadata={"error": "生成失败，使用占位作品"},
                    creation_time=datetime.now(),
                    audio_features=audio_features
                )
                
                self.generation_complete = True
                print("占位作品创建完成")
                
            except Exception as placeholder_error:
                print(f"占位作品创建失败: {placeholder_error}")
                self.generation_complete = False
        finally:
            self.is_generating = False

    def _map_audio_to_art_parameters_fast(self, features: AudioFeatures) -> ArtParameters:
        """快速映射音频特征到艺术参数"""
        # 简化的映射逻辑，减少计算复杂度
        style = "行书"  # 默认风格，避免复杂选择逻辑
        
        # 基于音频特征的快速参数计算
        rms = min(features.rms_energy, 1.0)
        zcr = min(features.zero_crossing_rate, 1.0)
        
        return ArtParameters(
            style=style,
            content_text="",  # 稍后填充
            brush_thickness=0.3 + rms * 0.4,
            brush_speed=0.5 + zcr * 0.3,
            brush_pressure=0.4 + rms * 0.4,
            ink_density=0.6 + rms * 0.3,
            ink_blur=0.2 + zcr * 0.2,
            flywhite_intensity=0.3 + rms * 0.3,
            ink_spread=0.1 + zcr * 0.2,
            pause_intensity=0.2 + (1 - rms) * 0.3,
            rhythm_variation=0.3 + zcr * 0.4,
            tranquility=0.5 + features.canal_ambience_score * 0.3,
            vitality=0.3 + rms * 0.4,
            elegance=0.6 + features.canal_ambience_score * 0.2,
            water_influence=features.water_flow_indicator,
            boat_influence=features.boat_activity_indicator,
            bird_influence=features.bird_activity_indicator,
            wind_influence=features.wind_indicator
        )

    def _generate_content_text_fast(self, features: AudioFeatures, params: ArtParameters) -> str:
        """快速生成文字内容"""
        # 简化的文字生成逻辑
        water_words = ["水", "流", "波", "涛"]
        boat_words = ["船", "舟", "帆", "航"]
        nature_words = ["风", "云", "鸟", "柳"]
        
        # 根据音频特征快速选择词汇
        if features.water_flow_indicator > 0.6:
            return random.choice(water_words)
        elif features.boat_activity_indicator > 0.5:
            return random.choice(boat_words)
        elif features.bird_activity_indicator > 0.5:
            return random.choice(nature_words)
        else:
            return "静"

    def _render_cover_image_ultra_fast(self, params: ArtParameters) -> str:
        """超快速渲染封面图像"""
        try:
            print("开始超快速封面渲染...")
            
            # 使用更小的图像尺寸
            width, height = 400, 300
            
            # 创建纯色背景图像
            image = Image.new('RGB', (width, height), (248, 248, 248))  # 浅灰背景
            draw = ImageDraw.Draw(image)
            
            # 简单的文字绘制，无复杂效果
            font_size = min(width, height) // 6
            text = params.content_text
            
            # 计算文字位置
            text_bbox = draw.textbbox((0, 0), text)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            # 绘制文字
            draw.text((x, y), text, fill=(60, 60, 60))
            
            # 保存图像
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cover_{timestamp}.png"
            filepath = Path("output") / filename
            filepath.parent.mkdir(exist_ok=True)
            
            # 快速保存，无优化
            image.save(filepath)
            print(f"超快速封面渲染完成: {filepath}")
            
            return str(filepath)
            
        except Exception as e:
            print(f"超快速封面渲染失败: {e}")
            return self._create_placeholder_cover()

    def _render_animation_video_minimal(self, params: ArtParameters) -> str:
        """极简动画视频生成"""
        try:
            # 直接返回静态图像作为"视频"，避免复杂的视频生成
            print("使用静态图像代替视频生成...")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"animation_{timestamp}.png"  # 使用PNG而不是MP4
            filepath = Path("output") / filename
            filepath.parent.mkdir(exist_ok=True)
            
            # 创建简单的静态图像
            width, height = 400, 300
            image = Image.new('RGB', (width, height), (248, 248, 248))
            draw = ImageDraw.Draw(image)
            
            # 绘制文字
            text = params.content_text
            font_size = min(width, height) // 6
            text_bbox = draw.textbbox((0, 0), text)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            draw.text((x, y), text, fill=(60, 60, 60))
            
            # 添加简单的装饰
            draw.rectangle([10, 10, width-10, height-10], outline=(120, 120, 120), width=2)
            
            image.save(filepath)
            print(f"极简动画生成完成: {filepath}")
            
            return str(filepath)
            
        except Exception as e:
            print(f"极简动画生成失败: {e}")
            return self._create_placeholder_video()

    def _generate_metadata_fast(self, params: ArtParameters, features: AudioFeatures) -> Dict[str, Any]:
        """快速生成元数据"""
        return {
            "style": params.style,
            "content": params.content_text,
            "generation_time": datetime.now().isoformat(),
            "audio_duration": features.duration,
            "optimized": True
        }
    
    def generate_final_art(self, audio_features: AudioFeatures, selected_style: str) -> GeneratedArt:
        """生成最终艺术作品（优化同步方法）"""
        try:
            print(f"开始生成最终艺术作品，风格: {selected_style}")
            
            # 使用快速映射方法
            art_params = self._map_audio_to_art_parameters_fast(audio_features)
            art_params.style = selected_style
            
            # 根据选择的风格进行简单调整
            self._adjust_parameters_for_style_fast(art_params, selected_style)
            
            # 快速生成文字内容
            content_text = self._generate_content_text_fast(audio_features, art_params)
            art_params.content_text = content_text
            
            # 使用优化的渲染方法
            cover_path = self._render_cover_image_ultra_fast(art_params)
            video_path = self._render_animation_video_minimal(art_params)
            
            # 快速生成元数据
            metadata = self._generate_metadata_fast(art_params, audio_features)
            
            print("最终艺术作品生成完成")
            return GeneratedArt(
                parameters=art_params,
                cover_image_path=cover_path,
                animation_video_path=video_path,
                metadata=metadata,
                creation_time=datetime.now(),
                audio_features=audio_features
            )
            
        except Exception as e:
            print(f"最终艺术生成错误: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _adjust_parameters_for_style_fast(self, params: ArtParameters, style: str):
        """快速调整风格参数"""
        if style == "篆书":
            params.brush_speed *= 0.7  # 篆书笔速较慢
            params.ink_density = min(params.ink_density + 0.2, 1.0)  # 墨色更浓
            params.flywhite_intensity *= 0.5  # 减少飞白
        elif style == "水墨晕染":
            params.ink_spread = min(params.ink_spread + 0.3, 1.0)  # 增加晕染
            params.ink_blur = min(params.ink_blur + 0.2, 1.0)  # 增加模糊
        # 行书保持默认参数
    
    def is_generation_complete(self) -> bool:
        """检查生成是否完成 - 添加线程安全检查"""
        # 检查生成标志
        if not self.generation_complete:
            return False
        
        # 如果有生成线程，确保线程已完成
        if hasattr(self, 'generation_thread') and self.generation_thread:
            if self.generation_thread.is_alive():
                # 线程仍在运行，等待一小段时间
                self.generation_thread.join(timeout=0.1)
                return not self.generation_thread.is_alive()
        
        return True
    
    def get_progress(self) -> float:
        """获取生成进度"""
        return self.generation_progress
    
    def reset(self):
        """重置生成器"""
        self.is_generating = False
        self.generation_complete = False
        self.generation_progress = 0.0
        self.generated_art = None
        
        # 清理临时文件
        self._cleanup_temp_files()
    
    def _cleanup_temp_files(self):
        """清理临时文件"""
        try:
            # 清理临时帧目录
            temp_frames_dir = Path("temp_frames")
            if temp_frames_dir.exists():
                import shutil
                shutil.rmtree(temp_frames_dir)
                print("临时帧文件已清理")
            
            # 清理旧的输出文件（保留最新的5个）
            output_dir = Path("output")
            if output_dir.exists():
                # 获取所有封面文件
                cover_files = list(output_dir.glob("cover_*.png"))
                if len(cover_files) > 5:
                    # 按修改时间排序，删除旧文件
                    cover_files.sort(key=lambda x: x.stat().st_mtime)
                    for old_file in cover_files[:-5]:
                        old_file.unlink()
                        print(f"删除旧文件: {old_file}")
                
                # 获取所有视频文件
                video_files = list(output_dir.glob("animation_*.mp4"))
                if len(video_files) > 5:
                    video_files.sort(key=lambda x: x.stat().st_mtime)
                    for old_file in video_files[:-5]:
                        old_file.unlink()
                        print(f"删除旧文件: {old_file}")
                        
        except Exception as e:
            print(f"清理临时文件时出错: {e}")
    
    def _render_cover_image_fast(self, params: ArtParameters) -> str:
        """快速渲染封面图像"""
        try:
            print("开始快速封面渲染...")
            
            # 使用更小的图像尺寸以提高速度
            width, height = 800, 600  # 减小尺寸
            
            # 创建图像
            image = Image.new('RGB', (width, height), (250, 248, 240))  # 宣纸色
            draw = ImageDraw.Draw(image)
            
            # 简化的水墨效果
            self._draw_simple_ink_background(draw, width, height, params)
            
            # 绘制文字
            self._draw_text_fast(draw, params.content_text, width, height, params)
            
            # 保存图像
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cover_{timestamp}.png"
            filepath = Path("output") / filename
            filepath.parent.mkdir(exist_ok=True)
            
            image.save(filepath, optimize=True, quality=85)  # 优化保存
            print(f"快速封面渲染完成: {filepath}")
            
            return str(filepath)
            
        except Exception as e:
            print(f"快速封面渲染失败: {e}")
            return self._create_placeholder_cover()
    
    def _render_animation_video_fast(self, params: ArtParameters) -> str:
        """快速生成动画视频"""
        try:
            if not HAS_MOVIEPY:
                print("MoviePy不可用，跳过视频生成")
                return self._create_placeholder_video()
            
            print("开始快速视频生成...")
            
            # 减少视频时长和帧率以提高速度
            duration = 3  # 减少到3秒
            fps = 12  # 降低帧率
            width, height = 640, 480  # 更小的分辨率
            
            # 生成关键帧而不是所有帧
            key_frames = []
            frame_count = duration * fps
            
            for i in range(0, frame_count, 3):  # 每3帧生成一个关键帧
                progress = i / frame_count
                frame = self._create_simple_frame(width, height, params, progress)
                key_frames.append(frame)
            
            # 创建视频
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"animation_{timestamp}.mp4"
            filepath = Path("output") / filename
            filepath.parent.mkdir(exist_ok=True)
            
            # 使用简化的视频生成
            clip = ImageSequenceClip(key_frames, fps=fps//3)  # 降低实际帧率
            clip.write_videofile(str(filepath), verbose=False, logger=None)
            
            print(f"快速视频生成完成: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"快速视频生成失败: {e}")
            return self._create_placeholder_video()
    
    def _draw_simple_ink_background(self, draw, width, height, params):
        """绘制简化的水墨背景"""
        # 简单的渐变背景
        for i in range(height // 4):
            alpha = int(20 * params.ink_density * (1 - i / (height // 4)))
            if alpha > 0:
                color = (200 - alpha, 200 - alpha, 200 - alpha)
                draw.rectangle([0, i*4, width, (i+1)*4], fill=color)
    
    def _draw_text_fast(self, draw, text, width, height, params):
        """快速绘制文字"""
        try:
            # 使用系统默认字体
            font_size = min(width, height) // 8
            
            # 计算文字位置
            text_width = len(text) * font_size
            text_height = font_size
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            # 绘制文字
            draw.text((x, y), text, fill=(50, 50, 50))
            
        except Exception as e:
            print(f"文字绘制失败: {e}")
    
    def _create_simple_frame(self, width, height, params, progress):
        """创建简单的动画帧"""
        image = Image.new('RGB', (width, height), (250, 248, 240))
        draw = ImageDraw.Draw(image)
        
        # 简单的动画效果
        alpha = int(255 * progress)
        color = (50, 50, 50, alpha)
        
        # 绘制简单的文字
        font_size = min(width, height) // 10
        text_width = len(params.content_text) * font_size
        x = (width - text_width) // 2
        y = (height - font_size) // 2
        
        draw.text((x, y), params.content_text, fill=(50, 50, 50))
        
        return np.array(image)
    
    def _create_placeholder_cover(self) -> str:
        """创建占位封面"""
        try:
            image = Image.new('RGB', (400, 300), (250, 248, 240))
            draw = ImageDraw.Draw(image)
            draw.text((150, 140), "水墨", fill=(100, 100, 100))
            
            filepath = Path("output") / "placeholder_cover.png"
            filepath.parent.mkdir(exist_ok=True)
            image.save(filepath)
            
            return str(filepath)
        except:
            return "placeholder_cover.png"
    
    def _create_placeholder_video(self) -> str:
        """创建占位视频"""
        return "placeholder_video.mp4"

# 测试代码
if __name__ == "__main__":
    # 测试艺术生成器
    from audio_rec import AudioFeatures
    
    # 创建测试音频特征
    test_features = AudioFeatures(
        duration=35.0,
        sample_rate=32000,
        rms_energy=0.1,
        zero_crossing_rate=0.05,
        spectral_centroid=np.array([1000, 1200, 800]),
        spectral_rolloff=np.array([2000, 2500, 1800]),
        spectral_bandwidth=np.array([500, 600, 400]),
        mfcc=np.random.random((13, 100)),
        water_flow_indicator=0.7,
        boat_activity_indicator=0.3,
        bird_activity_indicator=0.5,
        wind_indicator=0.2,
        canal_ambience_score=0.8,
        low_freq_energy=0.4,
        mid_freq_energy=0.3,
        high_freq_energy=0.3
    )
    
    # 测试生成器
    config = {
        'video_duration': 7,
        'video_fps': 24,
        'video_resolution': [960, 540]
    }
    
    generator = ArtGenerator(config)
    
    print("开始测试艺术生成...")
    
    # 测试同步生成
    art = generator.generate_final_art(test_features, "行书")
    
    if art:
        print(f"艺术作品生成成功:")
        print(f"风格: {art.parameters.style}")
        print(f"内容: {art.parameters.content_text}")
        print(f"封面: {art.cover_image_path}")
        print(f"视频: {art.animation_video_path}")
    else:
        print("艺术作品生成失败")
    
    print("测试完成")