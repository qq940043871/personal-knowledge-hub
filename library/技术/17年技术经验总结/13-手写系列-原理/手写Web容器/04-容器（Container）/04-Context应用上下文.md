# Context应用上下文

> 模块：容器（Container）
> 更新时间：2026-03-29

---

## 一、Context职责

```
Context对应一个Web应用：
  - 管理多个Servlet（Wrapper）
  - 加载web.xml配置
  - 管理Session
  - 管理应用级资源
```

*图：Context 作为Web应用容器的组成（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 200" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="250" y="20" width="220" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="47" text-anchor="middle" font-size="14" fill="#1e293b">Context：对应一个Web应用</text>
  <line x1="340" y1="64" x2="105" y2="114" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="355" y1="64" x2="280" y2="114" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="365" y1="64" x2="440" y2="114" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="380" y1="64" x2="615" y2="114" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="19" y="120" width="160" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="99" y="143" text-anchor="middle" font-size="14" fill="#1e293b">管理Servlet</text>
  <text x="99" y="163" text-anchor="middle" font-size="13" fill="#475569">Wrapper 子容器</text>
  <rect x="193" y="120" width="160" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="273" y="143" text-anchor="middle" font-size="14" fill="#1e293b">加载web.xml</text>
  <text x="273" y="163" text-anchor="middle" font-size="13" fill="#475569">应用配置</text>
  <rect x="367" y="120" width="160" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="447" y="143" text-anchor="middle" font-size="14" fill="#1e293b">管理Session</text>
  <text x="447" y="163" text-anchor="middle" font-size="13" fill="#475569">SessionManager</text>
  <rect x="541" y="120" width="160" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="621" y="143" text-anchor="middle" font-size="14" fill="#1e293b">应用级资源</text>
  <text x="621" y="163" text-anchor="middle" font-size="13" fill="#475569">parameters 等</text>
</svg>

---

## 二、StandardContext实现：servletPath路由与应用级组件

`StandardContext` 持有 path、docBase、ServletContext、初始化参数、Filter 配置与 SessionManager；`StandardContextValve` 先为请求设置 contextPath，再按 servletPath 查找 Wrapper，**找不到时回退默认 Servlet（"/"），仍找不到则返回 404**。

```java
public class StandardContext extends ContainerBase implements Context {
    private String path;              // Context路径
    private String docBase;           // 应用目录
    private ServletContext servletContext;
    private Map<String, String> parameters = new HashMap<>();
    private Map<String, FilterConfig> filters = new HashMap<>();
    private SessionManager sessionManager;
    
    public StandardContext() {
        super();
        pipeline.setBasic(new StandardContextValve());
        this.servletContext = new ApplicationContext(this);
        this.sessionManager = new StandardSessionManager();
    }
    
    @Override
    public String getPath() {
        return path;
    }
    
    @Override
    public void setPath(String path) {
        this.path = path;
    }
    
    @Override
    public String getDocBase() {
        return docBase;
    }
    
    @Override
    public void setDocBase(String docBase) {
        this.docBase = docBase;
    }
    
    @Override
    public ServletContext getServletContext() {
        return servletContext;
    }
    
    @Override
    public void addParameter(String name, String value) {
        parameters.put(name, value);
    }
    
    @Override
    public String getParameter(String name) {
        return parameters.get(name);
    }
    
    private class StandardContextValve extends ValveBase {
        @Override
        public void invoke(Request request, Response response) throws IOException {
            // 包装请求，设置Context路径
            request.setContextPath(path);
            
            // 根据Servlet路径找到对应的Wrapper
            String servletPath = getServletPath(request.getRequestURI());
            Wrapper wrapper = (Wrapper) findChild(servletPath);
            
            if (wrapper == null) {
                // 查找默认Servlet
                wrapper = (Wrapper) findChild("/");
            }
            
            if (wrapper != null) {
                request.setWrapper(wrapper);
                wrapper.invoke(request, response);
            } else {
                response.sendError(404, "Servlet not found");
            }
        }
        
        private String getServletPath(String uri) {
            String pathWithoutContext = uri.substring(path.length());
            return pathWithoutContext.isEmpty() ? "/" : pathWithoutContext;
        }
    }
}
```

---

*下一步：Wrapper Servlet包装器*
