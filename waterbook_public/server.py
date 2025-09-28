#!/usr/bin/env python3
"""
运河水墨Web服务器
提供艺术作品展示页面、文件下载和二维码分享功能
支持响应式设计，适配手机和平板访问
"""

import os
import json
import socket
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from typing import Dict, Any, Optional
import mimetypes
from datetime import datetime

from generator import GeneratedArt

class CanalWebHandler(BaseHTTPRequestHandler):
    """运河水墨Web请求处理器"""
    
    def __init__(self, *args, server_instance=None, **kwargs):
        """初始化处理器"""
        self.server_instance = server_instance
        self.app_instance = server_instance.app_instance if server_instance else None
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理GET请求"""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            
            if path == '/':
                self._serve_main_page()
            elif path == '/api/status':
                self._serve_status_api()
            elif path.startswith('/api/'):
                self._serve_api_error(404, "API endpoint not found")
            elif path.endswith('.png') or path.endswith('.jpg') or path.endswith('.jpeg'):
                self._serve_static_file(path)
            elif path.endswith('.mp4') or path.endswith('.webm'):
                self._serve_video_file(path)
            elif path.endswith('.json'):
                self._serve_json_file(path)
            else:
                self._serve_404()
                
        except Exception as e:
            print(f"Web请求处理错误: {e}")
            self._serve_error(500, "Internal Server Error")
    
    def _serve_api_error(self, code: int, message: str):
        """返回API错误响应"""
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        error_response = {
            'error': message,
            'code': code,
            'timestamp': datetime.now().isoformat()
        }
        
        self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
    
    def _serve_error(self, code: int, message: str):
        """返回HTML错误页面"""
        self.send_response(code)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>错误 {code}</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h1>错误 {code}</h1>
            <p>{message}</p>
            <a href="/">返回主页</a>
        </body>
        </html>
        """
        
        self.wfile.write(error_html.encode('utf-8'))
    
    def _serve_404(self):
        """返回404页面"""
        self._serve_error(404, "页面未找到")
    
    def _serve_main_page(self):
        """提供主页"""
        try:
            html_content = self._generate_index_html()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(html_content.encode('utf-8'))))
            self.end_headers()
            
            self.wfile.write(html_content.encode('utf-8'))
            
        except Exception as e:
            print(f"主页生成错误: {e}")
            self._send_error_response(500, "Failed to generate page")
    
    def _serve_status_api(self):
        """提供状态API"""
        status = {
            'server': 'Waterbook Web Server',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat(),
            'has_artwork': self.app_instance and hasattr(self.app_instance, 'generated_art') and self.app_instance.generated_art is not None
        }
        
        self._send_json_response(status)
    
    def _serve_metadata_api(self):
        """提供元数据API"""
        if self.server_instance and self.server_instance.current_art:
            metadata = self.server_instance.current_art.metadata
            self._send_json_response(metadata)
        else:
            self._send_json_response({'error': 'No artwork available'}, 404)
    
    def _serve_download(self, path: str):
        """提供文件下载"""
        # 提取文件名
        filename = path.split('/')[-1]
        
        # 安全检查
        if '..' in filename or '/' in filename:
            self._send_error_response(400, "Invalid filename")
            return
        
        # 查找文件
        file_path = Path('www') / filename
        
        if not file_path.exists():
            self._send_error_response(404, "File not found")
            return
        
        try:
            # 确定MIME类型
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type is None:
                mime_type = 'application/octet-stream'
            
            # 读取文件
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # 发送响应
            self.send_response(200)
            self.send_header('Content-Type', mime_type)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.end_headers()
            
            self.wfile.write(content)
            
        except Exception as e:
            print(f"文件下载错误: {e}")
            self._send_error_response(500, "Download failed")
    
    def _serve_static_file(self, path: str):
        """提供静态文件"""
        # 移除开头的斜杠
        if path.startswith('/'):
            path = path[1:]
        
        # 安全检查
        if '..' in path:
            self._send_error_response(400, "Invalid path")
            return
        
        file_path = Path('www') / path
        
        if not file_path.exists():
            self._send_error_response(404, "File not found")
            return
        
        try:
            # 确定MIME类型
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type is None:
                mime_type = 'application/octet-stream'
            
            # 读取文件
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # 发送响应
            self.send_response(200)
            self.send_header('Content-Type', mime_type)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            
            self.wfile.write(content)
            
        except Exception as e:
            print(f"静态文件服务错误: {e}")
            self._send_error_response(500, "File serve failed")
    
    def _send_json_response(self, data: Dict[str, Any], status_code: int = 200):
        """发送JSON响应"""
        json_content = json.dumps(data, ensure_ascii=False, indent=2)
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(json_content.encode('utf-8'))))
        self.end_headers()
        
        self.wfile.write(json_content.encode('utf-8'))
    
    def _send_error_response(self, status_code: int, message: str):
        """发送错误响应"""
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>错误 {status_code}</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h1>错误 {status_code}</h1>
            <p>{message}</p>
        </body>
        </html>
        """
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(error_html.encode('utf-8'))))
        self.end_headers()
        
        self.wfile.write(error_html.encode('utf-8'))
    
    def _generate_index_html(self) -> str:
        """生成主页HTML"""
        
        # 获取当前艺术作品信息
        if self.app_instance and hasattr(self.app_instance, 'generated_art') and self.app_instance.generated_art:
            art = self.app_instance.generated_art
            has_art = True
            
            title = art.metadata.get('title', '水上书作品')
            style = art.parameters.style
            content_text = art.parameters.content_text
            creation_time = art.creation_time.strftime('%Y年%m月%d日 %H:%M:%S')
            
            # 音频特征
            water_flow = art.parameters.water_influence
            boat_activity = art.parameters.boat_influence
            bird_activity = art.parameters.bird_influence
            wind_strength = art.parameters.wind_influence
            
            # 艺术参数
            brush_thickness = art.parameters.brush_thickness
            ink_density = art.parameters.ink_density
            flywhite_intensity = art.parameters.flywhite_intensity
            tranquility = art.parameters.tranquility
            elegance = art.parameters.elegance
            
        else:
            has_art = False
            title = "水上书"
            style = ""
            content_text = ""
            creation_time = ""
            water_flow = boat_activity = bird_activity = wind_strength = 0
            brush_thickness = ink_density = flywhite_intensity = tranquility = elegance = 0
        
        # 获取服务器IP
        try:
            hostname = socket.gethostname()
            server_ip = socket.gethostbyname(hostname)
        except:
            server_ip = "localhost"
        
        html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #f5f5f0 0%, #e8e8e0 100%);
            color: #1e1e1e;
            line-height: 1.6;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 30px 0;
            background: rgba(255, 255, 255, 0.8);
            border-radius: 15px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }}
        
        .header h1 {{
            font-size: 2.5em;
            color: #2d5a87;
            margin-bottom: 10px;
            font-weight: 300;
        }}
        
        .header p {{
            font-size: 1.1em;
            color: #666;
        }}
        
        .artwork-section {{
            display: {'block' if has_art else 'none'};
            margin-bottom: 40px;
        }}
        
        .artwork-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }}
        
        .artwork-display {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            text-align: center;
        }}
        
        .artwork-image {{
            max-width: 100%;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
            margin-bottom: 15px;
        }}
        
        .artwork-info {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }}
        
        .info-section {{
            margin-bottom: 25px;
        }}
        
        .info-section h3 {{
            color: #2d5a87;
            margin-bottom: 15px;
            font-size: 1.3em;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 5px;
        }}
        
        .info-item {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            padding: 5px 0;
        }}
        
        .info-label {{
            font-weight: 500;
            color: #555;
        }}
        
        .info-value {{
            color: #2d5a87;
            font-weight: 600;
        }}
        
        .progress-bar {{
            width: 100px;
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #4a90e2, #7bb3f0);
            border-radius: 4px;
            transition: width 0.3s ease;
        }}
        
        .download-section {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            text-align: center;
        }}
        
        .download-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .download-item {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            text-decoration: none;
            color: #333;
            transition: all 0.3s ease;
            border: 2px solid transparent;
        }}
        
        .download-item:hover {{
            background: #e9ecef;
            border-color: #4a90e2;
            transform: translateY(-2px);
        }}
        
        .download-icon {{
            font-size: 2em;
            margin-bottom: 10px;
            display: block;
        }}
        
        .no-artwork {{
            display: {'none' if has_art else 'block'};
            text-align: center;
            padding: 60px 20px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }}
        
        .no-artwork h2 {{
            color: #666;
            margin-bottom: 15px;
        }}
        
        .no-artwork p {{
            color: #999;
            font-size: 1.1em;
        }}
        
        .status-indicator {{
            margin: 20px 0;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }}
        
        .status-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #ccc;
            animation: pulse 2s infinite;
        }}
        
        .status-dot.status-success {{
            background: #28a745;
        }}
        
        .status-dot.status-waiting {{
            background: #ffc107;
        }}
        
        .status-dot.status-error {{
            background: #dc3545;
        }}
        
        .instructions {{
            margin-top: 30px;
            text-align: left;
            max-width: 400px;
            margin-left: auto;
            margin-right: auto;
        }}
        
        .instructions h3 {{
            color: #2d5a87;
            margin-bottom: 15px;
            text-align: center;
        }}
        
        .instructions ol {{
            color: #666;
            line-height: 1.8;
        }}
        
        .instructions li {{
            margin-bottom: 8px;
        }}
        
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
            100% {{ opacity: 1; }}
        }}
        
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            .artwork-grid {{
                grid-template-columns: 1fr;
            }}
            
            .container {{
                padding: 10px;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
            
            .download-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>水上书</h1>
            <p>Waterbook - 水上环境声音艺术生成器</p>
        </div>
        
        <div class="artwork-section">
            <div class="artwork-grid">
                <div class="artwork-display">
                    <img src="cover.png" alt="水墨作品" class="artwork-image" onerror="this.style.display='none'">
                    <h3>{content_text}</h3>
                    <p>风格：{style}</p>
                </div>
                
                <div class="artwork-info">
                    <div class="info-section">
                        <h3>作品信息</h3>
                        <div class="info-item">
                            <span class="info-label">标题：</span>
                            <span class="info-value">{title}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">风格：</span>
                            <span class="info-value">{style}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">内容：</span>
                            <span class="info-value">{content_text}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">创作时间：</span>
                            <span class="info-value">{creation_time}</span>
                        </div>
                    </div>
                    
                    <div class="info-section">
                        <h3>环境声音分析</h3>
                        <div class="info-item">
                            <span class="info-label">水流强度：</span>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {water_flow*100:.0f}%"></div>
                            </div>
                        </div>
                        <div class="info-item">
                            <span class="info-label">船只活动：</span>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {boat_activity*100:.0f}%"></div>
                            </div>
                        </div>
                        <div class="info-item">
                            <span class="info-label">鸟类活动：</span>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {bird_activity*100:.0f}%"></div>
                            </div>
                        </div>
                        <div class="info-item">
                            <span class="info-label">风声强度：</span>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {wind_strength*100:.0f}%"></div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="info-section">
                        <h3>艺术参数</h3>
                        <div class="info-item">
                            <span class="info-label">笔触粗细：</span>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {brush_thickness*100:.0f}%"></div>
                            </div>
                        </div>
                        <div class="info-item">
                            <span class="info-label">墨浓度：</span>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {ink_density*100:.0f}%"></div>
                            </div>
                        </div>
                        <div class="info-item">
                            <span class="info-label">飞白强度：</span>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {flywhite_intensity*100:.0f}%"></div>
                            </div>
                        </div>
                        <div class="info-item">
                            <span class="info-label">宁静度：</span>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {tranquility*100:.0f}%"></div>
                            </div>
                        </div>
                        <div class="info-item">
                            <span class="info-label">雅致度：</span>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: {elegance*100:.0f}%"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="download-section">
                <h3>下载作品</h3>
                <p>点击下方链接下载完整的艺术作品文件</p>
                
                <div class="download-grid">
                    <a href="download/cover.png" class="download-item">
                        <span class="download-icon">🖼️</span>
                        <strong>封面图像</strong>
                        <p>PNG格式高清图像</p>
                    </a>
                    
                    <a href="download/loop.mp4" class="download-item">
                        <span class="download-icon">🎬</span>
                        <strong>动画视频</strong>
                        <p>MP4格式动画视频</p>
                    </a>
                    
                    <a href="download/raw.wav" class="download-item">
                        <span class="download-icon">🎵</span>
                        <strong>原始音频</strong>
                        <p>WAV格式环境声音</p>
                    </a>
                    
                    <a href="download/meta.json" class="download-item">
                        <span class="download-icon">📄</span>
                        <strong>元数据</strong>
                        <p>JSON格式详细信息</p>
                    </a>
                </div>
            </div>
        </div>
        
        <div class="no-artwork">
            <h2>暂无艺术作品</h2>
            <p>请在水上书应用中创作新的艺术作品</p>
            <div class="status-indicator">
                <div class="status-dot" id="statusDot"></div>
                <span id="statusText">检查应用状态中...</span>
            </div>
            <div class="instructions">
                <h3>使用说明</h3>
                <ol>
                    <li>确保水上书应用正在运行</li>
                    <li>按空格键或点击按钮开始录制环境声音</li>
                    <li>等待声音分析并生成水墨艺术作品</li>
                    <li>作品完成后将自动显示在此页面</li>
                </ol>
            </div>
        </div>
        
        <div class="footer">
            <p>水上书 Waterbook © 2024</p>
            <p>服务器地址: http://{server_ip}:8000</p>
            <p id="lastUpdate">最后更新: <span id="updateTime">--</span></p>
        </div>
    </div>
    
    <script>
        let statusCheckInterval;
        
        function updateStatus() {{
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {{
                    const statusDot = document.getElementById('statusDot');
                    const statusText = document.getElementById('statusText');
                    const updateTime = document.getElementById('updateTime');
                    
                    if (statusDot && statusText) {{
                        if (data.has_artwork) {{
                            statusDot.className = 'status-dot status-success';
                            statusText.textContent = '有新作品可用';
                            // 如果有新作品且当前显示无作品页面，则刷新
                            if (document.querySelector('.no-artwork').style.display !== 'none') {{
                                setTimeout(() => location.reload(), 1000);
                            }}
                        }} else {{
                            statusDot.className = 'status-dot status-waiting';
                            statusText.textContent = '等待新作品生成...';
                        }}
                    }}
                    
                    if (updateTime) {{
                        updateTime.textContent = new Date().toLocaleTimeString();
                    }}
                }})
                .catch(error => {{
                    const statusDot = document.getElementById('statusDot');
                    const statusText = document.getElementById('statusText');
                    
                    if (statusDot && statusText) {{
                        statusDot.className = 'status-dot status-error';
                        statusText.textContent = '连接失败';
                    }}
                }});
        }}
        
        // 页面加载完成后开始状态检查
        document.addEventListener('DOMContentLoaded', function() {{
            updateStatus();
            statusCheckInterval = setInterval(updateStatus, 3000);
        }});
        
        // 页面卸载时清理定时器
        window.addEventListener('beforeunload', function() {{
            if (statusCheckInterval) {{
                clearInterval(statusCheckInterval);
            }}
        }});
    </script>
</body>
</html>
        """
        
        return html_template

