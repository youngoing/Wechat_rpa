import asyncio
from dataclasses import dataclass
from typing import List, Dict
import uiautomation as auto
import logging
import json
import time
import fastapi
from fastapi import WebSocket, WebSocketDisconnect
import os
import subprocess
import pyautogui

@dataclass
class WsSendMsg:
    receiver: str  
    content: str

@dataclass
class WsRecvMsg:
    sender: str
    content: str

@dataclass
class WsFavoriteMsg:
    favorite_name: str
    friend_name: str

class WeChatRPA:
    def __init__(self):
        self.wx_window = None
        self.welcome_msg = "你好，我是小助手，有什么可以帮你的吗？"
        self.send_queue = asyncio.Queue()  # 发送队列
        self.recv_queue = asyncio.Queue()  # 接收队列
        self.task_queue = asyncio.Queue()  # 任务队列
        self.processing_lock = asyncio.Lock()  # 处理锁
        self.is_processing = False  # 是否正在处理任务
        self.processed_messages = set()  # 已处理消息的集合

    def human_move_to(self, x, y):
        """模拟人类移动鼠标"""
        try:
            pyautogui.moveTo(x, y, duration=0.3)
            return True
        except Exception as e:
            logging.error(f"移动鼠标时出错: {str(e)}")
            return False

    async def start_wechat(self):
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
    async def process_task_queue(self):
        """处理任务队列"""
        while True:
            try:
                # 获取任务
                task = await self.task_queue.get()
                async with self.processing_lock:
                    self.is_processing = True
                    try:
                        if task['type'] == 'send_text':
                            success = await self.async_send_message(task['msg'])
                            if not success:
                                logging.error(f"消息发送失败: {task['msg']}")
                        elif task['type'] == 'monitor':
                            await self.get_session_list()
                        elif task['type'] == 'get_messages':
                            # 处理获取消息的任务
                            await self.click_chat(task['chat_name'], task['msg_count'])
                        elif task['type'] == 'new_friend':
                            # 处理新好友验证消息
                            logging.info(f"处理新好友验证消息: {task['chat_name']}")
                            # 这里可以添加你想要的处理逻辑，比如发送欢迎消息
                            welcome_msg = WsSendMsg(
                                receiver=task['chat_name'],
                                content=self.welcome_msg
                            )
                            success = await self.async_send_message(welcome_msg)
                            if not success:
                                logging.error(f"发送欢迎消息失败: {task['chat_name']}")
                        elif task['type'] == 'send_favorite':
                            logging.info(f"处理发送收藏消息: {task['favorite_name']} -> {task['friend_name']}")
                            success = await self.find_favorite_and_send_to_friend(task['favorite_name'], task['friend_name'])
                            if not success:
                                logging.error(f"发送收藏消息失败: {task['favorite_name']} -> {task['friend_name']}")
                        else:
                            logging.error(f"未知任务类型: {task['type']}")
                    finally:
                        self.is_processing = False
                        self.task_queue.task_done()
            except Exception as e:
                logging.error(f"处理任务出错: {str(e)}")
            await asyncio.sleep(0.1)
    async def find_wechat_window(self)->bool:
        """查找微信主窗口"""
        try:
            # 使用微信的类名查找
            self.wx_window = auto.WindowControl(ClassName='WeChatMainWndForPC', searchDepth=3)
            if self.wx_window.Exists():
                logging.info("通过类名成功找到微信窗口")
                self.wx_window.SetActive()
                time.sleep(0.5)
                return True
            
            # 如果仍未找到，可能微信未启动，尝试启动
            logging.warning("未找到微信窗口，尝试启动微信...")
            await self.start_wechat()
            time.sleep(1)  # 等待微信启动
            
            # 再次尝试查找
            for name in ['微信', 'WeChat']:
                self.wx_window = auto.WindowControl(Name=name, searchDepth=3)
                if self.wx_window.Exists():
                    logging.info(f"启动后成功找到微信窗口，窗口名称: {name}")
                    self.wx_window.SetActive()
                    time.sleep(0.5)
                    return True
            
            logging.error("尝试启动后仍未找到微信窗口")
            return False
        except Exception as e:
            logging.error(f"查找微信窗口时出错: {str(e)}")
            return False

    async def search_and_open_chat(self, contact_name)->bool:
        """搜索并打开指定联系人的聊天窗口"""
        try:
            # 点击搜索框
            search_box = self.wx_window.EditControl(Name='Search')
            if not search_box.Exists():
                logging.error("未找到搜索框")
                return False
            
            search_box.Click()
            # 清空搜索框
            search_box.SendKeys('{Ctrl}a')
            time.sleep(0.2)
            search_box.SendKeys('{Delete}')
            time.sleep(0.2)
            
            # 输入联系人名称
            search_box.SendKeys(contact_name)
            time.sleep(0.3)  # 等待搜索结果
            search_box.SendKeys('{Enter}')
            time.sleep(0.3)
            return True
            
        except Exception as e:
            logging.error(f"搜索联系人时出错: {str(e)}")
            return False
    async def process_send_queue(self):
        """处理发送队列"""
        while True:
            if not self.send_queue.empty():
                msg = await self.send_queue.get()
                # 根据消息类型将任务加入任务队列
                if isinstance(msg, WsSendMsg):
                    await self.task_queue.put({
                        'type': 'send_text',
                        'msg': msg
                    })
                elif isinstance(msg, WsFavoriteMsg):
                    await self.task_queue.put({
                        'type': 'send_favorite',
                        'favorite_name': msg.favorite_name,
                        'friend_name': msg.friend_name
                    })
            else:
                await asyncio.sleep(0.1)
    async def click_button(self, button_name)->bool:
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
    
    async def async_send_message(self, msg: WsSendMsg) -> bool:
        """异步执行发送操作"""
        try:
            # 直接调用异步发送方法
            return await self._sync_send(msg)
        except Exception as e:
            logging.error(f"异步发送异常: {str(e)}")
            return False
    async def find_favorite_and_send_to_friend(self, favorite_name, friend_name):
        """查找收藏项并直接发送给朋友"""
        try:
            logging.info(f"开始查找收藏项并发送给朋友: {favorite_name} -> {friend_name}")
            # 先点击收藏按钮打开收藏列表
            if not await self.click_button("Favorites"):
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
            await self.click_button("Chats")
    
    async def _sync_send(self, msg: WsSendMsg) -> bool:
        """实际发送逻辑"""
        try:
            if not await self.search_and_open_chat(msg.receiver):
                return False
            
            # 优化输入框查找逻辑
            edit_box = self.wx_window.EditControl(ControlType=auto.ControlType.EditControl, 
                                     IsKeyboardFocusable=True,
                                     searchDepth=10)
            
            if edit_box.Exists():
                edit_box.SendKeys(msg.content + "{Enter}")
                logging.info(f"已发送至 {msg.receiver}: {msg.content}")
                return True
            return False
        except Exception as e:
            logging.error(f"发送异常: {str(e)}")
            return False
    
    async def get_session_list(self):
        """获取会话列表和新消息"""
        try:
            chat_list = self.wx_window.ListControl(Name='会话')
            if chat_list.Exists():
                new_messages = {}  # 存储新消息数量的字典
                
                for item in chat_list.GetChildren():
                    if item.ControlType == auto.ControlType.ListItemControl:
                        chat_name = item.Name
                        
                        # 获取当前会话项的所有面板文本
                        def get_item_pane_texts(control, depth=5):
                            texts = []
                            try:
                                # 如果深度为0，直接返回
                                if depth <= 0:
                                    logging.debug(f"达到最大搜索深度: {depth}")
                                    return texts
                                
                                # 记录当前控件的类型和名称
                                logging.debug(f"当前控件类型: {control.ControlType}, 名称: {control.Name}")
                                
                                # 获取当前控件下的所有子控件
                                text_controls = control.GetChildren()
                                logging.debug(f"找到 {len(text_controls)} 个子控件")
                                
                                for child in text_controls:
                                    # 记录每个子控件的类型和名称
                                    logging.debug(f"子控件类型: {child.ControlType}, 名称: {child.Name}")
                                    
                                    # 检查子控件的Name属性
                                    if child.Name:
                                        texts.append(child.Name)
                                        logging.debug(f"找到控件Name: {child.Name}")
                                        if any(f"以上是打招呼的内容" in text for text in texts):
                                            logging.debug("找到目标文本，提前返回")
                                            return texts
                                    
                                    # 检查子控件是否是TextControl
                                    if child.ControlType == auto.ControlType.TextControl:
                                        text = child.GetWindowText()
                                        if text:
                                            texts.append(text)
                                            logging.debug(f"找到TextControl文本: {text}")
                                            if any(f"以上是打招呼的内容" in text for text in texts):
                                                logging.debug("找到目标文本，提前返回")
                                                return texts
                                        else:
                                            logging.debug("TextControl没有文本内容")
                                    
                                    # 如果子控件是PaneControl，递归搜索其下的TextControl
                                    if child.ControlType == auto.ControlType.PaneControl:
                                        logging.debug(f"发现PaneControl，开始递归搜索，当前深度: {depth}")
                                        pane_texts = get_item_pane_texts(child, depth - 1)
                                        if pane_texts:
                                            texts.extend(pane_texts)
                                            logging.debug(f"从PaneControl中找到文本: {pane_texts}")
                                            if any(f"以上是打招呼的内容" in text for text in texts):
                                                logging.debug("找到目标文本，提前返回")
                                                return texts
                                        else:
                                            logging.debug("PaneControl中没有找到文本")
                                            
                            except Exception as e:
                                logging.error(f"收集文本时出错: {str(e)}", exc_info=True)
                            return texts
                        
                        # 获取当前会话项的面板文本
                        item_texts = get_item_pane_texts(item)
                        logging.debug(f"会话 {chat_name} 的面板文本: {item_texts}")
                        
                        # 检查是否是新好友验证消息
                        expected_text = f"你已添加了{chat_name}，现在可以开始聊天了"
                        if any(expected_text in text for text in item_texts):
                            # 不回复名称为空的好友
                            if chat_name.strip() == "":
                                logging.warning(f"检测到新好友验证消息: {chat_name}，但名称为空，跳过")
                                continue
                            logging.info(f"检测到新好友验证消息: {chat_name}")
                            await self.task_queue.put({
                                'type': 'new_friend',
                                'chat_name': chat_name
                            })
                            continue
                        
                        # 原有的新消息检测逻辑
                        import re
                        match = re.search(r'^(.*?)(\d+)条新消息$', chat_name)
                        if match:
                            original_name = match.group(1).strip()
                            msg_count = int(match.group(2))
                            new_messages[original_name] = msg_count
                            logging.info(f"会话: {original_name} 有 {msg_count} 条新消息")
                            await self.task_queue.put({
                                'type': 'get_messages',
                                'chat_name': original_name,
                                'msg_count': msg_count
                            })
                
                return new_messages
            else:
                logging.error("未找到会话列表")
                return {}
        except Exception as e:
            logging.error(f"获取会话列表出错: {str(e)}")
            return {}

    async def click_chat(self, chat_name: str, msg_count: int):
        """点击指定会话并获取消息"""
        try:
            chat_list = self.wx_window.ListControl(Name='会话')
            if chat_list.Exists():
                chat_item = chat_list.ListItemControl(Name=chat_name)
                if chat_item.Exists():
                    chat_item.Click()
                    time.sleep(0.5)
                    await self.get_detailed_messages(chat_name, msg_count)
                    return True
                else:
                    for item in chat_list.GetChildren():
                        if item.ControlType == auto.ControlType.ListItemControl and chat_name in item.Name:
                            item.Click()
                            time.sleep(0.5)
                            await self.get_detailed_messages(chat_name, msg_count)
                            return True
                    logging.error(f"未找到会话: {chat_name}")
                    return False
            else:
                logging.error("未找到会话列表")
                return False
        except Exception as e:
            logging.error(f"点击会话出错: {str(e)}")
            return False

    async def get_detailed_messages(self, chat_name: str, msg_count: int):
        """获取详细消息内容"""
        try:
            def find_message_list_in_ancestors(control, depth=3):
                try:
                    def search_in_children(parent_control):
                        if (parent_control.ControlType == auto.ControlType.ListControl and 
                            parent_control.Name == '消息' and parent_control.Exists()):
                            return parent_control
                        
                        for child in parent_control.GetChildren():
                            result = search_in_children(child)
                            if result:
                                return result
                        return None
                    
                    message_list = search_in_children(control)
                    if message_list:
                        return message_list
                    
                    if depth > 0:
                        parent = control.GetParentControl()
                        if parent:
                            return find_message_list_in_ancestors(parent, depth - 1)
                            
                except Exception as e:
                    logging.debug(f"在某一层查找消息列表时出错: {str(e)}")
                return None

            chat_area = find_message_list_in_ancestors(self.wx_window)
            if not chat_area or not chat_area.Exists():
                logging.error("未找到消息列表")
                return []

            valid_messages = []  # 存储有效的消息
            
            # 先收集所有有效消息
            for item in chat_area.GetChildren():
                if item.ControlType == auto.ControlType.ListItemControl:
                    content = item.Name

                    if any(x in content.lower() for x in ['am', 'pm', 'yesterday', ':', '上午', '下午']):
                        continue
                    
                    if any(x in content for x in ['[Location]', 'Voice Call', '[图片]', '[表情]', '[文件]']):
                        continue
                    
                    if content.strip():
                        valid_messages.append(content)
            
            # 只处理最新的msg_count条消息
            for content in valid_messages[-msg_count:]:
                message_id = f"{chat_name}_{content}"
                if message_id not in self.processed_messages:  # 使用类级别的集合
                    self.processed_messages.add(message_id)  # 添加到类级别的集合
                    await self.recv_queue.put(WsRecvMsg(
                        sender=chat_name,
                        content=content
                    ))
                    logging.debug(f"新消息已加入队列: {chat_name} -> {content}")  # 添加调试日志

            return []
        except Exception as e:
            logging.error(f"获取详细消息出错: {str(e)}")
            return []

    async def _monitor_messages(self):
        """监控新消息的内部方法"""
        try:
            await self.get_session_list()
        except Exception as e:
            logging.error(f"监控消息出错: {str(e)}")
    async def message_monitor(self):
        """持续监控新消息"""
        while True:
            await self.task_queue.put({
                'type': 'monitor'
            })
            await asyncio.sleep(5)  # 每2秒检查一次

