#!/usr/bin/env python3
"""
运河环境声音采集和特征提取模块
专门用于采集和分析运河环境中的自然声音（水流声、船只声、鸟鸣声、风声等）
"""

import numpy as np
import sounddevice as sd
import librosa
import threading
import time
import wave
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from scipy import signal
from collections import deque

@dataclass
class AudioFeatures:
    """音频特征数据类"""
    # 基础特征
    duration: float
    sample_rate: int
    rms_energy: float
    zero_crossing_rate: float
    
    # 频谱特征
    spectral_centroid: np.ndarray
    spectral_rolloff: np.ndarray
    spectral_bandwidth: np.ndarray
    mfcc: np.ndarray
    
    # 运河环境特征
    water_flow_indicator: float      # 水流指示器 (0-1)
    boat_activity_indicator: float   # 船只活动指示器 (0-1)
    bird_activity_indicator: float   # 鸟类活动指示器 (0-1)
    wind_indicator: float           # 风声指示器 (0-1)
    
    # 环境评分
    canal_ambience_score: float     # 运河氛围综合评分 (0-1)
    
    # 频带能量分布
    low_freq_energy: float          # 低频能量 (20-300 Hz)
    mid_freq_energy: float          # 中频能量 (300-2000 Hz)
    high_freq_energy: float         # 高频能量 (2000-8000 Hz)

class AudioRecorder:
    """运河环境声音录制器"""
    
    def __init__(self, config: Dict):
        """初始化录制器"""
        self.config = config
        self.sample_rate = config.get('samplerate', 32000)
        self.channels = config.get('channels', 1)
        self.record_seconds = config.get('record_seconds', 35)
        self.frame_ms = config.get('frame_ms', 20)
        
        # 计算帧大小
        self.frame_size = int(self.sample_rate * self.frame_ms / 1000)
        self.hop_length = self.frame_size // 2
        
        # 录制状态
        self.is_recording = False
        self.recording_complete = False
        self.audio_data = None
        self.realtime_buffer = deque(maxlen=100)  # 实时数据缓冲区
        
        # 特征提取器
        self.feature_extractor = CanalFeatureExtractor(self.sample_rate)
        
        # 线程安全
        self.lock = threading.Lock()
        
        print(f"音频录制器初始化完成 - {self.sample_rate}Hz, {self.channels}ch, {self.record_seconds}s")
    
    def start_recording(self):
        """开始录制"""
        with self.lock:
            if self.is_recording:
                return
            
            self.is_recording = True
            self.recording_complete = False
            self.audio_data = []
            self.realtime_buffer.clear()
        
        # 启动录制线程
        self.record_thread = threading.Thread(target=self._record_audio, daemon=True)
        self.record_thread.start()
        
        print("开始录制运河环境声音...")
    
    def _record_audio(self):
        """录制音频的线程函数"""
        try:
            # 录制参数
            duration = self.record_seconds
            
            def audio_callback(indata, frames, time, status):
                """音频回调函数"""
                if status:
                    print(f"录制状态: {status}")
                
                # 存储音频数据
                with self.lock:
                    if self.is_recording:
                        self.audio_data.append(indata.copy())
                        
                        # 更新实时缓冲区
                        mono_data = np.mean(indata, axis=1) if indata.shape[1] > 1 else indata.flatten()
                        self.realtime_buffer.append(mono_data)
            
            # 开始录制
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=audio_callback,
                blocksize=self.frame_size
            ):
                # 录制指定时长
                time.sleep(duration)
            
            # 录制完成
            with self.lock:
                self.is_recording = False
                self.recording_complete = True
                
                # 合并音频数据
                if self.audio_data:
                    self.audio_data = np.concatenate(self.audio_data, axis=0)
                    if self.audio_data.ndim > 1:
                        self.audio_data = np.mean(self.audio_data, axis=1)  # 转为单声道
                
            print("运河环境声音录制完成")
            
        except Exception as e:
            print(f"录制错误: {e}")
            with self.lock:
                self.is_recording = False
                self.recording_complete = True
    
    def get_realtime_data(self) -> Optional[np.ndarray]:
        """获取实时音频数据用于可视化"""
        try:
            with self.lock:
                if len(self.realtime_buffer) > 0:
                    # 返回最近的音频帧
                    return np.array(self.realtime_buffer[-1])
                return None
        except Exception as e:
            print(f"获取实时音频数据异常: {e}")
            return None
    
    def get_progress(self) -> float:
        """获取录制进度 (0-1)"""
        if not self.is_recording and not self.recording_complete:
            return 0.0
        
        if self.recording_complete:
            return 1.0
        
        # 估算进度（基于已录制的数据量）
        with self.lock:
            if self.audio_data:
                recorded_samples = sum(len(chunk) for chunk in self.audio_data)
                total_samples = self.sample_rate * self.record_seconds
                return min(recorded_samples / total_samples, 1.0)
        
        return 0.0
    
    def is_recording_complete(self) -> bool:
        """检查录制是否完成"""
        return self.recording_complete
    
    def get_features(self) -> Optional[AudioFeatures]:
        """获取提取的音频特征"""
        if not self.recording_complete or self.audio_data is None:
            return None
        
        return self.feature_extractor.extract_features(self.audio_data, self.sample_rate)
    
    def save_audio(self, filepath: str):
        """保存录制的音频"""
        if self.audio_data is None:
            return False
        
        try:
            # 归一化音频数据
            audio_normalized = np.int16(self.audio_data * 32767)
            
            with wave.open(filepath, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_normalized.tobytes())
            
            print(f"音频已保存: {filepath}")
            return True
        except Exception as e:
            print(f"音频保存失败: {e}")
            return False
    
    def stop(self):
        """停止录制"""
        with self.lock:
            self.is_recording = False
    
    def reset(self):
        """重置录制器"""
        with self.lock:
            self.is_recording = False
            self.recording_complete = False
            self.audio_data = None
            self.realtime_buffer.clear()

