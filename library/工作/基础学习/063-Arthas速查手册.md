下面给你整理一份**超实用、B2B电商场景专用的 Arthas 实战手册**，结构清晰、命令直接复制可用，完全是**架构师/全栈排查问题必备**的精简版，你可以直接存成文档用。

# Arthas 实战手册（B2B 分布式系统定位神器）
## 一、Arthas 是什么
+ 阿里开源的 **Java 在线诊断工具**
+ 不用重启、不用加日志、不用改代码
+ 直接在线看：方法耗时、入参出参、异常、SQL、慢调用、线程、JVM
+ 你们系统定位：**接口慢、菜单出不来、仓单匹配慢、同步异常** 神器

---

## 二、启动命令
```bash
# 下载
curl -O https://arthas.aliyun.com/arthas-boot.jar

# 启动
java -jar arthas-boot.jar
```

启动后选择要诊断的 Java 进程即可。

---

## 三、最常用核心命令（按场景分类）
### 1. 看接口整体性能
#### watch 监控方法入参、出参、耗时
```bash
watch 包名.类名 方法名 '{params,returnObj,throwExp}' -n 5 -x 3
```

#### 只看耗时超过 100ms 的方法
```bash
watch 包名.类名 方法名 '{cost}' '#cost>100'
```

### 2. 定位谁慢（trace 最强）
```bash
trace 包名.类名 方法名
```

+ 自动打印方法内部**所有调用路径+耗时**
+ 一眼看出：是查库慢？调用其他服务慢？还是循环慢？

### 3. 实时查看方法调用频率、最慢排名
```bash
monitor 包名.类名 方法名 -n 10
```

### 4. 查看当前最耗 CPU 的线程
```bash
thread -n 3
```

### 5. 查看死锁、线程阻塞
```bash
thread -b
```

### 6. 查看 JVM 概况
```bash
jvm
```

### 7. 反编译线上代码，确认是否部署成功
```bash
jad 包名.类名
```

### 8. 搜索类、搜索方法
```bash
sc *Service*
sm 包名.类名 *
```

### 9. 查看方法被谁调用（调用链路）
```bash
stack 包名.类名 方法名
```

### 10. 实时查看异常
```bash
watch 包名.类名 方法名 throwExp -e
```

---

## 四、针对你们 B2B 平台的专用排查命令（重点）
### 场景1：挂牌接口慢 / 仓单选择慢
```bash
trace com.xx.service.ListingService createListing
```

看里面哪一步耗时：

+ 查商品？
+ 查仓单？
+ 查合同？
+ 调用其他微服务？

### 场景2：客户登录看不到菜单、权限加载慢
```bash
trace com.xx.service.MenuService getCurrentMenu
trace com.xx.service.CustomerService getCustomerInfo
```

### 场景3：MQ 消费客户/商品同步异常
```bash
watch com.xx.mq.CustomerConsumer consume '{params,throwExp}' -e
```

### 场景4：接口偶尔超时，定位偶发问题
```bash
trace com.xx.controller.XxController xxMethod '#cost>500'
```

### 场景5：定位数据库慢查询
```bash
trace org.apache.ibatis.executor.CachingExecutor query
```

---

## 五、排查性能问题标准流程（你可以直接写进总结）
1. **thread** 看是否线程阻塞、CPU 高
2. **trace** 定位方法内部哪一步真正耗时
3. **watch** 看入参是否异常、返回是否正确
4. **jad** 确认代码是否最新部署
5. **stack** 看谁调用了该方法
6. **jvm** 看内存、GC 是否异常

通过这套流程，**10 分钟内可定位 90% 性能问题**，包括：

+ 接口慢
+ 偶发超时
+ 仓单/商品/客户同步异常
+ 菜单加载慢
+ 数据库查询慢
+ 微服务调用慢

---

## 六、你可以在述职/汇报中直接说的话术
在分布式系统性能瓶颈定位过程中，我大量使用 **Arthas 在线诊断工具**，无需重启服务、无需修改代码，通过 `trace` 分析方法内部调用耗时、`watch` 监控入参出参异常、`thread` 排查线程阻塞与 CPU 占用，快速定位到慢接口、慢 SQL、跨服务调用延迟、消息消费异常等问题，结合全链路追踪，最终精准识别系统架构层面的性能瓶颈。

---

需要我再给你做一份 **一页 A4 纸精简版（可打印）** 或者 **带注释的命令速查表** 吗？
