# NIO与多路复用

> 模块：网络基础
> 更新时间：2026-03-29

---

## 一、IO模型对比

```
BIO（阻塞IO）：
  - 一个连接一个线程
  - 简单但并发受限
  - 适合连接数少的场景

NIO（非阻塞IO）：
  - 单线程处理多连接
  - Selector多路复用
  - 适合高并发场景

AIO（异步IO）：
  - 操作系统回调
  - 真正异步
  - 实现复杂
```

---

## 二、Selector核心

```java
public class NioEndpoint {
    private Selector selector;
    private ServerSocketChannel serverChannel;
    
    public void start() throws IOException {
        selector = Selector.open();
        serverChannel = ServerSocketChannel.open();
        serverChannel.bind(new InetSocketAddress(8080));
        serverChannel.configureBlocking(false);
        serverChannel.register(selector, SelectionKey.OP_ACCEPT);
        
        while (true) {
            int ready = selector.select();
            if (ready == 0) continue;
            
            Set<SelectionKey> keys = selector.selectedKeys();
            Iterator<SelectionKey> iterator = keys.iterator();
            
            while (iterator.hasNext()) {
                SelectionKey key = iterator.next();
                iterator.remove();
                
                if (key.isAcceptable()) {
                    accept(key);
                } else if (key.isReadable()) {
                    read(key);
                } else if (key.isWritable()) {
                    write(key);
                }
            }
        }
    }
    
    private void accept(SelectionKey key) throws IOException {
        ServerSocketChannel server = (ServerSocketChannel) key.channel();
        SocketChannel client = server.accept();
        client.configureBlocking(false);
        client.register(selector, SelectionKey.OP_READ);
    }
    
    private void read(SelectionKey key) throws IOException {
        SocketChannel client = (SocketChannel) key.channel();
        ByteBuffer buffer = ByteBuffer.allocate(8192);
        int len = client.read(buffer);
        
        if (len > 0) {
            buffer.flip();
            processRequest(buffer, client);
        } else if (len == -1) {
            client.close();
        }
    }
}
```

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 400" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="360" y="32" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">Selector事件循环</text>
  <rect x="260" y="56" width="200" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="83" text-anchor="middle" font-size="13" fill="#1e293b">select() 等待就绪事件</text>
  <line x1="360" y1="100" x2="360" y2="124" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="260" y="128" width="200" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="155" text-anchor="middle" font-size="13" fill="#1e293b">遍历 selectedKeys</text>
  <path d="M360,172 V196 H160 V216" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <path d="M360,172 V216" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <path d="M360,172 V196 H560 V216" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <text x="240" y="190" text-anchor="middle" font-size="12" fill="#475569">可接受</text>
  <text x="380" y="190" text-anchor="middle" font-size="12" fill="#475569">可读</text>
  <text x="480" y="190" text-anchor="middle" font-size="12" fill="#475569">可写</text>
  <rect x="60" y="220" width="200" height="54" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="160" y="242" text-anchor="middle" font-size="13" fill="#1e293b">isAcceptable</text>
  <text x="160" y="262" text-anchor="middle" font-size="12" fill="#475569">accept并注册OP_READ</text>
  <rect x="260" y="220" width="200" height="54" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="242" text-anchor="middle" font-size="13" fill="#1e293b">isReadable</text>
  <text x="360" y="262" text-anchor="middle" font-size="12" fill="#475569">read 读取请求</text>
  <rect x="460" y="220" width="200" height="54" rx="8" fill="#f5f3ff" stroke="#7c3aed" stroke-width="1.5"/>
  <text x="560" y="242" text-anchor="middle" font-size="13" fill="#1e293b">isWritable</text>
  <text x="560" y="262" text-anchor="middle" font-size="12" fill="#475569">write 写回响应</text>
  <path d="M660,247 H690 V78 H466" fill="none" stroke="#64748b" stroke-width="1.5" stroke-dasharray="5,4" marker-end="url(#ar1)"/>
  <text x="672" y="170" text-anchor="middle" font-size="12" fill="#475569">循环</text>
  <text x="360" y="372" text-anchor="middle" font-size="13" fill="#475569">BIO一个连接一个线程，NIO单线程多路复用</text>
</svg>

*图：Selector事件循环示意（依正文整理）*

---

## 三、Buffer操作

```java
ByteBuffer buffer = ByteBuffer.allocate(1024);

// 写入数据
buffer.put(data);

// 切换读模式
buffer.flip();

// 读取数据
byte[] result = new byte[buffer.remaining()];
buffer.get(result);

// 清空/重置
buffer.clear();   // 清空
buffer.rewind();  // 重置position
```

---

*下一步：线程模型设计*
