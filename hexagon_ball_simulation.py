import pygame
import pymunk
import pymunk.pygame_util
import sys
import math
import os
from pygame.locals import *

# 设置环境编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 初始化pygame和pymunk
pygame.init()

# 屏幕设置
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("六边形内球体弹跳模拟")

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)

# 物理空间设置
space = pymunk.Space()
space.gravity = (0, 500)  # 设置重力
space.damping = 0.9  # 设置阻尼（摩擦）

# 绘图选项
draw_options = pymunk.pygame_util.DrawOptions(screen)

# 六边形参数
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2
OUTER_RADIUS = 200
MIDDLE_RADIUS = 150
INNER_RADIUS = 100
BALL_RADIUS = 15

# 创建六边形顶点
def create_hexagon_vertices(center_x, center_y, radius, missing_edge=None):
    vertices = []
    for i in range(6):
        angle = math.pi / 3 * i + math.pi / 6  # 从顶部开始，每60度一个顶点
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        vertices.append((x, y))
    
    # 如果指定了缺失边，则返回不包含该边的顶点列表
    if missing_edge is not None:
        # 创建边的列表，每条边由两个顶点定义
        edges = []
        for i in range(6):
            edge = [vertices[i], vertices[(i+1) % 6]]
            if i != missing_edge:  # 如果不是缺失的边，则添加
                edges.append(edge)
        return edges
    
    return vertices

# 创建静态线段（六边形的边）
def create_static_line(p1, p2, space):
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    shape = pymunk.Segment(body, p1, p2, 2)
    shape.elasticity = 0.8  # 弹性
    shape.friction = 0.5    # 摩擦
    space.add(body, shape)
    return shape

# 创建球体
def create_ball(position, space):
    body = pymunk.Body(1, pymunk.moment_for_circle(1, 0, BALL_RADIUS))
    body.position = position
    shape = pymunk.Circle(body, BALL_RADIUS)
    shape.elasticity = 0.8  # 弹性
    shape.friction = 0.5    # 摩擦
    space.add(body, shape)
    return body

# 创建六边形结构
def create_hexagons(space):
    shapes = []
    
    # 外层六边形 - 完整
    outer_vertices = create_hexagon_vertices(CENTER_X, CENTER_Y, OUTER_RADIUS)
    for i in range(6):
        shape = create_static_line(outer_vertices[i], outer_vertices[(i+1) % 6], space)
        shapes.append(shape)
    
    # 中层六边形 - 缺少一条边
    middle_edges = create_hexagon_vertices(CENTER_X, CENTER_Y, MIDDLE_RADIUS, missing_edge=0)
    for edge in middle_edges:
        shape = create_static_line(edge[0], edge[1], space)
        shapes.append(shape)
    
    # 内层六边形 - 缺少一条边
    inner_edges = create_hexagon_vertices(CENTER_X, CENTER_Y, INNER_RADIUS, missing_edge=3)
    for edge in inner_edges:
        shape = create_static_line(edge[0], edge[1], space)
        shapes.append(shape)
    
    return shapes

# 旋转六边形
def rotate_hexagons(hexagons, angles):
    # 获取每个六边形的中心点和半径
    centers_radii = [
        (CENTER_X, CENTER_Y, OUTER_RADIUS),
        (CENTER_X, CENTER_Y, MIDDLE_RADIUS),
        (CENTER_X, CENTER_Y, INNER_RADIUS)
    ]
    
    # 移除旧的六边形
    for shape in hexagons:
        space.remove(shape.body, shape)
    
    new_shapes = []
    
    # 外层六边形 - 完整，旋转角度为angles[0]
    outer_vertices = []
    for i in range(6):
        angle = math.pi / 3 * i + math.pi / 6 + angles[0]
        x = centers_radii[0][0] + centers_radii[0][2] * math.cos(angle)
        y = centers_radii[0][1] + centers_radii[0][2] * math.sin(angle)
        outer_vertices.append((x, y))
    
    for i in range(6):
        shape = create_static_line(outer_vertices[i], outer_vertices[(i+1) % 6], space)
        new_shapes.append(shape)
    
    # 中层六边形 - 缺少一条边，旋转角度为angles[1]
    middle_vertices = []
    for i in range(6):
        angle = math.pi / 3 * i + math.pi / 6 + angles[1]
        x = centers_radii[1][0] + centers_radii[1][2] * math.cos(angle)
        y = centers_radii[1][1] + centers_radii[1][2] * math.sin(angle)
        middle_vertices.append((x, y))
    
    # 确定缺失边的索引（考虑旋转后）
    missing_middle = int((0 - angles[1] * 3 / math.pi) % 6)
    for i in range(6):
        if i != missing_middle:
            shape = create_static_line(middle_vertices[i], middle_vertices[(i+1) % 6], space)
            new_shapes.append(shape)
    
    # 内层六边形 - 缺少一条边，旋转角度为angles[2]
    inner_vertices = []
    for i in range(6):
        angle = math.pi / 3 * i + math.pi / 6 + angles[2]
        x = centers_radii[2][0] + centers_radii[2][2] * math.cos(angle)
        y = centers_radii[2][1] + centers_radii[2][2] * math.sin(angle)
        inner_vertices.append((x, y))
    
    # 确定缺失边的索引（考虑旋转后）
    missing_inner = int((3 - angles[2] * 3 / math.pi) % 6)
    for i in range(6):
        if i != missing_inner:
            shape = create_static_line(inner_vertices[i], inner_vertices[(i+1) % 6], space)
            new_shapes.append(shape)
    
    return new_shapes

