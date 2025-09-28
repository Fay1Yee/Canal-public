# 水上书 WaterBook

🌊 **运河环境声音艺术生成器** - 采集运河环境声音特征，生成独特的水墨风格艺术作品

## 📖 项目概述

水上书是一个创新的环境声音艺术生成系统，专门采集和分析运河环境中的自然声音（水流声、船只声、鸟鸣声、风声等），运用基于规则的映射算法生成相应的水墨书法艺术参数，最终输出包含封面图像、动画视频和元数据的完整艺术作品。

### ✨ 核心特色

- 🎵 **运河环境声音采集与分析** - 专业采集35秒运河环境声音，提取水流、船只、鸟类等特征
- 🖌️ **智能水墨艺术映射** - 将环境声音特征映射为水墨参数（笔速、粗细、飞白、墨晕、停顿强度等）
- 🎭 **多风格生成** - 提供行书、篆书、水墨晕染三种书法风格
- 📱 **沉浸式运河场景界面** - 基于Pygame的全屏交互界面，呈现完整运河环境
- 🌐 **本地Web服务** - 自动生成精美下载页面，支持二维码分享
- 🔧 **跨平台兼容** - 支持树莓派GPIO和键盘模拟，适配不同硬件环境

## 🏗️ 系统架构

```
E0 吸引 → E1 聆听 → E2 采集 → E3 生成 → E4 选择 → E5 展示 → E6 重置
    ↑                                                                        ↓
    └─────────────────── 循环状态机 ──────────────────────────────┘
```

### 状态说明

- **E0 吸引**: 展示运河水墨主题，等待用户交互
- **E1 聆听**: 环境声音检测和采集准备（8秒）
- **E2 采集**: 运河环境声音采集和实时频谱显示（30-45秒）
- **E3 生成**: 环境声音特征分析和内容生成（≤2秒）
- **E4 选择**: 水墨风格选择界面（5-10秒）
- **E5 展示**: 艺术作品展示和下载页面（10-15秒）
- **E6 重置**: 清理和重置（5秒）

## 🌊 运河环境声音特征

### 专业声音识别
- **水流声检测** (50-500 Hz) - 识别运河水流的连续性和强度
- **船只引擎声** (100-1000 Hz) - 检测船只航行和引擎特征
- **鸟类活动** (1000-8000 Hz) - 捕捉运河沿岸鸟类鸣叫
- **风声环境音** (20-200 Hz) - 分析环境风声和氛围音

### 环境指标计算
- **水流指示器** - 基于低频一致性的水流检测
- **船只活动指示器** - 中频峰值的船只检测
- **鸟类活动指示器** - 高频突发的鸟类检测
- **运河氛围综合评分** - 多特征融合的环境评估

## 📋 系统要求

### 硬件要求

- **推荐**: 树莓派 4B/5 (4GB+ RAM)
- **最低**: 支持Python 3.8+的任意设备
- **音频**: 高质量麦克风或音频输入设备（用于环境声音采集）
- **显示**: 1280x720或更高分辨率显示器
- **存储**: 至少2GB可用空间

### 软件要求

- **操作系统**: Linux (推荐树莓派OS)、macOS、Windows
- **Python**: 3.8或更高版本
- **音频系统**: ALSA/PulseAudio (Linux) 或系统默认 (macOS/Windows)

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-repo/canal-ink-wash.git
cd canal-ink-wash
```

### 2. 安装依赖

```bash
# 使用脚本自动安装
./scripts/run.sh -i

# 或手动安装
pip3 install -r requirements.txt
```

### 3. 运行应用

```bash
# 直接运行
python3 app.py

# 或使用启动脚本
./scripts/run.sh

# 非树莓派环境（使用键盘模拟）
./scripts/run.sh --no-gpio
```

## ⚙️ 配置

### config.yaml 配置文件

```yaml
audio:
  samplerate: 32000      # 采样率
  channels: 1            # 声道数
  record_seconds: 35     # 环境声音采集时长
  frame_ms: 20          # 帧长度
  band_splits_hz: [300, 2000]  # 频带分割点

gpio:
  button_pin: 17        # GPIO按钮引脚
  long_press_sec: 1.2   # 长按时间阈值

ui:
  width: 1280           # 界面宽度
  height: 720           # 界面高度
  font: "assets/fonts/NotoSansSC-Regular.otf"  # 字体文件

server:
  port: 8000            # Web服务端口

states:
  E1_seconds: 8         # 各状态持续时间
  E4_seconds: 8
  E5_seconds: 12
  E6_seconds: 5
