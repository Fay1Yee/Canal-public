#!/usr/bin/env python3
"""
实时音频可视化模块
支持基于传统音频特征的声音分类和实时频谱显示
当前使用回退分类器进行基础音频分析，深度学习模型已禁用以确保稳定性
"""

import numpy as np
import pygame
import librosa
import time
import threading
from typing import Dict, List, Tuple, Optional, Any
from collections import deque
import math

# 可选依赖处理 - 更安全的导入方式
HAS_TENSORFLOW = False
HAS_PANNS = False

# 禁用TensorFlow和PANNs以避免段错误
# 在macOS环境下这些库可能导致兼容性问题
try:
    # 暂时禁用这些导入以确保应用程序稳定运行
    # import tensorflow as tf
    # import tensorflow_hub as hub
    # HAS_TENSORFLOW = True
    print("信息: 为稳定性禁用TensorFlow，使用回退分类")
except ImportError:
    print("警告: TensorFlow不可用，使用基础音频分类")

try:
    # 暂时禁用PANNs导入
    # import panns_inference
    # from panns_inference import AudioTagging, SoundEventDetection, labels
    # HAS_PANNS = True
    print("信息: 为稳定性禁用PANNs，使用回退分类")
except ImportError:
    print("警告: PANNs不可用，使用回退分类")

