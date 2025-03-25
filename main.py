import asyncio
from dataclasses import dataclass
from typing import List, Dict
import uiautomation as auto
import logging
import json
import time
import fastapi
from fastapi import WebSocket, WebSocketDisconnect


@dataclass
class WsSendMsg:
    receiver: str  
    content: str

@dataclass
class WsRecvMsg:
    sender: str
    content: str

class WeChatRPA:
    def __init__(self):
        self.wx_window = None
        self.send_queue = asyncio.Queue()  # 发送队列
        self.recv_queue = asyncio.Queue()  # 接收队列
        self.task_queue = asyncio.Queue()  # 任务队列
        self.processing_lock = asyncio.Lock()  # 处理锁
        self.is_processing = False  # 是否正在处理任务
        self.processed_messages = set()  # 已处理消息的集合，移到类级别
    async def process_task_queue(self):
        """处理任务队列"""
        while True:
            try:
                # 获取任务
                task = await self.task_queue.get()
                async with self.processing_lock:
                    self.is_processing = True
                    try:
                        if task['type'] == 'send':
                            success = await self.async_send_message(task['msg'])
                            if not success:
                                logging.error(f"消息发送失败: {task['msg']}")
                        elif task['type'] == 'monitor':
                            await self.get_session_list()
                        elif task['type'] == 'get_messages':
                            # 处理获取消息的任务
                            await self.click_chat(task['chat_name'], task['msg_count'])
                    finally:
                        self.is_processing = False
                        self.task_queue.task_done()
            except Exception as e:
                logging.error(f"处理任务出错: {str(e)}")
            await asyncio.sleep(0.1)
    def find_wechat_window(self)->bool:
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
            self.start_wechat()
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
    def search_and_open_chat(self, contact_name):
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
            time.sleep(0.5)  # 等待搜索结果
            search_box.SendKeys('{Enter}')
            time.sleep(0.5)
            return True
            
        except Exception as e:
            logging.error(f"搜索联系人时出错: {str(e)}")
            return False
    async def process_send_queue(self):
        """处理发送队列"""
        while True:
            if not self.send_queue.empty():
                msg = await self.send_queue.get()
                # 将发送任务加入任务队列
                await self.task_queue.put({
                    'type': 'send',
                    'msg': msg
                })
            await asyncio.sleep(0.1)
    
    async def async_send_message(self, msg: WsSendMsg) -> bool:
        """异步执行发送操作"""
        loop = asyncio.get_event_loop()
        try:
            # 将同步操作放入线程池执行
            return await loop.run_in_executor(
                None, 
                lambda: self._sync_send(msg)
            )
        except Exception as e:
            logging.error(f"异步发送异常: {str(e)}")
            return False
    
    def _sync_send(self, msg: WsSendMsg) -> bool:
        """实际同步发送逻辑（原send_message改进）"""
        try:
            if not self.search_and_open_chat(msg.receiver):
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
                        import re
                        match = re.search(r'^(.*?)(\d+)条新消息$', chat_name)
                        if match:
                            original_name = match.group(1).strip()
                            msg_count = int(match.group(2))
                            new_messages[original_name] = msg_count
                            logging.info(f"会话: {original_name} 有 {msg_count} 条新消息")
                            # 将获取消息的任务加入队列
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
            await asyncio.sleep(2)  # 每2秒检查一次

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
            if msg_data.get("type") == "send":
                msg = WsSendMsg(
                    receiver=msg_data["receiver"],
                    content=msg_data["content"]
                )
                await self.rpa.send_queue.put(msg)
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
    if not wechat_rpa.find_wechat_window():
        logging.error("微信窗口初始化失败")
        return
    
    # 初始化WebSocket服务
    ws_server = WsServer(wechat_rpa)
    
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
    asyncio.run(main())