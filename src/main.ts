let ws: WebSocket;

const send_msg_list = [
    "你的笑容总是让我心跳加速。",   
    "有时候，我在想你的时候，会忍不住傻笑。",
    "我喜欢和你在一起的每一刻。",
    "你知道吗？我最近常常梦到你。",
    "每次和你聊天，时间都过得特别快。",
    "你的声音真好听，听得我心里暖暖的。",
    "我觉得我们之间有种特别的默契。",
    "你总是能让我感到特别的开心。",
    "和你在一起的时候，我感觉自己是世界上最幸运的人。",
    "你的眼神总是让我有种想靠近的冲动。",
    "如果有一天我消失了，你会想我吗？",
    "你让我觉得这个世界充满了可能性。",
    "我想和你一起分享每一个日落。",
    "每次看到你，我的心情都会变得很好。",
    "你身上的香气总是让我想靠近。",
    "和你在一起的时候，时间总是过得飞快。",
    "你的存在让我觉得生活更美好。",
    "我喜欢你的一切，甚至是你的小缺点。",
    "有你在身边，我就觉得无所畏惧。",
    "有时候，我觉得你是我命中注定的那个人。",
    "你的微笑是我一天的动力。",
    "我想知道你在想什么，总是那么神秘。",
    "你在我心中占据了一个特别的位置。",
    "我希望我们能有更多的时间在一起。",
    "你的每一句话都让我心动不已。",
    "我最喜欢的事情就是和你一起闲聊。",
    "你的一条消息能让我开心一整天。",
    "我觉得你身上有种难以抗拒的魅力。",
    "你让我相信，爱情真的存在。",
    "如果可以，我愿意和你一起走遍每一个地方。",
]
const sender_name_list = [
    "何毅彬",
    "听桥"
]
interface WsRecvMsg {
    sender: string;
    content: string;
}
interface WsSendMsg {
    receiver: string;
    content: string;
}

// 获取随机消息
function getRandomMessage() {
    const randomIndex = Math.floor(Math.random() * send_msg_list.length);
    return send_msg_list[randomIndex];
}

// 获取随机发送者
function getRandomSender() {
    const randomIndex = Math.floor(Math.random() * sender_name_list.length);
    return sender_name_list[randomIndex];
}

function connectWebSocket() {
    ws = new WebSocket('ws://localhost:8000/ws/client1');

    ws.onopen = () => {
        console.log("WebSocket连接已建立");
        // 连接成功后开始定时发送消息
        setInterval(sendMessage, 10000);
    };

    ws.onclose = (event) => {
        console.log("WebSocket连接已关闭，状态码：", event.code);
        // 3秒后尝试重连
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = (error) => {
        console.error("WebSocket错误:", error);
        // 检查服务器是否运行
        console.log("请确保服务器已启动且运行在 http://localhost:8000");
    };

    ws.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'receive') {
                console.log(`来自 ${msg.sender} 的消息: ${msg.content}`);
            }
        } catch (e) {
            console.error("解析消息错误:", e);
        }
    };
}

// 初始连接
connectWebSocket();

// 发送消息函数
function sendMessage() {
    if (ws.readyState === WebSocket.OPEN) {
        const content = getRandomMessage();
        const sender = getRandomSender();
        
        ws.send(JSON.stringify({
            type: "send",
            receiver:sender,
            content
        }));
        
        console.log(`发送消息: ${sender} -> ${content}`);
    } else {
        console.log("WebSocket未连接，消息未发送");
    }
}