class CanalFeatureExtractor:
    """运河环境声音特征提取器"""
    
    def __init__(self, sample_rate: int = 32000):
        """初始化特征提取器"""
        self.sample_rate = sample_rate
        
        # 频带分割点（Hz）
        self.low_freq_max = 300
        self.mid_freq_max = 2000
        self.high_freq_max = 8000
        
        # 运河环境声音特征频率范围
        self.water_flow_range = (50, 500)      # 水流声频率范围
        self.boat_engine_range = (100, 1000)   # 船只引擎声频率范围
        self.bird_range = (1000, 8000)         # 鸟类鸣叫频率范围
        self.wind_range = (20, 200)            # 风声频率范围
    
    def extract_features(self, audio_data: np.ndarray, sample_rate: int) -> AudioFeatures:
        """提取完整的音频特征（高度优化版本）"""
        try:
            print("开始音频特征提取...")
            start_time = time.time()
            
            # 确保audio_data是numpy数组
            if isinstance(audio_data, list):
                audio_data = np.array(audio_data, dtype=np.float32)
            elif not isinstance(audio_data, np.ndarray):
                audio_data = np.array(audio_data, dtype=np.float32)
            
            # 确保是一维数组
            if len(audio_data.shape) > 1:
                audio_data = audio_data.flatten()
            
            # 如果数据为空或太短，返回默认特征
            if len(audio_data) < 1024:
                print("音频数据太短，使用默认特征")
                return self._get_default_features(sample_rate)
            
            # 优化1：智能音频长度处理 - 只保留关键片段
            if len(audio_data) > sample_rate * 8:  # 超过8秒的音频
                print("音频过长，进行智能采样优化...")
                # 保留前3秒、中间2秒、后3秒
                front_samples = sample_rate * 3
                back_samples = sample_rate * 3
                middle_target = sample_rate * 2
                
                middle_start = len(audio_data) // 2 - middle_target // 2
                middle_end = middle_start + middle_target
                
                # 重新组合音频
                audio_data = np.concatenate([
                    audio_data[:front_samples],
                    audio_data[middle_start:middle_end],
                    audio_data[-back_samples:]
                ])
                print(f"音频长度优化到 {len(audio_data) / sample_rate:.1f}秒")
            
            # 基础特征 - 快速计算
            duration = len(audio_data) / sample_rate
            rms_energy = np.sqrt(np.mean(audio_data ** 2))
            
            # 优化2：更快的过零率计算
            zero_crossing_rate = np.mean(np.abs(np.diff(np.sign(audio_data)))) / 2
            
            print(f"基础特征计算完成 ({time.time() - start_time:.2f}s)")
            
            # 优化3：简化频谱特征计算
            try:
                # 使用更小的参数减少计算量
                n_fft = 512  # 固定较小的FFT大小
                hop_length = 256  # 较大的hop_length
                
                # 只计算关键的频谱特征
                spectral_centroid = librosa.feature.spectral_centroid(
                    y=audio_data, sr=sample_rate, n_fft=n_fft, hop_length=hop_length)[0]
                
                # 简化其他特征计算
                spectral_rolloff = spectral_centroid * 2  # 近似计算
                spectral_bandwidth = spectral_centroid * 0.5  # 近似计算
                
                # 优化4：减少MFCC计算量
                mfcc = librosa.feature.mfcc(
                    y=audio_data, sr=sample_rate, n_mfcc=6, n_fft=n_fft, hop_length=hop_length)
                
                print(f"频谱特征计算完成 ({time.time() - start_time:.2f}s)")
                
            except Exception as e:
                print(f"频谱特征提取失败: {e}")
                # 使用默认值
                spectral_centroid = np.array([1000.0])
                spectral_rolloff = np.array([2000.0])
                spectral_bandwidth = np.array([500.0])
                mfcc = np.random.random((6, 10)) * 0.1
            
            # 优化5：高效的环境特征提取
            # 使用单次FFT计算所有环境特征
            segment_length = min(4096, len(audio_data))  # 更小的段长度
            segment = audio_data[:segment_length]  # 只使用开头部分
            
            fft_result = np.fft.fft(segment)
            freqs = np.fft.fftfreq(len(fft_result), 1/sample_rate)
            
            # 只取正频率部分
            positive_freq_idx = freqs >= 0
            freqs = freqs[positive_freq_idx]
            magnitude = np.abs(fft_result[positive_freq_idx])
            
            # 使用快速版本的环境特征计算
            water_flow_indicator = self._calculate_water_flow_indicator_fast(freqs, magnitude)
            boat_activity_indicator = self._calculate_boat_activity_indicator_fast(freqs, magnitude)
            bird_activity_indicator = self._calculate_bird_activity_indicator_fast(freqs, magnitude)
            wind_indicator = self._calculate_wind_indicator_fast(freqs, magnitude)
            
            print(f"环境特征计算完成 ({time.time() - start_time:.2f}s)")
            
            # 频带能量分布 - 快速计算
            low_freq_energy = self._calculate_band_energy_fast(freqs, magnitude, 20, 300)
            mid_freq_energy = self._calculate_band_energy_fast(freqs, magnitude, 300, 2000)
            high_freq_energy = self._calculate_band_energy_fast(freqs, magnitude, 2000, 8000)
            
            # 归一化能量分布
            total_energy = low_freq_energy + mid_freq_energy + high_freq_energy
            if total_energy > 0:
                low_freq_energy /= total_energy
                mid_freq_energy /= total_energy
                high_freq_energy /= total_energy
            
            # 运河氛围评分
            canal_ambience_score = self._calculate_canal_ambience_score(
                water_flow_indicator, boat_activity_indicator, 
                bird_activity_indicator, wind_indicator
            )
            
            total_time = time.time() - start_time
            print(f"音频特征提取完成，总耗时: {total_time:.2f}s")
            
            return AudioFeatures(
                duration=duration,
                sample_rate=sample_rate,
                rms_energy=rms_energy,
                zero_crossing_rate=zero_crossing_rate,
                spectral_centroid=spectral_centroid,
                spectral_rolloff=spectral_rolloff,
                spectral_bandwidth=spectral_bandwidth,
                mfcc=mfcc,
                water_flow_indicator=water_flow_indicator,
                boat_activity_indicator=boat_activity_indicator,
                bird_activity_indicator=bird_activity_indicator,
                wind_indicator=wind_indicator,
                canal_ambience_score=canal_ambience_score,
                low_freq_energy=low_freq_energy,
                mid_freq_energy=mid_freq_energy,
                high_freq_energy=high_freq_energy
            )
            
        except Exception as e:
            print(f"特征提取异常: {e}")
            import traceback
            traceback.print_exc()
            return self._get_default_features(sample_rate)
    
    def _get_default_features(self, sample_rate: int) -> AudioFeatures:
        """获取默认特征（当提取失败时使用）"""
        return AudioFeatures(
            duration=1.0,
            sample_rate=sample_rate,
            rms_energy=0.1,
            zero_crossing_rate=0.05,
            spectral_centroid=np.array([1000.0]),
            spectral_rolloff=np.array([2000.0]),
            spectral_bandwidth=np.array([500.0]),
            mfcc=np.random.random((13, 10)) * 0.1,
            water_flow_indicator=0.5,
            boat_activity_indicator=0.3,
            bird_activity_indicator=0.4,
            wind_indicator=0.2,
            canal_ambience_score=0.6,
            low_freq_energy=0.4,
            mid_freq_energy=0.3,
            high_freq_energy=0.3
        )
    
    def _calculate_band_energy_fast(self, freqs: np.ndarray, magnitude: np.ndarray, 
                              freq_min: float, freq_max: float) -> float:
        """计算指定频带的能量（快速版本）"""
        band_mask = (freqs >= freq_min) & (freqs <= freq_max)
        if np.any(band_mask):
            return float(np.sum(magnitude[band_mask] ** 2))
        return 0.0

    def _calculate_water_flow_indicator_fast(self, freqs: np.ndarray, magnitude: np.ndarray) -> float:
        """计算水流指示器（快速版本）"""
        # 简化版本：只计算水流频率范围的能量占比
        water_energy = self._calculate_band_energy_fast(freqs, magnitude, *self.water_flow_range)
        total_energy = np.sum(magnitude ** 2)
        
        if total_energy == 0:
            return 0.0
        
        water_ratio = water_energy / total_energy
        return np.clip(water_ratio * 2, 0, 1)  # 放大系数

    def _calculate_boat_activity_indicator_fast(self, freqs: np.ndarray, magnitude: np.ndarray) -> float:
        """计算船只活动指示器（快速版本）"""
        # 简化版本：检测船只引擎频率范围的峰值
        boat_energy = self._calculate_band_energy_fast(freqs, magnitude, *self.boat_engine_range)
        total_energy = np.sum(magnitude ** 2)
        
        if total_energy == 0:
            return 0.0
        
        boat_ratio = boat_energy / total_energy
        return np.clip(boat_ratio * 3, 0, 1)  # 放大系数

    def _calculate_bird_activity_indicator_fast(self, freqs: np.ndarray, magnitude: np.ndarray) -> float:
        """计算鸟类活动指示器（快速版本）"""
        # 简化版本：高频能量占比
        bird_energy = self._calculate_band_energy_fast(freqs, magnitude, *self.bird_range)
        total_energy = np.sum(magnitude ** 2)
        
        if total_energy == 0:
            return 0.0
        
        bird_ratio = bird_energy / total_energy
        return np.clip(bird_ratio * 2, 0, 1)

    def _calculate_wind_indicator_fast(self, freqs: np.ndarray, magnitude: np.ndarray) -> float:
        """计算风声指示器（快速版本）"""
        # 简化版本：极低频能量占比
        wind_energy = self._calculate_band_energy_fast(freqs, magnitude, *self.wind_range)
        total_energy = np.sum(magnitude ** 2)
        
        if total_energy == 0:
            return 0.0
        
        wind_ratio = wind_energy / total_energy
        return np.clip(wind_ratio * 4, 0, 1)  # 放大系数
    
    def _calculate_water_flow_indicator(self, freqs: np.ndarray, magnitude: np.ndarray, 
                                       audio_data: np.ndarray) -> float:
        """计算水流声指示器"""
        # 水流声特征：低频连续性、频谱平滑度
        water_energy = self._calculate_band_energy(freqs, magnitude, *self.water_flow_range)
        total_energy = np.sum(magnitude ** 2)
        
        if total_energy == 0:
            return 0.0
        
        # 水流声占比
        water_ratio = water_energy / total_energy
        
        # 计算频谱连续性（水流声通常比较连续）
        continuity = self._calculate_spectral_continuity(freqs, magnitude, *self.water_flow_range)
        
        # 计算时域稳定性（水流声相对稳定）
        stability = self._calculate_temporal_stability(audio_data)
        
        # 综合指标
        indicator = (water_ratio * 0.4 + continuity * 0.3 + stability * 0.3)
        return np.clip(indicator, 0, 1)
    
    def _calculate_boat_activity_indicator(self, freqs: np.ndarray, magnitude: np.ndarray, 
                                          audio_data: np.ndarray) -> float:
        """计算船只活动指示器"""
        # 船只声特征：中频峰值、周期性变化
        boat_energy = self._calculate_band_energy(freqs, magnitude, *self.boat_engine_range)
        total_energy = np.sum(magnitude ** 2)
        
        if total_energy == 0:
            return 0.0
        
        # 船只声占比
        boat_ratio = boat_energy / total_energy
        
        # 检测中频峰值
        mid_freq_peaks = self._detect_frequency_peaks(freqs, magnitude, *self.boat_engine_range)
        
        # 检测周期性（船只引擎的周期性特征）
        periodicity = self._calculate_periodicity(audio_data)
        
        # 综合指标
        indicator = (boat_ratio * 0.4 + mid_freq_peaks * 0.3 + periodicity * 0.3)
        return np.clip(indicator, 0, 1)
    
    def _calculate_bird_activity_indicator(self, freqs: np.ndarray, magnitude: np.ndarray, 
                                          audio_data: np.ndarray) -> float:
        """计算鸟类活动指示器"""
        # 鸟鸣声特征：高频突发、短时变化
        bird_energy = self._calculate_band_energy(freqs, magnitude, *self.bird_range)
        total_energy = np.sum(magnitude ** 2)
        
        if total_energy == 0:
            return 0.0
        
        # 鸟鸣声占比
        bird_ratio = bird_energy / total_energy
        
        # 检测高频突发
        high_freq_bursts = self._detect_frequency_bursts(freqs, magnitude, *self.bird_range)
        
        # 检测短时变化（鸟鸣的间歇性特征）
        variability = self._calculate_temporal_variability(audio_data)
        
        # 综合指标
        indicator = (bird_ratio * 0.4 + high_freq_bursts * 0.3 + variability * 0.3)
        return np.clip(indicator, 0, 1)
    
    def _calculate_wind_indicator(self, freqs: np.ndarray, magnitude: np.ndarray, 
                                 audio_data: np.ndarray) -> float:
        """计算风声指示器"""
        # 风声特征：极低频、宽频带噪声
        wind_energy = self._calculate_band_energy(freqs, magnitude, *self.wind_range)
        total_energy = np.sum(magnitude ** 2)
        
        if total_energy == 0:
            return 0.0
        
        # 风声占比
        wind_ratio = wind_energy / total_energy
        
        # 计算频谱平坦度（风声通常是宽频带噪声）
        spectral_flatness = self._calculate_spectral_flatness(freqs, magnitude, *self.wind_range)
        
        # 计算低频连续性
        low_freq_continuity = self._calculate_spectral_continuity(freqs, magnitude, *self.wind_range)
        
        # 综合指标
        indicator = (wind_ratio * 0.4 + spectral_flatness * 0.3 + low_freq_continuity * 0.3)
        return np.clip(indicator, 0, 1)
    
    def _calculate_canal_ambience_score(self, water_flow: float, boat_activity: float, 
                                       bird_activity: float, wind: float) -> float:
        """计算运河氛围综合评分"""
        # 理想的运河环境应该有适度的水流声、偶尔的船只声、鸟鸣声和轻微的风声
        
        # 水流声权重最高（运河的核心特征）
        water_score = water_flow * 0.4
        
        # 船只活动适中为佳
        boat_score = (1 - abs(boat_activity - 0.3)) * 0.25
        
        # 鸟类活动增加自然感
        bird_score = bird_activity * 0.2
        
        # 轻微风声增加氛围
        wind_score = (1 - abs(wind - 0.2)) * 0.15
        
        total_score = water_score + boat_score + bird_score + wind_score
        return np.clip(total_score, 0, 1)
    
    def _calculate_spectral_continuity(self, freqs: np.ndarray, magnitude: np.ndarray, 
                                      freq_min: float, freq_max: float) -> float:
        """计算频谱连续性"""
        band_mask = (freqs >= freq_min) & (freqs <= freq_max)
        if not np.any(band_mask):
            return 0.0
        
        band_magnitude = magnitude[band_mask]
        if len(band_magnitude) < 2:
            return 0.0
        
        # 计算相邻频率点的差异
        diff = np.diff(band_magnitude)
        continuity = 1 - (np.std(diff) / (np.mean(band_magnitude) + 1e-8))
        return np.clip(continuity, 0, 1)
    
    def _calculate_temporal_stability(self, audio_data: np.ndarray) -> float:
        """计算时域稳定性"""
        # 将音频分段计算RMS
        segment_length = len(audio_data) // 10
        if segment_length < 1:
            return 0.0
        
        rms_values = []
        for i in range(0, len(audio_data) - segment_length, segment_length):
            segment = audio_data[i:i + segment_length]
            rms = np.sqrt(np.mean(segment ** 2))
            rms_values.append(rms)
        
        if len(rms_values) < 2:
            return 0.0
        
        # 稳定性 = 1 - 变异系数
        mean_rms = np.mean(rms_values)
        std_rms = np.std(rms_values)
        stability = 1 - (std_rms / (mean_rms + 1e-8))
        return np.clip(stability, 0, 1)
    
    def _detect_frequency_peaks(self, freqs: np.ndarray, magnitude: np.ndarray, 
                               freq_min: float, freq_max: float) -> float:
        """检测频率峰值"""
        band_mask = (freqs >= freq_min) & (freqs <= freq_max)
        if not np.any(band_mask):
            return 0.0
        
        band_magnitude = magnitude[band_mask]
        
        # 使用scipy检测峰值
        peaks, _ = signal.find_peaks(band_magnitude, height=np.mean(band_magnitude))
        
        # 峰值强度
        if len(peaks) > 0:
            peak_strength = np.mean(band_magnitude[peaks]) / (np.mean(band_magnitude) + 1e-8)
            return np.clip(peak_strength - 1, 0, 1)  # 减1是因为我们要的是超出平均值的部分
        
        return 0.0
    
    def _calculate_periodicity(self, audio_data: np.ndarray) -> float:
        """计算周期性"""
        # 使用自相关检测周期性
        correlation = np.correlate(audio_data, audio_data, mode='full')
        correlation = correlation[correlation.size // 2:]
        
        # 寻找除了零延迟外的最大相关值
        if len(correlation) > 1:
            max_corr = np.max(correlation[1:]) / (correlation[0] + 1e-8)
            return np.clip(max_corr, 0, 1)
        
        return 0.0
    
    def _detect_frequency_bursts(self, freqs: np.ndarray, magnitude: np.ndarray, 
                                freq_min: float, freq_max: float) -> float:
        """检测频率突发"""
        band_mask = (freqs >= freq_min) & (freqs <= freq_max)
        if not np.any(band_mask):
            return 0.0
        
        band_magnitude = magnitude[band_mask]
        
        # 计算能量突发程度
        mean_energy = np.mean(band_magnitude)
        max_energy = np.max(band_magnitude)
        
        if mean_energy > 0:
            burst_ratio = max_energy / mean_energy
            return np.clip((burst_ratio - 1) / 10, 0, 1)  # 归一化到0-1
        
        return 0.0
    
    def _calculate_temporal_variability(self, audio_data: np.ndarray) -> float:
        """计算时域变异性"""
        # 计算短时能量变化
        frame_length = len(audio_data) // 20  # 20个帧
        if frame_length < 1:
            return 0.0
        
        energies = []
        for i in range(0, len(audio_data) - frame_length, frame_length):
            frame = audio_data[i:i + frame_length]
            energy = np.sum(frame ** 2)
            energies.append(energy)
        
        if len(energies) < 2:
            return 0.0
        
        # 变异系数
        mean_energy = np.mean(energies)
        std_energy = np.std(energies)
        variability = std_energy / (mean_energy + 1e-8)
        return np.clip(variability, 0, 1)
    
    def _calculate_spectral_flatness(self, freqs: np.ndarray, magnitude: np.ndarray, 
                                    freq_min: float, freq_max: float) -> float:
        """计算频谱平坦度"""
        band_mask = (freqs >= freq_min) & (freqs <= freq_max)
        if not np.any(band_mask):
            return 0.0
        
        band_magnitude = magnitude[band_mask]
        
        # 几何平均 / 算术平均
        geometric_mean = np.exp(np.mean(np.log(band_magnitude + 1e-8)))
        arithmetic_mean = np.mean(band_magnitude)
        
        if arithmetic_mean > 0:
            flatness = geometric_mean / arithmetic_mean
            return np.clip(flatness, 0, 1)
        
        return 0.0

# 测试代码
if __name__ == "__main__":
    # 测试音频录制器
    config = {
        'samplerate': 32000,
        'channels': 1,
        'record_seconds': 5,  # 测试用短时间
        'frame_ms': 20
    }
    
    recorder = AudioRecorder(config)
    
    print("开始测试录制...")
    recorder.start_recording()
    
    # 等待录制完成
    while not recorder.is_recording_complete():
        progress = recorder.get_progress()
        print(f"录制进度: {progress:.1%}")
        time.sleep(0.5)
    
    # 获取特征
    features = recorder.get_features()
    if features:
        print(f"\n音频特征:")
        print(f"时长: {features.duration:.2f}s")
        print(f"RMS能量: {features.rms_energy:.4f}")
        print(f"水流指示器: {features.water_flow_indicator:.3f}")
        print(f"船只活动指示器: {features.boat_activity_indicator:.3f}")
        print(f"鸟类活动指示器: {features.bird_activity_indicator:.3f}")
        print(f"风声指示器: {features.wind_indicator:.3f}")
        print(f"运河氛围评分: {features.canal_ambience_score:.3f}")
    
    print("测试完成")