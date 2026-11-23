## 📋 概述

Canal 是阿里巴巴开源的数据库 Binlog 订阅工具，用于实时数据同步和变更捕获，是构建实时数据管道的核心组件。

**核心功能：**

- MySQL Binlog 实时订阅
- 数据变更实时捕获
- 高可靠性和可扩展性
- 多种消费模式支持

## 🏗️ 架构设计

```
<code>┌─────────────────────────────────────────────────────┐<br/>│                    Canal 架构                         │<br/>├─────────────────────────────────────────────────────┤<br/>│  MySQL → Binlog → Canal Server → Canal Client → 目标系统  │<br/>│                                                     │<br/>│  1. MySQL 开启 Binlog                              │<br/>│  2. Canal 模拟 slave 连接                          │<br/>│  3. 解析 Binlog 事件                               │<br/>│  4. 发送到客户端处理                               │<br/>└─────────────────────────────────────────────────────┘</code>
```

## 🚀 快速开始

### 1. 环境准备

```
<code># 1. 开启 MySQL Binlog<br/># 修改 my.cnf<br/>[mysqld]<br/>log-bin=mysql-bin  # 开启 binlog<br/>binlog-format=ROW  # 选择 ROW 模式<br/>server_id=1        # 服务器 ID<br/><br/># 2. 重启 MySQL<br/>systemctl restart mysql<br/><br/># 3. 创建 Canal 用户<br/>mysql -u root -p<br/>CREATE USER 'canal'@'%' IDENTIFIED BY 'canal';<br/>GRANT SELECT, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'canal'@'%';<br/>FLUSH PRIVILEGES;</code>
```

### 2. 安装 Canal

```
<code># 下载 Canal<br/>wget https://github.com/alibaba/canal/releases/download/canal-1.1.7/canal.deployer-1.1.7.tar.gz<br/><br/># 解压<br/>mkdir /opt/canal<br/>tar -zxvf canal.deployer-1.1.7.tar.gz -C /opt/canal<br/><br/># 配置<br/>cd /opt/canal/conf/example<br/>vi instance.properties</code>
```

### 3. 配置 Canal

```
<code># instance.properties 配置<br/>canal.instance.master.address=127.0.0.1:3306<br/>canal.instance.dbUsername=canal<br/>canal.instance.dbPassword=canal<br/>canal.instance.connectionCharset=UTF-8<br/>canal.instance.tsdb.enable=true<br/>canal.instance.gtidon=false<br/><br/># 表过滤规则<br/>canal.instance.filter.regex=.*\..*<br/>canal.instance.filter.black.regex=mysql\.slave_.*</code>
```

### 4. 启动 Canal

```
<code># 启动 Canal 服务<br/>cd /opt/canal/bin<br/>./startup.sh<br/><br/># 查看日志<br/>cd /opt/canal/logs/example<br/>tail -f example.log</code>
```

## 🔧 核心配置

### 1. 服务端配置

| th | th | th |
| --- | --- | --- |
| td | td | td |
| td | td | td |

### 2. 全局配置

```
<code># conf/canal.properties<br/>canal.id=1<br/>canal.ip=127.0.0.1<br/>canal.port=11111<br/><br/># 解析线程数<br/>canal.instance.parser.parallelThreadSize=16<br/><br/># 内存限制<br/>canal.instance.memory.buffer.size=16384<br/>canal.instance.memory.buffer.memunit=KB<br/><br/># 存储模式<br/>canal.instance.mode=memory<br/># canal.instance.mode=persistence</code>
```

### 3. 实例配置

```
<code># conf/example/instance.properties<br/><br/># MySQL 连接信息<br/>canal.instance.master.address=127.0.0.1:3306<br/>canal.instance.dbUsername=canal<br/>canal.instance.dbPassword=canal<br/><br/># 起始位置<br/>canal.instance.master.journal.name=<br/>canal.instance.master.position=<br/>canal.instance.master.timestamp=<br/>canal.instance.gtid=<br/><br/># 表过滤<br/>canal.instance.filter.regex=test\..*<br/># 黑名单<br/>canal.instance.filter.black.regex=test\.test_black</code>
```

