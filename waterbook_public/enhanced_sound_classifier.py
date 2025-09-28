#!/usr/bin/env python3
"""
增强声音分类器
集成多种先进的音频分类模型，包括SoundMind、YAMNet等
专门针对运河环境声音进行优化
"""

import numpy as np
import librosa
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from collections import deque
import threading
import json

# 尝试导入深度学习框架
# 暂时禁用深度学习框架以避免段错误
TF_AVAILABLE = False
TORCH_AVAILABLE = False
print("深度学习框架已禁用，使用传统分类方法")

# try:
#     import tensorflow as tf
#     import tensorflow_hub as hub
#     TF_AVAILABLE = True
#     print("TensorFlow已加载，深度学习分类器可用")
# except ImportError:
#     TF_AVAILABLE = False
#     print("TensorFlow不可用，将使用传统分类方法")

# try:
#     import torch
#     import torchaudio
#     TORCH_AVAILABLE = True
#     print("PyTorch已加载，可使用更多预训练模型")
# except ImportError:
#     TORCH_AVAILABLE = False
#     print("PyTorch不可用")

@dataclass
class SoundClassification:
    """声音分类结果"""
    class_name: str
    confidence: float
    category: str  # 'water', 'boat', 'bird', 'wind', 'human', 'music', 'nature', 'quiet', 'unknown'
    subcategory: str  # 更细分的类别
    features: Dict[str, float]  # 相关特征
    timestamp: float

@dataclass
class ClassificationHistory:
    """分类历史记录"""
    classifications: deque
    confidence_trends: Dict[str, deque]
    category_stability: Dict[str, float]
    last_update: float

