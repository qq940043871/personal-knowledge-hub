# Spring JdbcTemplate 基本用法

> ⚠️ 本篇为为知笔记导出存档，导出时丢失了部分数字（如参数占位序号），代码不可直接复制执行，仅作思路与用法参考。
> 2026-11-08：setter/占位序号已按 JDBC 绑定顺序（SQL 中 `?` 的出现次序）修复，修复处以"注"标注；无法推断的值以 `<占位>` 标注。

提供了JdbcTemplate 来封装数据库jdbc操作细节：
包括： 数据库连接[打开/关闭] ，异常转义 ，SQL执行 ，查询结果的转换

使用模板方式封装 jdbc数据库操作-固定流程的动作，提供丰富callback回调接口功能，方便用户自定义加工细节，更好模块化jdbc操作，简化传统的JDBC操作的复杂和繁琐过程。

## 使用JdbcTemplate 更新(insert /update /delete)

```java
int k = jdbcTemplate.update("UPDATE tblname SET prop=?,prop=?...", new Object[]{...});

jdbcTemplate.update("INSERT INTO tblname VALUES(?,?,..)", new Object[]{...},
	 new int[]{Types.VARCHAR,Types.NUMERIC});

jdbcTemplate.update("INSERT INTO tblname VALUES(?,?,..)",
        new PreparedStatementSetter(){
               public void setValues(PreparedStatement ps) throws SQLException{
                    // 注：原导出参数缺失，以下序号按 SQL 中 ? 的绑定顺序修复（第1~4个）
                    ps.setLong(1, user.getId());
                    ps.setString(2, user.getName());
                    ps.setDate(3, new java.sql.Date(new Date().getTime()));
                    ps.setTimestamp(4, new Timestamp(new Date().getTime()));
               }
        }
);
```

## 使用JdbcTemplate 查询 (select)

```java
final User user = new User();
jdbcTemplate.query("SELECT id,name,.. FROM tblname WHERE id=?", // 注：原导出"?"丢失，此处为修复值
       new RowCallbackHandler(){
              public void processRow(ResultSet rs) throws SQLException{
                    // 注：原导出列序号缺失，按 SELECT 字段顺序修复（id=1, name=2）
                    user.setId(rs.getLong(1));
                    user.setName(rs.getString(2));
              }
      }
);

List uGroup = jdbcTemplate.query("SELECT id,name,.. FROM tblname WHERE igroup=?", // 注：原导出"?"丢失，此处为修复值
     new RowMapper(){
            public Object mapRow(ResultSet rs,int no) throws SQLException{
                     User user = new User();
                     // 注：原导出列序号缺失，按 SELECT 字段顺序修复（id=1, name=2）
                     user.setId(rs.getLong(1));
                     user.setName(rs.getString(2));
                     return user ;
            }
     }
};
```

## 使用JdbcTemplate 便捷方法

> 注：原导出数字缺失，下方 `new Integer []{<id值>}` 中的 `<id值>` 为占位，请填入实际查询参数值。

```java
List uNames = jdbcTemplate.queryForList("SELECT name FROM tblname WHERE id>?",
	new Integer []{<id值>}, String.class);

List<Map> uMapList = (List<Map>) jdbcTemplate.queryForList( "SELECT id, name FROM tblname WHERE id>?",
		 new Integer []{<id值>});
for(Map<String,Object> uMap :uMapList){
      Integer id = uMap.get("id");
      String name = uMap.get("name");
};

String user = jdbcTemplate.queryForObject("SELECT name FROM tblname WHERE id=?",
	 new Integer []{<id值>}, String.class );

int uNum = jdbcTemplate.queryForInt("SELECT count(*) FROM tblname WHERE id>?",
	new Integer []{<id值>});
```

## 使用jdbc 操作类

### a)扩展 MappingSqlQuery类

```java
class JdbcQueryObject extends MappingSqlQuery { // extends SqlQuery
      public JdbcQueryObject (DataSource ds,String sql){
            this.setDataSource( ds );
            this.setSql( sql );
            this.declareParameter(new Sqlparameter("propName",
                Types.VARCHAR);// propName 提示作用
        this.compile();
      }
      public Object mapRow(ResultSet rs,int p) throws SQLException{
                 // ...
     }
}
JdbcQueryObject queryObj = new JdbcQueryObject( ds,
      "SELECT .. FROM tblName WHERE param=?");
List list = queryObj.execute(new Object[]{...});
```

### b)使用 SqlFunction 类 查询单条结果

```java
SqlFunction queryFun = new SqlFunction( ds,
      "select count(*) from tblName where ..." ,new int[]{Types.CHAR,...} );
queryFun.compile();
queryFun.run(new Object[]{p1,p2,..}); // 注：原导出参数缺失，序号 p1/p2 按参数顺序修复
```

### c)使用 SqlUpdate 类 更新

```java
SqlUpdate updateFunc = new SqlUpdate(ds ,"INSERT tblName ...");
updateFunc.declareParameter( new SqlParameter("prop",Types.CHAR) );
updateFunc.compile();
updateFunc.update(new String[]{s,s});
```

## 支持jdbc 事务

spring的事务管理有两种方式：编程式事务、声明式事务

这里谈一下 基于数据库单一资源的编程式事务:

spring用实现TransactionDefinition接口的类定义事务的属性：传播行为；隔离级别；超时值；只读标志

默认实现为：DefaultTransactionDefinition类

```java
PlatformTransactionManager tm =
new DataSourceTransactionManager(
            jdbcTemplate.getDataSource() );
TransactionStatus status = null;
try{
    //null 默认事务属性配置DefaultTransactionDefinition
    status = tm.getTransaction(null);
  for(final String wd: words){
   try {
     jdbcTemplate.update( insertWordSql,
          new PreparedStatementSetter(){

	public void setValues(PreparedStatement pstate)
                     throws SQLException {
	        	// 注：原导出参数缺失，序号按 SQL 中 ? 的绑定顺序修复（第1、2个）
			pstate.setString(1, wd) ;
			pstate.setTimestamp(2,
			new Timestamp( new Date().getTime() ));
	}
        }
     );

   } catch (DataAccessException e) {
       e.printStackTrace();
       //tm.rollback(status);
    }
    } // end for
} finally {
     tm.commit(status);
}
```

来源： [http://www.open-open.com/lib/view/openhtml](http://www.open-open.com/lib/view/openhtml)
