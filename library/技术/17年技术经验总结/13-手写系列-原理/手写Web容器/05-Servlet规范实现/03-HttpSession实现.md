# HttpSession实现

> 模块：Servlet规范实现
> 更新时间：2026-03-29

---

## 一、Session管理：创建、过期校验与后台清理

`StandardSessionManager` 用 ConcurrentHashMap 保存会话，默认超时 1800 秒（30 分钟）；**getSession 时做惰性过期检查，超时即移除并 invalidate**；另有每 60 秒检查一次的后台守护线程统一清理过期 Session。SessionId 为去掉连字符的 UUID。

```java
public class StandardSessionManager implements SessionManager {
    private ConcurrentHashMap<String, HttpSession> sessions = new ConcurrentHashMap<>();
    private int sessionTimeout = 1800;  // 30分钟
    
    public HttpSession createSession() {
        String sessionId = generateSessionId();
        StandardSession session = new StandardSession(sessionId);
        session.setMaxInactiveInterval(sessionTimeout);
        sessions.put(sessionId, session);
        return session;
    }
    
    public HttpSession getSession(String sessionId) {
        HttpSession session = sessions.get(sessionId);
        if (session != null) {
            if (session.getMaxInactiveInterval() > 0) {
                long inactiveTime = System.currentTimeMillis() - session.getLastAccessedTime();
                if (inactiveTime > session.getMaxInactiveInterval() * 1000L) {
                    sessions.remove(sessionId);
                    session.invalidate();
                    return null;
                }
            }
            ((StandardSession) session).setLastAccessedTime(System.currentTimeMillis());
        }
        return session;
    }
    
    private String generateSessionId() {
        return UUID.randomUUID().toString().replace("-", "");
    }
    
    // 后台线程清理过期Session
    public void startBackgroundProcessor() {
        Thread cleaner = new Thread(() -> {
            while (true) {
                try {
                    Thread.sleep(60000);  // 每分钟检查一次
                    cleanExpiredSessions();
                } catch (InterruptedException e) {
                    break;
                }
            }
        }, "SessionCleaner");
        cleaner.setDaemon(true);
        cleaner.start();
    }
    
    private void cleanExpiredSessions() {
        sessions.forEach((id, session) -> {
            if (session.getMaxInactiveInterval() > 0) {
                long inactiveTime = System.currentTimeMillis() - session.getLastAccessedTime();
                if (inactiveTime > session.getMaxInactiveInterval() * 1000L) {
                    sessions.remove(id);
                    session.invalidate();
                }
            }
        });
    }
}
```

---

## 二、Session实现：StandardSession属性存取与失效保护

`StandardSession` 记录创建时间与最后访问时间；**invalidate 后 valid 置为 false，之后任何属性操作都会抛 IllegalStateException**。

```java
public class StandardSession implements HttpSession {
    private String id;
    private long creationTime;
    private long lastAccessedTime;
    private int maxInactiveInterval;
    private Map<String, Object> attributes = new ConcurrentHashMap<>();
    private boolean valid = true;
    
    public StandardSession(String id) {
        this.id = id;
        this.creationTime = System.currentTimeMillis();
        this.lastAccessedTime = creationTime;
    }
    
    @Override
    public String getId() {
        return id;
    }
    
    @Override
    public long getCreationTime() {
        return creationTime;
    }
    
    @Override
    public long getLastAccessedTime() {
        return lastAccessedTime;
    }
    
    public void setLastAccessedTime(long time) {
        this.lastAccessedTime = time;
    }
    
    @Override
    public int getMaxInactiveInterval() {
        return maxInactiveInterval;
    }
    
    @Override
    public void setMaxInactiveInterval(int interval) {
        this.maxInactiveInterval = interval;
    }
    
    @Override
    public Object getAttribute(String name) {
        checkValid();
        return attributes.get(name);
    }
    
    @Override
    public void setAttribute(String name, Object value) {
        checkValid();
        attributes.put(name, value);
    }
    
    @Override
    public void invalidate() {
        checkValid();
        attributes.clear();
        valid = false;
    }
    
    private void checkValid() {
        if (!valid) {
            throw new IllegalStateException("Session already invalidated");
        }
    }
}
```

*图：Session 从创建到失效的状态流转（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 230" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="200" y="16" width="320" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="43" text-anchor="middle" font-size="14" fill="#1e293b">createSession()：UUID 会话，默认超时 1800 秒</text>
  <line x1="310" y1="60" x2="228" y2="94" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="110" y="100" width="220" height="56" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="220" y="122" text-anchor="middle" font-size="14" fill="#1e293b">Session 有效</text>
  <text x="220" y="142" text-anchor="middle" font-size="13" fill="#475569">访问刷新 lastAccessedTime</text>
  <rect x="390" y="100" width="220" height="56" rx="8" fill="#fef2f2" stroke="#dc2626" stroke-width="1.5"/>
  <text x="500" y="122" text-anchor="middle" font-size="14" fill="#1e293b">已失效（invalidate）</text>
  <text x="500" y="142" text-anchor="middle" font-size="13" fill="#475569">失效后访问抛 IllegalStateException</text>
  <line x1="330" y1="128" x2="384" y2="128" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="360" y="182" text-anchor="middle" font-size="13" fill="#475569">超时（inactive &gt; maxInactiveInterval）或主动 invalidate()</text>
  <text x="360" y="204" text-anchor="middle" font-size="13" fill="#475569">后台线程每 60 秒清理过期 Session</text>
</svg>

---

*下一步：Cookie处理*
