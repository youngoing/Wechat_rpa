import uiautomation as auto
import time
import logging
import subprocess
import os
import random
import keyboard  # 需要先安装: pip install keyboard
import pyautogui  # 需要先安装: pip install pyautogui
import sys
# 收藏名称，必须包含

favorite_name = "黄旗山城市公园龙腾空间"

sender_name_list = [
    "何毅彬",
    "youngo",
    "听桥"
]
# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
class WeChatAutomation:
    def __init__(self):
        self.wx_window = None
        self.running = True  # 添加运行状态标志
    def human_click(self, x, y):
        """模拟人类点击"""
        try:
            # 先移动到目标位置
            self.human_move_to(x, y)
            
            # 随机短暂停顿
            time.sleep(random.uniform(0.1, 0.3))
            
            # 模拟点击，随机选择单击或双击
            if random.random() < 0.9:  # 90%概率单击
                pyautogui.click()
                time.sleep(random.uniform(0.05, 0.15))
            else:  # 10%概率双击
                pyautogui.doubleClick()
                time.sleep(random.uniform(0.1, 0.2))
                
        except Exception as e:
            logging.error(f"模拟人类点击失败: {str(e)}")    
    def human_type(self, text):
        """模拟人类输入文字"""
        try:
            # 随机的打字速度
            for char in text:
                pyautogui.typewrite(char)
                # 模拟不同字符间的输入时间差异
                time.sleep(random.uniform(0.05, 0.2))
                
            # 输入完成后的随机停顿
            time.sleep(random.uniform(0.2, 0.5))
            
        except Exception as e:
            logging.error(f"模拟人类输入文字失败: {str(e)}")
    def stop(self):
        """停止运行"""
        self.running = False
        logging.info("正在停止程序...")
        
    def find_wechat_window(self):
        """查找微信主窗口"""
        try:
            # 如果通过名称无法找到，尝试使用微信的类名查找
            self.wx_window = auto.WindowControl(ClassName='WeChatMainWndForPC', searchDepth=3)
            if self.wx_window.Exists():
                logging.info("通过类名成功找到微信窗口")
                self.wx_window.SetActive()
                # time.sleep(1)
                return True
            
            # 如果仍未找到，可能微信未启动，尝试启动
            logging.warning("未找到微信窗口，尝试启动微信...")
            self.start_wechat()
            time.sleep(2)  # 等待微信启动
            
            # 再次尝试查找
            for name in ['微信', 'WeChat']:
                self.wx_window = auto.WindowControl(ClassName='WeChatMainWndForPC', searchDepth=3)
                if self.wx_window.Exists():
                    logging.info(f"启动后成功找到微信窗口，窗口名称: {name}")
                    self.wx_window.SetActive()
                    # time.sleep(1)
                    return True
            
            logging.error("尝试启动后仍未找到微信窗口")
            return False
        except Exception as e:
            logging.error(f"查找微信窗口时出错: {str(e)}")
            return False
            
    def start_wechat(self):
        """尝试启动微信"""
        try:
            # 微信常见安装路径
            wechat_paths = [
                os.path.join(os.environ['ProgramFiles(x86)'], 'Tencent', 'WeChat', 'WeChat.exe'),
                os.path.join(os.environ['ProgramFiles'], 'Tencent', 'WeChat', 'WeChat.exe'),
                os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Tencent', 'WeChat', 'WeChat.exe')
            ]
            
            for path in wechat_paths:
                if os.path.exists(path):
                    logging.info(f"发现微信路径: {path}")
                    subprocess.Popen(path)
                    return True
            
            logging.error("未找到微信安装路径，请手动启动微信")
            return False
        except Exception as e:
            logging.error(f"启动微信时出错: {str(e)}")
            return False

    def human_move_to(self, x, y):
        """模拟人类移动鼠标"""
        try:
            # 计算当前位置到目标位置的距离
            current_x, current_y = pyautogui.position()
            distance = ((current_x - x) ** 2 + (current_y - y) ** 2) ** 0.5
            
            # 根据距离调整移动速度
            duration = min(1.0, distance / 2000) + random.uniform(0.1, 0.3)
            
            # 使用随机的缓动函数
            pyautogui.moveTo(x, y, duration=duration)
            
        except Exception as e:
            logging.error(f"模拟人类移动鼠标失败: {str(e)}")

    def click_button(self, button_name):
        """
        点击微信收藏按钮
        button_name: 按钮名称(收藏:Favorites, 主页面:Chats,联系人:Contacts,······)
        return: 是否点击成功
        """
        try:
            # 先确保微信窗口是激活的
            if self.wx_window and self.wx_window.Exists():
                self.wx_window.SetActive()
                time.sleep(0.5)
                
                # 方法1: 直接通过名称查找按钮控件
                favorites_button = self.wx_window.ButtonControl(Name=button_name, searchDepth=5)
                if favorites_button.Exists():
                    logging.info("找到Favorites按钮 (方法1)")
                    favorites_button.Click()
                    time.sleep(0.5)
                    return True
                
                time.sleep(0.3)
                pyautogui.click()
                time.sleep(0.5)
                return True
                
            else:
                logging.error("微信窗口不存在或未激活")
                return False
        except Exception as e:
            logging.error(f"点击收藏按钮时出错: {str(e)}")
            return False

    def find_favorite_and_send_to_friend(self, favorite_name, friend_name):
        """查找收藏项并直接发送给朋友"""
        try:
            logging.info(f"开始查找收藏项并发送给朋友: {favorite_name} -> {friend_name}")
            
            # 先点击收藏按钮打开收藏列表
            if not self.click_button("Favorites"):
                logging.error("无法点击收藏按钮")
                return False
            
            time.sleep(1)  # 等待收藏列表加载
            
            # 定义递归向上查找All Favorites列表的函数
            def find_all_favorites_in_ancestors(control, depth=6):
                try:
                    # 先检查当前控件是否是All Favorites列表
                    if (control.ControlType == auto.ControlType.ListControl and 
                        control.Name == 'All Favorites' and control.Exists()):
                        logging.info(f"找到All Favorites列表")
                        return control
                    
                    # 搜索当前控件的子控件
                    for child in control.GetChildren():
                        list_control = find_all_favorites_in_ancestors(child, 0)
                        if list_control:
                            return list_control
                    
                    # 如果当前深度允许，向上递归查找
                    if depth > 0:
                        parent = control.GetParentControl()
                        if parent:
                            return find_all_favorites_in_ancestors(parent, depth - 1)
                            
                except Exception as e:
                    logging.error(f"在递归查找All Favorites时出错: {str(e)}")
                return None
            
            # 查找收藏列表
            favorites_list = find_all_favorites_in_ancestors(self.wx_window)
            favorite_item = None
            
            if favorites_list and favorites_list.Exists():
                logging.info(f"找到All Favorites列表，开始查找收藏项: {favorite_name}")
                
                # 查找特定收藏项目
                list_items = favorites_list.GetChildren()
                logging.info(f"收藏列表中有{len(list_items)}个项目")
                
                for item in list_items:
                    try:
                        item_name = item.Name if hasattr(item, 'Name') else '无名称'
                        
                        if item.ControlType == auto.ControlType.ListItemControl and favorite_name in item_name:
                            logging.info(f"找到匹配的收藏项: {item_name}")
                            favorite_item = item
                            break
                    except Exception as e:
                        logging.error(f"检查列表项时出错: {str(e)}")
            
            # 如果找到了收藏项，直接右键点击
            if favorite_item and favorite_item.Exists():
                # 获取项目位置
                rect = favorite_item.BoundingRectangle
                center_x = (rect.left + rect.right) // 2
                center_y = (rect.top + rect.bottom) // 2
                
                # 移动到项目位置并右键点击
                self.human_move_to(center_x, center_y)
                time.sleep(0.3)
                pyautogui.rightClick()
                time.sleep(0.5)
                logging.info(f"已右键点击收藏项: {favorite_item.Name}")

                #向右和向下移动一点，然后左键点击
                pyautogui.move(10, 10)
                time.sleep(0.3)
                pyautogui.click()
                time.sleep(0.5)
                logging.info(f"已左键点击转发")
                time.sleep(0.2)

                
                # 点击搜索框
                search_box = self.wx_window.EditControl(Name='Search')
                if not search_box.Exists():
                    logging.warning("未找到标准搜索框，尝试找到备选搜索框...")
                    # 尝试其他可能的搜索框属性
                    search_box = self.wx_window.EditControl(searchDepth=3)
                if search_box.Exists():
                    search_box.Click()
                    # time.sleep(0.5)
                    # 清空搜索框
                    search_box.SendKeys('{Ctrl}a')
                    # time.sleep(0.2)
                    search_box.SendKeys('{Delete}')
                    # time.sleep(0.2)

                    # 输入联系人名称 - 使用SendKeys代替SetValue
                    search_box.SendKeys(friend_name)
                    # time.sleep(0.2)  # 增加等待时间
                    # 判断是否找到联系人
                    if search_box.Exists():
                        logging.info(f"成功找到联系人: {friend_name}")
                        search_box.SendKeys('{Enter}')
                        time.sleep(1.5)  # 等待搜索结果

                        logging.info("开始查找Send按钮")
                        send_button = self.wx_window.ButtonControl(Name="Send", searchDepth=6)
                        if not send_button.Exists():
                            send_button = self.wx_window.ButtonControl(Name="发送", searchDepth=6)
                        if send_button and send_button.Exists():
                            logging.info("直接查找找到Send按钮")
                            send_button.Click()
                            time.sleep(0.5)
                            return True
                        else:
                            logging.error("未找到Send按钮")
                            return False
                    else:
                        logging.error(f"未找到联系人: {friend_name}")
                        return False
                
            else:
                logging.error(f"未找到收藏项: {favorite_name}")
                return False
        except Exception as e:
            import traceback
            logging.error(f"查找收藏项并发送给好友时出错: {str(e)}")
            logging.error(f"详细错误信息: {traceback.format_exc()}")
            return False
        finally:
            # 点击主页按钮，返回主页面
            self.click_button("Chats")

    def find_and_click_send_button(self):
        """查找并点击Send按钮"""
        try:
            logging.info("开始查找Send按钮")
            send_button = self.wx_window.ButtonControl(Name="Send", searchDepth=6)
            if not send_button.Exists():
                send_button = self.wx_window.ButtonControl(Name="发送", searchDepth=6)
            
            if send_button and send_button.Exists():
                logging.info("直接查找找到Send按钮")
                send_button.Click()
                time.sleep(0.5)
                return True
            else:
                logging.error("未找到Send按钮")
                return False
        except Exception as e:
            import traceback
            logging.error(f"查找Send按钮出错: {str(e)}")
            logging.error(f"详细错误信息: {traceback.format_exc()}")
            return False

def main():
    # 创建自动化实例
    wx = WeChatAutomation()
    
    # 查找微信窗口
    if not wx.find_wechat_window():
        logging.error("无法找到或启动微信，请确保微信已正确安装")
        return
    wx.find_favorite_and_send_to_friend(favorite_name, sender_name_list[0])

if __name__ == "__main__":
    # 创建WeChatAutomation实例
    wx = WeChatAutomation()
    
    # 注册ESC键监听
    keyboard.on_press_key('esc', lambda _: wx.stop())
    
    logging.info("程序已启动，按ESC键停止运行")
    
    # 修改循环，增加运行状态检查
    count = 0
    try:
        while wx.running and count < 1000:  # 限制100次
            main()
            count += 1
            logging.info(f"已执行 {count}/100 次")
            
            # 检查是否按下ESC键
            if not wx.running:
                logging.info("检测到ESC键，正在停止程序...")
                sys.exit(0)
                

        # 随机等待1-50秒                
        time.sleep(random.randint(1, 50))
            
    except KeyboardInterrupt:
        logging.info("程序被手动中断")
    except Exception as e:
        logging.error(f"程序运行出错: {str(e)}")
    finally:
        logging.info(f"程序已停止，共执行 {count} 次")
