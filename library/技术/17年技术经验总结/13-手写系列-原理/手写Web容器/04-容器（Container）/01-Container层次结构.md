# Container层次结构

> 模块：容器（Container）
> 更新时间：2026-03-29

---

## 一、Container四层结构

```
Engine（引擎）
  └── Host（虚拟主机）
       └── Context（Web应用）
            └── Wrapper（Servlet包装器）

职责划分：
  Engine：全局引擎，管理多个虚拟主机
  Host：虚拟主机，对应一个域名
  Context：Web应用，对应一个Context Path
  Wrapper：Servlet包装器，封装单个Servlet
```

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 400" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="360" y="32" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">Container四层结构</text>
  <rect x="60" y="56" width="170" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="145" y="83" text-anchor="middle" font-size="13" fill="#1e293b">Engine 引擎</text>
  <rect x="100" y="140" width="170" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="185" y="167" text-anchor="middle" font-size="13" fill="#1e293b">Host 虚拟主机</text>
  <rect x="140" y="224" width="170" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="225" y="251" text-anchor="middle" font-size="13" fill="#1e293b">Context 应用</text>
  <rect x="180" y="308" width="170" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="265" y="335" text-anchor="middle" font-size="13" fill="#1e293b">Wrapper 包装器</text>
  <path d="M145,100 V120 H185 V138" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <path d="M185,184 V204 H225 V222" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <path d="M225,268 V288 H265 V306" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <text x="250" y="83" text-anchor="start" font-size="12" fill="#475569">全局引擎，管理多个虚拟主机</text>
  <text x="290" y="167" text-anchor="start" font-size="12" fill="#475569">虚拟主机，对应一个域名</text>
  <text x="330" y="251" text-anchor="start" font-size="12" fill="#475569">Web应用，对应Context Path</text>
  <text x="370" y="335" text-anchor="start" font-size="12" fill="#475569">封装单个Servlet</text>
  <text x="360" y="382" text-anchor="middle" font-size="13" fill="#475569">每层容器持有Pipeline，invoke逐层下传</text>
</svg>

*图：Container四层结构示意（依正文整理）*

---

## 二、接口设计

```java
public interface Container {
    String getName();
    void setName(String name);
    
    Container getParent();
    void setParent(Container parent);
    
    void addChild(Container child);
    void removeChild(Container child);
    Container findChild(String name);
    Container[] findChildren();
    
    void invoke(Request request, Response response);
    
    Pipeline getPipeline();
    void setPipeline(Pipeline pipeline);
}
```

---

## 三、基础实现

```java
public abstract class ContainerBase implements Container {
    protected String name;
    protected Container parent;
    protected Map<String, Container> children = new HashMap<>();
    protected Pipeline pipeline = new StandardPipeline();
    
    @Override
    public String getName() {
        return name;
    }
    
    @Override
    public void setName(String name) {
        this.name = name;
    }
    
    @Override
    public Container getParent() {
        return parent;
    }
    
    @Override
    public void setParent(Container parent) {
        this.parent = parent;
    }
    
    @Override
    public void addChild(Container child) {
        child.setParent(this);
        children.put(child.getName(), child);
    }
    
    @Override
    public void removeChild(Container child) {
        children.remove(child.getName());
        child.setParent(null);
    }
    
    @Override
    public Container findChild(String name) {
        return children.get(name);
    }
    
    @Override
    public Container[] findChildren() {
        return children.values().toArray(new Container[0]);
    }
    
    @Override
    public Pipeline getPipeline() {
        return pipeline;
    }
    
    @Override
    public void invoke(Request request, Response response) {
        pipeline.invoke(request, response);
    }
}
```

---

*下一步：Engine引擎实现*
