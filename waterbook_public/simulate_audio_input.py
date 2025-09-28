#!/usr/bin/env python3
"""
模拟音频输入脚本
通过播放测试音频文件来触发艺术作品生成流程
"""

import os
import time
import subprocess
import threading
from pathlib import Path

def play_audio_file(audio_file):
    """播放音频文件"""
    try:
        # 在macOS上使用afplay命令播放音频
        if os.system("which afplay > /dev/null 2>&1") == 0:
            print(f"使用afplay播放音频: {audio_file}")
            subprocess.run(['afplay', audio_file], check=True)
        else:
            print("未找到afplay命令，尝试其他播放器...")
            # 可以添加其他音频播放器的支持
            return False
        return True
    except Exception as e:
        print(f"音频播放失败: {e}")
        return False

def monitor_output_directory():
    """监控output目录的变化"""
    output_dir = Path("output")
    if not output_dir.exists():
        print("output目录不存在")
        return
    
    print("开始监控output目录...")
    initial_files = set(output_dir.glob("*"))
    print(f"初始文件数量: {len(initial_files)}")
    
    # 监控30秒
    for i in range(30):
        time.sleep(1)
        current_files = set(output_dir.glob("*"))
        new_files = current_files - initial_files
        
        if new_files:
            print(f"检测到新文件: {[f.name for f in new_files]}")
            
        if i % 5 == 0:
            print(f"监控中... ({i}/30秒)")
    
    print("监控结束")

def simulate_audio_input():
    """模拟音频输入"""
    print("=" * 50)
    print("模拟音频输入以触发艺术作品生成")
    print("=" * 50)
    
    # 检查测试音频文件
    test_audio = "test_input.wav"
    if not Path(test_audio).exists():
        print(f"测试音频文件不存在: {test_audio}")
        print("请确保已创建测试音频文件")
        return
    
    print(f"找到测试音频文件: {test_audio}")
    
    # 启动目录监控
    monitor_thread = threading.Thread(target=monitor_output_directory, daemon=True)
    monitor_thread.start()
    
    # 等待一下让监控开始
    time.sleep(2)
    
    # 播放音频文件
    print("开始播放音频...")
    success = play_audio_file(test_audio)
    
    if success:
        print("音频播放完成")
        print("等待艺术作品生成...")
        
        # 等待生成完成
        time.sleep(10)
        
        # 检查www目录的文件
        www_dir = Path("www")
        if www_dir.exists():
            files = list(www_dir.glob("*"))
            print(f"www目录文件: {[f.name for f in files]}")
            
            # 检查关键文件的时间戳
            key_files = ["cover.png", "loop.mp4", "meta.json"]
            for filename in key_files:
                file_path = www_dir / filename
                if file_path.exists():
                    mtime = file_path.stat().st_mtime
                    print(f"{filename}: {time.ctime(mtime)}")
                else:
                    print(f"{filename}: 不存在")
        else:
            print("www目录不存在")
    else:
        print("音频播放失败")
    
    print("模拟完成")

if __name__ == "__main__":
    simulate_audio_input()