class EnhancedSoundClassifier:
    """增强声音分类器"""
    
    def __init__(self, sample_rate: int = 32000, buffer_size: int = 50):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        
        # 分类历史
        self.history = ClassificationHistory(
            classifications=deque(maxlen=buffer_size),
            confidence_trends={},
            category_stability={},
            last_update=0.0
        )
        
        # 模型状态
        self.models_loaded = False
        self.yamnet_model = None
        self.soundmind_model = None
        self.fallback_classifier = None
        
        # 运河环境特定的类别映射
        self.canal_categories = {
            'water': ['水流', '水声', '波浪', '水花', '滴水', '流水'],
            'boat': ['船只', '引擎', '马达', '螺旋桨', '汽笛', '船舶'],
            'bird': ['鸟鸣', '鸟叫', '鸟类', '啁啾', '鸣叫', '飞鸟'],
            'wind': ['风声', '微风', '大风', '呼啸', '风吹'],
            'human': ['人声', '说话', '脚步', '咳嗽', '笑声', '呼喊'],
            'music': ['音乐', '歌曲', '乐器', '旋律', '节拍'],
            'nature': ['自然', '环境', '昆虫', '树叶', '雨声'],
            'quiet': ['安静', '静音', '无声', '寂静'],
            'unknown': ['未知', '其他', '噪音', '杂音']
        }
        
        # 类别权重（针对运河环境优化）
        self.category_weights = {
            'water': 1.5,    # 水声在运河环境中更重要
            'boat': 1.3,     # 船只声音也很重要
            'bird': 1.2,     # 鸟鸣声常见
            'wind': 1.1,     # 风声
            'nature': 1.0,   # 自然声音
            'human': 0.8,    # 人声相对较少
            'music': 0.6,    # 音乐不太常见
            'quiet': 0.9,    # 安静状态
            'unknown': 0.5   # 未知声音权重最低
        }
        
        # 初始化分类器
        self._init_classifiers()
        
        # 特征提取器
        self.feature_extractor = CanalAudioFeatureExtractor(sample_rate)
        
        print("增强声音分类器初始化完成")
    
    def _init_classifiers(self):
        """初始化各种分类器"""
        # 初始化YAMNet
        if TF_AVAILABLE:
            self._init_yamnet()
        
        # 初始化SoundMind（如果可用）
        if TORCH_AVAILABLE:
            self._init_soundmind()
        
        # 初始化回退分类器
        self._init_fallback_classifier()
        
        self.models_loaded = True
    
    def _init_yamnet(self):
        """初始化YAMNet模型"""
        try:
            print("正在加载YAMNet模型...")
            self.yamnet_model = hub.load('https://tfhub.dev/google/yamnet/1')
            
            # 加载类别名称
            class_map_path = tf.keras.utils.get_file(
                'yamnet_class_map.csv',
                'https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv'
            )
            
            with open(class_map_path) as f:
                self.yamnet_class_names = [line.strip().split(',')[2] for line in f.readlines()[1:]]
            
            print("YAMNet模型加载成功")
            
        except Exception as e:
            print(f"YAMNet模型加载失败: {e}")
            self.yamnet_model = None
    
    def _init_soundmind(self):
        """初始化SoundMind模型"""
        try:
            print("正在尝试加载SoundMind模型...")
            # 这里可以集成SoundMind或其他PyTorch音频分类模型
            # 由于SoundMind可能需要特定的安装，这里提供框架
            
            # 示例：使用预训练的音频分类模型
            # self.soundmind_model = torch.hub.load('pytorch/vision', 'resnet18', pretrained=True)
            
            print("SoundMind模型暂未集成，使用其他分类器")
            self.soundmind_model = None
            
        except Exception as e:
            print(f"SoundMind模型加载失败: {e}")
            self.soundmind_model = None
    
    def _init_fallback_classifier(self):
        """初始化回退分类器"""
        self.fallback_classifier = TraditionalAudioClassifier(self.sample_rate)
        print("传统音频分类器已初始化")
    
    def classify_audio(self, audio_data: np.ndarray) -> List[SoundClassification]:
        """对音频进行分类"""
        if not self.models_loaded or len(audio_data) == 0:
            return [SoundClassification(
                class_name="未知",
                confidence=0.0,
                category="unknown",
                subcategory="empty",
                features={},
                timestamp=time.time()
            )]
        
        classifications = []
        current_time = time.time()
        
        # 提取音频特征
        features = self.feature_extractor.extract_features(audio_data)
        
        # 使用多个分类器进行分类
        if self.yamnet_model is not None:
            yamnet_results = self._classify_with_yamnet(audio_data, features)
            classifications.extend(yamnet_results)
        
        if self.soundmind_model is not None:
            soundmind_results = self._classify_with_soundmind(audio_data, features)
            classifications.extend(soundmind_results)
        
        # 使用回退分类器
        fallback_results = self._classify_with_fallback(audio_data, features)
        classifications.extend(fallback_results)
        
        # 融合分类结果
        fused_results = self._fuse_classifications(classifications)
        
        # 更新历史记录
        self._update_history(fused_results, current_time)
        
        return fused_results
    
    def _classify_with_yamnet(self, audio_data: np.ndarray, features: Dict) -> List[SoundClassification]:
        """使用YAMNet进行分类"""
        try:
            # 重采样到16kHz（YAMNet要求）
            if self.sample_rate != 16000:
                audio_16k = librosa.resample(audio_data, orig_sr=self.sample_rate, target_sr=16000)
            else:
                audio_16k = audio_data.copy()
            
            # 确保音频长度合适
            if len(audio_16k) < 16000:  # 至少1秒
                audio_16k = np.pad(audio_16k, (0, 16000 - len(audio_16k)))
            elif len(audio_16k) > 16000 * 10:  # 最多10秒
                audio_16k = audio_16k[:16000 * 10]
            
            # 转换为TensorFlow张量
            waveform = tf.convert_to_tensor(audio_16k, dtype=tf.float32)
            
            # 运行YAMNet
            scores, embeddings, spectrogram = self.yamnet_model(waveform)
            
            # 获取平均分数
            mean_scores = tf.reduce_mean(scores, axis=0)
            
            # 获取前10个类别
            top_indices = tf.nn.top_k(mean_scores, k=10).indices.numpy()
            
            results = []
            for idx in top_indices:
                class_name = self.yamnet_class_names[idx]
                confidence = float(mean_scores[idx])
                
                # 映射到运河环境类别
                category, subcategory = self._map_to_canal_category(class_name)
                
                # 应用运河环境权重
                weighted_confidence = confidence * self.category_weights.get(category, 1.0)
                
                results.append(SoundClassification(
                    class_name=class_name,
                    confidence=weighted_confidence,
                    category=category,
                    subcategory=subcategory,
                    features=features,
                    timestamp=time.time()
                ))
            
            return results
            
        except Exception as e:
            print(f"YAMNet分类错误: {e}")
            return []
    
    def _classify_with_soundmind(self, audio_data: np.ndarray, features: Dict) -> List[SoundClassification]:
        """使用SoundMind进行分类"""
        # 这里可以实现SoundMind分类逻辑
        # 目前返回空列表，等待具体模型集成
        return []
    
    def _classify_with_fallback(self, audio_data: np.ndarray, features: Dict) -> List[SoundClassification]:
        """使用回退分类器进行分类"""
        try:
            results = self.fallback_classifier.classify(audio_data, features)
            return results
        except Exception as e:
            print(f"回退分类器错误: {e}")
            return []
    
    def _map_to_canal_category(self, class_name: str) -> Tuple[str, str]:
        """将分类结果映射到运河环境类别"""
        class_name_lower = class_name.lower()
        
        # 水相关
        water_keywords = ['water', 'stream', 'river', 'flow', 'splash', 'wave', 'drip', 'rain']
        if any(keyword in class_name_lower for keyword in water_keywords):
            return 'water', class_name
        
        # 船只相关
        boat_keywords = ['boat', 'ship', 'engine', 'motor', 'propeller', 'vessel', 'maritime']
        if any(keyword in class_name_lower for keyword in boat_keywords):
            return 'boat', class_name
        
        # 鸟类相关
        bird_keywords = ['bird', 'chirp', 'tweet', 'sing', 'call', 'crow', 'duck', 'seagull']
        if any(keyword in class_name_lower for keyword in bird_keywords):
            return 'bird', class_name
        
        # 风相关
        wind_keywords = ['wind', 'breeze', 'gust', 'air', 'blow']
        if any(keyword in class_name_lower for keyword in wind_keywords):
            return 'wind', class_name
        
        # 人声相关
        human_keywords = ['speech', 'voice', 'talk', 'human', 'conversation', 'footstep', 'walk']
        if any(keyword in class_name_lower for keyword in human_keywords):
            return 'human', class_name
        
        # 音乐相关
        music_keywords = ['music', 'song', 'instrument', 'melody', 'rhythm', 'beat']
        if any(keyword in class_name_lower for keyword in music_keywords):
            return 'music', class_name
        
        # 自然相关
        nature_keywords = ['nature', 'insect', 'leaf', 'tree', 'environment', 'outdoor']
        if any(keyword in class_name_lower for keyword in nature_keywords):
            return 'nature', class_name
        
        # 安静相关
        quiet_keywords = ['silence', 'quiet', 'still', 'calm']
        if any(keyword in class_name_lower for keyword in quiet_keywords):
            return 'quiet', class_name
        
        return 'unknown', class_name
    
    def _fuse_classifications(self, classifications: List[SoundClassification]) -> List[SoundClassification]:
        """融合多个分类器的结果"""
        if not classifications:
            return []
        
        # 按类别分组
        category_groups = {}
        for cls in classifications:
            if cls.category not in category_groups:
                category_groups[cls.category] = []
            category_groups[cls.category].append(cls)
        
        # 计算每个类别的融合置信度
        fused_results = []
        for category, cls_list in category_groups.items():
            # 计算加权平均置信度
            total_confidence = sum(cls.confidence for cls in cls_list)
            avg_confidence = total_confidence / len(cls_list)
            
            # 选择最佳代表
            best_cls = max(cls_list, key=lambda x: x.confidence)
            
            # 创建融合结果
            fused_cls = SoundClassification(
                class_name=best_cls.class_name,
                confidence=avg_confidence,
                category=category,
                subcategory=best_cls.subcategory,
                features=best_cls.features,
                timestamp=time.time()
            )
            
            fused_results.append(fused_cls)
        
        # 按置信度排序
        fused_results.sort(key=lambda x: x.confidence, reverse=True)
        
        return fused_results[:5]  # 返回前5个结果
    
    def _update_history(self, classifications: List[SoundClassification], timestamp: float):
        """更新分类历史"""
        self.history.classifications.extend(classifications)
        self.history.last_update = timestamp
        
        # 更新置信度趋势
        for cls in classifications:
            if cls.category not in self.history.confidence_trends:
                self.history.confidence_trends[cls.category] = deque(maxlen=self.buffer_size)
            self.history.confidence_trends[cls.category].append(cls.confidence)
        
        # 计算类别稳定性
        self._calculate_category_stability()
    
    def _calculate_category_stability(self):
        """计算类别稳定性"""
        for category, trend in self.history.confidence_trends.items():
            if len(trend) > 5:
                # 计算置信度的标准差，越小越稳定
                stability = 1.0 - (np.std(list(trend)) / (np.mean(list(trend)) + 1e-8))
                self.history.category_stability[category] = max(0, min(1, stability))
    
    def get_dominant_categories(self, top_k: int = 3) -> List[Tuple[str, float]]:
        """获取主导类别"""
        if not self.history.classifications:
            return []
        
        # 统计最近的分类结果
        recent_classifications = list(self.history.classifications)[-20:]  # 最近20个
        category_scores = {}
        
        for cls in recent_classifications:
            if cls.category not in category_scores:
                category_scores[cls.category] = []
            category_scores[cls.category].append(cls.confidence)
        
        # 计算每个类别的平均置信度
        category_avg = {}
        for category, scores in category_scores.items():
            avg_score = np.mean(scores)
            stability = self.history.category_stability.get(category, 0.5)
            # 结合置信度和稳定性
            final_score = avg_score * (0.7 + 0.3 * stability)
            category_avg[category] = final_score
        
        # 排序并返回前k个
        sorted_categories = sorted(category_avg.items(), key=lambda x: x[1], reverse=True)
        return sorted_categories[:top_k]
    
    def get_classification_summary(self) -> Dict:
        """获取分类摘要"""
        dominant_categories = self.get_dominant_categories()
        
        return {
            'dominant_categories': dominant_categories,
            'total_classifications': len(self.history.classifications),
            'category_stability': dict(self.history.category_stability),
            'last_update': self.history.last_update,
            'active_categories': len(self.history.confidence_trends)
        }

