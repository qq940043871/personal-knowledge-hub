# XMReport 报表设计器集成文档

## 1. 技术栈

- **前端**：Vue.js 3、Element Plus、Ace Editor（代码编辑器）
- **后端**：Spring Boot 2.7.x、Java 8+
- **模板引擎**：Apache POI（处理 docx）、Freemarker（模板渲染）
- **PDF 生成**：iText 7、OpenPDF
- **数据库**：MySQL 8.0（存储模板配置和报表数据）
- **文件存储**：MinIO（存储模板文件和生成的 PDF）
- **容器化**：Docker、Docker Compose

## 2. 功能介绍

### 2.1 模板配置

- **DOCX 模板编辑**：支持上传和编辑 DOCX 模板文件
- **变量占位符**：支持在模板中使用 `${variable}` 形式的变量占位符
- **条件渲染**：支持 `{{#if condition}}...{{/if}}` 形式的条件渲染
- **循环渲染**：支持 `{{#each list}}...{{/each}}` 形式的循环渲染
- **表达式支持**：支持简单的表达式计算，如 `${a + b}`

### 2.2 数据源配置

- **数据库数据源**：支持 MySQL、Oracle、PostgreSQL 等数据库
- **API 数据源**：支持 RESTful API 数据源
- **Excel 数据源**：支持 Excel 文件作为数据源
- **CSV 数据源**：支持 CSV 文件作为数据源

### 2.3 报表生成

- **PDF 生成**：将填充后的 DOCX 模板转换为 PDF
- **DOCX 生成**：生成填充后的 DOCX 文件
- **Excel 生成**：生成 Excel 报表
- **HTML 生成**：生成 HTML 报表

### 2.4 报表管理

- **模板管理**：创建、编辑、删除模板
- **报表管理**：查看、下载、删除生成的报表
- **历史记录**：记录报表生成历史
- **权限控制**：基于角色的权限控制

### 2.5 HTTP 接口

- **模板管理接口**：上传、下载、更新、删除模板
- **报表生成接口**：根据模板和数据生成报表
- **数据源管理接口**：配置和管理数据源
- **报表查询接口**：查询生成的报表

## 3. 实现方案

### 3.1 项目结构

```
├── xmreport-frontend/              # 前端项目
│   ├── src/
│   │   ├── components/             # 组件
│   │   │   ├── TemplateEditor.vue  # 模板编辑器
│   │   │   ├── DataSourceConfig.vue # 数据源配置
│   │   │   └── ReportPreview.vue   # 报表预览
│   │   ├── views/                  # 页面
│   │   │   ├── TemplateManage.vue  # 模板管理
│   │   │   ├── DataSourceManage.vue # 数据源管理
│   │   │   └── ReportManage.vue    # 报表管理
│   │   ├── api/                    # API 调用
│   │   └── router/                 # 路由
│   ├── package.json                # 依赖配置
│   └── vite.config.js              # Vite 配置
├── xmreport-backend/               # 后端项目
│   ├── src/main/java
│   │   ├── com/xmreport/
│   │   │   ├── controller/         # 控制器
│   │   │   │   ├── TemplateController.java  # 模板管理接口
│   │   │   │   ├── ReportController.java    # 报表生成接口
│   │   │   │   └── DataSourceController.java # 数据源管理接口
│   │   │   ├── service/            # 服务
│   │   │   │   ├── TemplateService.java     # 模板服务
│   │   │   │   ├── ReportService.java       # 报表服务
│   │   │   │   └── DataSourceService.java   # 数据源服务
│   │   │   ├── model/              # 模型
│   │   │   │   ├── Template.java            # 模板模型
│   │   │   │   ├── Report.java              # 报表模型
│   │   │   │   └── DataSource.java          # 数据源模型
│   │   │   ├── utils/              # 工具类
│   │   │   │   ├── DocxUtils.java           # DOCX 处理工具
│   │   │   │   ├── PdfUtils.java            # PDF 生成工具
│   │   │   │   └── TemplateRenderer.java    # 模板渲染工具
│   │   │   └── config/             # 配置
│   │   │       └── MinIOConfig.java         # MinIO 配置
│   │   └── resources
│   │       ├── application.yml                # 应用配置
│   │       └── templates/                     # 内置模板
│   ├── pom.xml                                # Maven 依赖配置
│   └── Dockerfile                             # Docker 构建文件
├── docker-compose.yml                         # Docker Compose 配置
└── README.md                                  # 项目说明
```

