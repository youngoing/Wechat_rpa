# 微信RPA自动化工具

基于Python的微信PC客户端自动化工具，支持消息收发、收藏转发等功能。

## 功能特性

- 自动收发微信消息
- 新好友自动欢迎
- 收藏内容转发
- WebSocket实时通信
- 消息去重处理
- 异常自动重试

## 快速开始

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 启动微信RPA服务：
```bash
python main.py
```

3. 连接WebSocket服务：
```typescript
const ws = new WebSocket('ws://localhost:8000/ws/client1');
```

## 消息格式

### 发送文本消息
```json
{
    "type": "send_text",
    "receiver": "接收者名称",
    "content": "消息内容"
}
```

### 发送收藏内容
```json
{
    "type": "send_favorite",
    "favorite_name": "收藏内容名称",
    "friend_name": "接收者名称"
}
```

### 接收消息格式
```json
{
    "type": "receive",
    "sender": "发送者名称",
    "content": "消息内容"
}
```

## API说明

### WebSocket连接
- 端点：`ws://localhost:8000/ws/{client_id}`
- 参数：`client_id` - 客户端唯一标识符

### 消息发送示例
```typescript
// 发送文本消息
ws.send(JSON.stringify({
    type: "send_text",
    receiver: "接收者",
    content: "消息内容"
}));

// 发送收藏内容
ws.send(JSON.stringify({
    type: "send_favorite",
    favorite_name: "收藏内容",
    friend_name: "接收者"
}));
```

## 配置说明

服务器配置可在`main.py`中修改：
```python
config = uvicorn.Config(
    self.app,
    host="0.0.0.0",  # 监听地址
    port=8000,       # 监听端口
    log_level="info" # 日志级别
)
```

## 注意事项

1. 确保微信PC客户端已登录
2. 程序需要以管理员权限运行以访问UI自动化接口
3. 避免在消息处理过程中手动操作微信窗口
4. 建议在使用前备份重要的微信聊天记录
5. 新好友欢迎语需要开启免同意添加好友
6. 收藏转发功能需要确保收藏内容存在且可访问

## 错误处理

常见错误及解决方案：

1. 微信窗口未找到
   - 确保微信已启动并登录
   - 检查程序权限
   - 检查微信版本兼容性

2. WebSocket连接失败
   - 确认服务器地址和端口是否正确
   - 检查防火墙设置
   - 检查网络连接状态

3. 消息发送失败
   - 检查接收者名称是否正确
   - 确保微信窗口未被最小化
   - 检查消息内容是否包含特殊字符

4. 收藏转发失败
   - 确认收藏内容是否存在
   - 检查收藏内容名称是否正确
   - 确保接收者名称准确

## 开发计划

- [ ] 添加消息历史记录功能
- [ ] 实现消息队列持久化
- [ ] 添加更多消息类型支持（图片、文件等）
- [ ] 优化消息监控性能
- [ ] 添加用户认证机制
- [ ] 支持群聊消息处理
- [ ] 添加消息撤回功能
- [ ] 支持自定义欢迎语

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

[MIT License](LICENSE)

## 联系方式

如有问题或建议，请提交 Issue 或联系开发者。

## 更新日志

### v1.0.0
- 实现基本的消息收发功能
- 添加WebSocket服务器
- 实现任务队列管理
- 添加消息去重机制
- 实现新好友欢迎语
- 添加收藏内容转发功能
- 优化UI自动化操作
- 添加详细的日志记录