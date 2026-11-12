# ServletContext实现

> 模块：Servlet规范实现
> 更新时间：2026-03-29

---

## 一、ServletContext接口

接口方法按功能分为六组：路径与跨应用访问、初始化参数、全局属性、资源访问、请求分发器、日志。

*图：ServletContext 接口方法分组（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 180" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="240" y="20" width="240" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="47" text-anchor="middle" font-size="14" fill="#1e293b">ServletContext 接口</text>
  <line x1="340" y1="64" x2="66" y2="94" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="350" y1="64" x2="184" y2="94" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="358" y1="64" x2="302" y2="94" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="362" y1="64" x2="418" y2="94" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="370" y1="64" x2="536" y2="94" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="380" y1="64" x2="654" y2="94" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="4" y="100" width="112" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="60" y="122" text-anchor="middle" font-size="14" fill="#1e293b">路径</text>
  <text x="60" y="142" text-anchor="middle" font-size="13" fill="#475569">getContextPath</text>
  <rect x="124" y="100" width="112" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="180" y="122" text-anchor="middle" font-size="14" fill="#1e293b">初始化参数</text>
  <text x="180" y="142" text-anchor="middle" font-size="13" fill="#475569">getInitParameter</text>
  <rect x="244" y="100" width="112" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="300" y="122" text-anchor="middle" font-size="14" fill="#1e293b">全局属性</text>
  <text x="300" y="142" text-anchor="middle" font-size="13" fill="#475569">attributes</text>
  <rect x="364" y="100" width="112" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="420" y="122" text-anchor="middle" font-size="14" fill="#1e293b">资源访问</text>
  <text x="420" y="142" text-anchor="middle" font-size="13" fill="#475569">getRealPath</text>
  <rect x="484" y="100" width="112" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="540" y="122" text-anchor="middle" font-size="14" fill="#1e293b">请求分发</text>
  <text x="540" y="142" text-anchor="middle" font-size="13" fill="#475569">RequestDispatcher</text>
  <rect x="604" y="100" width="112" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="660" y="122" text-anchor="middle" font-size="14" fill="#1e293b">日志</text>
  <text x="660" y="142" text-anchor="middle" font-size="13" fill="#475569">log</text>
</svg>

```java
public interface ServletContext {
    String getContextPath();
    ServletContext getContext(String uripath);
    
    String getInitParameter(String name);
    Enumeration<String> getInitParameterNames();
    
    Object getAttribute(String name);
    void setAttribute(String name, Object object);
    void removeAttribute(String name);
    Enumeration<String> getAttributeNames();
    
    String getRealPath(String path);
    InputStream getResourceAsStream(String path);
    
    RequestDispatcher getRequestDispatcher(String path);
    RequestDispatcher getNamedDispatcher(String name);
    
    String getMimeType(String file);
    
    void log(String msg);
    void log(String message, Throwable throwable);
}
```

---

## 二、ApplicationContext实现

`ApplicationContext` 持有所属的 Context 容器；attributes 用 ConcurrentHashMap 保证并发安全，**setAttribute 传 null 等价于 removeAttribute**；getRealPath 以 docBase 拼接出真实路径，getRequestDispatcher 按 path 查找 Wrapper 构造分发器。

```java
public class ApplicationContext implements ServletContext {
    private Context context;
    private Map<String, Object> attributes = new ConcurrentHashMap<>();
    private Map<String, String> initParameters = new HashMap<>();
    private String contextPath;
    
    public ApplicationContext(Context context) {
        this.context = context;
        this.contextPath = context.getPath();
    }
    
    @Override
    public String getContextPath() {
        return contextPath;
    }
    
    @Override
    public String getInitParameter(String name) {
        return initParameters.get(name);
    }
    
    @Override
    public Object getAttribute(String name) {
        return attributes.get(name);
    }
    
    @Override
    public void setAttribute(String name, Object object) {
        if (object == null) {
            removeAttribute(name);
        } else {
            attributes.put(name, object);
        }
    }
    
    @Override
    public void removeAttribute(String name) {
        attributes.remove(name);
    }
    
    @Override
    public String getRealPath(String path) {
        if (!path.startsWith("/")) {
            path = "/" + path;
        }
        return context.getDocBase() + path;
    }
    
    @Override
    public InputStream getResourceAsStream(String path) {
        String realPath = getRealPath(path);
        try {
            return new FileInputStream(realPath);
        } catch (FileNotFoundException e) {
            return null;
        }
    }
    
    @Override
    public RequestDispatcher getRequestDispatcher(String path) {
        Wrapper wrapper = (Wrapper) context.findChild(path);
        if (wrapper != null) {
            return new ApplicationRequestDispatcher(wrapper);
        }
        return null;
    }
    
    @Override
    public void log(String msg) {
        System.out.println("[" + contextPath + "] " + msg);
    }
}
```

---

*下一步：HttpSession实现*