### 3.2 核心依赖

#### 前端依赖

```json
{
  "dependencies": {
    "vue": "^3.2.47",
    "element-plus": "^2.3.7",
    "axios": "^1.4.0",
    "ace-builds": "^1.32.0",
    "vue-router": "^4.2.2"
  },
  "devDependencies": {
    "vite": "^4.3.9",
    "@vitejs/plugin-vue": "^4.2.3"
  }
}
```

#### 后端依赖

```xml
<dependencies>
    <!-- Spring Boot Web -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    
    <!-- Spring Boot Data JPA -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-data-jpa</artifactId>
    </dependency>
    
    <!-- MySQL Driver -->
    <dependency>
        <groupId>mysql</groupId>
        <artifactId>mysql-connector-java</artifactId>
        <scope>runtime</scope>
    </dependency>
    
    <!-- Apache POI -->
    <dependency>
        <groupId>org.apache.poi</groupId>
        <artifactId>poi-ooxml</artifactId>
        <version>5.2.3</version>
    </dependency>
    
    <!-- Freemarker -->
    <dependency>
        <groupId>org.freemarker</groupId>
        <artifactId>freemarker</artifactId>
        <version>2.3.31</version>
    </dependency>
    
    <!-- iText 7 -->
    <dependency>
        <groupId>com.itextpdf</groupId>
        <artifactId>itext7-core</artifactId>
        <version>7.2.3</version>
    </dependency>
    
    <!-- MinIO Client -->
    <dependency>
        <groupId>io.minio</groupId>
        <artifactId>minio</artifactId>
        <version>8.5.2</version>
    </dependency>
    
    <!-- Jackson JSON -->
    <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
    </dependency>
</dependencies>
```

### 3.3 配置文件

#### 前端配置

```javascript
// vite.config.js
export default {
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true
      }
    }
  }
}
```

#### 后端配置

```yaml
spring:
  application:
    name: xmreport-service
  
  datasource:
    url: jdbc:mysql://localhost:3306/xmreport?useSSL=false&serverTimezone=UTC
    username: root
    password: password
  
  jpa:
    hibernate:
      ddl-auto: update
    show-sql: true

server:
  port: 8080

minio:
  endpoint: http://localhost:9000
  access-key: minioadmin
  secret-key: minioadmin
  bucket-name: xmreport

report:
  template-dir: templates/
  output-dir: output/
```

## 4. 核心功能实现

### 4.1 模板配置

#### 前端实现

- 上传 DOCX 模板文件
- 在线编辑模板内容，支持变量占位符、条件渲染和循环渲染
- 预览模板效果
- 保存模板配置

#### 后端实现

- 接收并存储模板文件到 MinIO
- 解析模板中的变量和表达式
- 验证模板语法
- 存储模板配置到数据库

### 4.2 数据源配置

#### 前端实现

- 配置数据库数据源（URL、用户名、密码等）
- 配置 API 数据源（URL、请求方法、参数等）
- 测试数据源连接
- 保存数据源配置

#### 后端实现

- 存储数据源配置到数据库
- 测试数据源连接
- 从数据源获取数据

### 4.3 报表生成

#### 前端实现

- 选择模板和数据源
- 输入报表参数
- 预览报表效果
- 生成并下载报表

#### 后端实现

- 从数据源获取数据
- 使用 Freemarker 渲染模板
- 使用 Apache POI 填充 DOCX 模板
- 使用 iText 7 将 DOCX 转换为 PDF
- 存储生成的报表到 MinIO
- 记录报表生成历史

