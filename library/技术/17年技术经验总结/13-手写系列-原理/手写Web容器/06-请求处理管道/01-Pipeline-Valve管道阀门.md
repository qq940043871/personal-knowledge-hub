# Pipeline-Valve管道阀门

> 模块：请求处理管道
> 更新时间：2026-03-29

---

## 一、Pipeline-Valve模式

```
请求 ──► Valve1 ──► Valve2 ──► Valve3 ──► BasicValve ──► Servlet

特点：
  - 责任链模式
  - 可插拔的阀门
  - 每个容器有自己的Pipeline
  - 最后一个是BasicValve
```

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 400" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="360" y="32" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">Pipeline-Valve责任链</text>
  <rect x="10" y="110" width="100" height="48" rx="8" fill="#ffffff" stroke="#64748b" stroke-width="1.5"/>
  <text x="60" y="139" text-anchor="middle" font-size="13" fill="#1e293b">请求</text>
  <rect x="126" y="110" width="100" height="48" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="176" y="139" text-anchor="middle" font-size="13" fill="#1e293b">Valve1</text>
  <rect x="242" y="110" width="100" height="48" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="292" y="139" text-anchor="middle" font-size="13" fill="#1e293b">Valve2</text>
  <rect x="358" y="110" width="100" height="48" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="408" y="139" text-anchor="middle" font-size="13" fill="#1e293b">Valve3</text>
  <rect x="474" y="110" width="120" height="48" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="534" y="139" text-anchor="middle" font-size="13" fill="#1e293b">BasicValve</text>
  <rect x="610" y="110" width="100" height="48" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="660" y="139" text-anchor="middle" font-size="13" fill="#1e293b">Servlet</text>
  <line x1="112" y1="134" x2="122" y2="134" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <line x1="228" y1="134" x2="238" y2="134" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <line x1="344" y1="134" x2="354" y2="134" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <line x1="460" y1="134" x2="470" y2="134" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <line x1="596" y1="134" x2="606" y2="134" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <text x="360" y="210" text-anchor="middle" font-size="13" fill="#475569">责任链模式：Valve通过invokeNext依次调用</text>
  <text x="360" y="240" text-anchor="middle" font-size="13" fill="#475569">每个容器都有自己的Pipeline，Valve可插拔</text>
  <text x="360" y="270" text-anchor="middle" font-size="13" fill="#475569">管道最后一个阀门固定为BasicValve</text>
  <rect x="180" y="300" width="360" height="80" rx="8" fill="#f5f3ff" stroke="#7c3aed" stroke-width="1.5"/>
  <text x="200" y="324" text-anchor="start" font-size="12" fill="#1e293b">StandardPipeline</text>
  <rect x="210" y="338" width="150" height="28" rx="6" fill="#ffffff" stroke="#7c3aed" stroke-width="1"/>
  <text x="285" y="357" text-anchor="middle" font-size="12" fill="#1e293b">valves 列表</text>
  <rect x="380" y="338" width="150" height="28" rx="6" fill="#ffffff" stroke="#7c3aed" stroke-width="1"/>
  <text x="455" y="357" text-anchor="middle" font-size="12" fill="#1e293b">basic 阀门</text>
</svg>

*图：Pipeline-Valve管道责任链示意（依正文整理）*

---

## 二、接口定义

```java
public interface Pipeline {
    Valve getBasic();
    void setBasic(Valve valve);
    
    void addValve(Valve valve);
    void removeValve(Valve valve);
    
    Valve[] getValves();
    
    void invoke(Request request, Response response) throws IOException;
}

public interface Valve {
    String getInfo();
    
    void invoke(Request request, Response response, ValveContext context) 
        throws IOException;
}
```

---

## 三、StandardPipeline实现

```java
public class StandardPipeline implements Pipeline {
    protected Valve basic;
    protected List<Valve> valves = new ArrayList<>();
    
    @Override
    public Valve getBasic() {
        return basic;
    }
    
    @Override
    public void setBasic(Valve valve) {
        this.basic = valve;
    }
    
    @Override
    public void addValve(Valve valve) {
        valves.add(valve);
    }
    
    @Override
    public void removeValve(Valve valve) {
        valves.remove(valve);
    }
    
    @Override
    public void invoke(Request request, Response response) throws IOException {
        StandardValveContext context = new StandardValveContext();
        context.invokeNext(request, response);
    }
    
    private class StandardValveContext implements ValveContext {
        private int stage = 0;
        
        @Override
        public void invokeNext(Request request, Response response) throws IOException {
            Valve valve;
            
            if (stage < valves.size()) {
                valve = valves.get(stage);
            } else if (stage == valves.size()) {
                valve = basic;
            } else {
                return;
            }
            
            stage++;
            valve.invoke(request, response, this);
        }
    }
}
```

---

## 四、常用Valve

```java
// 访问日志Valve
public class AccessLogValve extends ValveBase {
    @Override
    public void invoke(Request request, Response response, ValveContext context) 
        throws IOException {
        long start = System.currentTimeMillis();
        
        context.invokeNext(request, response);
        
        long duration = System.currentTimeMillis() - start;
        logAccess(request, response, duration);
    }
    
    private void logAccess(Request request, Response response, long duration) {
        System.out.printf("%s %s %d %dms%n",
            request.getMethod(),
            request.getRequestURI(),
            response.getStatus(),
            duration
        );
    }
}

// 错误处理Valve
public class ErrorReportValve extends ValveBase {
    @Override
    public void invoke(Request request, Response response, ValveContext context) 
        throws IOException {
        try {
            context.invokeNext(request, response);
        } catch (Exception e) {
            response.setStatus(500);
            response.setContentType("text/html");
            response.getWriter().println(
                "<h1>500 Internal Server Error</h1><pre>" + 
                e.getMessage() + "</pre>"
            );
        }
    }
}
```

---

*下一步：请求分发机制*
