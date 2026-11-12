# AST抽象语法树

> 模块：语法分析器
> 更新时间：2026-03-29

---

## 一、AST节点结构

```
Statement（语句）
├── SelectStatement（查询）
│   ├── columns: List<Expression>
│   ├── from: TableReference
│   ├── where: Expression
│   ├── groupBy: List<Expression>
│   ├── having: Expression
│   └── orderBy: List<OrderByItem>
│
├── InsertStatement（插入）
│   ├── table: String
│   ├── columns: List<String>
│   └── values: List<Expression>
│
├── UpdateStatement（更新）
│   ├── table: String
│   ├── assignments: Map<String, Expression>
│   └── where: Expression
│
├── DeleteStatement（删除）
│   ├── table: String
│   └── where: Expression
│
└── CreateTableStatement（建表）
    ├── name: String
    ├── columns: List<ColumnDefinition>
    └── constraints: List<Constraint>

Expression（表达式）
├── ColumnExpression（列引用）
├── LiteralExpression（字面量）
├── BinaryExpression（二元运算）
├── FunctionExpression（函数调用）
└── StarExpression（*）
```

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 460" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="380" y="32" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">AST节点体系</text>
  <rect x="295" y="56" width="170" height="50" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="380" y="86" text-anchor="middle" font-size="13" fill="#1e293b">Statement 语句</text>
  <path d="M380,106 V140 H76 V168" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <path d="M380,106 V140 H228 V168" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <path d="M380,106 V168" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <path d="M380,106 V140 H532 V168" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <path d="M380,106 V140 H684 V168" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="6" y="172" width="140" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="76" y="199" text-anchor="middle" font-size="13" fill="#1e293b">Select查询</text>
  <rect x="158" y="172" width="140" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="228" y="199" text-anchor="middle" font-size="13" fill="#1e293b">Insert插入</text>
  <rect x="310" y="172" width="140" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="380" y="199" text-anchor="middle" font-size="13" fill="#1e293b">Update更新</text>
  <rect x="462" y="172" width="140" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="532" y="199" text-anchor="middle" font-size="13" fill="#1e293b">Delete删除</text>
  <rect x="614" y="172" width="140" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="684" y="199" text-anchor="middle" font-size="13" fill="#1e293b">CreateTable建表</text>
  <rect x="295" y="250" width="170" height="50" rx="8" fill="#f5f3ff" stroke="#7c3aed" stroke-width="1.5"/>
  <text x="380" y="280" text-anchor="middle" font-size="13" fill="#1e293b">Expression 表达式</text>
  <path d="M380,300 V332 H76 V360" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <path d="M380,300 V332 H228 V360" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <path d="M380,300 V360" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <path d="M380,300 V332 H532 V360" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <path d="M380,300 V332 H684 V360" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="6" y="364" width="140" height="44" rx="8" fill="#f5f3ff" stroke="#7c3aed" stroke-width="1.5"/>
  <text x="76" y="391" text-anchor="middle" font-size="13" fill="#1e293b">Column列引用</text>
  <rect x="158" y="364" width="140" height="44" rx="8" fill="#f5f3ff" stroke="#7c3aed" stroke-width="1.5"/>
  <text x="228" y="391" text-anchor="middle" font-size="13" fill="#1e293b">Literal字面量</text>
  <rect x="310" y="364" width="140" height="44" rx="8" fill="#f5f3ff" stroke="#7c3aed" stroke-width="1.5"/>
  <text x="380" y="391" text-anchor="middle" font-size="13" fill="#1e293b">Binary二元运算</text>
  <rect x="462" y="364" width="140" height="44" rx="8" fill="#f5f3ff" stroke="#7c3aed" stroke-width="1.5"/>
  <text x="532" y="391" text-anchor="middle" font-size="13" fill="#1e293b">Function函数调用</text>
  <rect x="614" y="364" width="140" height="44" rx="8" fill="#f5f3ff" stroke="#7c3aed" stroke-width="1.5"/>
  <text x="684" y="391" text-anchor="middle" font-size="13" fill="#1e293b">StarExpression</text>
  <text x="380" y="442" text-anchor="middle" font-size="13" fill="#475569">语句与表达式节点组成SQL的抽象语法树</text>
</svg>

*图：AST节点体系示意（依正文整理）*

---

## 二、节点定义

```java
// 语句基类
public interface Statement {}

// SELECT语句
public class SelectStatement implements Statement {
    private List<Expression> columns;
    private TableReference from;
    private Expression where;
    private List<Expression> groupBy;
    private Expression having;
    private List<OrderByItem> orderBy;
    private Integer limit;
    private Integer offset;
    private boolean distinct;
}

// INSERT语句
public class InsertStatement implements Statement {
    private String table;
    private List<String> columns;
    private List<List<Expression>> valuesLists;
}

// UPDATE语句
public class UpdateStatement implements Statement {
    private String table;
    private Map<String, Expression> assignments;
    private Expression where;
}

// DELETE语句
public class DeleteStatement implements Statement {
    private String table;
    private Expression where;
}

// CREATE TABLE语句
public class CreateTableStatement implements Statement {
    private String tableName;
    private List<ColumnDefinition> columns;
    private List<Constraint> constraints;
}
```

---

## 三、表达式定义

```java
// 表达式基类
public interface Expression {}

// 列引用
public class ColumnExpression implements Expression {
    private String table;
    private String column;
}

// 字面量
public class LiteralExpression implements Expression {
    private Object value;
    
    public LiteralExpression(Object value) {
        this.value = value;
    }
}

// 二元运算
public class BinaryExpression implements Expression {
    public enum Op { EQ, NE, LT, GT, LE, GE, AND, OR, PLUS, MINUS, STAR, SLASH }
    
    private Op op;
    private Expression left;
    private Expression right;
}

// 函数调用
public class FunctionExpression implements Expression {
    private String name;
    private List<Expression> args;
}

// 星号表达式
public class StarExpression implements Expression {}
```

---

## 四、树遍历

```java
public class AstVisitor {
    
    public Object visit(SelectStatement stmt) {
        // 访问子节点
        for (Expression col : stmt.getColumns()) {
            visitExpression(col);
        }
        
        if (stmt.getFrom() != null) {
            visitTableReference(stmt.getFrom());
        }
        
        if (stmt.getWhere() != null) {
            visitExpression(stmt.getWhere());
        }
        
        return null;
    }
    
    public void visitExpression(Expression expr) {
        if (expr instanceof ColumnExpression) {
            visitColumn((ColumnExpression) expr);
        } else if (expr instanceof LiteralExpression) {
            visitLiteral((LiteralExpression) expr);
        } else if (expr instanceof BinaryExpression) {
            visitBinary((BinaryExpression) expr);
        } else if (expr instanceof FunctionExpression) {
            visitFunction((FunctionExpression) expr);
        }
    }
}
```

---

*下一步：符号表管理*