class CanalAudioFeatureExtractor:
    """运河音频特征提取器"""
    
    def __init__(self, sample_rate: int = 32000):
        self.sample_rate = sample_rate
    
    def extract_features(self, audio_data: np.ndarray) -> Dict[str, float]:
        """提取音频特征"""
        features = {}
        
        try:
            # 基础特征
            features['rms_energy'] = np.sqrt(np.mean(audio_data ** 2))
            features['zero_crossing_rate'] = np.mean(np.abs(np.diff(np.sign(audio_data)))) / 2
            
            # 频谱特征
            if len(audio_data) > 512:
                # 频谱质心
                stft = librosa.stft(audio_data, n_fft=512)
                magnitude = np.abs(stft)
                freqs = librosa.fft_frequencies(sr=self.sample_rate, n_fft=512)
                
                spectral_centroid = np.sum(freqs[:, np.newaxis] * magnitude, axis=0) / (np.sum(magnitude, axis=0) + 1e-10)
                features['spectral_centroid'] = np.mean(spectral_centroid)
                
                # 频谱带宽
                spectral_bandwidth = np.sqrt(
                    np.sum(((freqs[:, np.newaxis] - spectral_centroid) ** 2) * magnitude, axis=0) / 
                    (np.sum(magnitude, axis=0) + 1e-10)
                )
                features['spectral_bandwidth'] = np.mean(spectral_bandwidth)
                
                # 频带能量
                freq_bands = {
                    'low_energy': (20, 300),
                    'mid_energy': (300, 2000),
                    'high_energy': (2000, 8000)
                }
                
                for band_name, (f_min, f_max) in freq_bands.items():
                    band_mask = (freqs >= f_min) & (freqs <= f_max)
                    if np.any(band_mask):
                        band_energy = np.mean(magnitude[band_mask] ** 2)
                        features[band_name] = band_energy
                    else:
                        features[band_name] = 0.0
            
            # 运河特定特征
            features.update(self._extract_canal_features(audio_data))
            
        except Exception as e:
            print(f"特征提取错误: {e}")
            # 返回默认特征
            features = {
                'rms_energy': 0.0,
                'zero_crossing_rate': 0.0,
                'spectral_centroid': 1000.0,
                'spectral_bandwidth': 500.0,
                'low_energy': 0.0,
                'mid_energy': 0.0,
                'high_energy': 0.0
            }
        
        return features
    
    def _extract_canal_features(self, audio_data: np.ndarray) -> Dict[str, float]:
        """提取运河特定特征"""
        features = {}
        
        try:
            # FFT分析
            fft_result = np.fft.fft(audio_data[:min(4096, len(audio_data))])
            freqs = np.fft.fftfreq(len(fft_result), 1/self.sample_rate)
            magnitude = np.abs(fft_result)
            
            # 只取正频率
            positive_idx = freqs >= 0
            freqs = freqs[positive_idx]
            magnitude = magnitude[positive_idx]
            
            # 水流特征 (50-500 Hz)
            water_mask = (freqs >= 50) & (freqs <= 500)
            features['water_flow_indicator'] = np.mean(magnitude[water_mask]) if np.any(water_mask) else 0.0
            
            # 船只特征 (100-1000 Hz)
            boat_mask = (freqs >= 100) & (freqs <= 1000)
            features['boat_activity_indicator'] = np.mean(magnitude[boat_mask]) if np.any(boat_mask) else 0.0
            
            # 鸟鸣特征 (1000-8000 Hz)
            bird_mask = (freqs >= 1000) & (freqs <= 8000)
            features['bird_activity_indicator'] = np.mean(magnitude[bird_mask]) if np.any(bird_mask) else 0.0
            
            # 风声特征 (20-200 Hz)
            wind_mask = (freqs >= 20) & (freqs <= 200)
            features['wind_indicator'] = np.mean(magnitude[wind_mask]) if np.any(wind_mask) else 0.0
            
        except Exception as e:
            print(f"运河特征提取错误: {e}")
            features = {
                'water_flow_indicator': 0.0,
                'boat_activity_indicator': 0.0,
                'bird_activity_indicator': 0.0,
                'wind_indicator': 0.0
            }
        
        return features

