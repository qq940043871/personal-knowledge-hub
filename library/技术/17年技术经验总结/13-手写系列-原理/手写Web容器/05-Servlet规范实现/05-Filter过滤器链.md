# Filter过滤器链

> 模块：Servlet规范实现
> 更新时间：2026-03-29

---

## 一、Filter接口

Filter 接口定义 init / doFilter / destroy 三个方法，doFilter 通过参数拿到 FilterChain。

```java
public interface Filter {
    void init(FilterConfig filterConfig) throws ServletException;
    
    void doFilter(ServletRequest request, ServletResponse response, FilterChain chain) 
        throws IOException, ServletException;
    
    void destroy();
}
```

---

## 二、FilterChain实现：过滤器递进与Servlet调用

`ApplicationFilterChain` 用 **pos 游标**驱动整条链：每次 doFilter 取出 `filters.get(pos++)` 调用，**游标走完后执行 servlet.service()**。

```java
public class ApplicationFilterChain implements FilterChain {
    private List<Filter> filters = new ArrayList<>();
    private Servlet servlet;
    private int pos = 0;
    
    public ApplicationFilterChain(Servlet servlet) {
        this.servlet = servlet;
    }
    
    public void addFilter(Filter filter) {
        filters.add(filter);
    }
    
    @Override
    public void doFilter(ServletRequest request, ServletResponse response) 
        throws IOException, ServletException {
        
        if (pos < filters.size()) {
            Filter filter = filters.get(pos++);
            filter.doFilter(request, response, this);
        } else {
            servlet.service(request, response);
        }
    }
}
```

*图：请求依次经过 Filter 链到达 Servlet（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 150" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="10" y="40" width="90" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="55" y="67" text-anchor="middle" font-size="14" fill="#1e293b">请求</text>
  <line x1="102" y1="62" x2="116" y2="62" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="120" y="40" width="120" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="180" y="67" text-anchor="middle" font-size="14" fill="#1e293b">Filter 1</text>
  <line x1="242" y1="62" x2="256" y2="62" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="260" y="40" width="120" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="320" y="67" text-anchor="middle" font-size="14" fill="#1e293b">Filter 2</text>
  <line x1="382" y1="62" x2="396" y2="62" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="400" y="40" width="120" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="460" y="67" text-anchor="middle" font-size="14" fill="#1e293b">Filter N</text>
  <line x1="522" y1="62" x2="536" y2="62" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="540" y="40" width="170" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="625" y="67" text-anchor="middle" font-size="14" fill="#1e293b">servlet.service()</text>
  <text x="360" y="104" text-anchor="middle" font-size="13" fill="#475569">每个 Filter 在 doFilter 内调用 chain.doFilter(request, response, this) 递进</text>
  <text x="360" y="126" text-anchor="middle" font-size="13" fill="#475569">游标 pos 走完（pos == filters.size()）后，执行 servlet.service()</text>
</svg>

---

## 三、FilterConfig：Filter的延迟加载与初始化

`ApplicationFilterConfig` 包装 FilterDef 提供过滤器名、ServletContext 与初始化参数；getFilter() **首次调用时反射创建 Filter 并执行 init()**，之后复用同一实例。

```java
public class ApplicationFilterConfig implements FilterConfig {
    private Context context;
    private FilterDef filterDef;
    private Filter filter;
    
    public ApplicationFilterConfig(Context context, FilterDef filterDef) {
        this.context = context;
        this.filterDef = filterDef;
    }
    
    @Override
    public String getFilterName() {
        return filterDef.getName();
    }
    
    @Override
    public ServletContext getServletContext() {
        return context.getServletContext();
    }
    
    @Override
    public String getInitParameter(String name) {
        return filterDef.getInitParameter(name);
    }
    
    @Override
    public Enumeration<String> getInitParameterNames() {
        return Collections.enumeration(filterDef.getInitParameterNames());
    }
    
    public Filter getFilter() throws ServletException {
        if (filter == null) {
            try {
                Class<?> clazz = Class.forName(filterDef.getFilterClass());
                filter = (Filter) clazz.newInstance();
                filter.init(this);
            } catch (Exception e) {
                throw new ServletException("Failed to create filter", e);
            }
        }
        return filter;
    }
}
```

---

*下一步：Pipeline-Valve管道阀门*
