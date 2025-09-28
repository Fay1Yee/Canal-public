#!/usr/bin/env python3
"""
水上书 Waterbook - 主程序
运河环境声音艺术生成器，采集运河环境声音特征，生成独特的水墨风格艺术作品

新增功能：
- 声音分类功能：基于传统音频特征分析识别运河环境中的不同声音类型
- 音素可视化功能：实时显示音频的音素特征
- 拟声词生成功能：基于音频特征生成中文拟声词
- 拟声词可视化功能：动态展示生成的拟声词
"""

import os
import sys
import time
import yaml
import pygame
import threading
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any

# 核心模块导入
from audio_rec import AudioRecorder
from canal_visualizer import CanalVisualizer
from generator import ArtGenerator
from visual import UIRenderer
from server import WebServer

# 新增功能模块导入
from enhanced_sound_classifier import EnhancedSoundClassifier
from phoneme_visualizer import PhonemeVisualizer
from onomatopoeia_generator import CanalOnomatopoeiaGenerator
from onomatopoeia_visualizer import OnomatopoeiaVisualizer
from performance_optimizer import get_optimizer, profile_function

class AppState(Enum):
    """应用状态枚举"""
    E0_ATTRACT = "E0_吸引"      # 展示运河水墨主题，等待用户交互
    E1_LISTEN = "E1_聆听"       # 环境声音检测和采集准备
    E2_RECORD = "E2_采集"       # 运河环境声音采集和实时频谱显示
    E3_GENERATE = "E3_生成"     # 环境声音特征分析和内容生成
    E4_SELECT = "E4_选择"       # 水墨风格选择界面
    E5_DISPLAY = "E5_展示"      # 艺术作品展示和下载页面
    E6_RESET = "E6_重置"        # 清理和重置

