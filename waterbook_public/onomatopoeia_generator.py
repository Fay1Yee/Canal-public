#!/usr/bin/env python3
"""
拟声词生成模块
基于音频特征生成中文拟声词，专门针对运河环境声音
"""

import numpy as np
import librosa
import math
import random
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import deque

@dataclass
class OnomatopoeiaFeature:
    """拟声词特征数据类"""
    word: str                    # 拟声词
    confidence: float            # 置信度 (0-1)
    intensity: float             # 强度 (0-1)
    duration: float              # 持续时间
    frequency_range: Tuple[float, float]  # 频率范围
    pattern_type: str            # 模式类型
    visual_color: Tuple[int, int, int]  # 可视化颜色

class CanalOnomatopoeiaGenerator:
    """运河拟声词生成器"""
    
    def __init__(self, sample_rate: int = 32000):
        self.sample_rate = sample_rate
        self.window_size = 2048
        self.hop_length = 512
        
        # 运河环境拟声词库
        self.onomatopoeia_dict = {
            # 水声类
            'water_flow': {
                'words': ['潺潺', '汩汩', '淙淙', '涓涓', '哗哗', '咕噜', '滴答'],
                'freq_range': (50, 800),
                'pattern': 'continuous_flow',
                'color': (85, 115, 145),
                'intensity_map': {
                    (0.0, 0.2): ['涓涓', '滴答'],
                    (0.2, 0.5): ['潺潺', '淙淙'],
                    (0.5, 0.8): ['汩汩', '咕噜'],
                    (0.8, 1.0): ['哗哗']
                }
            },
            'water_splash': {
                'words': ['扑通', '哗啦', '噗嗤', '啪嗒', '溅溅', '泼啦', '咕咚'],
                'freq_range': (1000, 4000),
                'pattern': 'burst_splash',
                'color': (235, 240, 245),
                'intensity_map': {
                    (0.0, 0.3): ['啪嗒', '噗嗤'],
                    (0.3, 0.6): ['溅溅', '咕咚'],
                    (0.6, 0.9): ['哗啦', '泼啦'],
                    (0.9, 1.0): ['扑通']
                }
            },
            'water_bubble': {
                'words': ['咕嘟', '咕噜', '泡泡', '咕咚', '嘟嘟', '噗噗', '咕咕'],
                'freq_range': (100, 600),
                'pattern': 'bubble_pop',
                'color': (135, 155, 175),
                'intensity_map': {
                    (0.0, 0.4): ['嘟嘟', '噗噗'],
                    (0.4, 0.7): ['咕嘟', '泡泡'],
                    (0.7, 1.0): ['咕噜', '咕咚']
                }
            },
            
            # 船只类
            'boat_engine': {
                'words': ['突突', '轰轰', '嗡嗡', '咚咚', '噗噗', '哒哒', '嘟嘟'],
                'freq_range': (80, 300),
                'pattern': 'rhythmic_engine',
                'color': (85, 65, 55),
                'intensity_map': {
                    (0.0, 0.3): ['噗噗', '嘟嘟'],
                    (0.3, 0.6): ['突突', '哒哒'],
                    (0.6, 0.8): ['嗡嗡', '咚咚'],
                    (0.8, 1.0): ['轰轰']
                }
            },
            'boat_horn': {
                'words': ['嘟嘟', '呜呜', '嘀嘀', '哔哔', '嘟呜', '呜嘟', '嘀呜'],
                'freq_range': (200, 1000),
                'pattern': 'tonal_horn',
                'color': (180, 45, 35),
                'intensity_map': {
                    (0.0, 0.4): ['嘀嘀', '哔哔'],
                    (0.4, 0.7): ['嘟嘟', '嘀呜'],
                    (0.7, 1.0): ['呜呜', '嘟呜']
                }
            },
            'boat_paddle': {
                'words': ['啪啪', '扑扑', '拍拍', '咚咚', '噗噗', '哗哗', '咕咚'],
                'freq_range': (200, 1500),
                'pattern': 'rhythmic_paddle',
                'color': (115, 95, 85),
                'intensity_map': {
                    (0.0, 0.3): ['噗噗', '扑扑'],
                    (0.3, 0.6): ['啪啪', '拍拍'],
                    (0.6, 1.0): ['咚咚', '哗哗']
                }
            },
            
            # 自然环境类
            'bird_call': {
                'words': ['啾啾', '叽叽', '喳喳', '咕咕', '嘎嘎', '唧唧', '啁啁'],
                'freq_range': (2000, 8000),
                'pattern': 'melodic_bird',
                'color': (95, 125, 105),
                'intensity_map': {
                    (0.0, 0.3): ['唧唧', '啁啁'],
                    (0.3, 0.6): ['啾啾', '叽叽'],
                    (0.6, 0.9): ['喳喳', '咕咕'],
                    (0.9, 1.0): ['嘎嘎']
                }
            },
            'wind_sound': {
                'words': ['呼呼', '嗖嗖', '飕飕', '呜呜', '嘶嘶', '沙沙', '簌簌'],
                'freq_range': (100, 2000),
                'pattern': 'continuous_wind',
                'color': (200, 210, 220),
                'intensity_map': {
                    (0.0, 0.2): ['簌簌', '沙沙'],
                    (0.2, 0.5): ['嘶嘶', '飕飕'],
                    (0.5, 0.8): ['嗖嗖', '呜呜'],
                    (0.8, 1.0): ['呼呼']
                }
            },
            'tree_rustle': {
                'words': ['沙沙', '簌簌', '哗哗', '飒飒', '瑟瑟', '萧萧', '飘飘'],
                'freq_range': (500, 3000),
                'pattern': 'rustle_leaves',
                'color': (75, 95, 65),
                'intensity_map': {
                    (0.0, 0.3): ['簌簌', '飘飘'],
                    (0.3, 0.6): ['沙沙', '瑟瑟'],
                    (0.6, 0.9): ['飒飒', '萧萧'],
                    (0.9, 1.0): ['哗哗']
                }
            },
            
            # 人文环境类
            'footsteps': {
                'words': ['咚咚', '踏踏', '啪啪', '嗒嗒', '咔咔', '噔噔', '蹬蹬'],
                'freq_range': (60, 500),
                'pattern': 'rhythmic_steps',
                'color': (100, 95, 90),
                'intensity_map': {
                    (0.0, 0.3): ['嗒嗒', '踏踏'],
                    (0.3, 0.6): ['咚咚', '噔噔'],
                    (0.6, 1.0): ['啪啪', '蹬蹬']
                }
            },
            'voice_human': {
                'words': ['嗯嗯', '啊啊', '哦哦', '呃呃', '唔唔', '嘿嘿', '哈哈'],
                'freq_range': (85, 2000),
                'pattern': 'human_voice',
                'color': (70, 70, 70),
                'intensity_map': {
                    (0.0, 0.3): ['嗯嗯', '唔唔'],
                    (0.3, 0.6): ['啊啊', '哦哦'],
                    (0.6, 1.0): ['嘿嘿', '哈哈']
                }
            },
            'bridge_creak': {
                'words': ['吱吱', '嘎嘎', '咯咯', '咔咔', '嘎吱', '咯吱', '嘎咯'],
                'freq_range': (300, 1500),
                'pattern': 'creaking_wood',
                'color': (85, 65, 55),
                'intensity_map': {
                    (0.0, 0.4): ['吱吱', '咯咯'],
                    (0.4, 0.7): ['嘎嘎', '咔咔'],
                    (0.7, 1.0): ['嘎吱', '咯吱']
                }
            }
        }
        
        # 拟声词历史记录
        self.onomatopoeia_history = deque(maxlen=50)
        self.current_words = {}
        
        # 组合规则
        self.combination_rules = {
            'water_flow': {
                'repetition': ['潺潺潺', '汩汩汩', '哗哗哗'],
                'variation': ['潺潺汩汩', '汩汩哗哗', '淙淙潺潺']
            },
            'boat_engine': {
                'repetition': ['突突突', '轰轰轰', '嗡嗡嗡'],
                'variation': ['突突轰轰', '嗡嗡突突', '咚咚突突']
            },
            'bird_call': {
                'repetition': ['啾啾啾', '叽叽叽', '喳喳喳'],
                'variation': ['啾叽啾', '喳啾喳', '叽喳叽']
            }
        }
    
    def generate_onomatopoeia(self, audio_data: np.ndarray) -> List[OnomatopoeiaFeature]:
        """生成拟声词"""
        if len(audio_data) == 0:
            return []
        
        try:
            # 计算频谱特征
            stft = librosa.stft(audio_data, n_fft=self.window_size, hop_length=self.hop_length)
            magnitude = np.abs(stft)
            freqs = librosa.fft_frequencies(sr=self.sample_rate, n_fft=self.window_size)
            
            # 计算音频特征
            audio_features = self._extract_audio_features(magnitude, freqs)
            
            # 生成拟声词
            generated_words = []
            
            for sound_type, sound_info in self.onomatopoeia_dict.items():
                feature = self._generate_single_onomatopoeia(
                    audio_features, sound_type, sound_info
                )
                if feature.confidence > 0.15:  # 只保留置信度较高的拟声词
                    generated_words.append(feature)
            
            # 应用组合规则
            enhanced_words = self._apply_combination_rules(generated_words, audio_features)
            
            # 更新历史记录
            self.onomatopoeia_history.append(enhanced_words)
            self.current_words = {word.word: word for word in enhanced_words}
            
            return enhanced_words
            
        except Exception as e:
            print(f"拟声词生成错误: {e}")
            return []
    
    def _extract_audio_features(self, magnitude: np.ndarray, freqs: np.ndarray) -> Dict:
        """提取音频特征"""
        features = {}
        
        # 总能量
        features['total_energy'] = np.mean(magnitude ** 2)
        
        # 频谱质心
        spectral_centroid = np.sum(freqs[:, np.newaxis] * magnitude, axis=0) / (np.sum(magnitude, axis=0) + 1e-10)
        features['spectral_centroid'] = np.mean(spectral_centroid)
        
        # 频谱带宽
        spectral_bandwidth = np.sqrt(
            np.sum(((freqs[:, np.newaxis] - spectral_centroid) ** 2) * magnitude, axis=0) / 
            (np.sum(magnitude, axis=0) + 1e-10)
        )
        features['spectral_bandwidth'] = np.mean(spectral_bandwidth)
        
        # 频谱平坦度
        geometric_mean = np.exp(np.mean(np.log(magnitude + 1e-10), axis=0))
        arithmetic_mean = np.mean(magnitude, axis=0)
        spectral_flatness = geometric_mean / (arithmetic_mean + 1e-10)
        features['spectral_flatness'] = np.mean(spectral_flatness)
        
        # 零交叉率（近似）
        if magnitude.shape[1] > 1:
            energy_diff = np.diff(np.mean(magnitude, axis=0))
            zero_crossings = np.sum(energy_diff[:-1] * energy_diff[1:] < 0)
            features['zero_crossing_rate'] = zero_crossings / len(energy_diff)
        else:
            features['zero_crossing_rate'] = 0
        
        # 频带能量分布
        freq_bands = {
            'low': (0, 500),
            'mid': (500, 2000),
            'high': (2000, 8000)
        }
        
        for band_name, (f_min, f_max) in freq_bands.items():
            band_mask = (freqs >= f_min) & (freqs <= f_max)
            if np.any(band_mask):
                band_energy = np.mean(magnitude[band_mask, :] ** 2)
                features[f'{band_name}_energy'] = band_energy
            else:
                features[f'{band_name}_energy'] = 0
        
        # 节奏性检测
        if magnitude.shape[1] > 4:
            energy_series = np.mean(magnitude, axis=0)
            autocorr = np.correlate(energy_series, energy_series, mode='full')
            max_autocorr = np.max(autocorr[len(autocorr)//2+1:])
            features['rhythmicity'] = max_autocorr / (np.max(autocorr) + 1e-10)
        else:
            features['rhythmicity'] = 0
        
        return features
    
    def _generate_single_onomatopoeia(self, audio_features: Dict, sound_type: str, 
                                    sound_info: Dict) -> OnomatopoeiaFeature:
        """生成单个拟声词"""
        # 计算频率匹配度
        freq_min, freq_max = sound_info['freq_range']
        centroid = audio_features['spectral_centroid']
        
        if freq_min <= centroid <= freq_max:
            freq_match = 1.0
        else:
            # 计算距离匹配度
            if centroid < freq_min:
                freq_match = max(0, 1 - (freq_min - centroid) / freq_min)
            else:
                freq_match = max(0, 1 - (centroid - freq_max) / freq_max)
        
        # 计算模式匹配度
        pattern_match = self._calculate_pattern_match(audio_features, sound_info['pattern'])
        
        # 计算总体置信度
        confidence = (freq_match * 0.6 + pattern_match * 0.4) * audio_features['total_energy']
        confidence = min(confidence, 1.0)
        
        # 根据强度选择拟声词
        intensity = min(audio_features['total_energy'] * 5, 1.0)  # 归一化强度
        selected_word = self._select_word_by_intensity(sound_info, intensity)
        
        # 估算持续时间
        duration = self._estimate_duration(audio_features)
        
        return OnomatopoeiaFeature(
            word=selected_word,
            confidence=confidence,
            intensity=intensity,
            duration=duration,
            frequency_range=sound_info['freq_range'],
            pattern_type=sound_info['pattern'],
            visual_color=sound_info['color']
        )
    
    def _calculate_pattern_match(self, audio_features: Dict, pattern_type: str) -> float:
        """计算模式匹配度"""
        if pattern_type == 'continuous_flow':
            # 连续流动：低零交叉率，高低频能量
            return (1 - audio_features['zero_crossing_rate']) * 0.5 + \
                   audio_features['low_energy'] / (audio_features['total_energy'] + 1e-10) * 0.5
        
        elif pattern_type == 'burst_splash':
            # 突发溅射：高零交叉率，高中高频能量
            return audio_features['zero_crossing_rate'] * 0.3 + \
                   audio_features['mid_energy'] / (audio_features['total_energy'] + 1e-10) * 0.4 + \
                   audio_features['high_energy'] / (audio_features['total_energy'] + 1e-10) * 0.3
        
        elif pattern_type == 'bubble_pop':
            # 气泡破裂：中等零交叉率，低中频能量
            zcr_score = 1 - abs(audio_features['zero_crossing_rate'] - 0.5) * 2
            return zcr_score * 0.4 + \
                   audio_features['low_energy'] / (audio_features['total_energy'] + 1e-10) * 0.6
        
        elif pattern_type == 'rhythmic_engine':
            # 节奏性引擎：高节奏性，低频为主
            return audio_features['rhythmicity'] * 0.6 + \
                   audio_features['low_energy'] / (audio_features['total_energy'] + 1e-10) * 0.4
        
        elif pattern_type == 'tonal_horn':
            # 音调性号角：低频谱平坦度（集中频率），中频为主
            tonal_score = 1 - audio_features['spectral_flatness']
            return tonal_score * 0.5 + \
                   audio_features['mid_energy'] / (audio_features['total_energy'] + 1e-10) * 0.5
        
        elif pattern_type == 'melodic_bird':
            # 旋律性鸟鸣：高频为主，中等频谱平坦度
            return audio_features['high_energy'] / (audio_features['total_energy'] + 1e-10) * 0.7 + \
                   audio_features['spectral_flatness'] * 0.3
        
        elif pattern_type == 'continuous_wind':
            # 连续风声：高频谱平坦度，宽频带
            return audio_features['spectral_flatness'] * 0.5 + \
                   min(audio_features['spectral_bandwidth'] / 1000, 1.0) * 0.5
        
        elif pattern_type == 'rhythmic_steps':
            # 节奏性脚步：高节奏性，低频为主
            return audio_features['rhythmicity'] * 0.7 + \
                   audio_features['low_energy'] / (audio_features['total_energy'] + 1e-10) * 0.3
        
        else:
            return audio_features['total_energy']
    
    def _select_word_by_intensity(self, sound_info: Dict, intensity: float) -> str:
        """根据强度选择拟声词"""
        intensity_map = sound_info.get('intensity_map', {})
        
        for (min_int, max_int), words in intensity_map.items():
            if min_int <= intensity <= max_int:
                return random.choice(words)
        
        # 如果没有匹配的强度范围，随机选择
        return random.choice(sound_info['words'])
    
    def _estimate_duration(self, audio_features: Dict) -> float:
        """估算拟声词持续时间"""
        # 基于能量和节奏性估算
        base_duration = 0.5  # 基础持续时间（秒）
        
        # 能量越高，持续时间可能越长
        energy_factor = min(audio_features['total_energy'] * 2, 2.0)
        
        # 节奏性高的声音可能持续时间更长
        rhythm_factor = 1 + audio_features['rhythmicity']
        
        return base_duration * energy_factor * rhythm_factor
    
    def _apply_combination_rules(self, words: List[OnomatopoeiaFeature], 
                               audio_features: Dict) -> List[OnomatopoeiaFeature]:
        """应用组合规则生成复合拟声词"""
        enhanced_words = words.copy()
        
        # 如果有高强度的声音，考虑重复
        high_intensity_words = [w for w in words if w.intensity > 0.7]
        
        for word in high_intensity_words:
            # 查找对应的组合规则
            for sound_type, rules in self.combination_rules.items():
                if word.pattern_type in sound_type or any(base in word.word for base in ['潺', '突', '啾']):
                    # 根据持续时间决定是否重复
                    if word.duration > 1.0:
                        if random.random() < 0.3:  # 30%概率生成重复词
                            repeated_word = random.choice(rules['repetition'])
                            enhanced_word = OnomatopoeiaFeature(
                                word=repeated_word,
                                confidence=word.confidence * 0.9,
                                intensity=word.intensity,
                                duration=word.duration,
                                frequency_range=word.frequency_range,
                                pattern_type=word.pattern_type,
                                visual_color=word.visual_color
                            )
                            enhanced_words.append(enhanced_word)
                    
                    # 根据复杂度决定是否变化
                    if audio_features['spectral_bandwidth'] > 500:
                        if random.random() < 0.2:  # 20%概率生成变化词
                            varied_word = random.choice(rules['variation'])
                            enhanced_word = OnomatopoeiaFeature(
                                word=varied_word,
                                confidence=word.confidence * 0.8,
                                intensity=word.intensity,
                                duration=word.duration * 1.2,
                                frequency_range=word.frequency_range,
                                pattern_type=word.pattern_type,
                                visual_color=word.visual_color
                            )
                            enhanced_words.append(enhanced_word)
                    break
        
        return enhanced_words
    
    def get_top_onomatopoeia(self, top_k: int = 3) -> List[OnomatopoeiaFeature]:
        """获取当前最主要的拟声词"""
        if not self.current_words:
            return []
        
        # 按置信度和强度的乘积排序
        sorted_words = sorted(
            self.current_words.values(),
            key=lambda x: x.confidence * x.intensity,
            reverse=True
        )
        
        return sorted_words[:top_k]
    
    def get_onomatopoeia_by_type(self, pattern_type: str) -> List[OnomatopoeiaFeature]:
        """根据模式类型获取拟声词"""
        return [word for word in self.current_words.values() 
                if word.pattern_type == pattern_type]
    
    def get_recent_onomatopoeia(self, seconds: float = 2.0) -> List[OnomatopoeiaFeature]:
        """获取最近一段时间的拟声词"""
        if not self.onomatopoeia_history:
            return []
        
        # 简单实现：返回最近几个时间窗口的拟声词
        recent_count = max(1, int(seconds * 10))  # 假设10Hz更新频率
        recent_words = []
        
        for i in range(min(recent_count, len(self.onomatopoeia_history))):
            recent_words.extend(self.onomatopoeia_history[-(i+1)])
        
        # 去重并按置信度排序
        unique_words = {}
        for word in recent_words:
            if word.word not in unique_words or word.confidence > unique_words[word.word].confidence:
                unique_words[word.word] = word
        
        return sorted(unique_words.values(), key=lambda x: x.confidence, reverse=True)

if __name__ == "__main__":
    # 测试代码
    import pygame
    
    pygame.init()
    
    generator = CanalOnomatopoeiaGenerator()
    
    print("运河拟声词生成器测试")
    print("=" * 40)
    
    # 生成测试音频数据
    sample_rate = 32000
    duration = 0.1  # 100ms
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # 测试不同类型的声音
    test_sounds = {
        '水流声': 0.3 * np.sin(2 * np.pi * 200 * t) * (1 + 0.2 * np.sin(2 * np.pi * 5 * t)),
        '水花声': 0.5 * np.random.normal(0, 1, len(t)) * np.exp(-t * 20),
        '船只引擎': 0.4 * (np.sin(2 * np.pi * 120 * t) + 0.3 * np.sin(2 * np.pi * 240 * t)),
        '鸟鸣声': 0.3 * np.sin(2 * np.pi * (3000 + 1000 * np.sin(2 * np.pi * 10 * t)) * t),
        '风声': 0.2 * np.random.normal(0, 1, len(t)) * (1 + np.sin(2 * np.pi * 2 * t))
    }
    
    for sound_name, audio_data in test_sounds.items():
        print(f"\n测试 {sound_name}:")
        
        # 生成拟声词
        onomatopoeia_list = generator.generate_onomatopoeia(audio_data)
        
        # 显示结果
        if onomatopoeia_list:
            top_words = generator.get_top_onomatopoeia(3)
            for i, word in enumerate(top_words, 1):
                print(f"  {i}. {word.word} (置信度: {word.confidence:.3f}, 强度: {word.intensity:.3f})")
        else:
            print("  未检测到拟声词")
    
    print("\n测试完成")