```

## 🎮 使用说明

### 树莓派GPIO操作

- **GPIO17 短按**: 确认/下一步
- **GPIO17 长按**: 特殊操作（跳过倒计时等）

### 键盘操作（非GPIO环境）

- **空格键**: 短按操作
- **回车键**: 长按操作
- **ESC键**: 退出应用
- **F11键**: 切换全屏

### 界面导航

1. **E0 吸引**: 按任意键开始聆听运河环境
2. **E1 聆听**: 保持安静，让设备检测环境声音
3. **E2 采集**: 系统自动采集运河环境声音，观察实时频谱
4. **E3 生成**: 自动处理环境声音特征，请等待
5. **E4 选择**: 短按切换水墨风格，长按确认选择
6. **E5 展示**: 查看艺术作品，扫描二维码下载
7. **E6 重置**: 自动重置到E0

## 🌊 运河可视化特色

### 沉浸式运河场景
- **动态水波** - 根据环境声音强度实时变化的运河水面
- **航行船只** - 3艘不同大小的船只在运河中自然航行
- **传统桥梁** - 运河特色桥梁，颜色随音频特征变化
- **河岸环境** - 完整的建筑、树木、天空运河环境

### 专业音频可视化
- **频谱水面反射** - 音频频谱以水面反射形式呈现
- **环境声音指示器** - 实时显示水流、船只、鸟类检测结果
- **运河主题配色** - 运河蓝、运河绿、桥梁棕等专属色彩

## 📁 项目结构

```
canal-ink-wash/
├── app.py              # 主程序入口
├── audio_rec.py        # 环境声音采集和特征提取
├── canal_visualizer.py # 运河场景可视化
├── generator.py        # 内容生成和规则映射
├── visual.py           # UI渲染和界面绘制
├── ink_wash_pygame.py  # 水墨风格渲染
├── server.py           # Web服务器
├── config.yaml         # 配置文件
├── requirements.txt    # Python依赖
├── README.md          # 项目文档
├── assets/            # 资源文件
│   ├── words.json     # 象声词词典
│   ├── fonts/         # 字体文件
│   └── icons/         # 图标文件
├── www/               # Web输出目录
│   ├── index.html     # 自动生成的主页
│   ├── cover.png      # 生成的封面
│   ├── loop.mp4       # 生成的动画
│   ├── raw.wav        # 采集的环境声音
│   └── meta.json      # 元数据
└── scripts/           # 脚本文件
    ├── run.sh         # 启动脚本
    └── waterbook.service  # systemd服务
```

## 🎨 艺术生成原理

### 环境声音到艺术参数映射

1. **水流声特征** → 笔画流畅度和连续性
2. **船只声特征** → 笔画力度和节奏变化
3. **鸟鸣声特征** → 飞白效果和灵动性
4. **风声特征** → 墨晕扩散和氛围感

### 水墨风格生成

- **行书风格** - 流畅自然，适合水流声主导的环境
- **篆书风格** - 古朴庄重，适合宁静的运河环境
- **水墨晕染** - 艺术表现，适合丰富的环境声音

## 🌐 Web服务

应用启动本地Web服务（端口8000），提供以下功能：

- **艺术作品展示页**: `http://localhost:8000/`
- **文件下载**: 封面图像、动画视频、原始环境声音、元数据
- **二维码分享**: 自动生成当前IP的访问二维码
- **响应式设计**: 支持手机和平板访问