## 📡 客户端开发

### 1. Java 客户端

```
<code>import com.alibaba.otter.canal.client.CanalConnector;<br/>import com.alibaba.otter.canal.client.CanalConnectors;<br/>import com.alibaba.otter.canal.protocol.CanalEntry;<br/>import com.alibaba.otter.canal.protocol.Message;<br/><br/>import java.net.InetSocketAddress;<br/>import java.util.List;<br/><br/>public class CanalClient {<br/>    public static void main(String[] args) {<br/>        // 创建连接<br/>        CanalConnector connector = CanalConnectors.newSingleConnector(<br/>            new InetSocketAddress("127.0.0.1", 11111),<br/>            "example", "", ""<br/>        );<br/><br/>        try {<br/>            // 连接<br/>            connector.connect();<br/>            // 订阅所有表<br/>            connector.subscribe("\".*\\..*\"");<br/>            // 回滚到上次位置<br/>            connector.rollback();<br/><br/>            while (true) {<br/>                // 获取消息<br/>                Message message = connector.getWithoutAck(100);<br/>                long batchId = message.getId();<br/><br/>                if (batchId == -1 || message.getEntries().isEmpty()) {<br/>                    try {<br/>                        Thread.sleep(1000);<br/>                    } catch (InterruptedException e) {<br/>                        e.printStackTrace();<br/>                    }<br/>                    continue;<br/>                }<br/><br/>                // 处理消息<br/>                handleEntries(message.getEntries());<br/><br/>                // 确认消息<br/>                connector.ack(batchId);<br/>            }<br/>        } finally {<br/>            connector.disconnect();<br/>        }<br/>    }<br/><br/>    private static void handleEntries(List&lt;CanalEntry.Entry&gt; entries) {<br/>        for (CanalEntry.Entry entry : entries) {<br/>            if (entry.getEntryType() == CanalEntry.EntryType.TRANSACTIONBEGIN || <br/>                entry.getEntryType() == CanalEntry.EntryType.TRANSACTIONEND) {<br/>                continue;<br/>            }<br/><br/>            CanalEntry.RowChange rowChange;<br/>            try {<br/>                rowChange = CanalEntry.RowChange.parseFrom(entry.getStoreValue());<br/>            } catch (Exception e) {<br/>                throw new RuntimeException("解析数据失败", e);<br/>            }<br/><br/>            CanalEntry.EventType eventType = rowChange.getEventType();<br/>            String tableName = entry.getHeader().getTableName();<br/><br/>            System.out.println("表名: " + tableName + ", 操作: " + eventType);<br/><br/>            for (CanalEntry.RowData rowData : rowChange.getRowDatasList()) {<br/>                if (eventType == CanalEntry.EventType.DELETE) {<br/>                    printColumns(rowData.getBeforeColumnsList());<br/>                } else if (eventType == CanalEntry.EventType.INSERT) {<br/>                    printColumns(rowData.getAfterColumnsList());<br/>                } else {<br/>                    System.out.println("更新前:");<br/>                    printColumns(rowData.getBeforeColumnsList());<br/>                    System.out.println("更新后:");<br/>                    printColumns(rowData.getAfterColumnsList());<br/>                }<br/>            }<br/>        }<br/>    }<br/><br/>    private static void printColumns(List&lt;CanalEntry.Column&gt; columns) {<br/>        for (CanalEntry.Column column : columns) {<br/>            System.out.println(column.getName() + " : " + column.getValue() + <br/>                           " (更新: " + column.getUpdated() + ")");<br/>        }<br/>    }<br/>}</code>
```

### 2. Python 客户端

