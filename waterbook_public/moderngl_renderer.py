#!/usr/bin/env python3
"""
ModernGL GPU加速渲染系统
用于运河水墨的高性能水纹、倒影和粒子效果渲染
"""

import numpy as np
import pygame
from typing import Optional, Tuple, List
import math
import time

# 可选依赖处理
try:
    import moderngl
    HAS_MODERNGL = True
except ImportError:
    print("警告: ModernGL不可用，使用回退渲染")
    HAS_MODERNGL = False

class ModernGLRenderer:
    """ModernGL GPU加速渲染器"""
    
    def __init__(self, width: int, height: int):
        """初始化ModernGL渲染器"""
        self.width = width
        self.height = height
        self.ctx = None
        self.initialized = False
        
        if HAS_MODERNGL:
            try:
                self._init_moderngl()
                self._create_shaders()
                self._create_buffers()
                self.initialized = True
                print("ModernGL GPU渲染器初始化成功")
            except Exception as e:
                print(f"ModernGL初始化失败，使用CPU渲染: {e}")
                self.initialized = False
        else:
            print("ModernGL不可用，使用CPU渲染")
    
    def _init_moderngl(self):
        """初始化ModernGL上下文"""
        # 创建OpenGL上下文
        self.ctx = moderngl.create_context()
        
        # 创建帧缓冲区
        self.fbo = self.ctx.framebuffer(
            color_attachments=[self.ctx.texture((self.width, self.height), 4)]
        )
        
        # 设置视口
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
    
    def _create_shaders(self):
        """创建着色器程序"""
        
        # 水波着色器
        self.water_shader = self._create_water_shader()
        
        # 倒影着色器
        self.reflection_shader = self._create_reflection_shader()
        
        # 粒子着色器
        self.particle_shader = self._create_particle_shader()
        
        # 频谱可视化着色器
        self.spectrum_shader = self._create_spectrum_shader()
    
    def _create_water_shader(self):
        """创建水波着色器"""
        vertex_shader = """
        #version 330 core
        
        in vec2 position;
        in vec2 texcoord;
        
        out vec2 v_texcoord;
        out vec2 v_position;
        
        uniform float time;
        uniform vec2 resolution;
        
        void main() {
            v_texcoord = texcoord;
            v_position = position;
            
            // 添加水波动画
            vec2 wave_pos = position;
            wave_pos.y += sin(position.x * 10.0 + time * 2.0) * 0.02;
            wave_pos.y += sin(position.x * 15.0 + time * 3.0) * 0.01;
            
            gl_Position = vec4(wave_pos, 0.0, 1.0);
        }
        """
        
        fragment_shader = """
        #version 330 core
        
        in vec2 v_texcoord;
        in vec2 v_position;
        
        out vec4 fragColor;
        
        uniform float time;
        uniform vec2 resolution;
        uniform float audio_intensity;
        uniform vec3 water_color;
        
        // 噪声函数
        float noise(vec2 p) {
            return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
        }
        
        // 水波函数
        float water_wave(vec2 pos, float time) {
            float wave = 0.0;
            wave += sin(pos.x * 8.0 + time * 1.5) * 0.1;
            wave += sin(pos.y * 6.0 + time * 2.0) * 0.08;
            wave += sin((pos.x + pos.y) * 4.0 + time * 1.2) * 0.06;
            return wave;
        }
        
        void main() {
            vec2 uv = v_texcoord;
            vec2 pos = v_position;
            
            // 基础水色
            vec3 color = water_color;
            
            // 水波扰动
            float wave = water_wave(pos * 5.0, time);
            wave *= (1.0 + audio_intensity * 2.0);  // 音频响应
            
            // 添加波纹效果
            float ripple = sin(length(pos - vec2(0.5)) * 20.0 - time * 4.0) * 0.1;
            wave += ripple;
            
            // 水面反射
            float reflection = smoothstep(0.4, 0.6, uv.y + wave * 0.1);
            color = mix(color, color * 1.3, reflection);
            
            // 添加噪声纹理
            float n = noise(uv * 100.0 + time * 0.1);
            color += n * 0.05;
            
            // 透明度基于深度
            float alpha = 0.8 + wave * 0.2;
            
            fragColor = vec4(color, alpha);
        }
        """
        
        return self.ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
    
    def _create_reflection_shader(self):
        """创建倒影着色器"""
        vertex_shader = """
        #version 330 core
        
        in vec2 position;
        in vec2 texcoord;
        
        out vec2 v_texcoord;
        
        void main() {
            v_texcoord = texcoord;
            gl_Position = vec4(position, 0.0, 1.0);
        }
        """
        
        fragment_shader = """
        #version 330 core
        
        in vec2 v_texcoord;
        out vec4 fragColor;
        
        uniform sampler2D scene_texture;
        uniform float time;
        uniform float reflection_strength;
        
        void main() {
            vec2 uv = v_texcoord;
            
            // 翻转Y坐标创建倒影
            vec2 reflection_uv = vec2(uv.x, 1.0 - uv.y);
            
            // 添加水波扰动
            float wave_distort = sin(uv.x * 10.0 + time * 2.0) * 0.01;
            wave_distort += sin(uv.x * 15.0 + time * 3.0) * 0.005;
            reflection_uv.x += wave_distort;
            
            // 采样场景纹理
            vec4 reflection_color = texture(scene_texture, reflection_uv);
            
            // 调整倒影强度和颜色
            reflection_color.rgb *= reflection_strength;
            reflection_color.rgb = mix(reflection_color.rgb, vec3(0.2, 0.4, 0.6), 0.3);
            
            // 距离衰减
            float fade = smoothstep(0.0, 0.5, uv.y);
            reflection_color.a *= fade;
            
            fragColor = reflection_color;
        }
        """
        
        return self.ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
    
    def _create_particle_shader(self):
        """创建粒子着色器"""
        vertex_shader = """
        #version 330 core
        
        in vec2 position;
        in vec2 velocity;
        in float life;
        in float size;
        
        out float v_life;
        out float v_size;
        
        uniform float time;
        uniform mat4 projection;
        
        void main() {
            v_life = life;
            v_size = size;
            
            // 粒子位置更新
            vec2 pos = position + velocity * time;
            
            gl_Position = projection * vec4(pos, 0.0, 1.0);
            gl_PointSize = size * (1.0 - life);  // 生命周期影响大小
        }
        """
        
        fragment_shader = """
        #version 330 core
        
        in float v_life;
        in float v_size;
        
        out vec4 fragColor;
        
        uniform vec3 particle_color;
        
        void main() {
            // 圆形粒子
            vec2 coord = gl_PointCoord - vec2(0.5);
            float dist = length(coord);
            
            if (dist > 0.5) {
                discard;
            }
            
            // 软边缘
            float alpha = 1.0 - smoothstep(0.3, 0.5, dist);
            alpha *= (1.0 - v_life);  // 生命周期影响透明度
            
            fragColor = vec4(particle_color, alpha);
        }
        """
        
        return self.ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
    
    def _create_spectrum_shader(self):
        """创建频谱可视化着色器"""
        vertex_shader = """
        #version 330 core
        
        in vec2 position;
        in float frequency;
        in float amplitude;
        
        out float v_amplitude;
        out vec2 v_position;
        
        uniform float time;
        
        void main() {
            v_amplitude = amplitude;
            v_position = position;
            
            // 频谱条高度
            vec2 pos = position;
            pos.y *= amplitude;
            
            gl_Position = vec4(pos, 0.0, 1.0);
        }
        """
        
        fragment_shader = """
        #version 330 core
        
        in float v_amplitude;
        in vec2 v_position;
        
        out vec4 fragColor;
        
        uniform vec3 spectrum_color;
        uniform float time;
        
        void main() {
            // 基于幅度的颜色
            vec3 color = spectrum_color;
            color = mix(color, color * 2.0, v_amplitude);
            
            // 添加闪烁效果
            float flicker = sin(time * 10.0 + v_position.x * 20.0) * 0.1 + 0.9;
            color *= flicker;
            
            // 透明度基于幅度
            float alpha = v_amplitude * 0.8 + 0.2;
            
            fragColor = vec4(color, alpha);
        }
        """
        
        return self.ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
    
    def _create_buffers(self):
        """创建顶点缓冲区"""
        # 全屏四边形
        quad_vertices = np.array([
            -1.0, -1.0, 0.0, 0.0,  # 左下
             1.0, -1.0, 1.0, 0.0,  # 右下
             1.0,  1.0, 1.0, 1.0,  # 右上
            -1.0,  1.0, 0.0, 1.0   # 左上
        ], dtype=np.float32)
        
        quad_indices = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)
        
        self.quad_vbo = self.ctx.buffer(quad_vertices.tobytes())
        self.quad_ibo = self.ctx.buffer(quad_indices.tobytes())
        
        # 创建VAO
        self.quad_vao = self.ctx.vertex_array(
            self.water_shader,
            [(self.quad_vbo, '2f 2f', 'position', 'texcoord')],
            self.quad_ibo
        )
    
    def render_water_surface(self, audio_intensity: float = 0.0, 
                           water_color: Tuple[float, float, float] = (0.2, 0.4, 0.6)) -> Optional[pygame.Surface]:
        """渲染水面效果"""
        if not self.initialized:
            return None
        
        try:
            # 绑定帧缓冲区
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 0.0)
            
            # 设置uniform变量
            self.water_shader['time'] = time.time()
            self.water_shader['resolution'] = (self.width, self.height)
            self.water_shader['audio_intensity'] = audio_intensity
            self.water_shader['water_color'] = water_color
            
            # 渲染
            self.quad_vao.render()
            
            # 读取像素数据
            data = self.fbo.color_attachments[0].read()
            
            # 转换为pygame surface
            surface = pygame.image.fromstring(data, (self.width, self.height), 'RGBA')
            return pygame.transform.flip(surface, False, True)  # 翻转Y轴
            
        except Exception as e:
            print(f"GPU水面渲染错误: {e}")
            return None
    
    def render_spectrum_reflection(self, spectrum_data: np.ndarray) -> Optional[pygame.Surface]:
        """渲染频谱倒影效果"""
        if not self.initialized or spectrum_data is None:
            return None
        
        try:
            # 创建频谱顶点数据
            bar_count = len(spectrum_data)
            vertices = []
            
            for i, amplitude in enumerate(spectrum_data):
                x = (i / bar_count) * 2.0 - 1.0  # 归一化到[-1, 1]
                vertices.extend([
                    x, -1.0, i / bar_count, amplitude,  # 底部
                    x,  1.0, i / bar_count, amplitude   # 顶部
                ])
            
            vertices = np.array(vertices, dtype=np.float32)
            
            # 更新缓冲区
            spectrum_vbo = self.ctx.buffer(vertices.tobytes())
            spectrum_vao = self.ctx.vertex_array(
                self.spectrum_shader,
                [(spectrum_vbo, '2f 1f 1f', 'position', 'frequency', 'amplitude')]
            )
            
            # 渲染
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 0.0)
            
            self.spectrum_shader['time'] = time.time()
            self.spectrum_shader['spectrum_color'] = (0.3, 0.6, 0.9)
            
            spectrum_vao.render(moderngl.LINES)
            
            # 读取结果
            data = self.fbo.color_attachments[0].read()
            surface = pygame.image.fromstring(data, (self.width, self.height), 'RGBA')
            return pygame.transform.flip(surface, False, True)
            
        except Exception as e:
            print(f"GPU频谱渲染错误: {e}")
            return None
    
    def create_particle_system(self, particle_count: int = 1000):
        """创建粒子系统"""
        if not self.initialized:
            return None
        
        # 生成随机粒子数据
        positions = np.random.uniform(-1.0, 1.0, (particle_count, 2)).astype(np.float32)
        velocities = np.random.uniform(-0.1, 0.1, (particle_count, 2)).astype(np.float32)
        lives = np.random.uniform(0.0, 1.0, particle_count).astype(np.float32)
        sizes = np.random.uniform(2.0, 8.0, particle_count).astype(np.float32)
        
        # 交错数据
        particle_data = np.column_stack([positions, velocities, lives, sizes])
        
        return {
            'vbo': self.ctx.buffer(particle_data.tobytes()),
            'count': particle_count,
            'data': particle_data
        }
    
    def render_particles(self, particle_system: dict, particle_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)):
        """渲染粒子系统"""
        if not self.initialized or not particle_system:
            return None
        
        try:
            # 创建VAO
            particle_vao = self.ctx.vertex_array(
                self.particle_shader,
                [(particle_system['vbo'], '2f 2f 1f 1f', 'position', 'velocity', 'life', 'size')]
            )
            
            # 渲染
            self.fbo.use()
            
            # 设置投影矩阵
            projection = np.eye(4, dtype=np.float32)
            self.particle_shader['projection'].write(projection.tobytes())
            self.particle_shader['time'] = time.time()
            self.particle_shader['particle_color'] = particle_color
            
            # 启用点精灵
            self.ctx.enable(moderngl.PROGRAM_POINT_SIZE)
            particle_vao.render(moderngl.POINTS)
            
            # 读取结果
            data = self.fbo.color_attachments[0].read()
            surface = pygame.image.fromstring(data, (self.width, self.height), 'RGBA')
            return pygame.transform.flip(surface, False, True)
            
        except Exception as e:
            print(f"GPU粒子渲染错误: {e}")
            return None
    
    def cleanup(self):
        """清理资源"""
        if self.initialized and self.ctx:
            try:
                self.ctx.release()
                print("ModernGL资源已清理")
            except:
                pass