class AudioClassifier:
    """音频分类器，集成多种模型"""
    
    def __init__(self):
        """初始化音频分类器"""
        self.yamnet_model = None
        self.panns_model = None
        self.class_names = []
        self.initialized = False
        
        # 检查PANNs可用性
        panns_available = HAS_PANNS
        
        # 尝试加载PANNs模型（优先）
        if panns_available:
            try:
                self._load_panns_model()
                print("PANNs音频分类模型加载成功")
            except Exception as e:
                print(f"PANNs模型加载失败: {e}")
                panns_available = False
        
        # 如果PANNs不可用，尝试YAMNet
        if not panns_available and HAS_TENSORFLOW:
            try:
                self._load_yamnet_model()
                print("YAMNet音频分类模型加载成功")
            except Exception as e:
                print(f"YAMNet模型加载失败: {e}")
                self._setup_fallback_classifier()
        else:
            self._setup_fallback_classifier()
        
        self.initialized = True
    
    def _load_panns_model(self):
        """加载PANNs模型"""
        # 初始化PANNs音频标记模型
        self.panns_model = AudioTagging(checkpoint_path=None, device='cpu')
        
        # PANNs使用AudioSet标签
        self.class_names = [
            "水声", "溪流", "船只", "机动船", "帆船", 
            "鸟类", "鸟鸣", "啁啾", "鸟叫",
            "风声", "风噪", "微风",
            "人声", "对话", "叙述",
            "音乐", "乐器", "歌唱",
            "车辆", "汽车", "交通",
            "自然", "环境音", "安静"
        ]
        self.model_type = "panns"
    
    def _load_yamnet_model(self):
        """加载YAMNet模型"""
        # 加载预训练的YAMNet模型
        self.yamnet_model = hub.load('https://tfhub.dev/google/yamnet/1')
        
        # 加载类别名称
        class_map_path = tf.keras.utils.get_file(
            'yamnet_class_map.csv',
            'https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv'
        )
        
        with open(class_map_path) as f:
            lines = f.readlines()
            self.class_names = [line.split(',')[2].strip().strip('"') for line in lines[1:]]
        
        self.model_type = "yamnet"
    
    def _setup_fallback_classifier(self):
        """设置回退分类器"""
        print("使用基础音频分类器")
        self.class_names = [
            "水声", "船只", "鸟鸣", "风声", "人声", 
            "音乐", "车辆", "自然", "安静", "未知"
        ]
        self.model_type = "fallback"
    
    def classify_audio(self, audio_data: np.ndarray, sample_rate: int = 32000) -> Dict[str, float]:
        """分类音频数据"""
        if not self.initialized:
            return {"未知": 1.0}
        
        try:
            # 优先使用增强分类器
            if hasattr(self, 'enhanced_classifier') and self.enhanced_classifier is not None:
                classifications = self.enhanced_classifier.classify_audio(audio_data)
                if classifications:
                    # 转换为兼容格式
                    result = {}
                    for cls in classifications[:3]:  # 取前3个结果
                        result[cls.class_name] = cls.confidence
                    return result
            
            # 回退到传统分类器
            if hasattr(self, 'panns_model') and self.panns_model is not None:
                return self._classify_with_panns(audio_data, sample_rate)
            elif hasattr(self, 'yamnet_model') and self.yamnet_model is not None:
                return self._classify_with_yamnet(audio_data, sample_rate)
            else:
                return self._classify_with_fallback(audio_data, sample_rate)
        except Exception as e:
            print(f"音频分类错误: {e}")
            return {"未知": 1.0}
    
    def _classify_with_panns(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """使用PANNs进行分类"""
        # PANNs需要32kHz采样率
        if sample_rate != 32000:
            audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=32000)
        
        # 确保音频长度合适（至少1秒）
        if len(audio_data) < 32000:
            audio_data = np.pad(audio_data, (0, 32000 - len(audio_data)))
        
        # PANNs需要batch维度
        audio_batch = audio_data[None, :]  # (1, samples)
        
        # 运行推理
        (clipwise_output, embedding) = self.panns_model.inference(audio_batch)
        
        # 获取前10个预测结果
        top_indices = np.argsort(clipwise_output[0])[-10:][::-1]
        
        result = {}
        for i in top_indices:
            if i < len(labels):
                class_name = labels[i]
                score = float(clipwise_output[0][i])
                
                # 映射到我们关心的类别
                mapped_class = self._map_panns_class(class_name)
                if mapped_class in result:
                    result[mapped_class] = max(result[mapped_class], score)
                else:
                    result[mapped_class] = score
        
        return result
    
    def _classify_with_yamnet(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """使用YAMNet进行分类"""
        # 重采样到16kHz（YAMNet要求）
        if sample_rate != 16000:
            audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=16000)
        
        # 确保音频长度合适
        if len(audio_data) < 16000:  # 至少1秒
            audio_data = np.pad(audio_data, (0, 16000 - len(audio_data)))
        
        # 转换为TensorFlow张量
        waveform = tf.convert_to_tensor(audio_data, dtype=tf.float32)
        
        # 运行模型
        scores, embeddings, spectrogram = self.yamnet_model(waveform)
        
        # 获取平均分数
        mean_scores = tf.reduce_mean(scores, axis=0)
        
        # 获取前10个类别
        top_indices = tf.nn.top_k(mean_scores, k=10).indices
        
        result = {}
        for i in top_indices:
            class_name = self.class_names[i]
            score = float(mean_scores[i])
            
            # 映射到我们关心的类别
            mapped_class = self._map_yamnet_class(class_name)
            if mapped_class in result:
                result[mapped_class] = max(result[mapped_class], score)
            else:
                result[mapped_class] = score
        
        return result
    
    def _classify_with_fallback(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """使用基础方法进行分类"""
        # 计算基础音频特征
        rms = np.sqrt(np.mean(audio_data**2))
        zcr = librosa.feature.zero_crossing_rate(audio_data)[0].mean()
        
        # 频谱特征
        stft = librosa.stft(audio_data)
        magnitude = np.abs(stft)
        
        # 频率分布
        freq_bins = magnitude.shape[0]
        low_freq = np.mean(magnitude[:freq_bins//4])
        mid_freq = np.mean(magnitude[freq_bins//4:3*freq_bins//4])
        high_freq = np.mean(magnitude[3*freq_bins//4:])
        
        # 基于特征的简单分类
        result = {}
        
        if rms < 0.01:
            result["安静"] = 0.8
        elif low_freq > mid_freq and low_freq > high_freq:
            if zcr < 0.1:
                result["水声"] = 0.6
                result["船只"] = 0.3
            else:
                result["车辆"] = 0.5
        elif high_freq > mid_freq and high_freq > low_freq:
            result["鸟鸣"] = 0.7
            result["风声"] = 0.2
        else:
            result["自然"] = 0.5
            result["未知"] = 0.3
        
        # 归一化
        total = sum(result.values())
        if total > 0:
            result = {k: v/total for k, v in result.items()}
        
        return result
    
    def _map_panns_class(self, panns_class: str) -> str:
        """将PANNs类别映射到我们的类别"""
        panns_class_lower = panns_class.lower()
        
        if any(word in panns_class_lower for word in ['water', 'stream', 'river', 'flow']):
            return "水声"
        elif any(word in panns_class_lower for word in ['boat', 'ship', 'motor']):
            return "船只"
        elif any(word in panns_class_lower for word in ['bird', 'chirp', 'tweet', 'sing']):
            return "鸟鸣"
        elif any(word in panns_class_lower for word in ['wind', 'breeze', 'air']):
            return "风声"
        elif any(word in panns_class_lower for word in ['speech', 'voice', 'talk', 'conversation']):
            return "人声"
        elif any(word in panns_class_lower for word in ['music', 'instrument', 'song']):
            return "音乐"
        elif any(word in panns_class_lower for word in ['car', 'vehicle', 'traffic', 'engine']):
            return "车辆"
        elif any(word in panns_class_lower for word in ['nature', 'outdoor', 'ambient']):
            return "自然"
        elif any(word in panns_class_lower for word in ['silence', 'quiet']):
            return "安静"
        else:
            return "未知"
    
    def _map_yamnet_class(self, yamnet_class: str) -> str:
        """将YAMNet类别映射到我们的类别"""
        yamnet_class_lower = yamnet_class.lower()
        
        if any(word in yamnet_class_lower for word in ['water', 'stream', 'river', 'flow', 'splash']):
            return "水声"
        elif any(word in yamnet_class_lower for word in ['boat', 'ship', 'motor', 'engine']):
            return "船只"
        elif any(word in yamnet_class_lower for word in ['bird', 'chirp', 'tweet', 'sing']):
            return "鸟鸣"
        elif any(word in yamnet_class_lower for word in ['wind', 'breeze', 'air']):
            return "风声"
        elif any(word in yamnet_class_lower for word in ['speech', 'voice', 'talk', 'conversation']):
            return "人声"
        elif any(word in yamnet_class_lower for word in ['music', 'instrument', 'song']):
            return "音乐"
        elif any(word in yamnet_class_lower for word in ['car', 'vehicle', 'traffic']):
            return "车辆"
        elif any(word in yamnet_class_lower for word in ['nature', 'outdoor', 'ambient']):
            return "自然"
        elif any(word in yamnet_class_lower for word in ['silence', 'quiet']):
            return "安静"
        else:
            return "未知"

class RealtimeAudioVisualizer:
    """实时音频可视化器"""
    
    def __init__(self, width: int, height: int):
        """初始化实时音频可视化器"""
        self.width = width
        self.height = height
        
        # 字体加载（优先使用墨趣古风体）
        pygame.font.init()
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
                self.font_large = pygame.font.Font(font_path, 36)
                self.font_medium = pygame.font.Font(font_path, 24)
                self.font_small = pygame.font.Font(font_path, 18)
                print(f"音频可视化字体加载成功: {font_path}")
                break
            except:
                continue
        
        if not self.font_large:
            try:
                self.font_large = pygame.font.Font("墨趣古风体.ttf", 36)
                self.font_medium = pygame.font.Font("墨趣古风体.ttf", 24)
                self.font_small = pygame.font.Font("墨趣古风体.ttf", 18)
            except:
                self.font_large = pygame.font.Font(None, 36)
                self.font_medium = pygame.font.Font(None, 24)
                self.font_small = pygame.font.Font(None, 18)
            print("音频可视化使用默认字体")
        
        # 频谱分析参数
        self.window_size = 1024
        self.overlap = 0.5
        self.sample_rate = 32000
        
        # 频谱数据
        self.spectrum_data = None
        self.spectrum_history = []
        self.max_history = 50
        
        # 可视化参数
        self.bar_count = 64
        self.bar_width = self.width // self.bar_count
        self.max_bar_height = self.height // 3
        
        # 颜色渐变
        self.colors = self._generate_color_gradient()
        
        # 平滑参数
        self.smoothing_factor = 0.8
        self.previous_spectrum = None
        
        # 音频分类器
        try:
            from enhanced_sound_classifier import EnhancedSoundClassifier
            self.classifier = EnhancedSoundClassifier()
            self.classification_results = {}
            print("音频分类器初始化成功")
        except ImportError:
            self.classifier = None
            self.classification_results = {}
            print("音频分类器不可用")
        
        # 性能优化
        self.frame_count = 0
        self.update_interval = 2  # 每2帧更新一次分类
    
    def _generate_color_gradient(self) -> List[Tuple[int, int, int]]:
        """生成颜色渐变"""
        colors = []
        # 从深蓝到浅蓝到绿到黄到红的渐变
        for i in range(self.bar_count):
            ratio = i / (self.bar_count - 1)
            if ratio < 0.25:
                # 深蓝到浅蓝
                r = int(0 + ratio * 4 * 50)
                g = int(50 + ratio * 4 * 100)
                b = int(150 + ratio * 4 * 105)
            elif ratio < 0.5:
                # 浅蓝到绿
                local_ratio = (ratio - 0.25) * 4
                r = int(50 - local_ratio * 50)
                g = int(150 + local_ratio * 105)
                b = int(255 - local_ratio * 155)
            elif ratio < 0.75:
                # 绿到黄
                local_ratio = (ratio - 0.5) * 4
                r = int(0 + local_ratio * 255)
                g = int(255)
                b = int(100 - local_ratio * 100)
            else:
                # 黄到红
                local_ratio = (ratio - 0.75) * 4
                r = int(255)
                g = int(255 - local_ratio * 255)
                b = int(0)
            
            colors.append((min(255, max(0, r)), min(255, max(0, g)), min(255, max(0, b))))
        
        return colors
    
    def update(self, audio_data: np.ndarray):
        """更新音频数据"""
        if audio_data is None or len(audio_data) == 0:
            return
        
        try:
            # 更新波形历史
            self.waveform_history.extend(audio_data[-100:])  # 保留最后100个样本
            
            # 计算频谱
            if len(audio_data) >= self.fft_size:
                spectrum = self._compute_spectrum(audio_data)
                self.spectrum_history.append(spectrum)
            
            # 音频分类（每隔几帧进行一次，避免过于频繁）
            if len(self.spectrum_history) % 10 == 0:
                classification = self.classifier.classify_audio(audio_data, self.sample_rate)
                self.classification_history.append(classification)
                
        except Exception as e:
            print(f"音频可视化更新错误: {e}")
    
    def _compute_spectrum(self, audio_data: np.ndarray) -> np.ndarray:
        """计算音频频谱"""
        try:
            # 调整参数以适应音频长度
            n_fft = min(self.fft_size, len(audio_data))
            if n_fft < 512:
                n_fft = 512
            
            # 使用梅尔频谱
            mel_spec = librosa.feature.melspectrogram(
                y=audio_data,
                sr=self.sample_rate,
                n_fft=n_fft,
                hop_length=self.hop_length,
                n_mels=self.n_mels
            )
            
            # 转换为dB
            mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
            
            # 取平均值
            return np.mean(mel_spec_db, axis=1)
        except Exception as e:
            print(f"频谱计算错误: {e}")
            return np.zeros(self.n_mels)
    
    def render(self, screen: pygame.Surface):
        """渲染可视化效果"""
        # 创建半透明覆盖层
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # 渲染频谱图
        self._render_spectrum(overlay)
        
        # 渲染波形
        self._render_waveform(overlay)
        
        # 渲染分类结果
        self._render_classification(overlay)
        
        # 渲染实时指标
        self._render_metrics(overlay)
        
        # 混合到主屏幕
        screen.blit(overlay, (0, 0))
    
    def _render_spectrum(self, surface: pygame.Surface):
        """渲染频谱图 - 优化颜色和位置"""
        if not self.spectrum_history:
            return
        
        # 频谱瀑布图 - 调整位置避免左下角突兀
        spectrum_width = min(len(self.spectrum_history), self.width // 6)  # 减小宽度
        spectrum_height = self.height // 4  # 减小高度
        
        # 调整位置，避免左下角
        start_x = self.width // 4  # 从1/4处开始，避免左下角
        
        for i, spectrum in enumerate(list(self.spectrum_history)[-spectrum_width:]):
            x = start_x + i
            
            for j, magnitude in enumerate(spectrum):
                # 归一化幅度
                normalized_mag = (magnitude + 80) / 80  # -80dB到0dB
                normalized_mag = max(0, min(1, normalized_mag))
                
                # 过滤低幅度噪声
                if normalized_mag < 0.15:
                    continue
                
                # 使用更柔和的颜色，减少蓝色成分
                intensity = int(normalized_mag * 180)  # 降低整体强度
                color = (intensity // 4, intensity // 3, intensity // 2)  # 减少蓝色比重
                
                # 绘制像素
                y = int(j * spectrum_height / len(spectrum))
                if 0 <= y < spectrum_height:
                    pygame.draw.rect(surface, color, (x, y, 1, 1))  # 减小像素大小
    
    def _render_waveform(self, surface: pygame.Surface):
        """渲染波形"""
        if not self.waveform_history:
            return
        
        waveform_data = list(self.waveform_history)[-self.width//2:]  # 最近的数据
        
        if len(waveform_data) < 2:
            return
        
        # 波形显示区域
        waveform_y = self.height - 150
        waveform_height = 100
        
        # 绘制波形
        points = []
        for i, sample in enumerate(waveform_data):
            x = i * (self.width // 2) // len(waveform_data)
            y = waveform_y + int(sample * waveform_height / 2)
            y = max(waveform_y - waveform_height//2, min(waveform_y + waveform_height//2, y))
            points.append((x, y))
        
        if len(points) > 1:
            pygame.draw.lines(surface, (100, 200, 255), False, points, 2)
        
        # 绘制波形背景
        pygame.draw.rect(surface, (20, 20, 40, 100), 
                        (0, waveform_y - waveform_height//2, self.width//2, waveform_height))
    
    def _render_classification(self, surface: pygame.Surface):
        """渲染分类结果"""
        if not self.classification_history:
            return
        
        # 获取最新分类结果
        latest_classification = self.classification_history[-1]
        
        # 分类结果显示区域
        class_x = self.width - 300
        class_y = 50
        class_width = 250
        
        # 背景
        pygame.draw.rect(surface, (0, 0, 0, 150), 
                        (class_x, class_y, class_width, 200))
        
        # 标题
        try:
            font = pygame.font.Font("墨趣古风体.ttf", 24)
        except:
            font = pygame.font.Font(None, 24)
        model_type = getattr(self.classifier, 'model_type', 'fallback')
        title_text = f"声音分类 ({model_type.upper()})"
        title_surface = font.render(title_text, True, (255, 255, 255))
        surface.blit(title_surface, (class_x + 10, class_y + 10))
        
        # 分类结果条形图
        y_offset = class_y + 40
        bar_height = 20
        
        # 按分数排序
        sorted_classes = sorted(latest_classification.items(), key=lambda x: x[1], reverse=True)
        
        for i, (class_name, score) in enumerate(sorted_classes[:5]):
            # 条形图
            bar_width = int(score * (class_width - 20))
            color = self.colors.get(class_name, (128, 128, 128))
            
            pygame.draw.rect(surface, color, 
                           (class_x + 10, y_offset, bar_width, bar_height))
            
            # 文字标签
            try:
                label_font = pygame.font.Font("墨趣古风体.ttf", 18)
            except:
                label_font = pygame.font.Font(None, 18)
            label_text = f"{class_name}: {score:.2f}"
            text_surface = label_font.render(label_text, True, (255, 255, 255))
            surface.blit(text_surface, (class_x + 15, y_offset + 2))
            
            y_offset += bar_height + 5
    
    def _render_classification_overlay(self, surface: pygame.Surface):
        """渲染分类结果覆盖层"""
        if not self.classification_results:
            return
        
        # 背景半透明面板
        overlay = pygame.Surface((300, 200))
        overlay.set_alpha(180)
        overlay.fill((20, 20, 30))
        surface.blit(overlay, (self.width - 320, 20))
        
        # 标题
        title_surface = self.font_medium.render("声音分类", True, (255, 255, 255))
        surface.blit(title_surface, (self.width - 310, 30))
        
        # 分类结果
        y_offset = 60
        for class_name, score in sorted(self.classification_results.items(), 
                                      key=lambda x: x[1], reverse=True)[:5]:
            # 分类条
            bar_width = int(score * 200)
            bar_rect = pygame.Rect(self.width - 310, y_offset, bar_width, 20)
            
            # 根据分类类型选择颜色
            if class_name in ['水声', 'water']:
                color = (100, 150, 200)
            elif class_name in ['船只', 'boat']:
                color = (150, 100, 50)
            elif class_name in ['鸟鸣', 'bird']:
                color = (200, 200, 100)
            else:
                color = (128, 128, 128)
            
            pygame.draw.rect(surface, color, bar_rect)
            pygame.draw.rect(surface, (255, 255, 255), bar_rect, 1)
            
            # 标签
            label_text = f"{class_name}: {score:.2f}"
            text_surface = self.font_small.render(label_text, True, (255, 255, 255))
            surface.blit(text_surface, (self.width - 305, y_offset + 2))
            
            y_offset += 25
    
    def _render_metrics(self, surface: pygame.Surface):
        """渲染实时指标"""
        if not self.waveform_history:
            return
        
        # 计算实时指标
        recent_data = np.array(list(self.waveform_history)[-1000:])
        
        rms = np.sqrt(np.mean(recent_data**2))
        peak = np.max(np.abs(recent_data))
        zcr = np.mean(np.diff(np.signbit(recent_data)))
        
        # 指标显示
        metrics_x = 20
        metrics_y = 20
        
        try:
            font = pygame.font.Font("墨趣古风体.ttf", 20)
        except:
            font = pygame.font.Font(None, 20)
        
        metrics = [
            f"有效值: {rms:.4f}",
            f"峰值: {peak:.4f}",
            f"过零率: {zcr:.4f}",
            f"样本数: {len(self.waveform_history)}"
        ]
        
        for i, metric in enumerate(metrics):
            text_surface = font.render(metric, True, (255, 255, 255))
            # 添加背景
            text_rect = text_surface.get_rect()
            pygame.draw.rect(surface, (0, 0, 0, 150), 
                           (metrics_x - 5, metrics_y + i * 25 - 2, text_rect.width + 10, text_rect.height + 4))
            surface.blit(text_surface, (metrics_x, metrics_y + i * 25))
    
    def get_dominant_class(self) -> str:
        """获取主导声音类别"""
        if not self.classification_history:
            return "未知"
        
        # 统计最近的分类结果
        class_scores = {}
        for classification in list(self.classification_history)[-10:]:  # 最近10次
            for class_name, score in classification.items():
                if class_name not in class_scores:
                    class_scores[class_name] = []
                class_scores[class_name].append(score)
        
        # 计算平均分数
        avg_scores = {k: np.mean(v) for k, v in class_scores.items()}
        
        # 返回最高分数的类别
        return max(avg_scores.items(), key=lambda x: x[1])[0] if avg_scores else "未知"
    
    def get_classification_confidence(self) -> float:
        """获取分类置信度"""
        if not self.classification_history:
            return 0.0
        
        latest = self.classification_history[-1]
        if not latest:
            return 0.0
        
        # 返回最高分数作为置信度
        return max(latest.values())

# 测试代码
if __name__ == "__main__":
    # 测试实时音频可视化器
    pygame.init()
    
    width, height = 1280, 720
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("实时音频可视化测试")
    
    visualizer = RealtimeAudioVisualizer(width, height)
    
    # 生成测试音频数据
    sample_rate = 32000
    duration = 0.1  # 100ms
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    clock = pygame.time.Clock()
    running = True
    
    print("实时音频可视化测试启动")
    print("按ESC退出")
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # 生成测试音频（模拟不同类型的声音）
        freq = 440 + 200 * math.sin(time.time())  # 变化的频率
        test_audio = 0.1 * np.sin(2 * np.pi * freq * t)
        
        # 添加噪声
        test_audio += 0.05 * np.random.normal(0, 1, len(test_audio))
        
        # 更新可视化器
        visualizer.update(test_audio)
        
        # 清屏
        screen.fill((20, 20, 30))
        
        # 渲染可视化
        visualizer.render(screen)
        
        # 显示主导类别
        try:
            font = pygame.font.Font("墨趣古风体.ttf", 36)
        except:
            font = pygame.font.Font(None, 36)
        dominant_class = visualizer.get_dominant_class()
        confidence = visualizer.get_classification_confidence()
        
        class_text = font.render(f"主导声音: {dominant_class} ({confidence:.2f})", True, (255, 255, 255))
        screen.blit(class_text, (width // 2 - 150, height - 50))
        
        pygame.display.flip()
        clock.tick(30)  # 30 FPS
    
    pygame.quit()
    print("测试完成")