```
<code>from canal.client import Client<br/>from canal.protocol import EntryProtocol_pb2<br/><br/>class CanalPythonClient:<br/>    """Canal Python 客户端（伪代码骨架）"""<br/><br/>    def __init__(self, host='127.0.0.1', port=11111, destination='example'):<br/>        self.client = Client()<br/>        self.client.connect(host=host, port=port)<br/>        self.client.check_valid()<br/>        #   ★特殊点1 filter=r'.*\..*' 订阅所有库表（raw string，避免 \. 转义警告）<br/>        self.client.subscribe(destination=destination, filter=r'.*\..*')<br/><br/>    def run(self):<br/>        while True:<br/>            message = self.client.get(100)<br/>            for entry in message['entries']:<br/>                # 跳过事务开始/结束标记<br/>                if entry.entryType in (EntryProtocol_pb2.EntryType.TRANSACTIONBEGIN,<br/>                                       EntryProtocol_pb2.EntryType.TRANSACTIONEND):<br/>                    continue<br/>                # 解析 RowChange，拿到事件类型与表名<br/>                row_change = EntryProtocol_pb2.RowChange()<br/>                row_change.ParseFromString(entry.storeValue)<br/>                #   ★特殊点2 按 INSERT/DELETE/UPDATE 取 after/before/双份列数据<br/>                ...<br/>            self.client.ack(message['id'])  #   ★特殊点3 处理完必须 ack，否则重复投递<br/><br/>    def close(self):<br/>        self.client.disconnect()<br/><br/>if __name__ == '__main__':<br/>    client = CanalPythonClient()<br/>    try:<br/>        client.run()<br/>    finally:<br/>        client.close()</code>
```

## 📊 数据同步场景

### 1. 实时数据同步

```
<code>public class DataSyncHandler {<br/>    public void handleDataChange(CanalEntry.Entry entry) {<br/>        CanalEntry.RowChange rowChange = parseRowChange(entry);<br/>        String tableName = entry.getHeader().getTableName();<br/><br/>        // 根据表名路由到不同的处理逻辑<br/>        switch (tableName) {<br/>            case "user":<br/>                handleUserTable(rowChange);<br/>                break;<br/>            case "order":<br/>                handleOrderTable(rowChange);<br/>                break;<br/>            default:<br/>                break;<br/>        }<br/>    }<br/><br/>    private void handleUserTable(CanalEntry.RowChange rowChange) {<br/>        for (CanalEntry.RowData rowData : rowChange.getRowDatasList()) {<br/>            if (rowChange.getEventType() == CanalEntry.EventType.INSERT) {<br/>                // 处理插入<br/>                insertUser(rowData.getAfterColumnsList());<br/>            } else if (rowChange.getEventType() == CanalEntry.EventType.UPDATE) {<br/>                // 处理更新<br/>                updateUser(rowData.getAfterColumnsList());<br/>            } else if (rowChange.getEventType() == CanalEntry.EventType.DELETE) {<br/>                // 处理删除<br/>                deleteUser(rowData.getBeforeColumnsList());<br/>            }<br/>        }<br/>    }<br/><br/>    private void insertUser(List&lt;CanalEntry.Column&gt; columns) {<br/>        // 构建用户对象并插入目标系统<br/>        Map&lt;String, String&gt; userMap = new HashMap&lt;&gt;();<br/>        for (CanalEntry.Column column : columns) {<br/>            userMap.put(column.getName(), column.getValue());<br/>        }<br/>        // 插入到目标系统<br/>        userService.insert(userMap);<br/>    }<br/>}</code>
```

### 2. 数据清洗和转换

```
<code>public class DataTransformer {<br/>    public Map&lt;String, Object&gt; transformUser(Map&lt;String, String&gt; rawData) {<br/>        Map&lt;String, Object&gt; transformed = new HashMap&lt;&gt;();<br/><br/>        // 字段映射<br/>        transformed.put("userId", rawData.get("id"));<br/>        transformed.put("userName", rawData.get("name"));<br/>        transformed.put("email", rawData.get("email"));<br/><br/>        // 数据清洗<br/>        String phone = rawData.get("phone");<br/>        if (phone != null) {<br/>            transformed.put("phone", phone.replaceAll("\\s+", ""));<br/>        }<br/><br/>        // 时间转换<br/>        String createTime = rawData.get("create_time");<br/>        if (createTime != null) {<br/>            transformed.put("createTime", parseDateTime(createTime));<br/>        }<br/><br/>        return transformed;<br/>    }<br/>}</code>
```

## 🔍 监控与管理

### 1. 监控指标

| th | th | th |
| --- | --- | --- |
| td | td | td |
| td | td | td |
| td | td | td |

