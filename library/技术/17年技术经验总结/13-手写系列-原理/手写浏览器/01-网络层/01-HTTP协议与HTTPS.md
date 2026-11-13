# HTTP协议与HTTPS

> 模块：网络层
> 更新时间：2026-03-29

---

## 一、HTTP协议基础：无状态请求/响应协议与版本演进

HTTP 是**基于 TCP/IP 的无状态请求/响应协议**，默认端口 80（HTTP）/ 443（HTTPS）；从 0.9 到 3 共经历五代演进。

```
HTTP（HyperText Transfer Protocol）：
  - 无状态请求/响应协议
  - 基于TCP/IP
  - 默认端口80（HTTP）/443（HTTPS）

版本演进：
  HTTP/0.9：1991年，仅GET，HTML格式
  HTTP/1.0：1996年，引入请求头、状态码
  HTTP/1.1：1999年，持久连接、虚拟主机
  HTTP/2：2015年，多路复用、头部压缩
  HTTP/3：2022年，QUIC协议
```

---

## 二、HTTP请求：请求行、请求头与请求方法

请求由**请求行 + 请求头 + 空行 + 请求体**（POST/PUT 才有）构成；常用方法覆盖资源的获取、提交、上传、删除等语义。

```
HTTP请求格式：
  请求行：GET /index.html HTTP/1.1
  请求头：
    Host: www.example.com
    User-Agent: Mozilla/5.0
    Accept: text/html
    Connection: keep-alive
  空行
  请求体（POST/PUT）

请求方法：
  GET：获取资源
  POST：提交数据
  PUT：上传资源
  DELETE：删除资源
  HEAD：获取头部
  OPTIONS：跨域预检
  PATCH：部分更新
```

---

## 三、HTTP响应：状态行、响应头与状态码分类

响应由**状态行 + 响应头 + 空行 + 响应体**构成；状态码按首位分为 1xx~5xx 五类。

```
HTTP响应格式：
  状态行：HTTP/1.1 200 OK
  响应头：
    Content-Type: text/html
    Content-Length: 1234
    Cache-Control: max-age=3600
    Set-Cookie: session=abc123
  空行
  响应体：<html>...</html>

状态码分类：
  1xx：信息性
  2xx：成功（200 OK, 201 Created）
  3xx：重定向（301, 302, 304）
  4xx：客户端错误（400, 401, 403, 404）
  5xx：服务端错误（500, 502, 503）
```

---

## 四、HTTPS原理：HTTP + TLS/SSL 与四次握手

**HTTPS = HTTP + TLS/SSL**。TLS 握手共四步：双方互发 Hello 交换随机数与加密套件，客户端用服务端公钥加密预主密钥完成密钥交换，最终双方生成相同的会话密钥，**后续通信改用对称加密**。

```
HTTPS = HTTP + TLS/SSL

TLS握手过程：
  1. 客户端Hello
     - 客户端支持的TLS版本
     - 加密套件列表
     - 随机数A
  
  2. 服务端Hello
     - 选定TLS版本和加密套件
     - 证书（公钥）
     - 随机数B
  
  3. 密钥交换
     - 客户端生成预主密钥
     - 用服务端公钥加密后发送
  
  4. 完成握手
     - 双方用预主密钥+随机数生成会话密钥
     - 后续通信使用对称加密
```

*图：TLS 握手四步流程（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 300" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="60" y="20" width="170" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="145" y="45" text-anchor="middle" font-size="15" fill="#1e293b">客户端</text>
  <rect x="490" y="20" width="170" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="575" y="45" text-anchor="middle" font-size="15" fill="#1e293b">服务端</text>
  <line x1="230" y1="95" x2="485" y2="95" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="357" y="88" text-anchor="middle" font-size="13" fill="#1e293b">1. 客户端Hello：TLS版本 + 加密套件 + 随机数A</text>
  <line x1="490" y1="145" x2="235" y2="145" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="362" y="138" text-anchor="middle" font-size="13" fill="#1e293b">2. 服务端Hello：选定套件 + 证书(公钥) + 随机数B</text>
  <line x1="230" y1="195" x2="485" y2="195" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="357" y="188" text-anchor="middle" font-size="13" fill="#1e293b">3. 密钥交换：预主密钥用服务端公钥加密发送</text>
  <rect x="230" y="230" width="260" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="360" y="249" text-anchor="middle" font-size="14" fill="#1e293b">4. 双方生成相同会话密钥</text>
  <text x="360" y="267" text-anchor="middle" font-size="12" fill="#475569">预主密钥 + 随机数 → 后续通信对称加密</text>
</svg>

---

## 五、C++实现：请求/响应的序列化与解析

用 C++ 定义 `HttpRequest` 与 `HttpResponse`：请求对象负责**序列化**（方法、路径、版本、头部逐行写出，空行后接请求体），响应对象负责**解析**（依次解析状态行、响应头、响应体）。

```cpp
class HttpRequest {
public:
    std::string method;
    std::string path;
    std::string version;
    std::map<std::string, std::string> headers;
    std::string body;
    
    std::string serialize() {
        std::ostringstream oss;
        oss << method << " " << path << " " << version << "\r\n";
        
        for (auto& h : headers) {
            oss << h.first << ": " << h.second << "\r\n";
        }
        
        oss << "\r\n";
        oss << body;
        
        return oss.str();
    }
};

class HttpResponse {
public:
    int status_code;
    std::string status_message;
    std::map<std::string, std::string> headers;
    std::string body;
    
    bool parse(const std::string& raw) {
        // 解析状态行
        // 解析响应头
        // 解析响应体
    }
};
```

---

*下一步：TCP连接管理*
