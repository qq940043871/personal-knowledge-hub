# Keep-Alive长连接

> 模块：性能优化
> 更新时间：2026-03-29

---

## 一、Keep-Alive原理

> HTTP/1.1 **默认启用 Keep-Alive**，复用 TCP 连接；参数：timeout 控制连接超时、max 控制最大请求数。

```
HTTP/1.0：
  - 每个请求建立新连接
  - 连接开销大

HTTP/1.1：
  - 默认启用Keep-Alive
  - 复用TCP连接
  - 减少连接建立时间

参数：
  - timeout: 连接超时时间
  - max: 最大请求数
```

---

## 二、实现代码

> 循环内读取并处理请求；**Connection 不允许复用或读超时即断开**，否则响应 keep-alive 头、计数 +1 继续复用。

```java
public class KeepAliveManager {
    private int timeout = 60000;      // 60秒
    private int maxRequests = 100;    // 最多100个请求
    
    public void handleConnection(Socket socket) throws IOException {
        int requestCount = 0;
        
        while (requestCount < maxRequests) {
            socket.setSoTimeout(timeout);
            
            try {
                // 读取请求
                HttpRequest request = parseRequest(socket.getInputStream());
                
                // 处理请求
                HttpResponse response = processRequest(request);
                
                // 检查Connection头
                String connection = request.getHeader("Connection");
                boolean keepAlive = "keep-alive".equalsIgnoreCase(connection) ||
                                   "HTTP/1.1".equals(request.getProtocol());
                
                if (!keepAlive) {
                    response.setHeader("Connection", "close");
                    response.send();
                    break;
                }
                
                response.setHeader("Connection", "keep-alive");
                response.setHeader("Keep-Alive", "timeout=" + (timeout/1000) + 
                                                 ", max=" + (maxRequests - requestCount - 1));
                response.send();
                
                requestCount++;
                
            } catch (SocketTimeoutException e) {
                // 连接超时，关闭
                break;
            }
        }
        
        socket.close();
    }
}
```

*图：Keep-Alive 连接复用循环（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 230" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="20" y="24" width="110" height="48" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="75" y="53" text-anchor="middle" font-size="13" fill="#1e293b">接收连接</text>
  <line x1="130" y1="48" x2="158" y2="48" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="160" y="24" width="140" height="48" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="230" y="53" text-anchor="middle" font-size="13" fill="#1e293b">读取并处理请求</text>
  <line x1="300" y1="48" x2="328" y2="48" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="330" y="24" width="170" height="48" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="415" y="53" text-anchor="middle" font-size="13" fill="#1e293b">Connection 允许复用？</text>
  <line x1="500" y1="48" x2="528" y2="48" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="514" y="40" text-anchor="middle" font-size="12" fill="#475569">是</text>
  <rect x="530" y="24" width="170" height="48" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="615" y="45" text-anchor="middle" font-size="12" fill="#1e293b">响应 keep-alive 头</text>
  <text x="615" y="63" text-anchor="middle" font-size="12" fill="#1e293b">requestCount + 1</text>
  <path d="M615,24 L615,6 L230,6 L230,22" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="422" y="18" text-anchor="middle" font-size="11" fill="#475569">继续下一请求</text>
  <path d="M415,72 L415,146" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="423" y="96" font-size="12" fill="#475569">否</text>
  <rect x="20" y="150" width="140" height="48" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="90" y="179" text-anchor="middle" font-size="13" fill="#1e293b">读超时 timeout=60s</text>
  <line x1="160" y1="174" x2="178" y2="174" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="180" y="150" width="120" height="48" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="240" y="179" text-anchor="middle" font-size="13" fill="#1e293b">socket.close()</text>
  <rect x="330" y="150" width="170" height="48" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="415" y="179" text-anchor="middle" font-size="13" fill="#1e293b">响应 Connection: close</text>
  <line x1="328" y1="174" x2="304" y2="174" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="216" y="216" text-anchor="middle" font-size="12" fill="#475569">循环结束（max=100）或异常后执行</text>
</svg>

---

## 三、性能对比

> 10 个请求：无 Keep-Alive 需 10 次建立 + 10 次关闭；有 Keep-Alive 仅 1 次建立 + 1 次关闭，**性能提升 50-80%**。

```
无Keep-Alive：
  - 10个请求 = 10次连接建立 + 10次连接关闭
  - 总时间 ≈ 10 * (连接建立时间 + 请求处理时间 + 连接关闭时间)

有Keep-Alive：
  - 10个请求 = 1次连接建立 + 10次请求处理 + 1次连接关闭
  - 总时间 ≈ 连接建立时间 + 10 * 请求处理时间 + 连接关闭时间
  - 性能提升：50-80%
```

---

*下一步：HTTPS支持*