## 📄 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [Pygame](https://www.pygame.org/) - 游戏开发库
- [librosa](https://librosa.org/) - 音频分析库
- [MoviePy](https://zulko.github.io/moviepy/) - 视频处理库
- [Pillow](https://pillow.readthedocs.io/) - 图像处理库

---

**运河水墨** - 聆听运河之声，创造水墨之美 🌊🎨✨

## 📋 System Requirements

### Hardware Requirements

- **Recommended**: Raspberry Pi 4B/5 (4GB+ RAM)
- **Minimum**: Any device supporting Python 3.8+
- **Audio**: Microphone or audio input device
- **Display**: 1280x720 or higher resolution monitor
- **Storage**: At least 2GB available space

### Software Requirements

- **Operating System**: Linux (recommended Raspberry Pi OS), macOS, Windows
- **Python**: 3.8 or higher
- **Audio System**: ALSA/PulseAudio (Linux) or system default (macOS/Windows)

## 🚀 Quick Start

### 1. Clone Project

```bash
git clone https://github.com/your-repo/waterbook-public.git
cd waterbook-public
```

### 2. Install Dependencies

```bash
# Use script for automatic installation
./scripts/run.sh -i

# Or install manually
pip3 install -r requirements.txt
```

### 3. Run Application

```bash
# Run directly
python3 app.py

# Or use startup script
./scripts/run.sh

# Non-Raspberry Pi environment (using keyboard simulation)
./scripts/run.sh --no-gpio
```

## 🔧 Detailed Installation

### Raspberry Pi Installation

1. **Update System**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install System Dependencies**
   ```bash
   sudo apt install -y python3-pip python3-dev python3-venv
   sudo apt install -y libasound2-dev portaudio19-dev
   sudo apt install -y libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
   sudo apt install -y ffmpeg
   ```

3. **Configure Audio Permissions**
   ```bash
   sudo usermod -a -G audio $USER
   ```

4. **Configure GPIO Permissions**
   ```bash
   sudo usermod -a -G gpio $USER
   ```

5. **Restart System**
   ```bash
   sudo reboot
   ```

### macOS/Linux Installation

1. **Install Homebrew** (macOS)
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install System Dependencies**
   ```bash
   # macOS
   brew install python3 portaudio ffmpeg sdl2 sdl2_image sdl2_mixer sdl2_ttf
   
   # Ubuntu/Debian
   sudo apt install python3-pip portaudio19-dev ffmpeg libsdl2-dev
   
   # CentOS/RHEL
   sudo yum install python3-pip portaudio-devel ffmpeg SDL2-devel
   ```

3. **Create Virtual Environment** (Recommended)
   ```bash
   python3 -m venv waterbook-env
   source waterbook-env/bin/activate  # Linux/macOS
   # waterbook-env\Scripts\activate  # Windows
   ```

## ⚙️ Configuration

### config.yaml Configuration File

```yaml
audio:
  samplerate: 32000      # Sample rate
  channels: 1            # Number of channels
  record_seconds: 35     # Recording duration
  frame_ms: 20          # Frame length
  band_splits_hz: [300, 2000]  # Frequency band split points

gpio:
  button_pin: 17        # GPIO button pin
  long_press_sec: 1.2   # Long press time threshold

ui:
  width: 1280           # Interface width
  height: 720           # Interface height
  font: "assets/fonts/NotoSansSC-Regular.otf"  # Font file

server:
  port: 8000            # Web service port

states:
  E1_seconds: 8         # Duration of each state
  E4_seconds: 8
  E5_seconds: 12
  E6_seconds: 5
```

### Environment Variables

```bash
# Disable GPIO (non-Raspberry Pi environment)
export WATERBOOK_NO_GPIO=1

# Use virtual audio recording
export WATERBOOK_VIRTUAL_AUDIO=1

# Set log level
export WATERBOOK_LOG_LEVEL=DEBUG
```

## 🎮 Usage Instructions

### Raspberry Pi GPIO Operations

- **GPIO17 Short Press**: Confirm/Next step
- **GPIO17 Long Press**: Special operations (skip countdown, etc.)

### Keyboard Operations (Non-GPIO Environment)

- **Space Key**: Short press operation
- **Enter Key**: Long press operation
- **ESC Key**: Exit application
- **F11 Key**: Toggle fullscreen

### Interface Navigation

1. **E0 Attract**: Press any key to start
2. **E1 Guide**: Stand at designated position, wait for countdown or long press to skip
3. **E2 Record**: Speak into microphone, observe real-time spectrum
4. **E3 Generate**: Automatic processing, please wait
5. **E4 Select**: Short press to switch styles, long press to confirm selection
6. **E5 Display**: View artwork, scan QR code to download
7. **E6 Reset**: Automatically reset to E0

## 🌐 Web Service

The application starts a local web service on port 8000, providing the following features:

- **Artwork Display Page**: `http://localhost:8000/`
- **File Download**: Cover images, animated videos, original audio, metadata
- **QR Code Sharing**: Automatically generates access QR code for current IP
- **Responsive Design**: Supports mobile and tablet access

### Access URLs

- Local access: `http://localhost:8000`
- Network access: `http://[Device IP]:8000`
- QR Code: Displayed in bottom right corner of application interface

## 📁 Project Structure

```
waterbook_public/
├── app.py              # Main program entry
├── audio_rec.py        # Audio recording and feature extraction
├── generator.py        # Content generation and rule mapping
├── visual.py           # UI rendering and interface drawing
├── server.py           # Web server
├── config.yaml         # Configuration file
├── requirements.txt    # Python dependencies
├── README.md          # Project documentation
├── assets/            # Resource files
│   ├── words.json     # Onomatopoeia dictionary
│   ├── fonts/         # Font files
│   ├── icons/         # Icon files
│   └── best_loops/    # Attract loop materials
├── www/               # Web output directory
│   ├── index.html     # Auto-generated homepage
│   ├── cover.png      # Generated cover
│   ├── loop.mp4       # Generated animation
│   ├── raw.wav        # Recorded audio
│   └── meta.json      # Metadata
└── scripts/           # Script files
    ├── run.sh         # Startup script
    └── waterbook.service  # systemd service
```

## 🔧 Advanced Configuration

### System Service Installation

1. **Copy Service File**
   ```bash
   sudo cp scripts/waterbook.service /etc/systemd/system/
   ```

2. **Modify Service Configuration**
   ```bash
   sudo nano /etc/systemd/system/waterbook.service
   # Modify User, WorkingDirectory, ExecStart and other paths
   ```

3. **Enable Service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable waterbook.service
   sudo systemctl start waterbook.service
   ```

4. **Check Status**
   ```bash
   sudo systemctl status waterbook.service
   sudo journalctl -u waterbook.service -f
   ```

### Performance Optimization

1. **GPU Memory Allocation** (Raspberry Pi)
   ```bash
   sudo raspi-config
   # Advanced Options -> Memory Split -> 128
   ```

2. **Audio Buffer Optimization**
   ```bash
   # Adjust in config.yaml
   audio:
     frame_ms: 10  # Reduce latency
     buffer_size: 1024  # Adjust buffer size
   ```

3. **Video Generation Optimization**
   ```bash
   # Lower resolution to improve generation speed
   generation:
     video_resolution: [640, 360]
     video_fps: 15
   ```

## 🐛 Troubleshooting

### Common Issues

#### 1. Audio Device Issues

**Problem**: Cannot record audio or "device busy" error

**Solution**:
```bash
# Check audio devices
aplay -l
arecord -l

# Kill processes using audio
sudo fuser -k /dev/snd/*

# Restart audio services
sudo systemctl restart alsa-state
sudo systemctl restart pulseaudio

# Check permissions
sudo usermod -a -G audio $USER
```

#### 2. GPIO Permission Issues

**Problem**: GPIO access denied

**Solution**:
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Check device file permissions
ls -l /dev/gpiomem

# Reboot to take effect
sudo reboot
```

#### 3. Display Issues

**Problem**: Cannot start graphical interface or fullscreen display abnormal

**Solution**:
```bash
# Check display environment
echo $DISPLAY
echo $XDG_RUNTIME_DIR

# Set display permissions
xhost +local:

# Force use X11
export SDL_VIDEODRIVER=x11

# Or use Wayland
export SDL_VIDEODRIVER=wayland
```

#### 4. Dependency Installation Issues

**Problem**: pip installation fails or missing system libraries

**Solution**:
```bash
# Update pip
pip3 install --upgrade pip setuptools wheel

# Install build tools
sudo apt install build-essential python3-dev

# Clear pip cache
pip3 cache purge

# Use domestic mirror
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

#### 5. Performance Issues

**Problem**: Application runs slowly or stutters

**Solution**:
```bash
# Check system resources
top
free -h
df -h

# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable wifi-powersave

# Adjust configuration to reduce resource consumption
# In config.yaml:
ui:
  width: 1024
  height: 576
audio:
  samplerate: 22050
```

### Log Debugging

```bash
# View application logs
./scripts/run.sh -l

# View system logs
sudo journalctl -u waterbook.service --no-pager

# Enable debug mode
export WATERBOOK_LOG_LEVEL=DEBUG
python3 app.py
```

## 🤝 Development Guide

### Development Environment Setup

```bash
# Clone project
git clone https://github.com/your-repo/waterbook-public.git
cd waterbook-public

# Create development environment
python3 -m venv dev-env
source dev-env/bin/activate

# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8 mypy

# Run development mode
./scripts/run.sh -d
```

### Code Structure

- **app.py**: Main program and state machine logic
- **visual.py**: UI rendering, contains all drawing functions
- **audio_rec.py**: Audio recording and feature extraction
- **generator.py**: Content generation and rule mapping
- **server.py**: Web server and page generation

### Adding New Features

1. **New State**: Extend state machine in app.py
2. **New Style**: Add style generation logic in generator.py
3. **New UI**: Add drawing functions in visual.py
4. **New Features**: Extend feature extraction in audio_rec.py

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Pygame](https://www.pygame.org/) - Game development library
- [librosa](https://librosa.org/) - Audio analysis library
- [MoviePy](https://zulko.github.io/moviepy/) - Video processing library
- [Pillow](https://pillow.readthedocs.io/) - Image processing library

## 📞 Support

If you encounter issues or have suggestions, please:

1. Check the troubleshooting section of this documentation
2. Search existing [Issues](https://github.com/your-repo/waterbook-public/issues)
3. Create a new Issue describing your problem
4. Contact the development team

---

**Waterbook Public** - Transform sound into art, let technology serve creativity 🎨✨