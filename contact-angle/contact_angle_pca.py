#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
接触角计算 - 协方差矩阵/PCA方法
使用Santiso等人的协方差矩阵方法从COMSOL点云数据计算接触角
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.spatial import KDTree
import os

# 设置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class ContactAngleCalculator:
    """使用PCA/协方差矩阵方法计算接触角"""
    
    def __init__(self, z_threshold=0.05, k_neighbors=30, min_points=10):
        """
        初始化计算器
        
        参数:
            z_threshold: 接触线区域阈值（z坐标小于此值认为在固体表面）
            k_neighbors: k近邻数量
            min_points: 接触线最少点数（质量验证）
        """
        self.z_threshold = z_threshold
        self.k_neighbors = k_neighbors
        self.min_points = min_points
        
        # 存储数据
        self.points = None
        self.contact_points = None
        self.contact_indices = None
        self.local_normals = None
        self.mean_normal = None
        self.contact_angle = None
        
    def load_data(self, file_path):
        """
        加载COMSOL点云数据
        
        参数:
            file_path: txt文件路径
        
        返回:
            points: nx3 numpy数组，包含(x, y, z)坐标
        """
        print(f"正在加载数据: {file_path}")
        
        # 读取数据，跳过表头和COMSOL元数据行 (以 % 开头)
        # COMSOL 导出在不同机器上可能是 UTF-8/GBK/GB18030。
        data = []
        lines = None
        last_error = None
        for encoding in ("utf-8-sig", "gb18030", "gbk"):
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    lines = f.readlines()
                break
            except UnicodeDecodeError as exc:
                last_error = exc

        if lines is None:
            raise UnicodeDecodeError(
                "text-decoder",
                b"",
                0,
                1,
                f"无法解码文件 {file_path}: {last_error}",
            )

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('%'):
                continue
            parts = stripped.split()
            if len(parts) >= 3:
                try:
                    x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
                    data.append([x, y, z])
                except ValueError:
                    continue
        
        self.points = np.array(data)
        print(f"成功加载 {len(self.points)} 个点")
        print(f"点云范围: X=[{self.points[:, 0].min():.3f}, {self.points[:, 0].max():.3f}], "
              f"Y=[{self.points[:, 1].min():.3f}, {self.points[:, 1].max():.3f}], "
              f"Z=[{self.points[:, 2].min():.3f}, {self.points[:, 2].max():.3f}]")
        
        return self.points
    
    def extract_contact_region(self):
        """
        提取接触线区域的点（z ≈ 0）
        
        返回:
            contact_points: 接触线区域的点
            contact_indices: 接触线点在原点云中的索引
        """
        print(f"\n正在提取接触线区域 (z < {self.z_threshold})...")
        
        # 筛选z坐标接近0的点
        self.contact_indices = np.where(self.points[:, 2] < self.z_threshold)[0]
        self.contact_points = self.points[self.contact_indices]
        
        print(f"找到 {len(self.contact_points)} 个接触线区域点")
        
        if len(self.contact_points) < self.min_points:
            raise ValueError(f"接触线点数太少 ({len(self.contact_points)} < {self.min_points})，"
                           f"请检查数据或调整z_threshold参数")
        
        return self.contact_points, self.contact_indices
    
    def compute_local_normals(self):
        """
        使用协方差矩阵方法计算每个接触点的局部法向量
        
        返回:
            local_normals: nx3数组，每个接触点的局部法向量
        """
        print(f"\n正在计算局部法向量 (k={self.k_neighbors})...")
        
        # 构建KDTree用于快速近邻搜索
        # 使用全部点云构建树，确保能找到足够的邻居
        tree = KDTree(self.points)
        
        self.local_normals = []
        valid_contact_points = []
        valid_indices = []
        
        for i, point in enumerate(self.contact_points):
            # 查找k个最近邻（包括自己）
            distances, indices = tree.query(point, k=self.k_neighbors)
            
            # 获取邻居点
            neighbors = self.points[indices]
            
            # 计算质心（去中心化）
            centroid = np.mean(neighbors, axis=0)
            centered = neighbors - centroid
            
            # 构建协方差矩阵
            # Ω = (1/n) Σ(p_i - p_mean)(p_i - p_mean)^T
            cov_matrix = np.dot(centered.T, centered) / len(neighbors)
            
            # 特征值分解
            eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
            
            # 最小特征值对应的特征向量即为法向量
            # eigenvalues是升序排列的
            normal = eigenvectors[:, 0]
            
            # 调整法向方向：确保指向液滴外侧（气体侧）
            # 对于液滴，法向应该从接触点指向液滴中心的反方向
            # 计算接触点到液滴质心的向量
            droplet_center = np.mean(self.points[self.points[:, 2] > 0.1], axis=0)
            to_center = droplet_center - point
            
            # 如果法向与指向中心的向量夹角<90度，说明法向指向内侧，需要翻转
            if np.dot(normal, to_center) > 0:
                normal = -normal
            
            self.local_normals.append(normal)
            valid_contact_points.append(point)
            valid_indices.append(self.contact_indices[i])
        
        self.local_normals = np.array(self.local_normals)
        self.contact_points = np.array(valid_contact_points)
        self.contact_indices = np.array(valid_indices)
        
        print(f"成功计算 {len(self.local_normals)} 个局部法向量")
        
        return self.local_normals
    
    def calculate_contact_angle(self):
        """
        计算接触角
        
        返回:
            contact_angle: 接触角（度数）
            mean_normal: 平均法向量
        """
        print("\n正在计算接触角...")
        
        # 固体表面法向（假设完美水平面，指向液滴侧/向上）
        wall_normal = np.array([0, 0, 1])
        
        # 先计算每个局部法向量对应的接触角
        # 这是正确的方法：先计算角度，再求平均
        cos_thetas = np.dot(self.local_normals, wall_normal)
        cos_thetas = np.clip(cos_thetas, -1, 1)
        angles_between = np.arccos(cos_thetas) * 180 / np.pi
        
        # 接触角 = 180° - 法向夹角
        # 因为接触角是从液体侧测量的
        local_angles = 180 - angles_between
        
        # 对接触角求平均（这是正确的方法）
        self.contact_angle = np.mean(local_angles)
        angle_std = np.std(local_angles)
        
        # 从平均接触角反推平均法向量（用于可视化）
        # 平均接触角对应的法向与墙面法向的夹角
        angle_between_normals = 180 - self.contact_angle
        
        # 计算接触线中心到液滴中心的平均方向（径向方向）
        droplet_center = np.mean(self.points[self.points[:, 2] > 0.1], axis=0)
        contact_center = np.mean(self.contact_points, axis=0)
        radial_direction = droplet_center - contact_center
        radial_direction[2] = 0  # 在x-y平面上的投影
        if np.linalg.norm(radial_direction) > 1e-6:
            radial_direction = radial_direction / np.linalg.norm(radial_direction)
        else:
            radial_direction = np.array([1, 0, 0])  # 默认方向
        
        # 构建平均法向量：在径向-垂直平面内，与垂直方向夹角为angle_between_normals
        # 法向量的z分量 = cos(angle_between_normals)
        # 法向量在x-y平面上的投影 = sin(angle_between_normals) * radial_direction
        cos_theta_mean = np.cos(angle_between_normals * np.pi / 180)
        sin_theta_mean = np.sin(angle_between_normals * np.pi / 180)
        self.mean_normal = np.array([
            sin_theta_mean * radial_direction[0],
            sin_theta_mean * radial_direction[1],
            cos_theta_mean
        ])
        
        # 归一化（虽然理论上已经归一化，但为了数值稳定性）
        self.mean_normal = self.mean_normal / np.linalg.norm(self.mean_normal)
        
        print(f"\n{'='*50}")
        print(f"计算结果:")
        print(f"{'='*50}")
        print(f"平均法向量: [{self.mean_normal[0]:.6f}, {self.mean_normal[1]:.6f}, {self.mean_normal[2]:.6f}]")
        print(f"接触角: {self.contact_angle:.2f}°")
        print(f"局部接触角标准差: {angle_std:.2f}°")
        print(f"接触线点数: {len(self.contact_points)}")
        print(f"{'='*50}\n")
        
        return self.contact_angle, self.mean_normal
    
    def visualize(self, output_dir=None):
        """
        可视化结果
        
        参数:
            output_dir: 输出目录，如果为None则只显示不保存
        """
        print("正在生成可视化图像...")
        
        # 创建输出目录
        if output_dir is not None:
            os.makedirs(output_dir, exist_ok=True)
        
        # ========== 图1: 3D点云 + 接触线 + 法向量 ==========
        fig1 = plt.figure(figsize=(12, 10))
        ax1 = fig1.add_subplot(111, projection='3d')
        
        # 绘制全部点云（灰色半透明）
        ax1.scatter(self.points[:, 0], self.points[:, 1], self.points[:, 2],
                   c='gray', alpha=0.3, s=1, label='液滴表面')
        
        # 绘制接触线区域（红色）
        ax1.scatter(self.contact_points[:, 0], self.contact_points[:, 1], 
                   self.contact_points[:, 2], c='red', s=10, label='接触线区域')
        
        # 绘制平均法向量（从接触线中心点发出）
        contact_center = np.mean(self.contact_points, axis=0)
        arrow_length = 0.5
        ax1.quiver(contact_center[0], contact_center[1], contact_center[2],
                  self.mean_normal[0], self.mean_normal[1], self.mean_normal[2],
                  length=arrow_length, color='blue', arrow_length_ratio=0.3,
                  linewidth=3, label=f'平均法向 (θ={self.contact_angle:.1f}°)')
        
        # 绘制固体表面法向（绿色）
        ax1.quiver(contact_center[0], contact_center[1], 0,
                  0, 0, arrow_length,
                  length=1, color='green', arrow_length_ratio=0.3,
                  linewidth=3, label='固体法向')
        
        ax1.set_xlabel('X')
        ax1.set_ylabel('Y')
        ax1.set_zlabel('Z')
        ax1.set_title(f'液滴点云与接触角 (θ = {self.contact_angle:.2f}°)', fontsize=14)
        ax1.legend()
        ax1.set_box_aspect([1, 1, 0.5])
        
        if output_dir:
            plt.savefig(os.path.join(output_dir, '3D_pointcloud.png'), dpi=300, bbox_inches='tight')
        
        # ========== 图2: 侧视图 (X-Z平面) ==========
        fig2, ax2 = plt.subplots(figsize=(10, 8))
        
        # 绘制点云投影
        ax2.scatter(self.points[:, 0], self.points[:, 2], 
                   c='gray', alpha=0.3, s=1, label='液滴轮廓')
        ax2.scatter(self.contact_points[:, 0], self.contact_points[:, 2],
                   c='red', s=20, label='接触线')
        
        # 绘制固体表面
        x_range = [self.points[:, 0].min(), self.points[:, 0].max()]
        ax2.plot(x_range, [0, 0], 'k-', linewidth=2, label='固体表面')
        
        # 绘制法向量
        arrow_scale = 0.3
        ax2.arrow(contact_center[0], contact_center[2],
                 self.mean_normal[0] * arrow_scale, self.mean_normal[2] * arrow_scale,
                 head_width=0.05, head_length=0.08, fc='blue', ec='blue',
                 linewidth=2, label=f'界面法向')
        ax2.arrow(contact_center[0], 0, 0, arrow_scale,
                 head_width=0.05, head_length=0.08, fc='green', ec='green',
                 linewidth=2, label='固体法向')
        
        ax2.set_xlabel('X', fontsize=12)
        ax2.set_ylabel('Z', fontsize=12)
        ax2.set_title(f'侧视图 - 接触角 θ = {self.contact_angle:.2f}°', fontsize=14)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_aspect('equal')
        
        if output_dir:
            plt.savefig(os.path.join(output_dir, 'side_view.png'), dpi=300, bbox_inches='tight')
        
        # ========== 图3: 局部法向量分布 ==========
        fig3, ax3 = plt.subplots(figsize=(10, 6))
        
        # 计算每个局部法向的接触角
        wall_normal = np.array([0, 0, 1])
        cos_thetas = np.dot(self.local_normals, wall_normal)
        cos_thetas = np.clip(cos_thetas, -1, 1)
        angles_between = np.arccos(cos_thetas) * 180 / np.pi
        
        # 接触角 = 180° - 法向夹角
        local_angles = 180 - angles_between
        
        # 绘制直方图
        ax3.hist(local_angles, bins=30, alpha=0.7, color='blue', edgecolor='black')
        ax3.axvline(self.contact_angle, color='red', linestyle='--', linewidth=2,
                   label=f'平均值: {self.contact_angle:.2f}°')
        ax3.set_xlabel('局部接触角 (度)', fontsize=12)
        ax3.set_ylabel('频数', fontsize=12)
        ax3.set_title('局部接触角分布', fontsize=14)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        if output_dir:
            plt.savefig(os.path.join(output_dir, 'angle_distribution.png'), dpi=300, bbox_inches='tight')
        
        # 关闭所有图形以释放内存
        plt.close('all')
        
        if output_dir:
            print(f"可视化完成！图像已保存到: {output_dir}")
        else:
            print("可视化完成！")
    
    def run(self, file_path, output_dir=None):
        """
        运行完整的接触角计算流程
        
        参数:
            file_path: 输入txt文件路径
            output_dir: 输出目录
        
        返回:
            contact_angle: 接触角（度数）
        """
        # 1. 加载数据
        self.load_data(file_path)
        
        # 2. 提取接触线区域
        self.extract_contact_region()
        
        # 3. 计算局部法向量
        self.compute_local_normals()
        
        # 4. 计算接触角
        self.calculate_contact_angle()
        
        # 5. 可视化
        self.visualize(output_dir)
        
        return self.contact_angle


def main():
    """主函数"""
    # 输入文件路径
    input_file = "/Users/wubo/Downloads/contact-angle/接触角测量及前后资料/仿真相关/纯镓/Ga_Si_GaN_30_30.txt"
    
    # 输出目录
    output_dir = "/Users/wubo/Downloads/contact-angle/results"
    
    # 创建计算器实例
    calculator = ContactAngleCalculator(
        z_threshold=0.05,    # 接触线区域阈值
        k_neighbors=30,      # k近邻数量
        min_points=10        # 最少接触点数
    )
    
    # 运行计算
    contact_angle = calculator.run(input_file, output_dir)
    
    print(f"\n最终结果: 接触角 = {contact_angle:.2f}°")


if __name__ == "__main__":
    main()
