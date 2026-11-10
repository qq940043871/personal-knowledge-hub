# Nginx负载均衡配置

> 模块：负载均衡
> 更新时间：2026-03-29

---

## 一、负载均衡基础

### 架构图

```
                    ┌─────────────────┐
                    │   Nginx LB       │
                    │  (负载均衡器)    │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Backend 1  │      │  Backend 2  │      │  Backend 3  │
│   Node-A    │      │   Node-B    │      │   Node-C    │
│  192.168.1 │      │  192.168.2  │      │  192.168.3  │
└─────────────┘      └─────────────┘      └─────────────┘
```

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 440" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="360" y="32" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">Nginx负载均衡</text>
  <rect x="60" y="90" width="120" height="46" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="120" y="118" text-anchor="middle" font-size="13" fill="#1e293b">客户端</text>
  <rect x="300" y="90" width="140" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="370" y="118" text-anchor="middle" font-size="13" fill="#1e293b">Nginx LB</text>
  <line x1="182" y1="113" x2="294" y2="113" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="210" y="210" width="150" height="56" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="285" y="232" text-anchor="middle" font-size="13" fill="#1e293b">Backend 1</text>
  <text x="285" y="252" text-anchor="middle" font-size="12" fill="#475569">192.168.1.10</text>
  <rect x="380" y="210" width="150" height="56" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="455" y="232" text-anchor="middle" font-size="13" fill="#1e293b">Backend 2</text>
  <text x="455" y="252" text-anchor="middle" font-size="12" fill="#475569">192.168.1.11</text>
  <rect x="550" y="210" width="150" height="56" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="625" y="232" text-anchor="middle" font-size="13" fill="#1e293b">Backend 3</text>
  <text x="625" y="252" text-anchor="middle" font-size="12" fill="#475569">192.168.1.12</text>
  <path d="M370,136 V170 H285 V206" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <path d="M370,136 V206" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <path d="M370,136 V170 H625 V206" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <text x="360" y="312" text-anchor="middle" font-size="13" fill="#475569">负载均衡算法</text>
  <rect x="30" y="330" width="160" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="110" y="357" text-anchor="middle" font-size="13" fill="#1e293b">轮询（默认）</text>
  <rect x="220" y="330" width="160" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="300" y="357" text-anchor="middle" font-size="13" fill="#1e293b">加权轮询 weight</text>
  <rect x="410" y="330" width="160" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="490" y="357" text-anchor="middle" font-size="13" fill="#1e293b">ip_hash 会话保持</text>
  <rect x="590" y="330" width="120" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="650" y="357" text-anchor="middle" font-size="13" fill="#1e293b">least_conn</text>
  <text x="360" y="414" text-anchor="middle" font-size="13" fill="#475569">backup服务器仅在其余服务器不可用时启用</text>
</svg>

*图：Nginx负载均衡架构示意（依正文整理）*

---

## 二、upstream配置

### 基础配置

```nginx
# 在http块中定义upstream
upstream backend {
    server 192.168.1.10:8080;
    server 192.168.1.11:8080;
    server 192.168.1.12:8080;
}

server {
    listen 80;
    server_name example.com;
    
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### server参数

```nginx
upstream backend {
    # 完整语法
    server 192.168.1.10:8080 
        weight=5                  # 权重（默认1）
        max_fails=3               # 最大失败次数（默认1）
        fail_timeout=10s          # 失败超时时间（默认10秒）
        backup                   # 备份服务器
        down                     # 标记为不可用
        max_conns=1000            # 最大连接数
        slow_start=30s            # 慢启动时间（商业版）
        resolve                   # 动态DNS解析（商业版）
        ;
    
    server 192.168.1.11:8080 weight=5;
    server 192.168.1.12:8080 backup;  # 备用服务器
}
```

---

## 三、负载均衡算法

### 1. 轮询（默认）

```nginx
upstream backend {
    server 192.168.1.10:8080;
    server 192.168.1.11:8080;
    server 192.168.1.12:8080;
}
# 依次轮流向每个服务器分发请求
```

### 2. 加权轮询

```nginx
upstream backend {
    # weight越大，分配到的请求越多
    server 192.168.1.10:8080 weight=5;
    server 192.168.1.11:8080 weight=3;
    server 192.168.1.12:8080 weight=2;
}
# 10台机器分配：5台→Server1，3台→Server2，2台→Server3
```

### 3. IP哈希（ip_hash）

```nginx
upstream backend {
    ip_hash;  # 同一IP的请求始终发往同一后端
    server 192.168.1.10:8080;
    server 192.168.1.11:8080;
    server 192.168.1.12:8080;
}
# 优点：会话保持
# 缺点：新服务器上线会导致session失效
```

### 4. 最少连接（least_conn）

```nginx
upstream backend {
    least_conn;  # 分配给连接数最少的服务器
    server 192.168.1.10:8080;
    server 192.168.1.11:8080;
    server 192.168.1.12:8080;
}
```

### 5. 随机（random）

```nginx
upstream backend {
    random two [method];  # two=两个服务器中选一个
    server 192.168.1.10:8080;
    server 192.168.1.11:8080;
    server 192.168.1.12:8080;
}
```

### 6. 一致性哈希（商业版 / 推荐第三方）

```nginx
# 使用ngx_http_upstream_consistent_hash
upstream backend {
    consistent_hash $request_uri;
    server 192.168.1.10:8080;
    server 192.168.1.11:8080;
    server 192.168.1.12:8080;
}
```

---

## 四、健康检查

### 主动健康检查（商业版 / nginx_plus）

```nginx
upstream backend {
    zone backend 64k;
    
    server 192.168.1.10:8080;
    server 192.168.1.11:8080;
    
    # 健康检查配置
    health_check interval=5s fails=3 passes=2 uri=/health;
    slow_start 30s;
}
```

### 被动健康检查（开源版）

```nginx
upstream backend {
    server 192.168.1.10:8080 max_fails=3 fail_timeout=10s;
    server 192.168.1.11:8080 max_fails=3 fail_timeout=10s;
    server 192.168.1.12:8080 max_fails=3 fail_timeout=10s;
    
    # max_fails：连续失败次数达到此值，标记为不可用
    # fail_timeout：不可用持续时间
}

# 原理：
# 1. 当某server连续失败max_fails次
# 2. Nginx将其标记为不可用
# 3. 持续fail_timeout时间
# 4. 之后再次尝试一次
```

### 后端健康检查接口

```nginx
# Nginx代理配置
server {
    listen 80;
    server_name example.com;
    
    location /health {
        return 200 'OK';
        access_log off;
    }
    
    location / {
        proxy_pass http://backend;
    }
}

# 后端Spring Boot健康检查
@RestController
public class HealthController {
    @GetMapping("/health")
    public Map<String, String> health() {
        Map<String, String> result = new HashMap<>();
        result.put("status", "UP");
        result.put("timestamp", LocalDateTime.now().toString());
        return result;
    }
}
```

---

## 五、完整配置示例

```nginx
http {
    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'upstream: $upstream_addr';
    
    # 负载均衡配置
    upstream backend {
        # 使用IP哈希实现会话保持
        ip_hash;
        
        server 192.168.1.10:8080 weight=5 max_fails=3 fail_timeout=10s;
        server 192.168.1.11:8080 weight=5 max_fails=3 fail_timeout=10s;
        # 注：原稿此处截断，按常规配置补全（补齐该行指令与闭合花括号）
    }
}
```