class TraditionalAudioClassifier:
    """传统音频分类器（回退方案）"""
    
    def __init__(self, sample_rate: int = 32000):
        self.sample_rate = sample_rate
    
    def classify(self, audio_data: np.ndarray, features: Dict) -> List[SoundClassification]:
        """使用传统方法进行分类"""
        results = []
        current_time = time.time()
        
        # 基于特征的规则分类
        rms = features.get('rms_energy', 0.0)
        zcr = features.get('zero_crossing_rate', 0.0)
        low_energy = features.get('low_energy', 0.0)
        mid_energy = features.get('mid_energy', 0.0)
        high_energy = features.get('high_energy', 0.0)
        
        # 水流声检测
        if low_energy > mid_energy and low_energy > high_energy and zcr < 0.1:
            confidence = min(0.8, low_energy * 2)
            results.append(SoundClassification(
                class_name="水流声",
                confidence=confidence,
                category="water",
                subcategory="流水",
                features=features,
                timestamp=current_time
            ))
        
        # 鸟鸣声检测
        if high_energy > mid_energy and high_energy > low_energy and zcr > 0.2:
            confidence = min(0.7, high_energy * 1.5)
            results.append(SoundClassification(
                class_name="鸟鸣声",
                confidence=confidence,
                category="bird",
                subcategory="鸟类",
                features=features,
                timestamp=current_time
            ))
        
        # 船只声检测
        if mid_energy > 0.3 and rms > 0.05:
            confidence = min(0.6, mid_energy * 1.2)
            results.append(SoundClassification(
                class_name="船只声",
                confidence=confidence,
                category="boat",
                subcategory="引擎",
                features=features,
                timestamp=current_time
            ))
        
        # 安静状态检测
        if rms < 0.01:
            results.append(SoundClassification(
                class_name="安静",
                confidence=0.8,
                category="quiet",
                subcategory="静音",
                features=features,
                timestamp=current_time
            ))
        
        # 如果没有明确分类，标记为未知
        if not results:
            results.append(SoundClassification(
                class_name="未知声音",
                confidence=0.3,
                category="unknown",
                subcategory="其他",
                features=features,
                timestamp=current_time
            ))
        
        return results

