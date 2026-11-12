# NIO连接器实现

> 模块：连接器（Connector）
> 更新时间：2026-03-29

---

## 一、NIO模型

> NIO 的核心优势：**线程数 << 连接数**，用 Selector 多路复用减少线程切换开销。

```
特点：
  - 非阻塞IO
  - Selector多路复用
  - 单线程处理多连接
  - 适合高并发场景

优势：
  - 线程数 << 连接数
  - 减少线程切换开销
  - 扩展性好
```

---

## 二、Poller模式

> 主线程只负责 accept，连接轮询分配给多个 Poller；Poller 负责注册、select 与分发就绪事件。

```java
public class NioEndpoint {
    private ServerSocketChannel serverChannel;
    private Selector selector;
    private Poller[] pollers;
    private int pollerCount = 2;
    private volatile boolean running = false;
    
    public void start() throws IOException {
        // 初始化ServerSocketChannel
        serverChannel = ServerSocketChannel.open();
        serverChannel.bind(new InetSocketAddress(8080));
        serverChannel.configureBlocking(false);
        
        // 初始化Poller
        pollers = new Poller[pollerCount];
        for (int i = 0; i < pollerCount; i++) {
            pollers[i] = new Poller();
            new Thread(pollers[i], "Poller-" + i).start();
        }
        
        running = true;
        System.out.println("NIO Endpoint started on port 8080");
        
        // 主线程接收连接
        while (running) {
            SocketChannel client = serverChannel.accept();
            if (client != null) {
                client.configureBlocking(false);
                // 轮询分配给Poller
                pollers[Math.abs(client.hashCode()) % pollerCount].register(client);
            }
        }
    }
    
    private class Poller implements Runnable {
        private Selector selector;
        private ConcurrentLinkedQueue<SocketChannel> queue = new ConcurrentLinkedQueue<>();
        
        public Poller() throws IOException {
            this.selector = Selector.open();
        }
        
        public void register(SocketChannel channel) {
            queue.offer(channel);
            selector.wakeup();
        }
        
        @Override
        public void run() {
            while (running) {
                try {
                    // 处理新连接
                    SocketChannel channel;
                    while ((channel = queue.poll()) != null) {
                        channel.register(selector, SelectionKey.OP_READ, new NioSocketWrapper(channel));
                    }
                    
                    // 等待事件
                    selector.select(1000);
                    
                    // 处理就绪事件
                    Iterator<SelectionKey> iterator = selector.selectedKeys().iterator();
                    while (iterator.hasNext()) {
                        SelectionKey key = iterator.next();
                        iterator.remove();
                        
                        if (key.isReadable()) {
                            NioSocketWrapper wrapper = (NioSocketWrapper) key.attachment();
                            wrapper.process();
                        }
                    }
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        }
    }
}
```

*图：NIO 连接器 · Acceptor 与 Poller 事件流（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 310" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <text x="170" y="30" text-anchor="middle" font-size="15" font-weight="bold" fill="#1e293b">主线程（Acceptor）</text>
  <text x="530" y="30" text-anchor="middle" font-size="15" font-weight="bold" fill="#1e293b">Poller 线程 × pollerCount</text>
  <rect x="60" y="44" width="220" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="170" y="62" text-anchor="middle" font-size="14" fill="#1e293b">accept() 接收连接</text>
  <text x="170" y="80" text-anchor="middle" font-size="12" fill="#475569">configureBlocking(false)</text>
  <line x1="280" y1="66" x2="386" y2="66" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="333" y="56" text-anchor="middle" font-size="12" fill="#475569">轮询分配</text>
  <text x="333" y="84" text-anchor="middle" font-size="11" fill="#475569">hash % pollerCount</text>
  <rect x="390" y="44" width="280" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="530" y="62" text-anchor="middle" font-size="14" fill="#1e293b">新连接入队并唤醒</text>
  <text x="530" y="80" text-anchor="middle" font-size="12" fill="#475569">queue.offer(channel) → selector.wakeup()</text>
  <line x1="530" y1="88" x2="530" y2="108" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="390" y="112" width="280" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="530" y="130" text-anchor="middle" font-size="14" fill="#1e293b">注册 OP_READ</text>
  <text x="530" y="148" text-anchor="middle" font-size="12" fill="#475569">register(selector, OP_READ, NioSocketWrapper)</text>
  <line x1="530" y1="156" x2="530" y2="176" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="390" y="180" width="280" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="530" y="198" text-anchor="middle" font-size="14" fill="#1e293b">select 等待就绪事件</text>
  <text x="530" y="216" text-anchor="middle" font-size="12" fill="#475569">selector.select(1000)</text>
  <line x1="530" y1="224" x2="530" y2="244" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="390" y="248" width="280" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="530" y="266" text-anchor="middle" font-size="14" fill="#1e293b">处理可读事件</text>
  <text x="530" y="284" text-anchor="middle" font-size="12" fill="#475569">key.isReadable() → wrapper.process()</text>
</svg>

---

## 三、SocketWrapper

> NioSocketWrapper：读到数据则处理请求并写回响应，读到 -1 关闭连接。

```java
public class NioSocketWrapper {
    private SocketChannel channel;
    private ByteBuffer readBuffer = ByteBuffer.allocate(8192);
    private ByteBuffer writeBuffer = ByteBuffer.allocate(8192);
    
    public NioSocketWrapper(SocketChannel channel) {
        this.channel = channel;
    }
    
    public void process() throws IOException {
        int len = channel.read(readBuffer);
        
        if (len > 0) {
            readBuffer.flip();
            byte[] data = new byte[readBuffer.remaining()];
            readBuffer.get(data);
            readBuffer.clear();
            
            // 处理HTTP请求
            String response = processHttpRequest(new String(data));
            
            // 返回响应
            writeBuffer.put(response.getBytes());
            writeBuffer.flip();
            channel.write(writeBuffer);
            writeBuffer.clear();
        } else if (len == -1) {
            channel.close();
        }
    }
}
```

---

*下一步：连接池管理*