### 2. 管理 API

```
<code># 获取实例状态<br/>curl http://localhost:8080/api/v1/instance/example/status<br/><br/># 获取统计信息<br/>curl http://localhost:8080/api/v1/instance/example/stats<br/><br/># 手动触发切换<br/>curl -X POST http://localhost:8080/api/v1/instance/example/switch<br/><br/># 重置位置<br/>curl -X POST http://localhost:8080/api/v1/instance/example/reset</code>
```

### 3. 日志管理

```
<code># 服务端日志<br/>/opt/canal/logs/canal/canal.log<br/><br/># 实例日志<br/>/opt/canal/logs/example/example.log<br/><br/># 查看错误<br/>grep -i error /opt/canal/logs/example/example.log<br/><br/># 查看同步位置<br/>grep -i position /opt/canal/logs/example/example.log</code>
```

## 🛠️ 高级功能

### 1. 集群部署

```
<code># conf/canal.properties<br/>canal.zkServers=127.0.0.1:2181<br/>canal.instance.global.spring.xml=classpath:spring/default-instance.xml<br/>canal.instance.global.lazy=true</code>
```

### 2. 高可用配置

```
<code># conf/example/instance.properties<br/>canal.instance.master.address=192.168.1.100:3306<br/>canal.instance.master.journal.name=<br/>canal.instance.master.position=<br/><br/># 备库配置<br/>canal.instance.standby.address=192.168.1.101:3306<br/>canal.instance.standby.journal.name=<br/>canal.instance.standby.position=</code>
```

### 3. 过滤规则

| th | th | th |
| --- | --- | --- |
| td | td | td |
| td | td | td |
| td | td | td |

### 4. 性能优化

| th | th | th |
| --- | --- | --- |
| td | td | td |
| td | td | td |
| td | td | td |
| td | td | td |

## 🐛 常见问题

### Q: Binlog 解析失败？

```
<code># 检查 MySQL Binlog 配置<br/>mysql&gt; show variables like 'binlog_format';<br/># 确保为 ROW 模式<br/><br/># 检查 Canal 用户权限<br/>mysql&gt; show grants for 'canal'@'%';<br/># 确保有 REPLICATION SLAVE 权限<br/><br/># 查看 Canal 日志<br/>tail -f /opt/canal/logs/example/example.log</code>
```

### Q: 消费延迟高？

```
<code>// 1. 增加批量处理大小<br/>Message message = connector.getWithoutAck(500);  // 增加批量大小<br/><br/>// 2. 并行处理<br/>ExecutorService executor = Executors.newFixedThreadPool(10);<br/>for (CanalEntry.Entry entry : message.getEntries()) {<br/>    executor.submit(() -&gt; handleEntry(entry));<br/>}<br/><br/>// 3. 优化处理逻辑<br/>// 减少处理时间，使用异步处理</code>
```

### Q: 连接断开？

```
<code># 增加心跳检测<br/>canal.client.idleTimeout=60<br/>canal.client.soTimeout=60<br/><br/># 重连机制<br/>public void reconnect() {<br/>    while (true) {<br/>        try {<br/>            connector.connect();<br/>            connector.subscribe("\".*\\..*\"");<br/>            break;<br/>        } catch (Exception e) {<br/>            logger.error("重连失败", e);<br/>            try {<br/>                Thread.sleep(5000);<br/>            } catch (InterruptedException ie) {<br/>                break;<br/>            }<br/>        }<br/>    }<br/>}</code>
```

## 📚 相关资源

- **官方文档**: [https://github.com/alibaba/canal/wiki](https://github.com/alibaba/canal/wiki)
- **GitHub**: [https://github.com/alibaba/canal](https://github.com/alibaba/canal)
- **客户端 SDK**: [https://github.com/alibaba/canal/tree/master/client](https://github.com/alibaba/canal/tree/master/client)
- **示例代码**: [https://github.com/alibaba/canal/tree/master/example](https://github.com/alibaba/canal/tree/master/example)
- **常见问题**: [https://github.com/alibaba/canal/wiki/FAQ](https://github.com/alibaba/canal/wiki/FAQ)