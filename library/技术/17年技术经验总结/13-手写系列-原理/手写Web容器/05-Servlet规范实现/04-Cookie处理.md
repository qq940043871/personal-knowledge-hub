# Cookie处理

> 模块：Servlet规范实现
> 更新时间：2026-03-29

---

## 一、CookieParser：请求头解析与Cookie字符串生成

`CookieParser` 提供两个静态方法：parse 把请求头按 `;` 拆分、按第一个 `=` 分离出 name/value，**无 `=` 的项直接跳过**；toString 把 Cookie 拼回 `name=value`，并按非空/开启状态附加 Path、Domain、Max-Age、Secure、HttpOnly 属性。

```java
public class CookieParser {
    
    public static Cookie[] parse(String cookieHeader) {
        if (cookieHeader == null || cookieHeader.isEmpty()) {
            return new Cookie[0];
        }
        
        List<Cookie> cookies = new ArrayList<>();
        String[] pairs = cookieHeader.split(";");
        
        for (String pair : pairs) {
            int eq = pair.indexOf('=');
            if (eq > 0) {
                String name = pair.substring(0, eq).trim();
                String value = pair.substring(eq + 1).trim();
                cookies.add(new Cookie(name, value));
            }
        }
        
        return cookies.toArray(new Cookie[0]);
    }
    
    public static String toString(Cookie cookie) {
        StringBuilder sb = new StringBuilder();
        sb.append(cookie.getName()).append("=").append(cookie.getValue());
        
        if (cookie.getPath() != null) {
            sb.append("; Path=").append(cookie.getPath());
        }
        
        if (cookie.getDomain() != null) {
            sb.append("; Domain=").append(cookie.getDomain());
        }
        
        if (cookie.getMaxAge() > 0) {
            sb.append("; Max-Age=").append(cookie.getMaxAge());
        }
        
        if (cookie.getSecure()) {
            sb.append("; Secure");
        }
        
        if (cookie.isHttpOnly()) {
            sb.append("; HttpOnly");
        }
        
        return sb.toString();
    }
}
```

*图：Cookie 的解析与序列化两个方向（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 220" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <text x="360" y="26" text-anchor="middle" font-size="15" font-weight="bold" fill="#1e293b">解析 parse()：请求头字符串 → Cookie[]</text>
  <rect x="38" y="40" width="140" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="108" y="67" text-anchor="middle" font-size="14" fill="#1e293b">Cookie 请求头</text>
  <line x1="180" y1="62" x2="202" y2="62" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="206" y="40" width="140" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="276" y="67" text-anchor="middle" font-size="14" fill="#1e293b">split(';') 拆分</text>
  <line x1="348" y1="62" x2="370" y2="62" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="374" y="40" width="140" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="444" y="67" text-anchor="middle" font-size="14" fill="#1e293b">indexOf('=') 分离</text>
  <line x1="516" y1="62" x2="538" y2="62" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="542" y="40" width="140" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="612" y="67" text-anchor="middle" font-size="14" fill="#1e293b">Cookie[]</text>
  <text x="360" y="132" text-anchor="middle" font-size="15" font-weight="bold" fill="#1e293b">序列化 toString()：Cookie 对象 → 字符串</text>
  <rect x="38" y="148" width="140" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="108" y="175" text-anchor="middle" font-size="14" fill="#1e293b">Cookie 对象</text>
  <line x1="180" y1="170" x2="202" y2="170" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="206" y="148" width="140" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="276" y="175" text-anchor="middle" font-size="14" fill="#1e293b">name=value</text>
  <line x1="348" y1="170" x2="370" y2="170" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="374" y="148" width="140" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="444" y="175" text-anchor="middle" font-size="14" fill="#1e293b">拼接可选属性</text>
  <line x1="516" y1="170" x2="538" y2="170" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="542" y="148" width="140" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="612" y="175" text-anchor="middle" font-size="14" fill="#1e293b">Cookie 字符串</text>
</svg>

---

## 二、Cookie类

Cookie 类除 name/value 外，还支持 comment、domain、maxAge（默认 -1）、path、secure、httpOnly、version 等属性。

```java
public class Cookie implements Cloneable {
    private String name;
    private String value;
    private String comment;
    private String domain;
    private int maxAge = -1;
    private String path;
    private boolean secure;
    private boolean httpOnly;
    private int version;
    
    public Cookie(String name, String value) {
        this.name = name;
        this.value = value;
    }
    
    public String getName() { return name; }
    public String getValue() { return value; }
    public void setValue(String value) { this.value = value; }
    
    public String getComment() { return comment; }
    public void setComment(String comment) { this.comment = comment; }
    
    public String getDomain() { return domain; }
    public void setDomain(String domain) { this.domain = domain; }
    
    public int getMaxAge() { return maxAge; }
    public void setMaxAge(int maxAge) { this.maxAge = maxAge; }
    
    public String getPath() { return path; }
    public void setPath(String path) { this.path = path; }
    
    public boolean getSecure() { return secure; }
    public void setSecure(boolean secure) { this.secure = secure; }
    
    public boolean isHttpOnly() { return httpOnly; }
    public void setHttpOnly(boolean httpOnly) { this.httpOnly = httpOnly; }
}
```

---

*下一步：Filter过滤器链*