# 绘制六边形（用于视觉效果）
def draw_hexagons(screen, angles):
    # 外层六边形 - 完整
    outer_vertices = []
    for i in range(6):
        angle = math.pi / 3 * i + math.pi / 6 + angles[0]
        x = CENTER_X + OUTER_RADIUS * math.cos(angle)
        y = CENTER_Y + OUTER_RADIUS * math.sin(angle)
        outer_vertices.append((x, y))
    
    pygame.draw.polygon(screen, BLUE, outer_vertices, 2)
    
    # 中层六边形 - 缺少一条边
    middle_vertices = []
    for i in range(6):
        angle = math.pi / 3 * i + math.pi / 6 + angles[1]
        x = CENTER_X + MIDDLE_RADIUS * math.cos(angle)
        y = CENTER_Y + MIDDLE_RADIUS * math.sin(angle)
        middle_vertices.append((x, y))
    
    # 绘制中层六边形（除了缺失的边）
    missing_middle = int((0 - angles[1] * 3 / math.pi) % 6)
    for i in range(6):
        if i != missing_middle:
            pygame.draw.line(screen, GREEN, middle_vertices[i], middle_vertices[(i+1) % 6], 2)
    
    # 内层六边形 - 缺少一条边
    inner_vertices = []
    for i in range(6):
        angle = math.pi / 3 * i + math.pi / 6 + angles[2]
        x = CENTER_X + INNER_RADIUS * math.cos(angle)
        y = CENTER_Y + INNER_RADIUS * math.sin(angle)
        inner_vertices.append((x, y))
    
    # 绘制内层六边形（除了缺失的边）
    missing_inner = int((3 - angles[2] * 3 / math.pi) % 6)
    for i in range(6):
        if i != missing_inner:
            pygame.draw.line(screen, RED, inner_vertices[i], inner_vertices[(i+1) % 6], 2)

# 添加说明文字（使用内嵌字体避免中文乱码）
def draw_instructions(screen):
    # 尝试加载内嵌字体，如果存在的话
    try:
        # 检查是否在PyInstaller环境中运行
        if getattr(sys, 'frozen', False):
            # 如果是PyInstaller打包的环境，使用_MEIPASS路径
            base_path = sys._MEIPASS
        else:
            # 否则使用当前脚本所在目录
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        # 尝试加载字体文件
        font_path = os.path.join(base_path, "simsun.ttc")
        if os.path.exists(font_path):
            font = pygame.font.Font(font_path, 16)
        else:
            # 如果找不到字体文件，尝试使用系统字体
            font = pygame.font.SysFont('simsun', 16)
    except:
        # 如果出现任何错误，回退到系统字体
        try:
            font = pygame.font.SysFont('simsun', 16)
        except:
            font = pygame.font.Font(None, 16)  # 使用默认字体
    
    instructions = [
        "按 R 键: 重置球的位置",
        "按 ESC 键: 退出程序"
    ]
    
    for i, text in enumerate(instructions):
        try:
            text_surface = font.render(text, True, WHITE)
            screen.blit(text_surface, (10, 10 + i * 25))
        except:
            # 如果渲染失败，尝试使用ASCII字符
            ascii_text = "Press R: Reset ball position" if i == 0 else "Press ESC: Exit"
            text_surface = font.render(ascii_text, True, WHITE)
            screen.blit(text_surface, (10, 10 + i * 25))

# 主函数
def main():
    clock = pygame.time.Clock()
    
    # 创建初始六边形结构
    hexagons = create_hexagons(space)
    
    # 创建球体（初始位置在最内层六边形内）
    ball = create_ball((CENTER_X, CENTER_Y), space)
    
    # 旋转角度
    angles = [0, 0, 0]  # 外层、中层、内层的旋转角度
    rotation_speeds = [0.01, -0.015, 0.02]  # 旋转速度（正为顺时针，负为逆时针）
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                elif event.key == K_r:  # 重置球的位置
                    space.remove(ball.body, ball.shape)
                    ball = create_ball((CENTER_X, CENTER_Y), space)
        
        # 更新旋转角度
        for i in range(3):
            angles[i] += rotation_speeds[i]
        
        # 更新六边形结构
        hexagons = rotate_hexagons(hexagons, angles)
        
        # 更新物理
        space.step(1/60.0)
        
        # 绘制
        screen.fill(BLACK)
        draw_hexagons(screen, angles)
        draw_instructions(screen)
        
        # 绘制球体
        pygame.draw.circle(screen, WHITE, (int(ball.position.x), int(ball.position.y)), BALL_RADIUS)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
