#!/usr/bin/env python3
"""
运河音素实时可视化模块 - 水墨线条风格
专门用于分析和可视化运河环境中的音素特征，以水墨线条方式呈现
"""

import numpy as np
import pygame
import librosa
import math
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import deque

@dataclass
class PhonemeFeature:
    """音素特征数据类"""
    name: str                    # 音素名称
    frequency_range: Tuple[float, float]  # 频率范围
    intensity: float             # 强度 (0-1)
    duration: float              # 持续时间
    confidence: float            # 置信度 (0-1)
    visual_color: Tuple[int, int, int]  # 可视化颜色
    line_style: str              # 线条风格：'flowing', 'sharp', 'dotted', 'thick'

class CanalPhonemeAnalyzer:
    """运河音素分析器"""
    
    def __init__(self, sample_rate: int = 32000):
        """初始化运河音素分析器"""
        self.sample_rate = sample_rate
        self.window_size = 1024  # 从2048减少到1024，提高性能
        self.hop_length = 512    # 从512保持不变
        
        # 性能优化：减少历史记录长度
        self.phoneme_history = deque(maxlen=5)  # 从30减少到5
        self.current_phonemes = {}
        
        # 运河环境特定的音素定义（优化版本）
        self.canal_phonemes = {
            # 水流相关音素（低频连续音）
            'water_flow': {
                'name': '水流音',
                'freq_range': (50, 500),
                'pattern': 'continuous',
                'color': (100, 150, 200),
                'line_style': 'flowing',
                'onomatopoeia': ['潺潺', '汩汩', '淙淙']
            },
            
            # 船只引擎音（中低频节奏音）
            'boat_engine': {
                'name': '船只音',
                'freq_range': (100, 800),
                'pattern': 'rhythmic',
                'color': (150, 100, 80),
                'line_style': 'thick',
                'onomatopoeia': ['突突', '嘟嘟', '轰轰']
            },
            
            # 鸟鸣音（高频旋律音）
            'bird_call': {
                'name': '鸟鸣音',
                'freq_range': (2000, 6000),
                'pattern': 'melodic',
                'color': (80, 180, 100),
                'line_style': 'sharp',
                'onomatopoeia': ['啾啾', '唧唧', '喳喳']
            },
            
            # 风声（宽频噪声）
            'wind_sound': {
                'name': '风声',
                'freq_range': (200, 2000),
                'pattern': 'noise',
                'color': (120, 120, 120),
                'line_style': 'dotted',
                'onomatopoeia': ['呼呼', '嗖嗖', '飒飒']
            }
        }
        
        # 音素历史记录
        self.phoneme_history = deque(maxlen=100)
        self.current_phonemes = {}
        
    def analyze_phonemes(self, audio_data: np.ndarray) -> Dict[str, PhonemeFeature]:
        """分析音频中的音素特征"""
        if len(audio_data) == 0:
            return {}
        
        try:
            # 计算频谱
            stft = librosa.stft(audio_data, n_fft=self.window_size, hop_length=self.hop_length)
            magnitude = np.abs(stft)
            freqs = librosa.fft_frequencies(sr=self.sample_rate, n_fft=self.window_size)
            
            # 分析每个音素
            detected_phonemes = {}
            for phoneme_id, phoneme_info in self.canal_phonemes.items():
                feature = self._analyze_single_phoneme(magnitude, freqs, phoneme_id, phoneme_info)
                if feature.confidence > 0.1:  # 只保留置信度较高的音素
                    detected_phonemes[phoneme_id] = feature
            
            # 更新历史记录
            self.phoneme_history.append(detected_phonemes)
            self.current_phonemes = detected_phonemes
            
            return detected_phonemes
            
        except Exception as e:
            print(f"音素分析错误: {e}")
            return {}

    def _analyze_single_phoneme(self, magnitude: np.ndarray, freqs: np.ndarray, 
                               phoneme_id: str, phoneme_info: Dict) -> PhonemeFeature:
        """分析单个音素特征"""
        freq_min, freq_max = phoneme_info['freq_range']
        
        # 找到频率范围内的索引
        freq_mask = (freqs >= freq_min) & (freqs <= freq_max)
        if not np.any(freq_mask):
            return PhonemeFeature(
                name=phoneme_info['name'],
                frequency_range=(freq_min, freq_max),
                intensity=0.0,
                duration=0.0,
                confidence=0.0,
                visual_color=phoneme_info['color'],
                line_style=phoneme_info['line_style']
            )
        
        # 计算该频率范围内的平均能量
        freq_magnitude = magnitude[freq_mask, :]
        avg_energy = np.mean(freq_magnitude)
        
        # 计算强度（归一化）
        intensity = min(avg_energy * 10, 1.0)  # 调整缩放因子
        
        # 计算持续时间
        duration = self._estimate_duration(freq_magnitude)
        
        # 计算置信度（基于模式匹配）
        confidence = self._calculate_pattern_confidence(freq_magnitude, phoneme_info['pattern'])
        confidence *= intensity  # 强度越高，置信度越高
        
        return PhonemeFeature(
            name=phoneme_info['name'],
            frequency_range=(freq_min, freq_max),
            intensity=intensity,
            duration=duration,
            confidence=confidence,
            visual_color=phoneme_info['color'],
            line_style=phoneme_info['line_style']
        )

    def _calculate_pattern_confidence(self, magnitude: np.ndarray, pattern: str) -> float:
        """根据音素模式计算置信度"""
        if magnitude.size == 0:
            return 0.0
        
        try:
            if pattern == 'continuous_low':
                # 连续低频：检查能量的稳定性
                energy_std = np.std(np.mean(magnitude, axis=0))
                return max(0, 1.0 - energy_std * 5)
            
            elif pattern == 'burst_high':
                # 突发高频：检查能量峰值
                max_energy = np.max(magnitude)
                mean_energy = np.mean(magnitude)
                if mean_energy > 0:
                    return min(max_energy / mean_energy / 10, 1.0)
                return 0.0
            
            elif pattern == 'rhythmic_low':
                # 节奏性低频：检查周期性
                energy_series = np.mean(magnitude, axis=0)
                if len(energy_series) > 4:
                    autocorr = np.correlate(energy_series, energy_series, mode='full')
                    return min(np.max(autocorr[len(autocorr)//2+1:]) / np.max(autocorr) * 2, 1.0)
                return 0.0
            
            elif pattern == 'tonal_mid':
                # 音调性中频：检查频率集中度
                freq_concentration = np.max(magnitude) / (np.mean(magnitude) + 1e-6)
                return min(freq_concentration / 5, 1.0)
            
            elif pattern == 'melodic_high':
                # 旋律性高频：检查频率变化
                if magnitude.shape[1] > 1:
                    freq_variation = np.std(np.argmax(magnitude, axis=0))
                    return min(freq_variation / 10, 1.0)
                return 0.0
            
            elif pattern == 'noise_broad':
                # 宽频噪声：检查频谱平坦度
                spectral_flatness = np.exp(np.mean(np.log(magnitude + 1e-10))) / (np.mean(magnitude) + 1e-10)
                return min(spectral_flatness * 3, 1.0)
            
            elif pattern == 'percussive_low':
                # 打击性低频：检查瞬态特性
                if magnitude.shape[1] > 1:
                    onset_strength = np.max(np.diff(np.mean(magnitude, axis=0)))
                    return min(onset_strength * 20, 1.0)
                return 0.0
            
            elif pattern == 'formant_mid':
                # 共振峰中频：检查多峰特性
                freq_profile = np.mean(magnitude, axis=1)
                peaks = self._find_peaks(freq_profile)
                return min(len(peaks) / 3, 1.0)
            
            else:
                return np.mean(magnitude)
                
        except Exception as e:
            print(f"模式置信度计算错误: {e}")
            return 0.0
    
    def _find_peaks(self, signal: np.ndarray, threshold: float = 0.1) -> List[int]:
        """简单的峰值检测"""
        peaks = []
        for i in range(1, len(signal) - 1):
            if (signal[i] > signal[i-1] and signal[i] > signal[i+1] and 
                signal[i] > threshold):
                peaks.append(i)
        return peaks
    
    def _estimate_duration(self, magnitude: np.ndarray) -> float:
        """估算音素持续时间"""
        if magnitude.size == 0:
            return 0.0
        
        # 计算能量超过阈值的时间比例
        energy_series = np.mean(magnitude, axis=0)
        threshold = np.max(energy_series) * 0.1
        active_frames = np.sum(energy_series > threshold)
        
        # 转换为时间（秒）
        frame_duration = self.hop_length / self.sample_rate
        return active_frames * frame_duration
    
    def get_dominant_phonemes(self, top_k: int = 3) -> List[PhonemeFeature]:
        """获取当前最主要的音素"""
        if not self.current_phonemes:
            return []
        
        # 按置信度排序
        sorted_phonemes = sorted(
            self.current_phonemes.values(),
            key=lambda x: x.confidence * x.intensity,
            reverse=True
        )
        
        return sorted_phonemes[:top_k]

class PhonemeVisualizer:
    """音素可视化器 - 水墨线条风格"""
    
    def __init__(self, width: int, height: int):
        """初始化音素可视化器"""
        self.width = width
        self.height = height
        
        # 初始化音素分析器
        self.analyzer = CanalPhonemeAnalyzer()
        
        # 初始化pygame字体
        pygame.font.init()
        
        # 优先使用墨趣古风体
        font_paths = [
            "墨趣古风体.ttf",
            "assets/fonts/墨趣古风体.ttf"
        ]
        
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        
        for font_path in font_paths:
            try:
                self.font_large = pygame.font.Font(font_path, 36)
                self.font_medium = pygame.font.Font(font_path, 24)
                self.font_small = pygame.font.Font(font_path, 18)
                print(f"音素可视化字体加载成功: {font_path}")
                break
            except Exception as e:
                continue
        
        # 如果没有加载成功，使用默认字体
        if not self.font_large:
            try:
                self.font_large = pygame.font.Font("墨趣古风体.ttf", 36)
                self.font_medium = pygame.font.Font("墨趣古风体.ttf", 24)
                self.font_small = pygame.font.Font("墨趣古风体.ttf", 18)
                print("音素可视化字体加载成功: 墨趣古风体.ttf")
            except:
                # 最后的备用方案
                chinese_fonts = ['PingFang SC', 'STHeiti', 'SimHei', 'Microsoft YaHei']
                for font_name in chinese_fonts:
                    try:
                        self.font_large = pygame.font.SysFont(font_name, 36)
                        self.font_medium = pygame.font.SysFont(font_name, 24)
                        self.font_small = pygame.font.SysFont(font_name, 18)
                        print(f"音素可视化使用系统字体: {font_name}")
                        break
                    except:
                        continue
                
                if not self.font_large:
                    self.font_large = pygame.font.Font(None, 36)
                    self.font_medium = pygame.font.Font(None, 24)
                    self.font_small = pygame.font.Font(None, 18)
                    print("音素可视化使用默认字体")
                try:
                    self.font_large = pygame.font.Font("墨趣古风体.ttf", 36)
                    self.font_medium = pygame.font.Font("墨趣古风体.ttf", 24)
                    self.font_small = pygame.font.Font("墨趣古风体.ttf", 18)
                except:
                    self.font_large = pygame.font.Font(None, 36)
                    self.font_medium = pygame.font.Font(None, 24)
                    self.font_small = pygame.font.Font(None, 18)
        
        # 水墨笔画效果
        self.ink_strokes = []
        self.stroke_particles = []
        
        # 性能优化：减少更新频率
        self.last_update_time = 0
        self.update_interval = 0.1  # 每100ms更新一次，而不是每帧
        
        # 性能优化：限制历史记录长度
        self.max_history_length = 10  # 从30减少到10
        
        # 动画参数
        self.animation_time = 0
        
    def update(self, audio_data: np.ndarray):
        """更新音素分析和可视化（性能优化版本）"""
        if audio_data is None or len(audio_data) == 0:
            return
        
        current_time = time.time()
        
        # 性能优化：限制更新频率
        if current_time - self.last_update_time < self.update_interval:
            return
        
        self.last_update_time = current_time
        
        # 性能优化：降采样音频数据
        if len(audio_data) > 1600:  # 如果数据太长，进行降采样
            step = len(audio_data) // 1600
            audio_data = audio_data[::step]
        
        # 分析音素
        phonemes = self.analyzer.analyze_phonemes(audio_data)
        
        # 更新水墨笔画（减少频率）
        self._update_ink_strokes(phonemes)
        
        # 更新动画时间
        self.animation_time += self.update_interval
        
    def _update_ink_strokes(self, phonemes: Dict[str, PhonemeFeature]):
        """更新水墨笔画效果"""
        current_time = time.time()
        
        # 为每个检测到的音素创建笔画
        for phoneme_id, feature in phonemes.items():
            if feature.intensity > 0.2:  # 只为强度较高的音素创建笔画
                self._create_ink_stroke(phoneme_id, feature, current_time)
        
        # 清理过期的笔画
        self.ink_strokes = [stroke for stroke in self.ink_strokes 
                           if current_time - stroke['created_time'] < 3.0]
        self.stroke_particles = [particle for particle in self.stroke_particles 
                               if current_time - particle['created_time'] < 2.0]
    
    def _create_ink_stroke(self, phoneme_id: str, feature: PhonemeFeature, current_time: float):
        """创建水墨笔画"""
        # 根据音素类型确定笔画位置和形状
        base_y = self.height * 0.7  # 基准线位置
        
        # 根据频率范围确定垂直位置
        freq_ratio = (feature.frequency_range[0] + feature.frequency_range[1]) / 2 / 8000
        y_offset = (0.5 - freq_ratio) * self.height * 0.4
        
        # 创建笔画数据
        stroke = {
            'phoneme_id': phoneme_id,
            'feature': feature,
            'created_time': current_time,
            'points': self._generate_stroke_points(feature, base_y + y_offset),
            'alpha': 255,
            'thickness': max(1, int(feature.intensity * 8))
        }
        
        self.ink_strokes.append(stroke)
        
        # 创建笔画粒子效果
        for _ in range(int(feature.intensity * 10)):
            particle = {
                'x': np.random.randint(50, self.width - 50),
                'y': base_y + y_offset + np.random.randint(-20, 20),
                'vx': np.random.uniform(-2, 2),
                'vy': np.random.uniform(-1, 1),
                'size': np.random.uniform(1, 4),
                'alpha': int(feature.intensity * 200),
                'color': feature.visual_color,
                'created_time': current_time,
                'line_style': feature.line_style
            }
            self.stroke_particles.append(particle)
    
    def _generate_stroke_points(self, feature: PhonemeFeature, base_y: float) -> List[Tuple[int, int]]:
        """根据音素特征生成笔画点"""
        points = []
        stroke_length = int(feature.intensity * 200 + 50)
        
        if feature.line_style == 'flowing':
            # 流动线条 - 适合水流声、风声
            for i in range(stroke_length):
                x = 50 + i * 2
                y = base_y + math.sin(i * 0.1 + self.animation_time * 2) * feature.intensity * 20
                points.append((int(x), int(y)))
                
        elif feature.line_style == 'sharp':
            # 尖锐线条 - 适合水花声、船笛声
            for i in range(0, stroke_length, 5):
                x = 50 + i * 3
                y = base_y + ((-1) ** (i // 5)) * feature.intensity * 15
                points.append((int(x), int(y)))
                
        elif feature.line_style == 'dotted':
            # 点状线条 - 适合鸟鸣声
            for i in range(0, stroke_length, 8):
                x = 50 + i * 2
                y = base_y + math.sin(i * 0.2) * feature.intensity * 10
                points.append((int(x), int(y)))
                
        elif feature.line_style == 'thick':
            # 粗线条 - 适合引擎声
            for i in range(stroke_length):
                x = 50 + i
                y = base_y + math.sin(i * 0.05) * feature.intensity * 5
                points.append((int(x), int(y)))
        
        return points

    def render(self, screen: pygame.Surface):
        """渲染音素可视化 - 水墨线条风格"""
        # 渲染水墨笔画
        self._render_ink_strokes(screen)
        
        # 渲染笔画粒子
        self._render_stroke_particles(screen)
        
        # 渲染音素信息面板（简化版）
        self._render_phoneme_panel_ink_style(screen)
        
    def _render_ink_strokes(self, screen: pygame.Surface):
        """渲染水墨笔画"""
        current_time = time.time()
        
        for stroke in self.ink_strokes:
            age = current_time - stroke['created_time']
            # 笔画随时间淡化
            alpha = max(0, int(stroke['alpha'] * (1 - age / 3.0)))
            
            if len(stroke['points']) > 1 and alpha > 0:
                # 创建带透明度的表面
                stroke_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                
                # 根据线条风格绘制
                if stroke['feature'].line_style == 'dotted':
                    # 点状线条
                    for point in stroke['points'][::2]:  # 每隔一个点绘制
                        pygame.draw.circle(stroke_surface, 
                                         (*stroke['feature'].visual_color, alpha),
                                         point, stroke['thickness'])
                else:
                    # 连续线条
                    if len(stroke['points']) > 1:
                        pygame.draw.lines(stroke_surface, 
                                        (*stroke['feature'].visual_color, alpha),
                                        False, stroke['points'], stroke['thickness'])
                
                screen.blit(stroke_surface, (0, 0))
    
    def _render_stroke_particles(self, screen: pygame.Surface):
        """渲染笔画粒子效果"""
        current_time = time.time()
        
        for particle in self.stroke_particles:
            age = current_time - particle['created_time']
            # 粒子随时间淡化和移动
            alpha = max(0, int(particle['alpha'] * (1 - age / 2.0)))
            
            if alpha > 0:
                # 更新粒子位置
                particle['x'] += particle['vx']
                particle['y'] += particle['vy']
                particle['vy'] += 0.1  # 重力效果
                
                # 绘制粒子
                particle_surface = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
                pygame.draw.circle(particle_surface, 
                                 (*particle['color'], alpha),
                                 (int(particle['size']), int(particle['size'])), 
                                 int(particle['size']))
                
                screen.blit(particle_surface, 
                          (int(particle['x'] - particle['size']), 
                           int(particle['y'] - particle['size'])))
    
    def _render_phoneme_panel_ink_style(self, screen: pygame.Surface):
        """渲染水墨风格的音素信息面板"""
        if not self.font or not self.font_small:
            return
            
        try:
            # 调整位置避免与E2录制覆盖层重叠
            panel_x = 20
            panel_y = 180  # 从20调整到180，避免与上方内容重叠
            panel_width = 280
            panel_height = 150
            
            # 绘制水墨风格背景
            panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
            # 使用渐变透明度模拟宣纸质感
            for i in range(panel_height):
                alpha = int(120 * (1 - i / panel_height * 0.3))
                pygame.draw.line(panel_surface, (250, 248, 240, alpha), 
                               (0, i), (panel_width, i))
            
            # 绘制墨色边框
            pygame.draw.rect(panel_surface, (50, 50, 50, 150), 
                           (0, 0, panel_width, panel_height), 2)
            
            screen.blit(panel_surface, (panel_x, panel_y))
            
            # 标题 - 使用墨色
            title_text = self.font.render("运河音韵", True, (30, 30, 30))
            screen.blit(title_text, (panel_x + 10, panel_y + 10))
            
            # 显示主要音素及其拟声词
            dominant_phonemes = self.analyzer.get_dominant_phonemes(4)
            y_offset = 40
            
            for i, phoneme in enumerate(dominant_phonemes):
                # 音素名称 - 使用对应的墨色深浅
                name_text = self.font_small.render(
                    f"{phoneme.name}", True, phoneme.visual_color
                )
                screen.blit(name_text, (panel_x + 10, panel_y + y_offset))
                
                # 拟声词标注
                phoneme_info = self.analyzer.canal_phonemes.get(
                    [k for k, v in self.analyzer.canal_phonemes.items() 
                     if v['name'] == phoneme.name][0] if any(v['name'] == phoneme.name 
                     for v in self.analyzer.canal_phonemes.values()) else None
                )
                
                if phoneme_info and 'onomatopoeia' in phoneme_info:
                    # 随机选择一个拟声词
                    onomatopoeia = phoneme_info['onomatopoeia'][int(self.animation_time) % len(phoneme_info['onomatopoeia'])]
                    ono_text = self.font_small.render(f"「{onomatopoeia}」", True, (80, 80, 80))
                    screen.blit(ono_text, (panel_x + 150, panel_y + y_offset))
                
                # 强度线条 - 水墨风格，优化线条粗细
                line_length = int(phoneme.intensity * 80)
                line_thickness = max(1, int(phoneme.intensity * 2))  # 从4调整为2，减少线条粗细
                
                if line_length > 0:
                    line_surface = pygame.Surface((line_length, line_thickness), pygame.SRCALPHA)
                    # 渐变效果模拟墨迹浓淡
                    for x in range(line_length):
                        alpha = int(200 * (1 - x / line_length * 0.5))
                        pygame.draw.line(line_surface, (*phoneme.visual_color, alpha),
                                       (x, 0), (x, line_thickness))
                    
                    screen.blit(line_surface, (panel_x + 10, panel_y + y_offset + 15))
                
                y_offset += 30
                
        except Exception as e:
            print(f"音素面板渲染错误: {e}")

    def _render_phoneme_spectrum(self, screen: pygame.Surface):
        """渲染音素频谱图"""
        spectrum_x = self.width - 300
        spectrum_y = 10
        spectrum_width = 280
        spectrum_height = 150
        
        # 绘制半透明背景
        spectrum_surface = pygame.Surface((spectrum_width, spectrum_height))
        spectrum_surface.set_alpha(180)
        spectrum_surface.fill((20, 20, 30))
        screen.blit(spectrum_surface, (spectrum_x, spectrum_y))
        
        # 绘制边框
        pygame.draw.rect(screen, (100, 100, 100), 
                        (spectrum_x, spectrum_y, spectrum_width, spectrum_height), 2)
        
        # 标题
        title_text = self.font.render("音素频谱", True, (255, 255, 255))
        screen.blit(title_text, (spectrum_x + 10, spectrum_y + 10))
        
        # 绘制频谱条
        if self.analyzer.current_phonemes:
            bar_width = spectrum_width // len(self.analyzer.canal_phonemes)
            
            for i, (phoneme_id, phoneme_info) in enumerate(self.analyzer.canal_phonemes.items()):
                bar_x = spectrum_x + i * bar_width + 5
                bar_y = spectrum_y + 40
                bar_height = spectrum_height - 50
                
                # 获取当前音素强度
                intensity = 0.0
                if phoneme_id in self.analyzer.current_phonemes:
                    intensity = self.analyzer.current_phonemes[phoneme_id].intensity
                
                # 绘制频谱条
                filled_height = int(bar_height * intensity)
                if filled_height > 0:
                    pygame.draw.rect(screen, phoneme_info['color'], 
                                   (bar_x, bar_y + bar_height - filled_height, 
                                    bar_width - 2, filled_height))
                
                # 绘制边框
                pygame.draw.rect(screen, (80, 80, 80), 
                               (bar_x, bar_y, bar_width - 2, bar_height), 1)

if __name__ == "__main__":
    # 测试代码
    pygame.init()
    
    width, height = 1280, 720
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("运河音素可视化测试")
    
    visualizer = PhonemeVisualizer(width, height)
    clock = pygame.time.Clock()
    
    print("运河音素可视化测试启动")
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
        
        # 水流声（低频连续）
        test_audio += 0.3 * np.sin(2 * np.pi * 200 * t) * (1 + 0.2 * np.sin(2 * np.pi * 5 * t))
        
        # 鸟鸣声（高频旋律）
        if time.time() % 3 < 1:  # 每3秒鸣叫1秒
            bird_freq = 3000 + 1000 * np.sin(2 * np.pi * 10 * t)
            test_audio += 0.2 * np.sin(2 * np.pi * bird_freq * t)
        
        # 船只引擎（低频节奏）
        if time.time() % 5 < 2:  # 每5秒运行2秒
            engine_freq = 120 + 20 * np.sin(2 * np.pi * 2 * t)
            test_audio += 0.4 * np.sin(2 * np.pi * engine_freq * t)
        
        # 添加噪声
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