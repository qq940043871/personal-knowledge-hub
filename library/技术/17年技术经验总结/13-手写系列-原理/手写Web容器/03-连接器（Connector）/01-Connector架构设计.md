# Connector架构设计

> 模块：连接器（Connector）
> 更新时间：2026-03-29

---

## 一、Connector职责

> Connector 的核心职责：接收连接、解析 HTTP、封装 Request/Response、调用 Container、返回响应。

```
Connector核心功能：
  1. 接收网络连接
  2. 解析HTTP协议
  3. 封装Request/Response对象
  4. 调用Container处理请求
  5. 返回响应
```

---

## 二、架构设计

> 内部链路：Endpoint 接收连接 → Processor 解析 HTTP → Adapter 封装对象 → Container 处理。

```
┌─────────────────────────────────────────────┐
│                  Connector                    │
│                                              │
│  ┌───────────┐    ┌───────────────────────┐ │
│  │  Endpoint │───►│     Processor          │ │
│  │  (接收连接)│    │  (HTTP解析)            │ │
│  └───────────┘    └───────────┬───────────┘ │
│                               │              │
│                    ┌──────────▼──────────┐  │
│                    │     Adapter          │  │
│                    │  (Request/Response) │  │
│                    └──────────┬──────────┘  │
└───────────────────────────────┼─────────────┘
                                │
                    ┌───────────▼───────────┐
                    │      Container        │
                    └───────────────────────┘
```

---

## 三、核心组件

> 三个组件对应实现：NioEndpoint、Http11Processor、CoyoteAdapter，Handler 中完成解析→封装→调用 Container。

```java
public class Connector {
    private int port = 8080;
    private Endpoint endpoint;
    private Processor processor;
    private Adapter adapter;
    private Service service;
    
    public void start() throws Exception {
        // 初始化Endpoint
        endpoint = new NioEndpoint();
        endpoint.setPort(port);
        endpoint.setHandler(new ConnectHandler());
        
        // 初始化Processor
        processor = new Http11Processor();
        
        // 初始化Adapter
        adapter = new CoyoteAdapter();
        
        // 启动Endpoint
        endpoint.start();
    }
    
    private class ConnectHandler implements Handler {
        @Override
        public void process(Socket socket) {
            try {
                // 解析HTTP
                HttpRequest request = processor.parse(socket.getInputStream());
                HttpResponse response = new HttpResponse(socket.getOutputStream());
                
                // 转换为Servlet规范对象
                HttpServletRequest servletRequest = adapter.wrapRequest(request);
                HttpServletResponse servletResponse = adapter.wrapResponse(response);
                
                // 调用Container
                service.getContainer().invoke(servletRequest, servletResponse);
                
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }
}
```

---

*下一步：BIO连接器实现*
