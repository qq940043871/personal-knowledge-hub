这份 **Arthas 经典版 A4 速查表** 经过我重新排版与优化，保留了核心且高频的命令，补充了详细的注释和场景化用法，非常适合打印出来随身携带，作为排查问题的“圣经”。

---

# **ARTHAS 在线诊断工具 - 实战速查表**
**适用场景：** B2B 分布式系统、接口慢、偶发超时、数据不一致、CPU/GC 飙高
**核心定位：** 不重启、不改代码、在线追踪 JVM 与业务代码

---

## **一、启动与基础操作 (必须掌握)**
| 命令 | 注释与说明 | 复制即用 |
| :--- | :--- | :--- |
| **启动 Arthas** | **进入目标进程** (选择数字 1, 2, 3...) | `java -jar arthas-boot.jar` |
| **退出 Arthas** | 保持进程运行，退出控制台 | `exit` |
| **彻底停止 Arthas** | 卸载 agent，关闭诊断 | `stop` |
| **查看所有命令** | 快速查阅手册 | `help` |
| **查看系统属性** | 检查环境、版本、路径 | `sysprop` |
| **查看环境变量** | 检查配置、配置中心 | `sysenv` |

---

## **二、核心排查三板斧 (定位慢接口/慢方法)**
### **1. Trace (最强链路追踪)**
> **作用：** 打印方法内部的调用路径和耗时，**精准定位**是查库慢、调接口慢，还是逻辑慢。
**场景：** 挂牌接口慢、仓单匹配慢、下单卡顿。
>

```bash
# 监控指定方法内部耗时 (最常用)
trace com.xxx.service.ListingService createListing

# 监控耗时超过 500ms 的方法 (只关注慢调用)
trace com.xxx.service.*Service *Method '#cost > 500'

# 参数说明：
# -n 5  只执行5次，防止刷屏
# '#cost > 100' 只打印耗时超过100ms的链路
```

### **2. Watch (监控入参/出参/异常)**
> **作用：** 实时查看方法的输入参数、返回结果、抛出异常。
**场景：** 数据同步失败、参数校验不通过、返回数据为空。
>

```bash
# 查看方法的入参、返回、异常 (详细模式)
watch com.xxx.service.CustomerService getCustomerInfo '{params, returnObj, throwExp}' -x 3

# 只查看异常 (捕获报错)
watch com.xxx.mq.Consumer consume '{throwExp}' -e

# 参数说明：
# -x 3  展开深度为3层（默认1层，看不全对象）
# -e    只在发生异常时触发
```

### **3. Monitor (监控方法调用统计)**
> **作用：** 定期统计方法的调用次数、成功数、失败率、平均耗时。
**场景：** 高峰期接口报错率飙升、TPS 波动分析。
>

```bash
# 每2秒统计一次该方法的性能指标
monitor -c 2 com.xxx.service.OrderService createOrder

# 参数说明：
# -c 2  周期为2秒
```

---

## **三、深层排查与问题定位 (进阶技巧)**
### **4. Thread (排查 CPU 飙高/死锁)**
> **作用：** 查看线程堆栈，定位死锁、阻塞、最忙线程。
**场景：** 服务器 CPU 100%、接口假死、线程池耗尽。
>

```bash
# 查看最忙的3个线程 (定位CPU密集型任务)
thread -n 3

# 查看当前阻塞的线程 (找死锁)
thread -b

# 查看所有线程堆栈 (导出分析)
thread -i 1000 > thread_dump.txt
```

### **5. JVM (内存与 GC 诊断)**
> **作用：** 查看 JVM 内存、GC 情况、类加载情况。
**场景：** 系统频繁 Full GC、OOM 异常、内存泄漏。
>

```bash
# 查看JVM概况 (内存、线程、GC、类加载)
jvm

# 查看GC详细统计
gc

# 查看内存堆布局
heapdump
```

### **6. Sc / Sm (查找类/方法)**
> **作用：** 搜索类名、方法名，确认是否加载成功。
**场景：** 改了代码没生效、找不到某个类。
>

```bash
# 搜索包含"Service"的类
sc *Service*

# 搜索该类下的所有方法
sm com.xxx.service.UserService
```

### **7. Jad / Mc / Redefine (热部署/反编译)**
> **作用：** 反编译线上代码，确认版本；在线修改代码（热修复）。
**场景：** 线上代码版本疑问、紧急小修复无需重启。
>

```bash
# 反编译指定类 (确认线上代码)
jad com.xxx.service.UserService

# 在线修改代码并重新编译 (需谨慎)
mc /tmp/MyClass.java
redefine /tmp/MyClass.class
```

---

## **四、B2B 业务场景实战命令 (复制即用)**
### **场景 1：商品查询/仓单匹配慢 (核心业务)**
```bash
# 追踪商品查询服务
trace com.xxx.service.CommodityService queryCommodity

# 追踪仓单匹配逻辑
trace com.xxx.service.WarehouseService matchWarehouse
```

### **场景 2：客户登录/菜单权限异常**
```bash
# 监控获取用户信息接口
watch com.xxx.service.AuthService getCurrentUser '{params, returnObj}'

# 监控获取菜单接口
trace com.xxx.service.MenuService loadMenuList
```

### **场景 3：MQ 消息消费失败/延迟**
```bash
# 监控消费者方法，查看异常详情
watch com.xxx.mq.ListingConsumer listen '{params, throwExp}' -e
```

### **场景 4：数据库慢 SQL (结合 MyBatis)**
```bash
# 监控 MyBatis 查询执行耗时
trace org.apache.ibatis.executor.statement.PreparedStatementHandler parameterize
```

---

## **五、排查标准流程 (10分钟定案)**
1. **thread -n 3** -> 看 CPU 占用最高的线程是否业务逻辑。
2. **trace** 方法 -> 定位是内部逻辑慢，还是依赖其他服务/DB慢。
3. **watch** -> 确认参数和返回数据是否正常。
4. **jvm** -> 检查 GC 是否频繁、内存是否溢出。
5. **sc / jad** -> 确认代码版本是否一致。

---

**💡**** 使用贴士：**

+ **生产环境慎用：** 高频度的 `trace` 可能会短暂降低系统性能，建议在业务低峰期或非核心链路使用。
+ **-n 与 -c：** 控制监控次数，避免日志过多淹没系统。
+ **#cost：** 利用耗时过滤，只关注慢请求，高效排查。