# CPU回退渲染器
class CPUFallbackRenderer:
    """CPU回退渲染器，当ModernGL不可用时使用"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        print("使用CPU回退渲染器")
    
    def render_water_surface(self, audio_intensity: float = 0.0, 
                           water_color: Tuple[float, float, float] = (0.2, 0.4, 0.6)) -> pygame.Surface:
        """CPU水面渲染 - 改进版本"""
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # 填充基础水面颜色
        base_color = tuple(int(c * 255) for c in water_color)
        surface.fill((*base_color, 180))  # 半透明水面
        
        # 多层水波效果
        current_time = time.time()
        
        # 主要水波
        wave_points = []
        for x in range(0, self.width, 8):
            wave1 = math.sin(x * 0.01 + current_time * 1.5) * 8 * (1 + audio_intensity * 0.5)
            wave2 = math.sin(x * 0.02 + current_time * 2.0) * 4 * (1 + audio_intensity * 0.3)
            wave_y = wave1 + wave2
            wave_points.append((x, int(wave_y)))
        
        # 绘制水波线条
        if len(wave_points) > 1:
            # 浅色水波线
            light_color = tuple(min(255, int(c * 255 * 1.3)) for c in water_color)
            for i in range(len(wave_points) - 1):
                start_pos = (wave_points[i][0], wave_points[i][1] + self.height // 2)
                end_pos = (wave_points[i+1][0], wave_points[i+1][1] + self.height // 2)
                pygame.draw.line(surface, light_color, start_pos, end_pos, 2)
        
        # 添加水面反光效果
        for i in range(0, self.width, 20):
            reflection_intensity = (math.sin(i * 0.05 + current_time * 3) + 1) * 0.5
            if reflection_intensity > 0.7:
                reflection_color = (255, 255, 255, int(100 * reflection_intensity))
                pygame.draw.circle(surface, reflection_color, 
                                 (i, self.height // 2 + int(math.sin(i * 0.02) * 5)), 3)
        
        return surface
    
    def render_spectrum_reflection(self, spectrum_data: np.ndarray) -> pygame.Surface:
        """CPU频谱倒影渲染"""
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        if spectrum_data is not None and len(spectrum_data) > 0:
            bar_width = self.width // len(spectrum_data)
            for i, amplitude in enumerate(spectrum_data):
                height = int(amplitude * 100)
                x = i * bar_width
                color = (100, 150, 200, 128)
                pygame.draw.rect(surface, color, (x, self.height - height, bar_width, height))
        
        return surface
    
    def create_particle_system(self, particle_count: int = 100):
        """创建简单粒子系统"""
        return {
            'particles': [
                {
                    'x': np.random.uniform(0, self.width),
                    'y': np.random.uniform(0, self.height),
                    'vx': np.random.uniform(-1, 1),
                    'vy': np.random.uniform(-1, 1),
                    'life': np.random.uniform(0, 1),
                    'size': np.random.uniform(2, 6)
                }
                for _ in range(particle_count)
            ]
        }
    
    def render_particles(self, particle_system: dict, particle_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)):
        """CPU粒子渲染"""
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        if particle_system and 'particles' in particle_system:
            color = tuple(int(c * 255) for c in particle_color)
            for particle in particle_system['particles']:
                alpha = int((1 - particle['life']) * 255)
                size = int(particle['size'])
                
                # 确保坐标和大小是整数
                pos = (int(particle['x']), int(particle['y']))
                
                pygame.draw.circle(surface, (*color, alpha), pos, size)
        
        return surface
    
    def cleanup(self):
        """清理资源"""
        pass

# 工厂函数
def create_renderer(width: int, height: int):
    """创建渲染器（优先使用GPU，回退到CPU）"""
    if HAS_MODERNGL:
        gpu_renderer = ModernGLRenderer(width, height)
        if gpu_renderer.initialized:
            return gpu_renderer
    
    return CPUFallbackRenderer(width, height)

# 测试代码
if __name__ == "__main__":
    # 测试渲染器
    pygame.init()
    
    width, height = 800, 600
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("ModernGL渲染器测试")
    
    renderer = create_renderer(width, height)
    particle_system = renderer.create_particle_system(500)
    
    clock = pygame.time.Clock()
    running = True
    
    print("ModernGL渲染器测试启动")
    print("按ESC退出")
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # 清屏
        screen.fill((20, 20, 30))
        
        # 渲染水面
        water_surface = renderer.render_water_surface(
            audio_intensity=0.5,
            water_color=(0.2, 0.4, 0.6)
        )
        if water_surface:
            screen.blit(water_surface, (0, 0))
        
        # 渲染粒子
        particle_surface = renderer.render_particles(
            particle_system,
            particle_color=(0.8, 0.9, 1.0)
        )
        if particle_surface:
            screen.blit(particle_surface, (0, 0), special_flags=pygame.BLEND_ADD)
        
        pygame.display.flip()
        clock.tick(60)
    
    renderer.cleanup()
    pygame.quit()
    print("测试完成")