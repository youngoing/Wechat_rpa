
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

### 发送消息格式
```json
{
    "type": "send",
    "receiver": "接收者名称",
    "content": "消息内容"
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

### 消息发送
通过WebSocket连接发送JSON格式的消息：
```typescript
ws.send(JSON.stringify({
    type: "send",
    receiver: "接收者",
    content: "消息内容"
}));
```

## 配置说明

服务器配置可在`new.py`中修改：
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

## 错误处理

常见错误及解决方案：

1. 微信窗口未找到
   - 确保微信已启动并登录
   - 检查程序权限

2. WebSocket连接失败
   - 确认服务器地址和端口是否正确
   - 检查防火墙设置

3. 消息发送失败
   - 检查接收者名称是否正确
   - 确保微信窗口未被最小化

## 开发计划

- [ ] 添加消息历史记录功能
- [ ] 实现消息队列持久化
- [ ] 添加更多消息类型支持
- [ ] 优化消息监控性能
- [ ] 添加用户认证机制

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