if __name__ == "__main__":
    # 测试代码
    print("增强声音分类器测试")
    
    classifier = EnhancedSoundClassifier()
    
    # 生成测试音频
    duration = 2.0
    sample_rate = 32000
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # 模拟水流声
    water_sound = 0.3 * np.sin(2 * np.pi * 200 * t) * (1 + 0.2 * np.sin(2 * np.pi * 5 * t))
    water_sound += 0.1 * np.random.normal(0, 1, len(t))
    
    print("\n测试水流声分类:")
    results = classifier.classify_audio(water_sound)
    for result in results:
        print(f"  {result.class_name}: {result.confidence:.3f} ({result.category})")
    
    # 模拟鸟鸣声
    bird_sound = 0.4 * np.sin(2 * np.pi * 3000 * t) * np.exp(-t * 2)
    bird_sound += 0.05 * np.random.normal(0, 1, len(t))
    
    print("\n测试鸟鸣声分类:")
    results = classifier.classify_audio(bird_sound)
    for result in results:
        print(f"  {result.class_name}: {result.confidence:.3f} ({result.category})")
    
    # 获取分类摘要
    print("\n分类摘要:")
    summary = classifier.get_classification_summary()
    print(f"  主导类别: {summary['dominant_categories']}")
    print(f"  总分类数: {summary['total_classifications']}")
    
    print("测试完成")