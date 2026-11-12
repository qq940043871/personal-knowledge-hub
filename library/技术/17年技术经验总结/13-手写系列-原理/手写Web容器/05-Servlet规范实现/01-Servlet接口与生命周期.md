# Servlet接口与生命周期

> 模块：Servlet规范实现
> 更新时间：2026-03-29

---

## 一、Servlet生命周期

```
1. 加载：ClassLoader加载Servlet类
2. 实例化：创建Servlet实例
3. 初始化：调用init()方法
4. 服务：反复调用service()方法
5. 销毁：调用destroy()方法
```

*图：Servlet 生命周期五个阶段（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 360" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="190" y="20" width="340" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="47" text-anchor="middle" font-size="14" fill="#1e293b">1. 加载：ClassLoader加载Servlet类</text>
  <line x1="360" y1="64" x2="360" y2="84" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="190" y="88" width="340" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="115" text-anchor="middle" font-size="14" fill="#1e293b">2. 实例化：创建Servlet实例</text>
  <line x1="360" y1="132" x2="360" y2="152" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="190" y="156" width="340" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="183" text-anchor="middle" font-size="14" fill="#1e293b">3. 初始化：调用init()方法</text>
  <line x1="360" y1="200" x2="360" y2="220" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="190" y="224" width="340" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="360" y="251" text-anchor="middle" font-size="14" fill="#1e293b">4. 服务：反复调用service()方法</text>
  <line x1="360" y1="268" x2="360" y2="288" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="190" y="292" width="340" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="360" y="319" text-anchor="middle" font-size="14" fill="#1e293b">5. 销毁：调用destroy()方法</text>
</svg>

---

## 二、Servlet接口

Servlet 接口定义了 init / service / destroy 三个生命周期方法，外加 getServletConfig 与 getServletInfo 两个元信息方法。

```java
public interface Servlet {
    void init(ServletConfig config) throws ServletException;
    
    ServletConfig getServletConfig();
    
    void service(ServletRequest request, ServletResponse response) 
        throws ServletException, IOException;
    
    String getServletInfo();
    
    void destroy();
}
```

---

## 三、HttpServlet实现：service()按HTTP方法分发

`HttpServlet` 把 ServletRequest/ServletResponse 强转为 HTTP 类型后，**按 request.getMethod() 分发到对应的 doXXX 方法**；未被覆盖的 doXXX 默认返回 405（SC_METHOD_NOT_ALLOWED）。

```java
public abstract class HttpServlet extends GenericServlet {
    
    @Override
    public void service(ServletRequest req, ServletResponse res) 
        throws ServletException, IOException {
        
        HttpServletRequest request = (HttpServletRequest) req;
        HttpServletResponse response = (HttpServletResponse) res;
        
        service(request, response);
    }
    
    protected void service(HttpServletRequest request, HttpServletResponse response) 
        throws ServletException, IOException {
        
        String method = request.getMethod();
        
        if ("GET".equals(method)) {
            doGet(request, response);
        } else if ("POST".equals(method)) {
            doPost(request, response);
        } else if ("PUT".equals(method)) {
            doPut(request, response);
        } else if ("DELETE".equals(method)) {
            doDelete(request, response);
        } else if ("HEAD".equals(method)) {
            doHead(request, response);
        } else if ("OPTIONS".equals(method)) {
            doOptions(request, response);
        } else {
            response.sendError(HttpServletResponse.SC_METHOD_NOT_ALLOWED);
        }
    }
    
    protected void doGet(HttpServletRequest request, HttpServletResponse response) 
        throws ServletException, IOException {
        response.sendError(HttpServletResponse.SC_METHOD_NOT_ALLOWED);
    }
    
    protected void doPost(HttpServletRequest request, HttpServletResponse response) 
        throws ServletException, IOException {
        response.sendError(HttpServletResponse.SC_METHOD_NOT_ALLOWED);
    }
    
    // 其他doXXX方法...
}
```

---

## 四、ServletConfig

`StandardServletConfig` 持有所属 Wrapper 与初始化参数表；getServletContext() 通过 wrapper.getParent() 向上取得容器的 ServletContext。

```java
public class StandardServletConfig implements ServletConfig {
    private Wrapper wrapper;
    private Map<String, String> initParameters = new HashMap<>();
    
    public StandardServletConfig(Wrapper wrapper) {
        this.wrapper = wrapper;
    }
    
    @Override
    public String getServletName() {
        return wrapper.getName();
    }
    
    @Override
    public ServletContext getServletContext() {
        return wrapper.getParent().getServletContext();
    }
    
    @Override
    public String getInitParameter(String name) {
        return initParameters.get(name);
    }
    
    @Override
    public Enumeration<String> getInitParameterNames() {
        return Collections.enumeration(initParameters.keySet());
    }
}
```

---

*下一步：ServletContext实现*
