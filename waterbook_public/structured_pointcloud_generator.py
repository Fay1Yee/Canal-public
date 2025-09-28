#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结构化点云生成器
用于E2系统，生成具有特定形状（建筑物、植被等）的结构化点云
"""

import numpy as np
import math
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum

class StructureType(Enum):
    """结构类型枚举"""
    TRADITIONAL_BUILDING = "traditional_building"  # 传统建筑
    MODERN_BUILDING = "modern_building"           # 现代建筑
    PAGODA = "pagoda"                            # 塔楼
    TREE_CLUSTER = "tree_cluster"                # 树木群
    WILLOW_TREE = "willow_tree"                  # 柳树
    PINE_TREE = "pine_tree"                      # 松树
    BRIDGE_ARCH = "bridge_arch"                  # 桥拱
    BOAT_STRUCTURE = "boat_structure"            # 船只结构
    WATER_PAVILION = "water_pavilion"            # 水榭

@dataclass
class StructuredParticle:
    """结构化粒子"""
    x: float
    y: float
    z: float
    size: float
    color: Tuple[int, int, int]
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    life: float = 1.0
    particle_type: str = "structured"
    intensity: float = 0.0
    structure_id: int = 0  # 所属结构ID
    local_x: float = 0.0   # 结构内局部坐标
    local_y: float = 0.0
    local_z: float = 0.0

@dataclass
class StructureTemplate:
    """结构模板"""
    structure_type: StructureType
    base_width: float
    base_height: float
    base_depth: float
    particle_density: float  # 粒子密度
    color_palette: List[Tuple[int, int, int]]
    audio_responsiveness: float

class StructuredPointCloudGenerator:
    """结构化点云生成器"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.water_surface_y = height * 0.6
        
        # 结构模板库
        self.structure_templates = self._init_structure_templates()
        
        # 生成的结构
        self.structures = []
        self.structure_counter = 0
        
    def _init_structure_templates(self) -> Dict[StructureType, StructureTemplate]:
        """初始化结构模板库"""
        templates = {}
        
        # 传统建筑模板
        templates[StructureType.TRADITIONAL_BUILDING] = StructureTemplate(
            structure_type=StructureType.TRADITIONAL_BUILDING,
            base_width=80.0,
            base_height=120.0,
            base_depth=60.0,
            particle_density=0.8,
            color_palette=[(65, 65, 70), (90, 90, 95), (100, 100, 95)],
            audio_responsiveness=0.6
        )
        
        # 现代建筑模板
        templates[StructureType.MODERN_BUILDING] = StructureTemplate(
            structure_type=StructureType.MODERN_BUILDING,
            base_width=100.0,
            base_height=200.0,
            base_depth=80.0,
            particle_density=0.9,
            color_palette=[(45, 45, 50), (65, 65, 70), (85, 85, 90)],
            audio_responsiveness=0.8
        )
        
        # 塔楼模板
        templates[StructureType.PAGODA] = StructureTemplate(
            structure_type=StructureType.PAGODA,
            base_width=60.0,
            base_height=180.0,
            base_depth=60.0,
            particle_density=0.7,
            color_palette=[(70, 70, 65), (100, 100, 95), (130, 130, 125)],
            audio_responsiveness=0.5
        )
        
        # 树木群模板
        templates[StructureType.TREE_CLUSTER] = StructureTemplate(
            structure_type=StructureType.TREE_CLUSTER,
            base_width=120.0,
            base_height=80.0,
            base_depth=120.0,
            particle_density=0.6,
            color_palette=[(60, 60, 55), (90, 90, 85), (120, 120, 115)],
            audio_responsiveness=1.2
        )
        
        # 柳树模板
        templates[StructureType.WILLOW_TREE] = StructureTemplate(
            structure_type=StructureType.WILLOW_TREE,
            base_width=80.0,
            base_height=100.0,
            base_depth=80.0,
            particle_density=0.5,
            color_palette=[(60, 60, 55), (80, 80, 75), (100, 100, 95)],
            audio_responsiveness=1.5
        )
        
        # 松树模板
        templates[StructureType.PINE_TREE] = StructureTemplate(
            structure_type=StructureType.PINE_TREE,
            base_width=40.0,
            base_height=120.0,
            base_depth=40.0,
            particle_density=0.7,
            color_palette=[(50, 50, 45), (70, 70, 65), (90, 90, 85)],
            audio_responsiveness=1.0
        )
        
        # 桥拱模板
        templates[StructureType.BRIDGE_ARCH] = StructureTemplate(
            structure_type=StructureType.BRIDGE_ARCH,
            base_width=200.0,
            base_height=60.0,
            base_depth=40.0,
            particle_density=0.8,
            color_palette=[(70, 70, 65), (100, 100, 95), (130, 130, 125)],
            audio_responsiveness=0.4
        )
        
        # 船只结构模板
        templates[StructureType.BOAT_STRUCTURE] = StructureTemplate(
            structure_type=StructureType.BOAT_STRUCTURE,
            base_width=60.0,
            base_height=20.0,
            base_depth=15.0,
            particle_density=0.9,
            color_palette=[(70, 70, 65), (90, 90, 85), (110, 110, 105)],
            audio_responsiveness=1.8
        )
        
        # 水榭模板
        templates[StructureType.WATER_PAVILION] = StructureTemplate(
            structure_type=StructureType.WATER_PAVILION,
            base_width=80.0,
            base_height=60.0,
            base_depth=80.0,
            particle_density=0.6,
            color_palette=[(100, 100, 95), (120, 120, 115), (140, 140, 135)],
            audio_responsiveness=0.7
        )
        
        return templates
    
    def generate_structured_pointcloud(self, structure_type: StructureType, 
                                     center_x: float, center_y: float, 
                                     scale: float = 1.0) -> List[StructuredParticle]:
        """生成结构化点云"""
        template = self.structure_templates[structure_type]
        particles = []
        
        # 获取结构ID
        structure_id = self.structure_counter
        self.structure_counter += 1
        
        # 根据结构类型生成点云
        if structure_type == StructureType.TRADITIONAL_BUILDING:
            particles = self._generate_traditional_building(template, center_x, center_y, scale, structure_id)
        elif structure_type == StructureType.MODERN_BUILDING:
            particles = self._generate_modern_building(template, center_x, center_y, scale, structure_id)
        elif structure_type == StructureType.PAGODA:
            particles = self._generate_pagoda(template, center_x, center_y, scale, structure_id)
        elif structure_type == StructureType.TREE_CLUSTER:
            particles = self._generate_tree_cluster(template, center_x, center_y, scale, structure_id)
        elif structure_type == StructureType.WILLOW_TREE:
            particles = self._generate_willow_tree(template, center_x, center_y, scale, structure_id)
        elif structure_type == StructureType.PINE_TREE:
            particles = self._generate_pine_tree(template, center_x, center_y, scale, structure_id)
        elif structure_type == StructureType.BRIDGE_ARCH:
            particles = self._generate_bridge_arch(template, center_x, center_y, scale, structure_id)
        elif structure_type == StructureType.BOAT_STRUCTURE:
            particles = self._generate_boat_structure(template, center_x, center_y, scale, structure_id)
        elif structure_type == StructureType.WATER_PAVILION:
            particles = self._generate_water_pavilion(template, center_x, center_y, scale, structure_id)
        
        return particles
    
    def _generate_traditional_building(self, template: StructureTemplate, 
                                     center_x: float, center_y: float, 
                                     scale: float, structure_id: int) -> List[StructuredParticle]:
        """生成传统建筑点云"""
        particles = []
        width = template.base_width * scale
        height = template.base_height * scale
        depth = template.base_depth * scale
        
        # 计算粒子数量
        particle_count = int(width * height * depth * template.particle_density / 1000)
        
        for i in range(particle_count):
            # 生成建筑主体
            if i < particle_count * 0.7:  # 70%用于主体
                local_x = np.random.uniform(-width/2, width/2)
                local_y = np.random.uniform(-height, 0)
                local_z = np.random.uniform(0, depth)
            else:  # 30%用于屋顶
                # 屋顶形状（三角形）
                roof_progress = (i - particle_count * 0.7) / (particle_count * 0.3)
                roof_width = width * (1 - roof_progress * 0.8)
                local_x = np.random.uniform(-roof_width/2, roof_width/2)
                local_y = np.random.uniform(-height - height * 0.3, -height)
                local_z = np.random.uniform(0, depth)
            
            # 世界坐标
            world_x = center_x + local_x
            world_y = center_y + local_y
            world_z = 0.3 + local_z / depth * 0.5
            
            # 选择颜色
            color = template.color_palette[np.random.randint(0, len(template.color_palette))]
            
            # 粒子大小根据深度变化
            size = np.random.uniform(1.5, 4.0) * (1 + local_z / depth * 0.3)
            
            particle = StructuredParticle(
                x=world_x, y=world_y, z=world_z,
                size=size, color=color,
                structure_id=structure_id,
                local_x=local_x, local_y=local_y, local_z=local_z
            )
            particles.append(particle)
        
        return particles
    
    def _generate_modern_building(self, template: StructureTemplate, 
                                center_x: float, center_y: float, 
                                scale: float, structure_id: int) -> List[StructuredParticle]:
        """生成现代建筑点云"""
        particles = []
        width = template.base_width * scale
        height = template.base_height * scale
        depth = template.base_depth * scale
        
        particle_count = int(width * height * depth * template.particle_density / 1000)
        
        for i in range(particle_count):
            # 现代建筑通常是规整的长方体
            local_x = np.random.uniform(-width/2, width/2)
            local_y = np.random.uniform(-height, 0)
            local_z = np.random.uniform(0, depth)
            
            # 添加一些楼层结构
            floor_height = height / 8  # 假设8层
            floor_index = int(abs(local_y) / floor_height)
            
            # 世界坐标
            world_x = center_x + local_x
            world_y = center_y + local_y
            world_z = 0.2 + local_z / depth * 0.6
            
            # 根据楼层选择颜色
            color_index = min(floor_index % len(template.color_palette), len(template.color_palette) - 1)
            color = template.color_palette[color_index]
            
            size = np.random.uniform(1.0, 3.0)
            
            particle = StructuredParticle(
                x=world_x, y=world_y, z=world_z,
                size=size, color=color,
                structure_id=structure_id,
                local_x=local_x, local_y=local_y, local_z=local_z
            )
            particles.append(particle)
        
        return particles
    
    def _generate_pagoda(self, template: StructureTemplate, 
                        center_x: float, center_y: float, 
                        scale: float, structure_id: int) -> List[StructuredParticle]:
        """生成塔楼点云"""
        particles = []
        base_width = template.base_width * scale
        height = template.base_height * scale
        depth = template.base_depth * scale
        
        particle_count = int(base_width * height * depth * template.particle_density / 1000)
        
        # 塔楼分为多层，每层递减
        layers = 5
        layer_height = height / layers
        
        for i in range(particle_count):
            # 确定所在层
            layer = np.random.randint(0, layers)
            layer_y_start = -layer * layer_height
            layer_y_end = -(layer + 1) * layer_height
            
            # 每层宽度递减
            layer_width_factor = (layers - layer) / layers
            layer_width = base_width * layer_width_factor
            layer_depth = depth * layer_width_factor
            
            local_x = np.random.uniform(-layer_width/2, layer_width/2)
            local_y = np.random.uniform(layer_y_end, layer_y_start)
            local_z = np.random.uniform(0, layer_depth)
            
            world_x = center_x + local_x
            world_y = center_y + local_y
            world_z = 0.3 + local_z / depth * 0.4
            
            # 根据层数选择颜色
            color = template.color_palette[layer % len(template.color_palette)]
            size = np.random.uniform(1.5, 3.5) * layer_width_factor
            
            particle = StructuredParticle(
                x=world_x, y=world_y, z=world_z,
                size=size, color=color,
                structure_id=structure_id,
                local_x=local_x, local_y=local_y, local_z=local_z
            )
            particles.append(particle)
        
        return particles
    
    def _generate_tree_cluster(self, template: StructureTemplate, 
                             center_x: float, center_y: float, 
                             scale: float, structure_id: int) -> List[StructuredParticle]:
        """生成树木群点云"""
        particles = []
        width = template.base_width * scale
        height = template.base_height * scale
        depth = template.base_depth * scale
        
        particle_count = int(width * height * depth * template.particle_density / 800)
        
        # 生成多棵树
        tree_count = np.random.randint(3, 8)
        particles_per_tree = particle_count // tree_count
        
        for tree_idx in range(tree_count):
            # 树的位置
            tree_x = np.random.uniform(-width/3, width/3)
            tree_z = np.random.uniform(0, depth)
            tree_height = np.random.uniform(height * 0.6, height)
            crown_radius = np.random.uniform(15, 25) * scale
            
            for i in range(particles_per_tree):
                if i < particles_per_tree * 0.2:  # 20%用于树干
                    local_x = tree_x + np.random.uniform(-2, 2)
                    local_y = np.random.uniform(-tree_height * 0.8, 0)
                    local_z = tree_z + np.random.uniform(-2, 2)
                    color = template.color_palette[0]  # 深色树干
                    size = np.random.uniform(1.0, 2.5)
                else:  # 80%用于树冠
                    # 球形树冠
                    angle = np.random.uniform(0, 2 * np.pi)
                    radius = np.random.uniform(0, crown_radius)
                    crown_height = np.random.uniform(0, crown_radius * 0.8)
                    
                    local_x = tree_x + radius * np.cos(angle)
                    local_y = -tree_height * 0.3 - crown_height
                    local_z = tree_z + radius * np.sin(angle)
                    
                    color = template.color_palette[np.random.randint(1, len(template.color_palette))]
                    size = np.random.uniform(1.5, 4.0)
                
                world_x = center_x + local_x
                world_y = center_y + local_y
                world_z = 0.4 + local_z / depth * 0.4
                
                particle = StructuredParticle(
                    x=world_x, y=world_y, z=world_z,
                    size=size, color=color,
                    structure_id=structure_id,
                    local_x=local_x, local_y=local_y, local_z=local_z
                )
                particles.append(particle)
        
        return particles
    
    def _generate_willow_tree(self, template: StructureTemplate, 
                            center_x: float, center_y: float, 
                            scale: float, structure_id: int) -> List[StructuredParticle]:
        """生成柳树点云"""
        particles = []
        width = template.base_width * scale
        height = template.base_height * scale
        depth = template.base_depth * scale
        
        particle_count = int(width * height * depth * template.particle_density / 600)
        
        # 柳树特征：垂下的枝条
        for i in range(particle_count):
            if i < particle_count * 0.15:  # 15%用于树干
                local_x = np.random.uniform(-3, 3)
                local_y = np.random.uniform(-height * 0.7, 0)
                local_z = np.random.uniform(-3, 3)
                color = template.color_palette[0]
                size = np.random.uniform(1.5, 3.0)
            else:  # 85%用于垂柳枝条
                # 生成垂下的枝条
                branch_angle = np.random.uniform(0, 2 * np.pi)
                branch_radius = np.random.uniform(5, width/2)
                branch_length = np.random.uniform(height * 0.3, height * 0.9)
                
                local_x = branch_radius * np.cos(branch_angle)
                local_y = -np.random.uniform(height * 0.2, branch_length)
                local_z = branch_radius * np.sin(branch_angle)
                
                color = template.color_palette[np.random.randint(1, len(template.color_palette))]
                size = np.random.uniform(1.0, 2.5)
            
            world_x = center_x + local_x
            world_y = center_y + local_y
            world_z = 0.5 + local_z / depth * 0.3
            
            particle = StructuredParticle(
                x=world_x, y=world_y, z=world_z,
                size=size, color=color,
                structure_id=structure_id,
                local_x=local_x, local_y=local_y, local_z=local_z
            )
            particles.append(particle)
        
        return particles
    
    def _generate_pine_tree(self, template: StructureTemplate, 
                          center_x: float, center_y: float, 
                          scale: float, structure_id: int) -> List[StructuredParticle]:
        """生成松树点云"""
        particles = []
        width = template.base_width * scale
        height = template.base_height * scale
        depth = template.base_depth * scale
        
        particle_count = int(width * height * depth * template.particle_density / 400)
        
        # 松树特征：锥形树冠
        for i in range(particle_count):
            if i < particle_count * 0.2:  # 20%用于树干
                local_x = np.random.uniform(-2, 2)
                local_y = np.random.uniform(-height * 0.8, 0)
                local_z = np.random.uniform(-2, 2)
                color = template.color_palette[0]
                size = np.random.uniform(1.5, 3.0)
            else:  # 80%用于锥形树冠
                # 锥形分布
                cone_height_ratio = np.random.uniform(0, 1)
                cone_radius = width/2 * (1 - cone_height_ratio * 0.8)  # 向上递减
                
                angle = np.random.uniform(0, 2 * np.pi)
                radius = np.random.uniform(0, cone_radius)
                
                local_x = radius * np.cos(angle)
                local_y = -height * 0.2 - cone_height_ratio * height * 0.6
                local_z = radius * np.sin(angle)
                
                color = template.color_palette[np.random.randint(1, len(template.color_palette))]
                size = np.random.uniform(1.0, 3.0)
            
            world_x = center_x + local_x
            world_y = center_y + local_y
            world_z = 0.4 + local_z / depth * 0.4
            
            particle = StructuredParticle(
                x=world_x, y=world_y, z=world_z,
                size=size, color=color,
                structure_id=structure_id,
                local_x=local_x, local_y=local_y, local_z=local_z
            )
            particles.append(particle)
        
        return particles
    
    def _generate_bridge_arch(self, template: StructureTemplate, 
                            center_x: float, center_y: float, 
                            scale: float, structure_id: int) -> List[StructuredParticle]:
        """生成桥拱点云"""
        particles = []
        width = template.base_width * scale
        height = template.base_height * scale
        depth = template.base_depth * scale
        
        particle_count = int(width * height * depth * template.particle_density / 800)
        
        # 桥拱形状
        for i in range(particle_count):
            # 拱形分布
            local_x = np.random.uniform(-width/2, width/2)
            
            # 计算拱形高度
            arch_progress = abs(local_x) / (width/2)
            max_arch_height = height
            arch_height = max_arch_height * (1 - arch_progress * arch_progress)  # 抛物线
            
            local_y = np.random.uniform(-arch_height, 0)
            local_z = np.random.uniform(0, depth)
            
            world_x = center_x + local_x
            world_y = center_y + local_y
            world_z = 0.3 + local_z / depth * 0.4
            
            color = template.color_palette[np.random.randint(0, len(template.color_palette))]
            size = np.random.uniform(2.0, 4.0)
            
            particle = StructuredParticle(
                x=world_x, y=world_y, z=world_z,
                size=size, color=color,
                structure_id=structure_id,
                local_x=local_x, local_y=local_y, local_z=local_z
            )
            particles.append(particle)
        
        return particles
    
    def _generate_boat_structure(self, template: StructureTemplate, 
                               center_x: float, center_y: float, 
                               scale: float, structure_id: int) -> List[StructuredParticle]:
        """生成船只结构点云"""
        particles = []
        width = template.base_width * scale
        height = template.base_height * scale
        depth = template.base_depth * scale
        
        particle_count = int(width * height * depth * template.particle_density / 200)
        
        # 船只形状：椭圆形船体
        for i in range(particle_count):
            if i < particle_count * 0.8:  # 80%用于船体
                # 椭圆形船体
                angle = np.random.uniform(0, 2 * np.pi)
                radius_x = np.random.uniform(0, width/2)
                radius_z = np.random.uniform(0, depth/2)
                
                local_x = radius_x * np.cos(angle)
                local_y = np.random.uniform(-height, 0)
                local_z = radius_z * np.sin(angle)
            else:  # 20%用于船帆或上层建筑
                local_x = np.random.uniform(-width/4, width/4)
                local_y = np.random.uniform(-height * 2, -height)
                local_z = np.random.uniform(-depth/4, depth/4)
            
            world_x = center_x + local_x
            world_y = center_y + local_y
            world_z = 0.8 + local_z / depth * 0.2  # 船只在水面上
            
            color = template.color_palette[np.random.randint(0, len(template.color_palette))]
            size = np.random.uniform(1.0, 2.5)
            
            particle = StructuredParticle(
                x=world_x, y=world_y, z=world_z,
                size=size, color=color,
                structure_id=structure_id,
                local_x=local_x, local_y=local_y, local_z=local_z,
                velocity_x=np.random.uniform(-0.5, 0.5),  # 船只可以移动
                velocity_y=np.random.uniform(-0.1, 0.1)
            )
            particles.append(particle)
        
        return particles
    
    def _generate_water_pavilion(self, template: StructureTemplate, 
                               center_x: float, center_y: float, 
                               scale: float, structure_id: int) -> List[StructuredParticle]:
        """生成水榭点云"""
        particles = []
        width = template.base_width * scale
        height = template.base_height * scale
        depth = template.base_depth * scale
        
        particle_count = int(width * height * depth * template.particle_density / 600)
        
        # 水榭：开放式结构，主要是柱子和屋顶
        for i in range(particle_count):
            if i < particle_count * 0.3:  # 30%用于柱子
                # 4根柱子
                pillar_positions = [
                    (-width/3, -depth/3), (width/3, -depth/3),
                    (-width/3, depth/3), (width/3, depth/3)
                ]
                pillar_idx = i % 4
                pillar_x, pillar_z = pillar_positions[pillar_idx]
                
                local_x = pillar_x + np.random.uniform(-3, 3)
                local_y = np.random.uniform(-height * 0.8, 0)
                local_z = pillar_z + np.random.uniform(-3, 3)
                
                color = template.color_palette[0]
                size = np.random.uniform(2.0, 4.0)
            else:  # 70%用于屋顶和装饰
                local_x = np.random.uniform(-width/2, width/2)
                local_y = np.random.uniform(-height, -height * 0.7)
                local_z = np.random.uniform(-depth/2, depth/2)
                
                color = template.color_palette[np.random.randint(1, len(template.color_palette))]
                size = np.random.uniform(1.5, 3.0)
            
            world_x = center_x + local_x
            world_y = center_y + local_y
            world_z = 0.6 + local_z / depth * 0.2  # 水榭在水面附近
            
            particle = StructuredParticle(
                x=world_x, y=world_y, z=world_z,
                size=size, color=color,
                structure_id=structure_id,
                local_x=local_x, local_y=local_y, local_z=local_z
            )
            particles.append(particle)
        
        return particles
    
    def generate_canal_scene(self) -> List[StructuredParticle]:
        """生成完整的运河场景结构化点云"""
        all_particles = []
        
        # 左岸建筑群
        left_buildings = [
            (StructureType.TRADITIONAL_BUILDING, self.width * 0.15, self.height * 0.3, 0.8),
            (StructureType.PAGODA, self.width * 0.08, self.height * 0.25, 0.6),
            (StructureType.WATER_PAVILION, self.width * 0.25, self.height * 0.55, 0.7),
        ]
        
        for structure_type, x, y, scale in left_buildings:
            particles = self.generate_structured_pointcloud(structure_type, x, y, scale)
            all_particles.extend(particles)
        
        # 右岸建筑群
        right_buildings = [
            (StructureType.MODERN_BUILDING, self.width * 0.85, self.height * 0.2, 0.9),
            (StructureType.TRADITIONAL_BUILDING, self.width * 0.75, self.height * 0.35, 0.7),
            (StructureType.WATER_PAVILION, self.width * 0.92, self.height * 0.5, 0.6),
        ]
        
        for structure_type, x, y, scale in right_buildings:
            particles = self.generate_structured_pointcloud(structure_type, x, y, scale)
            all_particles.extend(particles)
        
        # 植被
        vegetation = [
            (StructureType.WILLOW_TREE, self.width * 0.2, self.height * 0.58, 1.0),
            (StructureType.TREE_CLUSTER, self.width * 0.12, self.height * 0.45, 0.8),
            (StructureType.PINE_TREE, self.width * 0.88, self.height * 0.42, 0.9),
            (StructureType.WILLOW_TREE, self.width * 0.78, self.height * 0.6, 0.8),
        ]
        
        for structure_type, x, y, scale in vegetation:
            particles = self.generate_structured_pointcloud(structure_type, x, y, scale)
            all_particles.extend(particles)
        
        # 桥梁
        bridge_particles = self.generate_structured_pointcloud(
            StructureType.BRIDGE_ARCH, self.width * 0.5, self.height * 0.6, 1.0
        )
        all_particles.extend(bridge_particles)
        
        # 船只（随机位置）
        boat_count = np.random.randint(2, 5)
        for _ in range(boat_count):
            boat_x = np.random.uniform(self.width * 0.3, self.width * 0.7)
            boat_y = np.random.uniform(self.height * 0.65, self.height * 0.8)
            boat_particles = self.generate_structured_pointcloud(
                StructureType.BOAT_STRUCTURE, boat_x, boat_y, np.random.uniform(0.6, 1.2)
            )
            all_particles.extend(boat_particles)
        
        return all_particles
    
    def update_particles_with_audio(self, particles: List[StructuredParticle], 
                                  audio_energy: float, frequency_bands: np.ndarray):
        """根据音频数据更新粒子"""
        for particle in particles:
            # 根据粒子类型获取对应的音频响应参数
            structure_type_map = {
                "traditional_building": StructureType.TRADITIONAL_BUILDING,
                "modern_building": StructureType.MODERN_BUILDING,
                "pagoda": StructureType.PAGODA,
                "tree_cluster": StructureType.TREE_CLUSTER,
                "willow_tree": StructureType.WILLOW_TREE,
                "pine_tree": StructureType.PINE_TREE,
                "bridge_arch": StructureType.BRIDGE_ARCH,
                "boat_structure": StructureType.BOAT_STRUCTURE,
                "water_pavilion": StructureType.WATER_PAVILION
            }
            
            # 默认使用传统建筑的模板
            structure_type = structure_type_map.get(
                particle.particle_type, 
                StructureType.TRADITIONAL_BUILDING
            )
            
            template = self.structure_templates.get(
                structure_type, 
                self.structure_templates[StructureType.TRADITIONAL_BUILDING]
            )
            
            # 音频响应
            responsiveness = template.audio_responsiveness
            particle.intensity = audio_energy * responsiveness
            
            # 根据频段调整粒子属性
            if len(frequency_bands) >= 3:
                # 低频影响大型结构
                if particle.particle_type in ["traditional_building", "modern_building", "pagoda"]:
                    particle.size *= (1 + frequency_bands[0] * 0.3)
                
                # 中频影响植被
                elif particle.particle_type in ["tree_cluster", "willow_tree", "pine_tree"]:
                    particle.velocity_x += frequency_bands[1] * 0.1 * np.random.uniform(-1, 1)
                    particle.velocity_y += frequency_bands[1] * 0.05 * np.random.uniform(-1, 1)
                
                # 高频影响船只和水榭
                elif particle.particle_type in ["boat_structure", "water_pavilion"]:
                    particle.velocity_x += frequency_bands[2] * 0.2 * np.random.uniform(-1, 1)
                    particle.velocity_y += frequency_bands[2] * 0.1 * np.random.uniform(-1, 1)
            
            # 更新粒子位置（基于速度）
            particle.x += particle.velocity_x
            particle.y += particle.velocity_y
            
            # 速度衰减
            particle.velocity_x *= 0.95
            particle.velocity_y *= 0.95

if __name__ == "__main__":
    # 测试结构化点云生成器
    generator = StructuredPointCloudGenerator(1280, 720)
    
    # 生成完整场景
    scene_particles = generator.generate_canal_scene()
    print(f"生成了 {len(scene_particles)} 个结构化粒子")
    
    # 统计各类型粒子数量
    type_counts = {}
    for particle in scene_particles:
        ptype = particle.particle_type
        type_counts[ptype] = type_counts.get(ptype, 0) + 1
    
    print("粒子类型分布:")
    for ptype, count in type_counts.items():
        print(f"  {ptype}: {count}")