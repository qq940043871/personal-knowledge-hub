# Gradle构建工具

> 模块：Java框架全景图 / 09-构建工具
> 更新时间：2026-06-20

---

## 一、Gradle 是什么

**Gradle是基于JVM的构建工具**，使用Groovy或Kotlin DSL配置，比Maven更灵活、构建速度更快，是**Android官方构建工具**。

### 核心特性

- **增量构建** — 只构建变化的部分
- **构建缓存** — 本地和远程缓存
- **并行执行** — 多任务并行构建
- **插件生态** — 丰富的插件支持

---

## 二、基本配置

### 2.1 build.gradle

```groovy
plugins {
    id 'java'
    id 'org.springframework.boot' version '3.2.0'
    id 'io.spring.dependency-management' version '1.1.4'
}

group = 'com.example'
version = '1.0.0'

java {
    sourceCompatibility = '17'
}

repositories {
    mavenCentral()
}

dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
    compileOnly 'org.projectlombok:lombok'
    annotationProcessor 'org.projectlombok:lombok'
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
}

tasks.named('test') {
    useJUnitPlatform()
}
```

### 2.2 settings.gradle

```groovy
rootProject.name = 'my-app'

include 'common'
include 'service'
include 'web'
```

---

## 三、依赖管理

### 3.1 依赖配置

```groovy
dependencies {
    // 编译和运行时依赖
    implementation 'com.google.guava:guava:32.1.3-jre'
    
    // 仅编译时依赖
    compileOnly 'javax.servlet:javax.servlet-api:4.0.1'
    
    // 仅运行时依赖
    runtimeOnly 'com.mysql:mysql-connector-j:8.0.33'
    
    // 仅测试依赖
    testImplementation 'junit:junit:4.13.2'
    
    // 注解处理器
    annotationProcessor 'org.projectlombok:lombok:1.18.30'
}
```

### 3.2 版本目录

```toml
# gradle/libs.versions.toml
[versions]
guava = "32.1.3-jre"
spring-boot = "3.2.0"

[libraries]
guava = { module = "com.google.guava:guava", version.ref = "guava" }
spring-boot-web = { module = "org.springframework.boot:spring-boot-starter-web", version.ref = "spring-boot" }

[bundles]
web = ["spring-boot-web"]
```

```groovy
dependencies {
    implementation libs.guava
    implementation libs.bundles.web
}
```

---

## 四、构建任务

### 4.1 常用命令

```bash
# 构建项目
./gradlew build

# 运行测试
./gradlew test

# 打包
./gradlew jar

# 清理
./gradlew clean

# 运行应用
./gradlew bootRun

# 查看依赖
./gradlew dependencies
```

### 4.2 自定义任务

```groovy
tasks.register('hello') {
    group = 'custom'
    description = 'Say hello'
    doLast {
        println 'Hello, Gradle!'
    }
}

tasks.register('copyDocs', Copy) {
    from 'docs'
    into 'build/docs'
}
```

---

## 五、多模块项目

```groovy
// settings.gradle
rootProject.name = 'my-project'
include 'common', 'service', 'web'
```

```groovy
// common/build.gradle
plugins {
    id 'java-library'
}

dependencies {
    api 'com.google.guava:guava:32.1.3-jre'
}
```

```groovy
// service/build.gradle
dependencies {
    implementation project(':common')
}
```

---

## 六、Spring Boot集成

```groovy
plugins {
    id 'org.springframework.boot' version '3.2.0'
    id 'io.spring.dependency-management' version '1.1.4'
}

bootJar {
    archiveBaseName = 'my-app'
    archiveVersion = '1.0.0'
}

bootRun {
    args = ['--server.port=8080']
}
```

---

## 七、与Maven对比

| 特性 | Gradle | Maven |
|------|--------|-------|
| 构建速度 | 快（增量构建） | 慢（全量构建） |
| 配置方式 | Groovy/Kotlin DSL | XML |
| 灵活性 | 高 | 低 |
| 学习曲线 | 中 | 低 |
| Android支持 | 官方支持 | 不支持 |

*图：Gradle 与 Maven 构建特性对比（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 245" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <rect x="110" y="15" width="140" height="38" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="180" y="39" text-anchor="middle" font-size="15" font-weight="bold" fill="#1e293b">Gradle</text>
  <rect x="470" y="15" width="140" height="38" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="540" y="39" text-anchor="middle" font-size="15" font-weight="bold" fill="#1e293b">Maven</text>
  <rect x="310" y="75" width="100" height="30" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="360" y="95" text-anchor="middle" font-size="13" fill="#1e293b">构建速度</text>
  <text x="280" y="95" text-anchor="end" font-size="13" fill="#1e293b">快（增量构建）</text>
  <text x="440" y="95" text-anchor="start" font-size="13" fill="#475569">慢（全量构建）</text>
  <rect x="310" y="115" width="100" height="30" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="360" y="135" text-anchor="middle" font-size="13" fill="#1e293b">配置方式</text>
  <text x="280" y="135" text-anchor="end" font-size="13" fill="#1e293b">Groovy/Kotlin DSL</text>
  <text x="440" y="135" text-anchor="start" font-size="13" fill="#475569">XML</text>
  <rect x="310" y="155" width="100" height="30" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="360" y="175" text-anchor="middle" font-size="13" fill="#1e293b">灵活性</text>
  <text x="280" y="175" text-anchor="end" font-size="13" fill="#1e293b">高</text>
  <text x="440" y="175" text-anchor="start" font-size="13" fill="#475569">低</text>
  <rect x="310" y="195" width="100" height="30" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="360" y="215" text-anchor="middle" font-size="13" fill="#1e293b">Android支持</text>
  <text x="280" y="215" text-anchor="end" font-size="13" fill="#1e293b">官方支持</text>
  <text x="440" y="215" text-anchor="start" font-size="13" fill="#475569">不支持</text>
</svg>

---

## 八、最佳实践

1. **使用Gradle Wrapper** — `gradlew`确保构建环境一致
2. **启用构建缓存** — 提升构建速度
3. **使用版本目录** — 统一管理依赖版本
4. **合理拆分模块** — 按职责拆分
5. **配置并行构建** — `org.gradle.parallel=true`

---

*Gradle适合需要高性能构建和灵活配置的项目。*
