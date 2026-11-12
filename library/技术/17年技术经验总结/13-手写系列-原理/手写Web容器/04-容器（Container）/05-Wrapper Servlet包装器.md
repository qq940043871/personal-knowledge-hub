# Wrapper Servlet包装器

> 模块：容器（Container）
> 更新时间：2026-03-29

---

## 一、Wrapper职责

```
Wrapper是最底层容器：
  - 封装单个Servlet实例
  - 管理Servlet生命周期
  - 处理Servlet请求
```

---

## 二、StandardWrapper实现：Servlet实例分配与生命周期

`StandardWrapper` 按 `singleThreadModel` 决定实例策略：**普通模式全局单实例；STM 模式使用 instancePool 实例池，上限 maxInstances（默认 20）**。`loadServlet()` 通过反射加载 Servlet 类并调用 `init()` 完成初始化；Valve 中按 allocate → Filter链 → doFilter → deallocate 的顺序处理请求。

```java
public class StandardWrapper extends ContainerBase implements Wrapper {
    private Servlet instance;
    private String servletClass;
    private boolean singleThreadModel = false;
    private Stack<Servlet> instancePool;
    private int maxInstances = 20;
    private AtomicInteger countAllocated = new AtomicInteger(0);
    
    public StandardWrapper() {
        super();
        pipeline.setBasic(new StandardWrapperValve());
    }
    
    @Override
    public String getServletClass() {
        return servletClass;
    }
    
    @Override
    public void setServletClass(String servletClass) {
        this.servletClass = servletClass;
    }
    
    @Override
    public Servlet allocate() throws ServletException {
        if (singleThreadModel) {
            synchronized (this) {
                if (instancePool == null) {
                    instancePool = new Stack<>();
                }
                if (!instancePool.isEmpty()) {
                    return instancePool.pop();
                }
                if (countAllocated.get() < maxInstances) {
                    countAllocated.incrementAndGet();
                    return loadServlet();
                }
            }
        } else {
            if (instance == null) {
                instance = loadServlet();
            }
            return instance;
        }
        return null;
    }
    
    @Override
    public void deallocate(Servlet servlet) {
        if (singleThreadModel && instancePool != null) {
            instancePool.push(servlet);
        }
    }
    
    private Servlet loadServlet() throws ServletException {
        try {
            Class<?> clazz = Class.forName(servletClass);
            Servlet servlet = (Servlet) clazz.newInstance();
            
            // 初始化Servlet
            ServletConfig config = new StandardServletConfig(this);
            servlet.init(config);
            
            return servlet;
        } catch (Exception e) {
            throw new ServletException("Failed to load servlet", e);
        }
    }
    
    private class StandardWrapperValve extends ValveBase {
        @Override
        public void invoke(Request request, Response response) throws IOException {
            try {
                Servlet servlet = allocate();
                
                // 应用Filter链
                FilterChain chain = new ApplicationFilterChain(servlet);
                
                // 执行Filter和Servlet
                chain.doFilter(request, response);
                
                deallocate(servlet);
            } catch (ServletException e) {
                throw new IOException("Servlet error", e);
            }
        }
    }
}
```

*图：StandardWrapperValve 的请求处理流程（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 370" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="210" y="20" width="300" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="47" text-anchor="middle" font-size="14" fill="#1e293b">StandardWrapperValve.invoke()</text>
  <line x1="360" y1="64" x2="360" y2="86" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="210" y="90" width="300" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="117" text-anchor="middle" font-size="14" fill="#1e293b">allocate()：获取 Servlet 实例</text>
  <line x1="360" y1="134" x2="360" y2="156" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="210" y="160" width="300" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="187" text-anchor="middle" font-size="14" fill="#1e293b">new ApplicationFilterChain(servlet)</text>
  <line x1="360" y1="204" x2="360" y2="226" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="210" y="230" width="300" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="257" text-anchor="middle" font-size="14" fill="#1e293b">chain.doFilter()：执行 Filter 与 Servlet</text>
  <line x1="360" y1="274" x2="360" y2="296" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="210" y="300" width="300" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="360" y="327" text-anchor="middle" font-size="14" fill="#1e293b">deallocate()：归还实例（STM 模式）</text>
</svg>

---

*下一步：Servlet接口与生命周期*
