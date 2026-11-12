# HTTP缓存机制

> 模块：网络层
> 更新时间：2026-03-29

---

## 一、缓存策略

```
HTTP缓存类型：
  1. 强缓存
     - Cache-Control / Expires
     - 不发送请求，直接使用缓存
     - 优先级：Cache-Control > Expires
  
  2. 协商缓存
     - Last-Modified / ETag
     - 发送请求，服务器判断是否使用缓存
     - 优先级：ETag > Last-Modified
```

---

## 二、缓存头

```
Cache-Control：
  max-age=3600         缓存有效期（秒）
  no-cache             强制协商缓存
  no-store             禁止缓存
  private              仅客户端缓存
  public               可被CDN等中间节点缓存
  must-revalidate       过期后必须验证

Expires：
  Expires: Wed, 21 Oct 2026 07:28:00 GMT

Last-Modified / If-Modified-Since：
  Last-Modified: Wed, 21 Oct 2026 07:28:00 GMT
  If-Modified-Since: Wed, 21 Oct 2026 07:28:00 GMT

ETag / If-None-Match：
  ETag: "33a64df551425fcc55e4d42a148795d9"
  If-None-Match: "33a64df551425fcc55e4d42a148795d9"
```

---

## 三、缓存决策流程

```
┌──────────────────────────────────────────────────────────┐
│                     请求资源                               │
└─────────────────────────┬────────────────────────────────┘
                          │
                          ▼
               ┌────────────────────────┐
               │  查找缓存？             │
               └───────────┬────────────┘
                    │是    │否
                    ▼       ▼
         ┌──────────────┐  ┌──────────────┐
         │  强缓存有效？ │  │  发起请求    │
         └──────┬───────┘  └──────┬───────┘
              │是   │否          │
              ▼     ▼            ▼
    直接返回    ▼       ┌──────────────┐
    缓存响应    │       │ 发送请求     │
              ▼       │ + 条件头     │
        ┌────────────┐│ └──────┬───────┘
        │  304 Not   ││        │
        │  Modified  ││        ▼
        └──────┬─────┘│  ┌─────────────┐
               │      │  │  200 OK     │
               ▼      │  │  (新内容)   │
        返回缓存响应   │  └──────┬──────┘
                       │        │
                       │        ▼
                       │  更新缓存
                       └────────┘
```

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 480" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="360" y="32" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">HTTP缓存决策流程</text>
  <rect x="260" y="56" width="200" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="83" text-anchor="middle" font-size="13" fill="#1e293b">请求资源</text>
  <line x1="360" y1="100" x2="360" y2="126" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="250" y="132" width="220" height="50" rx="24" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="360" y="162" text-anchor="middle" font-size="13" fill="#1e293b">本地有缓存？</text>
  <line x1="248" y1="157" x2="156" y2="157" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <text x="200" y="148" text-anchor="middle" font-size="12" fill="#475569">是</text>
  <rect x="30" y="132" width="120" height="50" rx="24" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="90" y="162" text-anchor="middle" font-size="13" fill="#1e293b">强缓存有效？</text>
  <line x1="90" y1="182" x2="90" y2="204" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <text x="104" y="198" text-anchor="start" font-size="12" fill="#475569">是</text>
  <rect x="20" y="210" width="140" height="50" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="90" y="230" text-anchor="middle" font-size="13" fill="#1e293b">直接使用缓存</text>
  <text x="90" y="250" text-anchor="middle" font-size="12" fill="#475569">不发送请求</text>
  <line x1="162" y1="235" x2="254" y2="235" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <text x="208" y="226" text-anchor="middle" font-size="12" fill="#475569">否</text>
  <line x1="360" y1="182" x2="360" y2="204" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <text x="374" y="198" text-anchor="start" font-size="12" fill="#475569">否</text>
  <rect x="260" y="210" width="200" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="237" text-anchor="middle" font-size="13" fill="#1e293b">发送请求+条件头</text>
  <line x1="360" y1="254" x2="360" y2="280" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="250" y="286" width="220" height="50" rx="24" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="360" y="316" text-anchor="middle" font-size="13" fill="#1e293b">资源是否变化？</text>
  <line x1="472" y1="311" x2="540" y2="311" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <text x="505" y="302" text-anchor="middle" font-size="12" fill="#475569">变化</text>
  <rect x="544" y="286" width="150" height="50" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="619" y="306" text-anchor="middle" font-size="13" fill="#1e293b">200 OK</text>
  <text x="619" y="326" text-anchor="middle" font-size="12" fill="#475569">返回新资源并更新缓存</text>
  <line x1="248" y1="311" x2="154" y2="311" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <text x="200" y="302" text-anchor="middle" font-size="12" fill="#475569">未变化</text>
  <rect x="20" y="286" width="130" height="50" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="85" y="306" text-anchor="middle" font-size="13" fill="#1e293b">304</text>
  <text x="85" y="326" text-anchor="middle" font-size="12" fill="#475569">Not Modified</text>
  <text x="360" y="398" text-anchor="middle" font-size="13" fill="#475569">强缓存：Cache-Control / Expires</text>
  <text x="360" y="424" text-anchor="middle" font-size="13" fill="#475569">协商缓存：ETag / Last-Modified</text>
  <text x="360" y="450" text-anchor="middle" font-size="13" fill="#475569">优先级：Cache-Control高于Expires，ETag高于Last-Modified</text>
</svg>

*图：HTTP缓存决策流程示意（依正文整理）*

---

## 四、C++实现

```cpp
class HttpCache {
private:
    std::map<std::string, CacheEntry> cache;
    std::mutex mutex;
    size_t maxCacheSize;
    
public:
    CacheResult get(const std::string& url) {
        std::lock_guard<std::mutex> lock(mutex);
        
        auto it = cache.find(url);
        if (it == cache.end()) {
            return CacheResult::NOT_FOUND;
        }
        
        CacheEntry& entry = it->second;
        
        // 检查过期
        if (entry.isExpired()) {
            cache.erase(it);
            return CacheResult::EXPIRED;
        }
        
        return CacheResult::HIT;
    }
    
    void put(const std::string& url, const HttpResponse& response) {
        std::lock_guard<std::mutex> lock(mutex);
        
        // 检查缓存大小
        if (cache.size() >= maxCacheSize) {
            evictOldest();
        }
        
        CacheEntry entry;
        entry.response = response;
        entry.cachedTime = time(nullptr);
        
        // 解析Cache-Control
        if (auto maxAge = response.getHeader("max-age")) {
            entry.expiresTime = entry.cachedTime + std::stoi(maxAge);
        }
        
        cache[url] = entry;
    }
    
    std::optional<HttpResponse> getCached(const std::string& url) {
        if (get(url) == CacheResult::HIT) {
            return cache[url].response;
        }
        return std::nullopt;
    }
};
```

---

*下一步：URL解析与规范*