class WsServer:
    def __init__(self, rpa: WeChatRPA):
        self.app = fastapi.FastAPI()
        self.manager = ConnectionManager()
        self.rpa = rpa
        
        @self.app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str):
            await self.manager.connect(websocket, client_id)
            try:
                while True:
                    data = await websocket.receive_text()
                    await self.handle_message(data)
            except WebSocketDisconnect:
                self.manager.disconnect(client_id)
    
    async def handle_message(self, data: str):
        """处理接收到的消息"""
        try:
            msg_data = json.loads(data)
            if msg_data.get("type") == "send_text":
                msg = WsSendMsg(
                    receiver=msg_data["receiver"],
                    content=msg_data["content"]
                )
                await self.rpa.send_queue.put(msg)
            elif msg_data.get("type") == "send_favorite":
                msg = WsFavoriteMsg(
                    favorite_name=msg_data["favorite_name"],
                    friend_name=msg_data["friend_name"]
                )
                await self.rpa.send_queue.put(msg)
            else:
                logging.error(f"ws接受到未知消息类型: {msg_data.get('type')}")
        except Exception as e:
            logging.error(f"消息处理错误: {str(e)}")
    
    async def broadcast_messages(self):
        """持续广播接收到的消息"""
        while True:
            if not self.rpa.recv_queue.empty():
                msg = await self.rpa.recv_queue.get()
                await self.manager.broadcast(msg)
            await asyncio.sleep(0.1)

    async def start_server(self):
        """启动FastAPI服务器"""
        import uvicorn
        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logging.info(f"Client {client_id} connected")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logging.info(f"Client {client_id} disconnected")
    
    async def send_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)
            logging.info(f"Sent message to {client_id}: {message}")
    
    async def broadcast(self, recv_msg: WsRecvMsg):
        for client_id, connection in self.active_connections.items():
            try:
                msg_json = json.dumps({
                    "type": "receive",
                    "sender": recv_msg.sender,
                    "content": recv_msg.content
                })
                logging.info(f"Broadcasted message to {client_id}: {recv_msg.sender} -> {recv_msg.content}")
                await connection.send_text(msg_json)
            except Exception as e:
                logging.error(f"Error broadcasting to {client_id}: {str(e)}")
                self.disconnect(client_id)
    
    async def process_messages(self):
        while True:
            try:
                message = await self.message_queue.get()
                if message.get("type") == "broadcast":
                    await self.broadcast(message["content"])
                elif message.get("type") == "direct":
                    await self.send_message(message["content"], message["client_id"])
                self.message_queue.task_done()
            except Exception as e:
                logging.error(f"Error processing message: {str(e)}")
async def main():
    # 初始化RPA
    wechat_rpa = WeChatRPA()
    if not await wechat_rpa.find_wechat_window():
        logging.error("微信窗口初始化失败")
        return
    
    # 初始化WebSocket服务
    ws_server = WsServer(wechat_rpa)

    # 保证刚开始微信处于主页面
    await wechat_rpa.click_button("Chats")
    # 创建任务列表
    tasks = [
        asyncio.create_task(wechat_rpa.process_task_queue()),  # 处理任务队列
        asyncio.create_task(wechat_rpa.process_send_queue()),  # 处理发送队列
        asyncio.create_task(wechat_rpa.message_monitor()),     # 监控新消息
        asyncio.create_task(ws_server.broadcast_messages()),    # 广播消息
        asyncio.create_task(ws_server.start_server())          # 启动服务器
    ]
    
    # 等待所有任务完成
    try:
        await asyncio.gather(*tasks)
    except Exception as e:
        logging.error(f"运行时错误: {str(e)}")
        for task in tasks:
            task.cancel()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    # 设置uiautomation的日志级别为WARNING，过滤掉其调试信息
    logging.getLogger('uiautomation').setLevel(logging.WARNING)
    asyncio.run(main())