*图：报表生成核心链路（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 230" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="20" y="30" width="190" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="115" y="57" text-anchor="middle" font-size="14" fill="#1e293b">从数据源获取数据</text>
  <line x1="210" y1="52" x2="260" y2="52" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="265" y="30" width="190" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="57" text-anchor="middle" font-size="14" fill="#1e293b">Freemarker 渲染模板</text>
  <line x1="455" y1="52" x2="505" y2="52" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="510" y="30" width="190" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="605" y="57" text-anchor="middle" font-size="14" fill="#1e293b">POI 填充 DOCX</text>
  <path d="M605 74 L605 110 L115 110 L115 138" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="20" y="145" width="190" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="115" y="172" text-anchor="middle" font-size="14" fill="#1e293b">iText 7 转换 PDF</text>
  <line x1="210" y1="167" x2="260" y2="167" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="265" y="145" width="190" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="172" text-anchor="middle" font-size="14" fill="#1e293b">报表存储到 MinIO</text>
  <line x1="455" y1="167" x2="505" y2="167" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="510" y="145" width="190" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="605" y="172" text-anchor="middle" font-size="14" fill="#1e293b">记录生成历史</text>
</svg>

### 4.4 HTTP 接口

#### 模板管理接口

- `POST /api/templates`：上传模板
- `GET /api/templates`：获取模板列表
- `GET /api/templates/{id}`：获取模板详情
- `PUT /api/templates/{id}`：更新模板
- `DELETE /api/templates/{id}`：删除模板

#### 报表生成接口

- `POST /api/reports`：生成报表
- `GET /api/reports`：获取报表列表
- `GET /api/reports/{id}`：获取报表详情
- `DELETE /api/reports/{id}`：删除报表

#### 数据源管理接口

- `POST /api/datasources`：创建数据源
- `GET /api/datasources`：获取数据源列表
- `GET /api/datasources/{id}`：获取数据源详情
- `PUT /api/datasources/{id}`：更新数据源
- `DELETE /api/datasources/{id}`：删除数据源
- `POST /api/datasources/{id}/test`：测试数据源连接

## 5. 部署方式

### 5.1 本地部署

1. 克隆项目代码
2. 启动 MySQL 数据库
3. 启动 MinIO 服务
4. 构建并运行后端服务
5. 构建并运行前端服务

### 5.2 Docker 部署

```dockerfile
# 后端 Dockerfile
FROM openjdk:8-jdk-alpine

WORKDIR /app

COPY target/xmreport-service.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]

# 前端 Dockerfile
FROM node:16-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 5.3 Docker Compose 部署

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: password
      MYSQL_DATABASE: xmreport
    ports:
      - "3306:3306"
    volumes:
      - mysql-data:/var/lib/mysql
  
  minio:
    image: minio/minio
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio-data:/data
    command: server --console-address ":9001" /data
  
  backend:
    build: ./xmreport-backend
    ports:
      - "8080:8080"
    depends_on:
      - mysql
      - minio
  
  frontend:
    build: ./xmreport-frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  mysql-data:
  minio-data:
```

## 6. 性能优化

1. **模板缓存**：缓存解析后的模板，减少重复解析
2. **数据缓存**：缓存数据源查询结果，减少数据库查询
3. **异步处理**：使用线程池处理报表生成任务
4. **批量处理**：支持批量生成报表
5. **文件压缩**：压缩生成的 PDF 文件，减少存储空间

## 7. 安全性

1. **输入验证**：对上传的模板和输入参数进行验证
2. **SQL 注入防护**：使用参数化查询，防止 SQL 注入
3. **XSS 防护**：对用户输入进行转义，防止 XSS 攻击
4. **权限控制**：基于角色的权限控制，限制用户操作
5. **HTTPS**：使用 HTTPS 协议传输数据
6. **敏感信息加密**：加密存储数据库密码等敏感信息

## 8. 扩展与维护

1. **支持更多模板格式**：可扩展支持 Excel、PowerPoint 等模板格式
2. **支持更多输出格式**：可扩展支持 CSV、XML 等输出格式
3. **支持更多数据源**：可扩展支持 MongoDB、Redis 等数据源
4. **监控与告警**：实现服务监控和异常告警机制
5. **日志记录**：记录操作日志，便于问题排查
6. **多语言支持**：支持多语言界面和报表

## 9. 总结：快速搭建企业级报表系统

XMReport 报表设计器是一个功能强大的开源报表工具，支持 DOCX 模板配置和 PDF 生成功能。通过本文档的指导，您可以快速搭建一个完整的报表系统，满足企业级报表需求。在实际应用中，您可以根据具体需求进行适当的调整和优化，以达到最佳的使用效果。
