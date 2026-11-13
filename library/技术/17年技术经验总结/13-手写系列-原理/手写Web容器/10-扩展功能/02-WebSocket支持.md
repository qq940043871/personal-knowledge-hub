# WebSocket支持

> 模块：扩展功能
> 更新时间：2026-03-29

---

## 一、WebSocket原理

> 三步握手：客户端发 Upgrade 请求 → 服务端返回 **101 Switching Protocols** → 建立双向通信。

```
HTTP升级到WebSocket：

1. 客户端发送升级请求
   GET /chat HTTP/1.1
   Upgrade: websocket
   Connection: Upgrade
   Sec-WebSocket-Key: ...

2. 服务端返回101响应
   HTTP/1.1 101 Switching Protocols
   Upgrade: websocket
   Connection: Upgrade
   Sec-WebSocket-Accept: ...

3. 建立双向通信
```

---

## 二、WebSocket处理

> 校验升级请求后计算 Sec-WebSocket-Accept：**key + magic（固定 GUID）经 SHA-1、Base64 编码**；返回 101 后进入帧循环，读到 Close 帧即结束。

```java
public class WebSocketUpgradeHandler {
    
    public boolean isUpgradeRequest(HttpRequest request) {
        String upgrade = request.getHeader("Upgrade");
        String connection = request.getHeader("Connection");
        
        return "websocket".equalsIgnoreCase(upgrade) && 
               connection != null && connection.contains("Upgrade");
    }
    
    public void handleUpgrade(HttpRequest request, HttpResponse response, 
                             Socket socket) throws IOException {
        // 验证请求
        if (!isValidUpgradeRequest(request)) {
            response.sendError(400, "Invalid WebSocket upgrade request");
            return;
        }
        
        // 计算Sec-WebSocket-Accept
        String key = request.getHeader("Sec-WebSocket-Key");
        String accept = calculateAccept(key);
        
        // 返回101响应
        response.setStatus(101);
        response.setHeader("Upgrade", "websocket");
        response.setHeader("Connection", "Upgrade");
        response.setHeader("Sec-WebSocket-Accept", accept);
        response.send();
        
        // 处理WebSocket通信
        handleWebSocketCommunication(socket);
    }
    
    private String calculateAccept(String key) throws IOException {
        String magic = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11";
        String input = key + magic;
        
        MessageDigest md = MessageDigest.getInstance("SHA-1");
        byte[] hash = md.digest(input.getBytes());
        
        return Base64.getEncoder().encodeToString(hash);
    }
    
    private void handleWebSocketCommunication(Socket socket) throws IOException {
        InputStream input = socket.getInputStream();
        OutputStream output = socket.getOutputStream();
        
        while (true) {
            // 读取WebSocket帧
            WebSocketFrame frame = readFrame(input);
            
            if (frame.isCloseFrame()) {
                break;
            }
            
            // 处理消息
            String message = frame.getPayload();
            System.out.println("WebSocket message: " + message);
            
            // 返回响应
            WebSocketFrame response = new WebSocketFrame(message);
            writeFrame(output, response);
        }
    }
}
```

*图：WebSocket 升级握手与帧循环（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 230" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="20" y="24" width="150" height="48" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="95" y="53" text-anchor="middle" font-size="13" fill="#1e293b">客户端发送升级请求</text>
  <line x1="170" y1="48" x2="198" y2="48" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="200" y="24" width="170" height="48" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="285" y="53" text-anchor="middle" font-size="13" fill="#1e293b">是否合法升级请求？</text>
  <text x="285" y="90" text-anchor="middle" font-size="12" fill="#475569">无效：sendError(400)</text>
  <line x1="370" y1="48" x2="398" y2="48" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="384" y="40" text-anchor="middle" font-size="12" fill="#475569">是</text>
  <rect x="400" y="24" width="190" height="48" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="495" y="53" text-anchor="middle" font-size="13" fill="#1e293b">计算 Sec-WebSocket-Accept</text>
  <text x="495" y="90" text-anchor="middle" font-size="12" fill="#475569">key + magic（固定 GUID）→ SHA-1 → Base64</text>
  <line x1="590" y1="48" x2="618" y2="48" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="620" y="24" width="80" height="48" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="660" y="53" text-anchor="middle" font-size="13" fill="#1e293b">返回 101</text>
  <path d="M660,72 L660,104 L50,104 L50,146" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="20" y="150" width="120" height="48" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="80" y="179" text-anchor="middle" font-size="13" fill="#1e293b">读取 WebSocket 帧</text>
  <line x1="140" y1="174" x2="168" y2="174" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="170" y="150" width="130" height="48" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="235" y="179" text-anchor="middle" font-size="13" fill="#1e293b">Close 帧？</text>
  <line x1="300" y1="174" x2="328" y2="174" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="314" y="166" text-anchor="middle" font-size="12" fill="#475569">否</text>
  <rect x="330" y="150" width="150" height="48" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="405" y="179" text-anchor="middle" font-size="13" fill="#1e293b">处理消息并回帧</text>
  <path d="M405,150 L405,128 L110,128 L110,146" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="257" y="124" text-anchor="middle" font-size="11" fill="#475569">循环读取下一帧</text>
  <path d="M235,198 L235,222 L560,222 L560,200" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="243" y="214" font-size="12" fill="#475569">是</text>
  <rect x="510" y="150" width="100" height="48" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="560" y="179" text-anchor="middle" font-size="13" fill="#1e293b">结束通信</text>
</svg>

---

*下一步：虚拟主机配置*
