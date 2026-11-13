# ACID特性

> 模块：事务管理
> 更新时间：2026-03-29

---

## 一、事务与 ACID 四特性总览

> 事务是一组原子性的数据库操作序列：**要么全部成功，要么全部失败**。

```
事务（Transaction）：
  一组原子性的数据库操作序列
  要么全部成功，要么全部失败

ACID特性：
  A - Atomicity（原子性）
  C - Consistency（一致性）
  I - Isolation（隔离性）
  D - Durability（持久性）
```

---

## 二、事务接口与状态流转

> commit 前先写 COMMIT 日志并强制刷盘；rollback 按**逆序 undo 所有操作**后再写 ROLLBACK 日志。

```java
public interface Transaction {
    long getTransactionId();
    void begin();
    void commit();
    void rollback();
    TransactionState getState();
}

public class TransactionImpl implements Transaction {
    private long txId;
    private TransactionState state;
    private List<Operation> operations;
    private TransactionManager manager;
    
    @Override
    public void begin() {
        this.txId = manager.generateTransactionId();
        this.state = TransactionState.ACTIVE;
        this.operations = new ArrayList<>();
        
        // 写入BEGIN日志
        logManager.logBegin(txId);
    }
    
    @Override
    public void commit() {
        if (state != TransactionState.ACTIVE) {
            throw new TransactionException("Transaction not active");
        }
        
        state = TransactionState.COMMITTING;
        
        // 写COMMIT日志
        logManager.logCommit(txId);
        logManager.flushLog();
        
        state = TransactionState.COMMITTED;
    }
    
    @Override
    public void rollback() {
        if (state != TransactionState.ACTIVE) {
            throw new TransactionException("Transaction not active");
        }
        
        state = TransactionState.ROLLING_BACK;
        
        // 回滚所有操作
        for (int i = operations.size() - 1; i >= 0; i--) {
            operations.get(i).undo();
        }
        
        // 写ROLLBACK日志
        logManager.logRollback(txId);
        
        state = TransactionState.ROLLED_BACK;
    }
}

public enum TransactionState {
    ACTIVE,
    COMMITTING,
    COMMITTED,
    ROLLING_BACK,
    ROLLED_BACK
}
```

*图：事务状态机——ACTIVE 出发，提交走 COMMITTING 到 COMMITTED，回滚走 ROLLING_BACK 到 ROLLED_BACK（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 230" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <text x="360" y="30" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">事务状态机（TransactionState）</text>
  <rect x="60" y="60" width="140" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="130" y="87" text-anchor="middle" font-size="14" fill="#1e293b">ACTIVE</text>
  <text x="130" y="125" text-anchor="middle" font-size="12" fill="#475569">begin() 进入</text>
  <rect x="300" y="60" width="150" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="375" y="87" text-anchor="middle" font-size="14" fill="#1e293b">COMMITTING</text>
  <rect x="540" y="60" width="150" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="615" y="87" text-anchor="middle" font-size="14" fill="#1e293b">COMMITTED</text>
  <rect x="300" y="160" width="150" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="375" y="187" text-anchor="middle" font-size="14" fill="#1e293b">ROLLING_BACK</text>
  <rect x="540" y="160" width="150" height="44" rx="8" fill="#fef2f2" stroke="#dc2626" stroke-width="1.5"/>
  <text x="615" y="187" text-anchor="middle" font-size="14" fill="#1e293b">ROLLED_BACK</text>
  <line x1="200" y1="82" x2="295" y2="82" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="247" y="74" text-anchor="middle" font-size="12" fill="#475569">写COMMIT日志</text>
  <line x1="450" y1="82" x2="535" y2="82" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="492" y="74" text-anchor="middle" font-size="12" fill="#475569">flushLog</text>
  <line x1="200" y1="100" x2="295" y2="170" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="215" y="150" text-anchor="middle" font-size="12" fill="#475569">rollback()</text>
  <line x1="450" y1="182" x2="535" y2="182" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="492" y="174" text-anchor="middle" font-size="12" fill="#475569">undo 所有操作</text>
</svg>

---

## 三、事务管理器：事务边界的开启与结束

> 提交或回滚完成后，**释放该事务的全部锁**，并从活跃事务表中移除。

```java
public class TransactionManager {
    private ConcurrentMap<Long, Transaction> activeTransactions;
    private LockManager lockManager;
    private LogManager logManager;
    
    public Transaction beginTransaction() {
        Transaction tx = new TransactionImpl(generateTxId(), this);
        activeTransactions.put(tx.getTransactionId(), tx);
        return tx;
    }
    
    public void commitTransaction(long txId) {
        Transaction tx = activeTransactions.get(txId);
        if (tx == null) {
            throw new TransactionException("Transaction not found");
        }
        
        tx.commit();
        lockManager.releaseAllLocks(txId);
        activeTransactions.remove(txId);
    }
    
    public void rollbackTransaction(long txId) {
        Transaction tx = activeTransactions.get(txId);
        if (tx == null) {
            throw new TransactionException("Transaction not found");
        }
        
        tx.rollback();
        lockManager.releaseAllLocks(txId);
        activeTransactions.remove(txId);
    }
}
```

---

*下一步：锁机制*