class CanalInkWashApp:
    """运河水墨主应用程序"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """初始化应用程序"""
        print("[DEBUG] 开始初始化应用程序")
        
        try:
            self.config = self._load_config(config_path)
            print("[DEBUG] 配置文件加载成功")
            
            self.current_state = AppState.E0_ATTRACT
            self.state_start_time = time.time()
            self.running = True
            
            # 初始化Pygame
            print("[DEBUG] 初始化Pygame...")
            pygame.init()
            pygame.mixer.init()
            print("[DEBUG] Pygame初始化完成")
            
            # 设置显示
            self.width = self.config['ui']['width']
            self.height = self.config['ui']['height']
            print(f"[DEBUG] 设置窗口尺寸: {self.width}x{self.height}")
            
            # 在macOS上强制显示窗口
            import os
            if os.name == 'posix':  # Unix/Linux/macOS
                os.environ['SDL_VIDEO_WINDOW_POS'] = '100,100'
            
            print("[DEBUG] 创建Pygame窗口...")
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("运河水墨 Canal Ink Wash")
            
            # 强制更新显示以确保窗口可见
            pygame.display.flip()
            print(f"Pygame窗口已创建: {self.width}x{self.height}")
            print(f"视频驱动: {pygame.display.get_driver()}")
            
            # 初始化组件
            print("[DEBUG] 初始化音频录制器...")
            self.audio_recorder = AudioRecorder(self.config['audio'])
            print("[DEBUG] 音频录制器初始化完成")
            
            print("[DEBUG] 初始化可视化器...")
            self.canal_visualizer = CanalVisualizer(self.width, self.height)
            print("[DEBUG] 可视化器初始化完成")
            
            print("[DEBUG] 初始化艺术生成器...")
            self.art_generator = ArtGenerator(self.config['generation'])
            print("[DEBUG] 艺术生成器初始化完成")
            
            print("[DEBUG] 初始化UI渲染器...")
            self.ui_renderer = UIRenderer(self.screen, self.width, self.height)
            print("[DEBUG] UI渲染器初始化完成")
            
            # 初始化新功能模块
            print("[DEBUG] 初始化声音分类器...")
            try:
                self.sound_classifier = EnhancedSoundClassifier()
                print("[DEBUG] 声音分类器初始化完成")
            except Exception as e:
                print(f"[WARNING] 声音分类器初始化失败: {e}")
                self.sound_classifier = None
            
            print("[DEBUG] 初始化音素可视化器...")
            try:
                self.phoneme_visualizer = PhonemeVisualizer(self.width, self.height)
                print("[DEBUG] 音素可视化器初始化完成")
            except Exception as e:
                print(f"[WARNING] 音素可视化器初始化失败: {e}")
                self.phoneme_visualizer = None
            
            print("[DEBUG] 初始化拟声词生成器...")
            try:
                self.onomatopoeia_generator = CanalOnomatopoeiaGenerator()
                print("[DEBUG] 拟声词生成器初始化完成")
            except Exception as e:
                print(f"[WARNING] 拟声词生成器初始化失败: {e}")
                self.onomatopoeia_generator = None
            
            print("[DEBUG] 初始化拟声词可视化器...")
            try:
                self.onomatopoeia_visualizer = OnomatopoeiaVisualizer(self.width, self.height)
                print("[DEBUG] 拟声词可视化器初始化完成")
            except Exception as e:
                print(f"[WARNING] 拟声词可视化器初始化失败: {e}")
                self.onomatopoeia_visualizer = None
            
            # 初始化性能优化器
            print("[DEBUG] 初始化性能优化器...")
            try:
                self.performance_optimizer = get_optimizer()
                self.performance_optimizer.target_fps = 60
                print("[DEBUG] 性能优化器初始化完成")
            except Exception as e:
                print(f"[WARNING] 性能优化器初始化失败: {e}")
                self.performance_optimizer = None
            
            # 初始化Web服务器
            print("[DEBUG] 初始化Web服务器...")
            self.web_server = WebServer(self.config.get('server', {}).get('port', 8000))
            self.web_server.set_app_instance(self)
            print("[DEBUG] Web服务器初始化完成")
            
            # GPIO设置（如果在树莓派上）
            print("[DEBUG] 设置GPIO...")
            self.gpio_enabled = self._setup_gpio()
            print(f"[DEBUG] GPIO设置完成，启用状态: {self.gpio_enabled}")
            
            # 状态数据
            self.audio_features = None
            self.selected_style = "行书"  # 默认风格
            self.generated_art = None
            
            print(f"水上书应用初始化完成 - {self.width}x{self.height}")
            print("[DEBUG] 应用程序初始化完成")
            
        except Exception as e:
            print(f"[ERROR] 应用程序初始化失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print(f"配置文件加载成功: {config_path}")
            # 为桌面本地模式提供完整默认配置
            return {
                'audio': {'samplerate': 32000, 'channels': 1, 'record_seconds': 35},
                'ui': {'width': 1280, 'height': 720, 'font': '墨趣古风体.ttf'},
                'server': {'port': 8000},
                'states': {'E1_seconds': 8, 'E4_seconds': 8, 'E5_seconds': 12, 'E6_seconds': 5},
                'generation': {'video_duration': 7, 'video_fps': 24},
                'gpio': {'button_pin': 17, 'long_press_sec': 1.2}
            }
        except Exception as e:
            print(f"配置文件加载失败: {e}")
            # 返回默认配置
            return {
                'audio': {'samplerate': 32000, 'channels': 1, 'record_seconds': 35},
                'ui': {'width': 1280, 'height': 720, 'font': '墨趣古风体.ttf'},
                'server': {'port': 8000},
                'states': {'E1_seconds': 8, 'E4_seconds': 8, 'E5_seconds': 12, 'E6_seconds': 5}
            }
    
    def _setup_gpio(self) -> bool:
        """设置GPIO（仅在树莓派上）"""
        try:
            # 检查是否禁用GPIO
            if os.getenv('WATERBOOK_NO_GPIO') == '1':
                print("GPIO已禁用，使用键盘模拟")
                return False
            
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.config['gpio']['button_pin'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            print("GPIO初始化成功")
            return True
        except ImportError:
            print("非树莓派环境，使用键盘模拟")
            return False
        except Exception as e:
            print(f"GPIO初始化失败: {e}")
            return False
    
    def start_web_server(self):
        """启动Web服务器"""
        try:
            self.web_server.start()
            print(f"Web服务器启动成功: {self.web_server.get_server_url()}")
        except Exception as e:
            print(f"Web服务器启动失败: {e}")
    
    def handle_input(self) -> tuple[bool, bool]:
        """处理输入事件，返回(短按, 长按)"""
        short_press = False
        long_press = False
        
        # 处理Pygame事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False, False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return False, False
                elif event.key == pygame.K_SPACE:
                    short_press = True
                elif event.key == pygame.K_RETURN:
                    long_press = True
                elif event.key == pygame.K_F11:
                    # 切换全屏
                    pygame.display.toggle_fullscreen()
        
        # GPIO输入处理
        if self.gpio_enabled:
            try:
                import RPi.GPIO as GPIO
                button_pin = self.config['gpio']['button_pin']
                
                if not GPIO.input(button_pin):  # 按钮按下（低电平）
                    press_start = time.time()
                    while not GPIO.input(button_pin):  # 等待释放
                        time.sleep(0.01)
                    press_duration = time.time() - press_start
                    
                    if press_duration >= self.config['gpio']['long_press_sec']:
                        long_press = True
                    else:
                        short_press = True
            except Exception as e:
                print(f"GPIO读取错误: {e}")
        
        return short_press, long_press
    
    def update_state(self, short_press: bool, long_press: bool):
        """更新状态机"""
        current_time = time.time()
        state_duration = current_time - self.state_start_time
        
        if self.current_state == AppState.E0_ATTRACT:
            # E0 吸引状态 - 等待任意输入开始
            if short_press or long_press:
                self._transition_to(AppState.E1_LISTEN)
        
        elif self.current_state == AppState.E1_LISTEN:
            # E1 聆听状态 - 环境声音检测准备
            if long_press:
                # 长按跳过倒计时
                self._transition_to(AppState.E2_RECORD)
            elif state_duration >= self.config['states']['E1_seconds']:
                # 自动进入采集状态
                self._transition_to(AppState.E2_RECORD)
        
        elif self.current_state == AppState.E2_RECORD:
            # E2 采集状态 - 自动采集完成后进入生成
            if self.audio_recorder.is_recording_complete():
                print("音频录制完成，获取特征数据")
                try:
                    self.audio_features = self.audio_recorder.get_features()
                    print(f"音频特征提取成功，时长: {self.audio_features.duration:.1f}秒")
                    
                    # 使用声音分类器分析音频
                    if self.sound_classifier:
                        try:
                            # 获取实时音频数据进行分类
                            audio_data = self.audio_recorder.get_realtime_data()
                            if audio_data is not None and len(audio_data) > 0:
                                classification_result = self.sound_classifier.classify_audio(audio_data)
                                print(f"声音分类结果: {classification_result}")
                                # 将分类结果存储到音频特征中
                                self.audio_features.sound_classification = classification_result
                        except Exception as e:
                            print(f"声音分类失败: {e}")
                    
                    # 使用拟声词生成器生成拟声词
                    if self.onomatopoeia_generator:
                        try:
                            onomatopoeia_list = self.onomatopoeia_generator.generate_onomatopoeia(
                                audio_data if audio_data is not None else np.array([])
                            )
                            if onomatopoeia_list:
                                # 获取最佳拟声词
                                best_onomatopoeia = onomatopoeia_list[0].word
                                print(f"生成拟声词: {best_onomatopoeia}")
                                # 将拟声词存储到音频特征中
                                self.audio_features.onomatopoeia = best_onomatopoeia
                            else:
                                self.audio_features.onomatopoeia = "无声"
                        except Exception as e:
                            print(f"拟声词生成失败: {e}")
                            self.audio_features.onomatopoeia = "无声"
                    
                    # 启动艺术生成
                    print("开始生成水墨艺术作品...")
                    self.art_generator.start_generation(self.audio_features)
                    
                    self._transition_to(AppState.E3_GENERATE)
                    
                except Exception as e:
                    print(f"音频特征提取失败: {e}")
                    # 使用默认特征继续
                    from audio_rec import AudioFeatures
                    import numpy as np
                    
                    self.audio_features = AudioFeatures(
                        duration=35.0,
                        sample_rate=32000,
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
                    
                    print("使用默认音频特征继续生成")
                    self.art_generator.start_generation(self.audio_features)
                    self._transition_to(AppState.E3_GENERATE)
        
        elif self.current_state == AppState.E3_GENERATE:
            # E3 生成状态 - 自动生成完成后进入选择
            try:
                if self.art_generator.is_generation_complete():
                    # 生成完成后，等待配置的暂停时间再转换
                    if state_duration >= self.config['states'].get('E3_seconds', 3.0):
                        print("艺术生成完成，暂停时间结束，转换到选择状态")
                        self._transition_to(AppState.E4_SELECT)
                elif state_duration >= 20.0:  # 延长超时时间到20秒
                    print("生成超时，强制转换到选择状态")
                    # 确保生成器状态正确
                    self.art_generator.generation_complete = True
                    self._transition_to(AppState.E4_SELECT)
            except Exception as e:
                print(f"生成状态检查错误: {e}")
                # 发生错误时强制转换到下一状态
                self.art_generator.generation_complete = True
                self._transition_to(AppState.E4_SELECT)
        
        elif self.current_state == AppState.E4_SELECT:
            # E4 选择状态 - 选择水墨风格
            if short_press:
                # 切换风格 - 启动风格切换动画
                styles = ["行书", "篆书", "水墨晕染"]
                current_index = styles.index(self.selected_style)
                old_style = self.selected_style
                self.selected_style = styles[(current_index + 1) % len(styles)]
                
                # 启动风格切换动画
                self.ui_renderer.start_style_switch_animation(old_style, self.selected_style)
                print(f"风格切换: {old_style} -> {self.selected_style}")
                
            elif long_press:
                # 确认选择，生成最终艺术作品
                try:
                    print(f"开始生成最终艺术作品，风格: {self.selected_style}")
                    
                    # 启动加载动画
                    self.ui_renderer.start_loading_animation()
                    
                    # 异步生成艺术作品以避免阻塞UI
                    def generate_art_async():
                        try:
                            generated_art = self.art_generator.generate_final_art(
                                self.audio_features, self.selected_style
                            )
                            
                            # 停止加载动画
                            self.ui_renderer.stop_loading_animation()
                            
                            if generated_art:
                                self.generated_art = generated_art
                                print("最终艺术作品生成成功")
                                # 更新Web服务器内容
                                if hasattr(self, 'web_server') and self.web_server:
                                    self.web_server.update_content(self.generated_art)
                                self._transition_to(AppState.E5_DISPLAY)
                            else:
                                print("最终艺术作品生成失败，进入重置状态")
                                self._transition_to(AppState.E6_RESET)
                        except Exception as e:
                            print(f"异步艺术生成异常: {e}")
                            import traceback
                            traceback.print_exc()
                            self.ui_renderer.stop_loading_animation()
                            self._transition_to(AppState.E6_RESET)
                    
                    # 在单独线程中生成艺术作品
                    threading.Thread(target=generate_art_async, daemon=True).start()
                    
                except Exception as e:
                    print(f"最终艺术生成异常: {e}")
                    import traceback
                    traceback.print_exc()
                    self.ui_renderer.stop_loading_animation()
                    self._transition_to(AppState.E6_RESET)
                    
            elif state_duration >= self.config['states']['E4_seconds']:
                # 超时自动确认当前选择
                try:
                    print(f"超时自动确认选择，风格: {self.selected_style}")
                    
                    # 启动加载动画
                    self.ui_renderer.start_loading_animation()
                    
                    # 异步生成艺术作品
                    def generate_art_timeout_async():
                        try:
                            generated_art = self.art_generator.generate_final_art(
                                self.audio_features, self.selected_style
                            )
                            
                            self.ui_renderer.stop_loading_animation()
                            
                            if generated_art:
                                self.generated_art = generated_art
                                print("超时生成艺术作品成功")
                                # 更新Web服务器内容
                                if hasattr(self, 'web_server') and self.web_server:
                                    self.web_server.update_content(self.generated_art)
                                self._transition_to(AppState.E5_DISPLAY)
                            else:
                                print("超时生成艺术作品失败，进入重置状态")
                                self._transition_to(AppState.E6_RESET)
                        except Exception as e:
                            print(f"超时异步艺术生成异常: {e}")
                            import traceback
                            traceback.print_exc()
                            self.ui_renderer.stop_loading_animation()
                            self._transition_to(AppState.E6_RESET)
                    
                    threading.Thread(target=generate_art_timeout_async, daemon=True).start()
                    
                except Exception as e:
                    print(f"超时艺术生成异常: {e}")
                    import traceback
                    traceback.print_exc()
                    self.ui_renderer.stop_loading_animation()
                    self._transition_to(AppState.E6_RESET)
        
        elif self.current_state == AppState.E5_DISPLAY:
            # E5 展示状态 - 展示艺术作品
            # 只有长按才能进入重置，避免意外触发
            if long_press:
                # 长按进入重置
                self._transition_to(AppState.E6_RESET)
            elif state_duration >= self.config['states']['E5_seconds']:
                # 自动进入重置
                self._transition_to(AppState.E6_RESET)
        
        elif self.current_state == AppState.E6_RESET:
            # E6 重置状态 - 清理和重置
            if state_duration >= self.config['states']['E6_seconds']:
                # 重置完成，回到吸引状态
                self._reset_app_state()
                self._transition_to(AppState.E0_ATTRACT)
    
    def _transition_to(self, new_state: AppState):
        """状态转换"""
        print(f"状态转换: {self.current_state.value} -> {new_state.value}")
        self.current_state = new_state
        self.state_start_time = time.time()
        
        # 状态进入时的特殊处理
        if new_state == AppState.E2_RECORD:
            # 开始录音
            self.audio_recorder.start_recording()
        elif new_state == AppState.E3_GENERATE:
            # 开始生成
            self.art_generator.start_generation(self.audio_features)
        elif new_state == AppState.E5_DISPLAY:
            # 桌面模式无需更新Web内容
            pass
    
    def _reset_app_state(self):
        """重置应用状态"""
        self.audio_features = None
        self.selected_style = "行书"
        self.generated_art = None
        self.audio_recorder.reset()
        self.art_generator.reset()
    
    def render(self):
        """渲染当前状态"""
        try:
            # 根据状态渲染不同内容
            if self.current_state == AppState.E0_ATTRACT:
                # 清屏
                self.screen.fill((245, 245, 240))  # 宣纸色
                self.ui_renderer.render_attract_screen()
            
            elif self.current_state == AppState.E1_LISTEN:
                # 清屏
                self.screen.fill((245, 245, 240))  # 宣纸色
                remaining_time = max(0, self.config['states']['E1_seconds'] - 
                                   (time.time() - self.state_start_time))
                self.ui_renderer.render_listen_screen(remaining_time)
            
            elif self.current_state == AppState.E2_RECORD:
                # E2状态：不清屏，直接渲染运河场景和覆盖层
                # 运河场景会自己处理背景渲染
                try:
                    audio_data = self.audio_recorder.get_realtime_data()
                    self.canal_visualizer.update(audio_data)
                    self.canal_visualizer.render(self.screen)
                    
                    # 渲染音素可视化（如果可用）
                    if self.phoneme_visualizer and audio_data is not None:
                        try:
                            self.phoneme_visualizer.update(audio_data)
                            self.phoneme_visualizer.render(self.screen)
                        except Exception as e:
                            print(f"音素可视化渲染异常: {e}")
                    
                    # 渲染拟声词可视化（如果可用）
                    if self.onomatopoeia_visualizer and audio_data is not None:
                        try:
                            # 计算音频强度并更新拟声词可视化器
                            audio_intensity = self.audio_recorder.get_audio_intensity() if hasattr(self.audio_recorder, 'get_audio_intensity') else 0.5
                            self.onomatopoeia_visualizer.update_audio_intensity(audio_intensity)
                            self.onomatopoeia_visualizer.update(audio_data)
                            self.onomatopoeia_visualizer.render(self.screen)
                        except Exception as e:
                            print(f"拟声词可视化渲染异常: {e}")
                    
                    self.ui_renderer.render_record_overlay(self.audio_recorder.get_progress())
                except Exception as e:
                    print(f"运河可视化渲染异常: {e}")
                    # 回退到简单界面
                    self.screen.fill((245, 245, 240))
                    self.ui_renderer.render_error_screen("运河场景渲染异常，请重试")
            
            elif self.current_state == AppState.E3_GENERATE:
                # 清屏
                self.screen.fill((245, 245, 240))  # 宣纸色
                self.ui_renderer.render_generate_screen(self.art_generator.get_progress())
            
            elif self.current_state == AppState.E4_SELECT:
                # 清屏
                self.screen.fill((245, 245, 240))  # 宣纸色
                remaining_time = max(0, self.config['states']['E4_seconds'] - 
                                   (time.time() - self.state_start_time))
                self.ui_renderer.render_select_screen(self.selected_style, remaining_time)
            
            elif self.current_state == AppState.E5_DISPLAY:
                # 清屏
                self.screen.fill((245, 245, 240))  # 宣纸色
                if self.generated_art:
                    try:
                        # 计算剩余时间
                        remaining_time = max(0, self.config['states']['E5_seconds'] - 
                                           (time.time() - self.state_start_time))
                        
                        # 更新本地书法生成器的音频数据
                        audio_data = self.audio_recorder.get_realtime_data()
                        if audio_data is not None:
                            self.ui_renderer.update_local_calligraphy_audio(audio_data)
                        
                        # 更新本地书法生成器的动画
                        dt = self.clock.get_time() / 1000.0  # 转换为秒
                        self.ui_renderer.update_local_calligraphy_animation(dt)
                        
                        self.ui_renderer.render_display_screen(self.generated_art, remaining_time)
                    except Exception as e:
                        print(f"渲染展示界面异常: {e}")
                        # 渲染异常时显示错误信息
                        self.ui_renderer.render_error_screen("艺术作品显示异常")
                else:
                    print("警告: generated_art为空，显示错误界面")
                    self.ui_renderer.render_error_screen("艺术作品生成失败")
            
            elif self.current_state == AppState.E6_RESET:
                # 清屏
                self.screen.fill((245, 245, 240))  # 宣纸色
                self.ui_renderer.render_reset_screen()
            
        except Exception as e:
            print(f"渲染过程发生严重异常: {e}")
            import traceback
            traceback.print_exc()
            # 尝试显示错误界面
            try:
                self.screen.fill((245, 245, 240))
                self.ui_renderer.render_error_screen("系统渲染异常")
            except:
                print("无法显示错误界面，系统可能需要重启")
    
    def run(self):
        """主运行循环"""
        print("水上书应用启动")
        
        # 启动Web服务器
        self.start_web_server()
        
        print("[DEBUG] 准备进入主事件循环")
        print(f"[DEBUG] 初始状态: {self.current_state.value}")
        print(f"[DEBUG] running标志: {self.running}")
        
        # 主事件循环
        clock = pygame.time.Clock()
        
        try:
            loop_count = 0
            while self.running:
                loop_count += 1
                if loop_count % 60 == 1:  # 每秒输出一次
                    print(f"[DEBUG] 主循环运行中 - 循环次数: {loop_count}")
                
                try:
                    # 性能监控开始
                    if self.performance_optimizer:
                        self.performance_optimizer.profiler.start_timer('main_loop')
                    
                    # 处理输入
                    short_press, long_press = self.handle_input()
                    
                    # 更新状态
                    self.update_state(short_press, long_press)
                    
                    # 渲染
                    self.render()
                    
                    # 性能监控结束
                    if self.performance_optimizer:
                        self.performance_optimizer.profiler.end_timer('main_loop')
                    
                except Exception as e:
                    print(f"主循环内部错误: {e}")
                    import traceback
                    traceback.print_exc()
                    # 继续运行而不是崩溃
                    continue
                
                # 控制帧率和显示更新
                try:
                    # 确保显示更新
                    pygame.display.flip()
                    # 控制帧率并应用性能优化
                    fps = clock.get_fps()
                    if self.performance_optimizer:
                        optimizations = self.performance_optimizer.apply_optimizations(fps)
                        if optimizations and loop_count % 300 == 0:  # 每5秒输出一次优化信息
                            print(f"[PERF] 应用优化: {optimizations}")
                    
                    clock.tick(60)
                except Exception as e:
                    print(f"帧率控制或显示更新错误: {e}")
                    # 使用简单的延时替代
                    time.sleep(1/60)
        
        except KeyboardInterrupt:
            print("\n用户中断程序")
        except Exception as e:
            print(f"程序运行错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        print("清理应用资源...")
        
        # 停止录音
        if self.audio_recorder:
            self.audio_recorder.stop()
        
        # 停止Web服务器
        if hasattr(self, 'web_server') and self.web_server:
            try:
                self.web_server.stop()
                print("Web服务器已停止")
            except Exception as e:
                print(f"停止Web服务器时出错: {e}")
        
        # 清理GPIO
        if self.gpio_enabled:
            try:
                import RPi.GPIO as GPIO
                GPIO.cleanup()
            except:
                pass
        
        # 退出Pygame
        pygame.quit()
        
        print("水上书应用已退出")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="水上书 - 水上环境声音艺术生成器")
    parser.add_argument('--config', default='config.yaml', help='配置文件路径')
    parser.add_argument('--no-gpio', action='store_true', help='禁用GPIO，使用键盘模拟')
    parser.add_argument('--fullscreen', action='store_true', help='全屏模式启动')
    
    args = parser.parse_args()
    
    # 设置环境变量
    if args.no_gpio:
        os.environ['WATERBOOK_NO_GPIO'] = '1'
    
    # 创建并运行应用
    app = CanalInkWashApp(args.config)
    
    if args.fullscreen:
        pygame.display.toggle_fullscreen()
    
    app.run()

if __name__ == "__main__":
    main()