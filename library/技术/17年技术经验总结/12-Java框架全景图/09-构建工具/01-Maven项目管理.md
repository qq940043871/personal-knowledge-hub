# Maven项目管理

> 模块：Java框架全景图 / 09-构建工具
> 更新时间：2026-06-20

---

## 一、Maven 是什么

**Maven是Java领域最主流的项目构建和依赖管理工具**，通过POM（Project Object Model）文件管理项目的构建、依赖、文档等。

### 核心特性

- **依赖管理** — 自动下载和管理项目依赖
- **构建生命周期** — 编译、测试、打包、部署标准化
- **插件体系** — 丰富的插件扩展构建能力
- **多模块支持** — 支持大型项目的模块化管理

---

## 二、POM文件结构

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    
    <modelVersion>4.0.0</modelVersion>
    
    <!-- 项目坐标 -->
    <groupId>com.example</groupId>
    <artifactId>my-app</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
    
    <!-- 父项目 -->
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
    </parent>
    
    <!-- 属性 -->
    <properties>
        <java.version>17</java.version>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
    </properties>
    
    <!-- 依赖 -->
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <optional>true</optional>
        </dependency>
    </dependencies>
    
    <!-- 构建配置 -->
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
```

---

## 三、依赖管理

### 3.1 依赖范围

| Scope | 编译 | 测试 | 运行 | 打包 |
|-------|------|------|------|------|
| compile | ✅ | ✅ | ✅ | ✅ |
| test | ❌ | ✅ | ❌ | ❌ |
| provided | ✅ | ✅ | ❌ | ❌ |
| runtime | ❌ | ✅ | ✅ | ✅ |
| system | ✅ | ✅ | ❌ | ❌ |

### 3.2 依赖传递

```
A → B → C (compile)
A 自动依赖 C
```

### 3.3 排除依赖

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
    <exclusions>
        <exclusion>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-tomcat</artifactId>
        </exclusion>
    </exclusions>
</dependency>
```

### 3.4 依赖版本管理

```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>com.google.guava</groupId>
            <artifactId>guava</artifactId>
            <version>32.1.3-jre</version>
        </dependency>
    </dependencies>
</dependencyManagement>
```

---

## 四、构建生命周期

> 默认生命周期：**validate → compile → test → package → verify → install → deploy**，每个环节都是标准化的一步。

### 4.1 默认生命周期

```
validate → compile → test → package → verify → install → deploy
```

*图：Maven 默认构建生命周期（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 200" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="35" y="30" width="140" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="105" y="57" text-anchor="middle" font-size="13" fill="#1e293b">validate 校验</text>
  <line x1="175" y1="52" x2="203" y2="52" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="205" y="30" width="140" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="275" y="57" text-anchor="middle" font-size="13" fill="#1e293b">compile 编译</text>
  <line x1="345" y1="52" x2="373" y2="52" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="375" y="30" width="140" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="445" y="57" text-anchor="middle" font-size="13" fill="#1e293b">test 测试</text>
  <line x1="515" y1="52" x2="543" y2="52" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="545" y="30" width="140" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="615" y="57" text-anchor="middle" font-size="13" fill="#1e293b">package 打包</text>
  <polyline points="615,74 615,97 190,97 190,118" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="120" y="120" width="140" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="190" y="147" text-anchor="middle" font-size="13" fill="#1e293b">verify 验证</text>
  <line x1="260" y1="142" x2="288" y2="142" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="290" y="120" width="140" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="147" text-anchor="middle" font-size="13" fill="#1e293b">install 安装</text>
  <line x1="430" y1="142" x2="458" y2="142" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="460" y="120" width="140" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="530" y="147" text-anchor="middle" font-size="13" fill="#1e293b">deploy 部署</text>
</svg>

### 4.2 常用命令

```bash
# 编译
mvn compile

# 运行测试
mvn test

# 打包
mvn package

# 安装到本地仓库
mvn install

# 部署到远程仓库
mvn deploy

# 清理
mvn clean

# 组合命令
mvn clean package -DskipTests
```

---

## 五、多模块项目

```xml
<!-- 父项目POM -->
<modules>
    <module>common</module>
    <module>service</module>
    <module>web</module>
</modules>
```

```
parent/
├── pom.xml
├── common/
│   └── pom.xml
├── service/
│   └── pom.xml
└── web/
    └── pom.xml
```

---

## 六、常用插件

```xml
<build>
    <plugins>
        <!-- 编译插件 -->
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-compiler-plugin</artifactId>
            <version>3.11.0</version>
            <configuration>
                <source>17</source>
                <target>17</target>
            </configuration>
        </plugin>
        
        <!-- 测试插件 -->
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-surefire-plugin</artifactId>
            <version>3.2.2</version>
        </plugin>
        
        <!-- 打包插件 -->
        <plugin>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-maven-plugin</artifactId>
        </plugin>
    </plugins>
</build>
```

---

## 七、最佳实践

1. **使用dependencyManagement** — 统一管理依赖版本
2. **合理设置依赖范围** — 避免不必要的依赖传递
3. **多模块拆分** — 按职责拆分模块
4. **使用Maven Wrapper** — 确保构建环境一致
5. **配置私服** — 使用Nexus/Artifactory管理私有依赖

---

## 八、与Gradle对比

| 特性 | Maven | Gradle |
|------|-------|--------|
| 构建速度 | 较慢 | 更快 |
| 配置方式 | XML | Groovy/Kotlin DSL |
| 灵活性 | 较低 | 高 |
| 学习曲线 | 低 | 中 |
| 生态成熟度 | 成熟 | 成熟 |

---

*Maven适合传统Java项目，Gradle适合Android和需要高性能构建的项目。*
