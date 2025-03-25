import time
import random
import pyautogui
import logging
from typing import List, Tuple

class HumanOperation:
    def __init__(self):
        self.last_mouse_position = None
        self.last_click_time = 0
        self.min_click_interval = 0.5  # 最小点击间隔时间
        
    def human_click(self, x: int, y: int, click_type: str = 'left', double: bool = False) -> None:
        """
        模拟人类点击操作
        :param x: 目标x坐标
        :param y: 目标y坐标
        :param click_type: 点击类型 ('left', 'right', 'middle')
        :param double: 是否双击
        """
        try:
            # 确保点击间隔符合人类操作习惯
            current_time = time.time()
            if current_time - self.last_click_time < self.min_click_interval:
                time.sleep(random.uniform(0.1, 0.3))
            
            # 模拟鼠标移动
            self.human_move_mouse(x, y)
            
            # 随机短暂停顿
            time.sleep(random.uniform(0.05, 0.15))
            
            # 执行点击
            if double:
                pyautogui.doubleClick(x, y, button=click_type)
            else:
                pyautogui.click(x, y, button=click_type)
            
            self.last_click_time = time.time()
            logging.info(f"模拟点击: 坐标({x}, {y}), 类型: {click_type}, 双击: {double}")
            
        except Exception as e:
            logging.error(f"模拟点击失败: {str(e)}")
    
    def human_type(self, text: str, min_delay: float = 0.05, max_delay: float = 0.2) -> None:
        """
        模拟人类输入文字
        :param text: 要输入的文本
        :param min_delay: 最小字符间隔时间
        :param max_delay: 最大字符间隔时间
        """
        try:
            # 输入前的随机停顿
            time.sleep(random.uniform(0.2, 0.5))
            
            # 随机的打字速度
            for char in text:
                # 模拟按键
                pyautogui.typewrite(char)
                
                # 模拟不同字符间的输入时间差异
                delay = random.uniform(min_delay, max_delay)
                # 特殊字符可能需要更长的输入时间
                if char in '!@#$%^&*()_+-=[]{}|;:,.<>?':
                    delay *= 1.5
                time.sleep(delay)
            
            # 输入完成后的随机停顿
            time.sleep(random.uniform(0.2, 0.5))
            logging.info(f"模拟输入文字: {text}")
            
        except Exception as e:
            logging.error(f"模拟人类输入文字失败: {str(e)}")
    
    def human_move_mouse(self, x: int, y: int, duration: float = None) -> None:
        """
        模拟人类移动鼠标
        :param x: 目标x坐标
        :param y: 目标y坐标
        :param duration: 移动持续时间，如果为None则随机生成
        """
        try:
            # 记录起始位置
            if self.last_mouse_position is None:
                self.last_mouse_position = pyautogui.position()
            
            # 计算移动距离
            distance = ((x - self.last_mouse_position.x) ** 2 + 
                       (y - self.last_mouse_position.y) ** 2) ** 0.5
            
            # 根据距离动态调整移动时间
            if duration is None:
                duration = min(max(distance * 0.01, 0.2), 1.0)
            
            # 添加随机抖动
            points = self._generate_human_mouse_path(
                self.last_mouse_position.x, self.last_mouse_position.y,
                x, y, duration
            )
            
            # 执行移动
            for point in points:
                pyautogui.moveTo(point[0], point[1])
                time.sleep(duration / len(points))
            
            self.last_mouse_position = pyautogui.position()
            logging.info(f"模拟鼠标移动: 从({self.last_mouse_position.x}, {self.last_mouse_position.y})到({x}, {y})")
            
        except Exception as e:
            logging.error(f"模拟鼠标移动失败: {str(e)}")
    
    def _generate_human_mouse_path(self, start_x: int, start_y: int, 
                                 end_x: int, end_y: int, duration: float) -> List[tuple]:
        """
        生成带有人类特征的鼠标移动路径
        :param start_x: 起始x坐标
        :param start_y: 起始y坐标
        :param end_x: 目标x坐标
        :param end_y: 目标y坐标
        :param duration: 移动持续时间
        :return: 路径点列表
        """
        points = []
        steps = int(duration * 60)  # 60fps
        
        for i in range(steps):
            t = i / steps
            # 使用贝塞尔曲线生成平滑路径
            x = start_x + (end_x - start_x) * t
            y = start_y + (end_y - start_y) * t
            
            # 添加随机抖动
            if 0 < t < 1:
                x += random.uniform(-2, 2) * (1 - abs(2 * t - 1))
                y += random.uniform(-2, 2) * (1 - abs(2 * t - 1))
            
            points.append((int(x), int(y)))
        
        return points
    
    def human_scroll(self, clicks: int = 1, direction: str = 'down') -> None:
        """
        模拟人类滚动操作
        :param clicks: 滚动次数
        :param direction: 滚动方向 ('up' 或 'down')
        """
        try:
            for _ in range(clicks):
                # 随机停顿
                time.sleep(random.uniform(0.1, 0.3))
                
                # 执行滚动
                if direction == 'down':
                    pyautogui.scroll(-120)
                else:
                    pyautogui.scroll(120)
                
                # 滚动后的随机停顿
                time.sleep(random.uniform(0.2, 0.5))
            
            logging.info(f"模拟滚动: {direction}, {clicks}次")
            
        except Exception as e:
            logging.error(f"模拟滚动失败: {str(e)}")
    
    def human_drag(self, start_x: int, start_y: int, 
                  end_x: int, end_y: int, duration: float = None) -> None:
        """
        模拟人类拖拽操作
        :param start_x: 起始x坐标
        :param start_y: 起始y坐标
        :param end_x: 目标x坐标
        :param end_y: 目标y坐标
        :param duration: 拖拽持续时间
        """
        try:
            # 移动到起始位置
            self.human_move_mouse(start_x, start_y)
            
            # 按下鼠标
            pyautogui.mouseDown()
            
            # 移动到目标位置
            self.human_move_mouse(end_x, end_y, duration)
            
            # 释放鼠标
            pyautogui.mouseUp()
            
            logging.info(f"模拟拖拽: 从({start_x}, {start_y})到({end_x}, {end_y})")
            
        except Exception as e:
            logging.error(f"模拟拖拽失败: {str(e)}")