class WebServer:
    """运河水墨Web服务器"""
    
    def __init__(self, port: int = 8000):
        """初始化Web服务器"""
        self.port = port
        self.running = False
        self.server = None
        self.app_instance = None
        
        print(f"Web服务器初始化 - 端口: {port}")
    
    def set_app_instance(self, app_instance):
        """设置应用实例引用"""
        self.app_instance = app_instance
    
    def start(self):
        """启动Web服务器"""
        if self.running:
            return
        
        try:
            # 创建自定义处理器类
            def handler_factory(*args, **kwargs):
                return CanalWebHandler(*args, server_instance=self, **kwargs)
            
            # 创建HTTP服务器
            self.server = HTTPServer(('0.0.0.0', self.port), handler_factory)  # 绑定所有接口
            self.running = True
            
            print(f"Web服务器启动成功 - http://0.0.0.0:{self.port}")
            
            # 在单独线程中运行服务器，避免阻塞主线程
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            
        except Exception as e:
            print(f"Web服务器启动失败: {e}")
            self.running = False
    
    def stop(self):
        """停止Web服务器"""
        if self.server and self.running:
            self.server.shutdown()
            self.server.server_close()
            self.running = False
            # 等待服务器线程结束
            if hasattr(self, 'server_thread') and self.server_thread.is_alive():
                self.server_thread.join(timeout=1.0)
            print("Web服务器已停止")
    
    def update_content(self, generated_art: GeneratedArt):
        """更新Web内容"""
        self.current_art = generated_art
        
        try:
            # 保存元数据到JSON文件
            meta_path = self.www_dir / 'meta.json'
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(generated_art.metadata, f, ensure_ascii=False, indent=2)
            
            # 如果有音频文件，复制到www目录
            if generated_art.audio_file_path and Path(generated_art.audio_file_path).exists():
                import shutil
                shutil.copy2(generated_art.audio_file_path, self.www_dir / 'raw.wav')
            
            print("Web内容更新完成")
            
        except Exception as e:
            print(f"Web内容更新失败: {e}")
    
    def get_server_url(self) -> str:
        """获取服务器URL"""
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            return f"http://{local_ip}:{self.port}"
        except:
            return f"http://localhost:{self.port}"

# 测试代码
if __name__ == "__main__":
    # 测试Web服务器
    config = {'port': 8000}
    
    server = WebServer(config)
    
    print("启动测试Web服务器...")
    print(f"访问地址: {server.get_server_url()}")
    print("按Ctrl+C停止服务器")
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n停止服务器...")
        server.stop()
        print("测试完成")