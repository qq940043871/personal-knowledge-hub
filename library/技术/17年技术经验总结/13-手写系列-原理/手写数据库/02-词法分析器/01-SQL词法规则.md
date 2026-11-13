# SQL词法规则

> 模块：词法分析器
> 更新时间：2026-03-29

---

## 一、Token类型

```
关键字：
  SELECT, FROM, WHERE, AND, OR, NOT, IN, LIKE, BETWEEN
  INSERT, INTO, VALUES, UPDATE, SET, DELETE
  CREATE, TABLE, DATABASE, INDEX, DROP, ALTER
  JOIN, LEFT, RIGHT, INNER, OUTER, ON
  GROUP, BY, HAVING, ORDER, ASC, DESC, LIMIT, OFFSET
  UNION, ALL, DISTINCT, AS, NULL, DEFAULT
  PRIMARY, KEY, FOREIGN, REFERENCES, CONSTRAINT, UNIQUE
  AUTO_INCREMENT, UNSIGNED, ZEROFILL
  INT, INTEGER, BIGINT, SMALLINT, TINYINT, FLOAT, DOUBLE, DECIMAL
  CHAR, VARCHAR, TEXT, BLOB, DATE, DATETIME, TIMESTAMP

标识符：
  表名、列名、数据库名

字面量：
  整数：123, -456
  浮点：3.14, -2.5e10
  字符串：'hello', "world"
  布尔：TRUE, FALSE, NULL

运算符：
  + - * / % = <> != < > <= >= ( ) , . ; :
  && || !

注释：
  -- 单行注释
  /* 多行注释 */
```

*图：SQL 词法 Token 五大类别（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 210" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="300" y="16" width="120" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="360" y="43" text-anchor="middle" font-size="15" fill="#1e293b">SQL Token</text>
  <line x1="330" y1="60" x2="92" y2="104" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="344" y1="60" x2="226" y2="104" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="360" y1="60" x2="360" y2="104" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="376" y1="60" x2="494" y2="104" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="390" y1="60" x2="628" y2="104" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="30" y="108" width="124" height="76" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="92" y="132" text-anchor="middle" font-size="14" fill="#1e293b">关键字</text>
  <text x="92" y="152" text-anchor="middle" font-size="12" fill="#475569">SELECT / WHERE</text>
  <text x="92" y="170" text-anchor="middle" font-size="12" fill="#475569">JOIN / LIMIT</text>
  <rect x="170" y="108" width="124" height="76" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="232" y="132" text-anchor="middle" font-size="14" fill="#1e293b">标识符</text>
  <text x="232" y="152" text-anchor="middle" font-size="12" fill="#475569">表名、列名</text>
  <text x="232" y="170" text-anchor="middle" font-size="12" fill="#475569">数据库名</text>
  <rect x="310" y="108" width="124" height="76" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="372" y="132" text-anchor="middle" font-size="14" fill="#1e293b">字面量</text>
  <text x="372" y="152" text-anchor="middle" font-size="12" fill="#475569">123 / 3.14</text>
  <text x="372" y="170" text-anchor="middle" font-size="12" fill="#475569">'hello' / TRUE</text>
  <rect x="450" y="108" width="124" height="76" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="512" y="132" text-anchor="middle" font-size="14" fill="#1e293b">运算符</text>
  <text x="512" y="152" text-anchor="middle" font-size="12" fill="#475569">+ - * / =</text>
  <text x="512" y="170" text-anchor="middle" font-size="12" fill="#475569">&lt;= &gt;= &lt;&gt;</text>
  <rect x="590" y="108" width="124" height="76" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="652" y="132" text-anchor="middle" font-size="14" fill="#1e293b">注释</text>
  <text x="652" y="152" text-anchor="middle" font-size="12" fill="#475569">-- 单行</text>
  <text x="652" y="170" text-anchor="middle" font-size="12" fill="#475569">/* 多行 */</text>
</svg>

---

## 二、关键字表

```java
public class Keywords {
    public static final Set<String> SQL_KEYWORDS = new HashSet<>(Arrays.asList(
        "SELECT", "FROM", "WHERE", "AND", "OR", "NOT", "IN", "LIKE", "BETWEEN",
        "INSERT", "INTO", "VALUES", "UPDATE", "SET", "DELETE",
        "CREATE", "TABLE", "DATABASE", "INDEX", "DROP", "ALTER",
        "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", "ON",
        "GROUP", "BY", "HAVING", "ORDER", "ASC", "DESC", "LIMIT", "OFFSET",
        "UNION", "ALL", "DISTINCT", "AS", "NULL", "DEFAULT",
        "PRIMARY", "KEY", "FOREIGN", "REFERENCES", "CONSTRAINT", "UNIQUE",
        "AUTO_INCREMENT", "INT", "INTEGER", "BIGINT", "FLOAT", "DOUBLE", 
        "DECIMAL", "CHAR", "VARCHAR", "TEXT", "BLOB", "DATE", "DATETIME"
    ));
    
    public static boolean isKeyword(String word) {
        return SQL_KEYWORDS.contains(word.toUpperCase());
    }
}
```

---

## 三、词法规则

```
标识符规则：
  [a-zA-Z_][a-zA-Z0-9_]*
  最大长度64

数字规则：
  整数：[0-9]+
  浮点：[0-9]*.[0-9]+
  科学计数：[0-9]+.[0-9]*[eE][+-]?[0-9]+

字符串规则：
  单引号：'[^']*'
  双引号："[^"]*"

运算符规则：
  单字符运算符：+ - * / % ( ) , ; . :
  双字符运算符：<= >= <> != || &&
  三字符运算符：!=
```

---

## 四、Token定义

```java
public class Token {
    public enum Type {
        // 关键字
        SELECT, FROM, WHERE, AND, OR, NOT, IN, LIKE, BETWEEN,
        INSERT, INTO, VALUES, UPDATE, SET, DELETE,
        CREATE, TABLE, DATABASE, INDEX, DROP, ALTER,
        JOIN, LEFT, RIGHT, INNER, OUTER, ON,
        GROUP, BY, HAVING, ORDER, ASC, DESC, LIMIT, OFFSET,
        UNION, ALL, DISTINCT, AS, NULL, DEFAULT,
        PRIMARY, KEY, FOREIGN, REFERENCES, UNIQUE,
        AUTO_INCREMENT, INT, VARCHAR, TEXT, DATE, DATETIME,
        
        // 字面量
        IDENTIFIER,    // 标识符
        STRING,        // 字符串
        INTEGER,       // 整数
        FLOAT,         // 浮点数
        BOOLEAN,       // TRUE/FALSE
        
        // 运算符
        PLUS, MINUS, STAR, SLASH, PERCENT,  // + - * / %
        EQ, NE, LT, GT, LE, GE,             // = <> < > <= >=
        LPAREN, RPAREN,                     // ( )
        COMMA, DOT, SEMICOLON,              // , . ;
        
        // 其他
        EOF, ERROR
    }
    
    public Type type;
    public String value;
    public int position;
    public int line;
    public int column;
}
```

---

*下一步：Token识别实现*
