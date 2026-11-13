# 日志先行（Write-Ahead Logging）

> 模块：存储引擎
> 更新时间：2026-03-29

---

## 一、WAL原理

```
WAL核心原则：
  日志必须先写入磁盘，然后才能修改数据页

优势：
  1. 随机写变顺序写
  2. 提高并发性能
  3. 支持崩溃恢复
```

---

## 二、日志结构

```java
public class LogRecord {
    private long LSN;           // 日志序列号
    private long transactionId; // 事务ID
    private short type;         // 日志类型
    private long pageId;        // 页ID
    private byte[] data;        // 日志数据
    
    // 日志类型
    public static final short UPDATE = 1;
    public static final short INSERT = 2;
    public static final short DELETE = 3;
    public static final short COMMIT = 4;
    public static final short ROLLBACK = 5;
    public static final short BEGIN = 6;
}
```

---

## 三、日志写入

```java
public class WALogManager {
    private LogBuffer logBuffer;
    private LogFile logFile;
    private long currentLSN = 0;
    
    public long logUpdate(long txId, long pageId, byte[] oldData, byte[] newData) {
        LogRecord record = new LogRecord();
        record.setLSN(++currentLSN);
        record.setTransactionId(txId);
        record.setType(LogRecord.UPDATE);
        record.setPageId(pageId);
        record.setOldData(oldData);
        record.setNewData(newData);
        
        // 写入日志缓冲区
        byte[] logBytes = record.toBytes();
        logBuffer.append(logBytes);
        
        // 如果需要，刷新到磁盘
        if (logBuffer.shouldFlush()) {
            flushLog();
        }
        
        return currentLSN;
    }
    
    public void commit(long txId) {
        LogRecord record = new LogRecord();
        record.setLSN(++currentLSN);
        record.setTransactionId(txId);
        record.setType(LogRecord.COMMIT);
        
        logBuffer.append(record.toBytes());
        flushLog();
        
        // 清理事务
        transactionManager.commit(txId);
    }
    
    public void flushLog() {
        logBuffer.flush();
        logFile.sync();
    }
}
```

*图：WAL 日志写入流程（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 250" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="25" y="30" width="170" height="34" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="110" y="52" text-anchor="middle" font-size="13" fill="#1e293b">事务执行修改</text>
  <line x1="195" y1="47" x2="210" y2="47" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="210" y="30" width="210" height="34" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="315" y="52" text-anchor="middle" font-size="13" fill="#1e293b">构造 LogRecord，分配 LSN</text>
  <line x1="420" y1="47" x2="440" y2="47" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="440" y="30" width="190" height="34" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="535" y="52" text-anchor="middle" font-size="13" fill="#1e293b">追加到 LogBuffer</text>
  <line x1="535" y1="64" x2="535" y2="94" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="445" y="94" width="180" height="34" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="535" y="116" text-anchor="middle" font-size="13" fill="#1e293b">shouldFlush()？</text>
  <path d="M445,111 L315,111 L315,150" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="380" y="105" font-size="12" fill="#475569">否</text>
  <rect x="210" y="150" width="210" height="34" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="315" y="172" text-anchor="middle" font-size="13" fill="#1e293b">暂留 LogBuffer，返回 LSN</text>
  <line x1="535" y1="128" x2="535" y2="150" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="545" y="144" font-size="12" fill="#475569">是</text>
  <rect x="430" y="150" width="220" height="34" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="540" y="172" text-anchor="middle" font-size="13" fill="#1e293b">flushLog()：flush + sync 落盘</text>
  <line x1="540" y1="184" x2="540" y2="202" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="430" y="202" width="220" height="34" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="540" y="224" text-anchor="middle" font-size="13" fill="#1e293b">日志先写磁盘，才能修改数据页</text>
</svg>

---

## 四、LSN与Checkpoint

```
LSN（Log Sequence Number）：
  - 递增的日志序列号
  - 用于定位日志位置
  - 关联数据页和日志

Checkpoint（检查点）：
  - 将内存中的脏页刷新到磁盘
  - 记录检查点位置
  - 缩短恢复时间
```

---

*下一步：查询计划生成*
