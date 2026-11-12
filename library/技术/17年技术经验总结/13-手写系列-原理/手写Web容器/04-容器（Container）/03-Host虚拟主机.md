# Host虚拟主机

> 模块：容器（Container）
> 更新时间：2026-03-29

---

## 一、Host职责

```
Host对应一个虚拟主机：
  - 管理多个Web应用（Context）
  - 支持域名绑定
  - 支持多域名映射同一Host
```

---

## 二、StandardHost实现：域名绑定与Context路由

`StandardHost` 在构造时把 `StandardHostValve` 挂到管道上作为基本阀；Valve 的核心逻辑是**从 URI 中截取 contextPath，找到对应 Context 后向下调用**，找不到时回退默认应用（空串），仍找不到则返回 404。

```java
public class StandardHost extends ContainerBase implements Host {
    private String appBase = "webapps";
    private String[] aliases;
    private boolean autoDeploy = true;
    
    public StandardHost() {
        super();
        pipeline.setBasic(new StandardHostValve());
    }
    
    @Override
    public String getAppBase() {
        return appBase;
    }
    
    @Override
    public void setAppBase(String appBase) {
        this.appBase = appBase;
    }
    
    @Override
    public String[] getAliases() {
        return aliases;
    }
    
    @Override
    public void addAlias(String alias) {
        if (aliases == null) {
            aliases = new String[] { alias };
        } else {
            String[] newAliases = new String[aliases.length + 1];
            System.arraycopy(aliases, 0, newAliases, 0, aliases.length);
            newAliases[aliases.length] = alias;
            aliases = newAliases;
        }
    }
    
    private class StandardHostValve extends ValveBase {
        @Override
        public void invoke(Request request, Response response) throws IOException {
            // 根据Context Path找到对应的Context容器
            String uri = request.getRequestURI();
            String contextPath = getContextPath(uri);
            
            Context context = (Context) findChild(contextPath);
            if (context == null) {
                context = (Context) findChild("");
            }
            
            if (context != null) {
                request.setContext(context);
                context.invoke(request, response);
            } else {
                response.sendError(404, "Context not found");
            }
        }
        
        private String getContextPath(String uri) {
            int secondSlash = uri.indexOf('/', 1);
            return secondSlash > 0 ? uri.substring(0, secondSlash) : uri;
        }
    }
}
```

*图：StandardHostValve 按contextPath路由到Context（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 260" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="250" y="20" width="220" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="47" text-anchor="middle" font-size="14" fill="#1e293b">请求URI（如 /app1/servlet）</text>
  <line x1="360" y1="64" x2="360" y2="88" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="230" y="92" width="260" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="119" text-anchor="middle" font-size="14" fill="#1e293b">StandardHostValve：截取contextPath</text>
  <line x1="336" y1="136" x2="152" y2="170" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="360" y1="136" x2="360" y2="170" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="384" y1="136" x2="568" y2="170" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="30" y="176" width="200" height="56" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="130" y="199" text-anchor="middle" font-size="14" fill="#1e293b">命中Context</text>
  <text x="130" y="220" text-anchor="middle" font-size="13" fill="#475569">setContext 后 invoke 下传</text>
  <rect x="260" y="176" width="200" height="56" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="360" y="199" text-anchor="middle" font-size="14" fill="#1e293b">未命中</text>
  <text x="360" y="220" text-anchor="middle" font-size="13" fill="#475569">回退 findChild("") 默认应用</text>
  <rect x="490" y="176" width="200" height="56" rx="8" fill="#fef2f2" stroke="#dc2626" stroke-width="1.5"/>
  <text x="590" y="199" text-anchor="middle" font-size="14" fill="#1e293b">均未命中</text>
  <text x="590" y="220" text-anchor="middle" font-size="13" fill="#475569">sendError(404, "Context not found")</text>
</svg>

---

*下一步：Context应用上下文*
