# PaddleOCR 集成文档

## 技术栈

- **PaddleOCR**：百度开源的OCR工具库，支持多种语言和场景的文字识别
- **Java**：后端开发语言
- **Spring Boot**：Web框架，用于提供HTTP接口
- **Maven**：依赖管理工具
- **OpenCV**：图像处理库，用于预处理
- **Docker**：容器化部署

## 功能介绍

### 证件识别

- **身份证识别**：识别身份证正面的姓名、性别、民族、出生日期、住址、身份证号等信息
- **护照识别**：识别护照的个人信息页内容
- **驾驶证识别**：识别驾驶证的相关信息

### 银行卡识别

- **银行卡号识别**：自动识别银行卡号
- **银行卡类型识别**：识别银行卡的类型（借记卡/信用卡）
- **银行名称识别**：识别发卡银行名称

### HTTP接口

- 提供RESTful API接口，支持图片上传和识别结果返回
- 支持Base64编码的图片数据
- 支持图片URL传入

## 实现方案

### 项目结构

```
├── src/main/java
│   ├── com/example/paddleocr
│   │   ├── controller
│   │   │   └── OCRController.java        # HTTP接口控制器
│   │   ├── service
│   │   │   ├── OCRService.java           # OCR服务接口
│   │   │   ├── impl
│   │   │   │   ├── IDCardRecognizer.java  # 身份证识别实现
│   │   │   │   ├── BankCardRecognizer.java # 银行卡识别实现
│   │   │   │   └── OCRServiceImpl.java    # OCR服务实现
│   │   ├── model
│   │   │   ├── IDCardInfo.java            # 身份证信息模型
│   │   │   ├── BankCardInfo.java          # 银行卡信息模型
│   │   │   └── OCRResult.java             # OCR结果模型
│   │   ├── utils
│   │   │   └── ImageUtils.java            # 图像处理工具
│   │   └── config
│   │       └── PaddleOCRConfig.java       # PaddleOCR配置
│   └── resources
│       ├── application.yml                # 应用配置
│       └── models/                        # PaddleOCR模型文件
├── pom.xml                                # Maven依赖配置
└── Dockerfile                             # Docker构建文件
```

### 核心依赖

```xml
<dependencies>
    <!-- Spring Boot Web -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    
    <!-- PaddleOCR Java SDK -->
    <dependency>
        <groupId>com.baidu.paddle</groupId>
        <artifactId>paddleocr</artifactId>
        <version>2.0.0</version>
    </dependency>
    
    <!-- OpenCV -->
    <dependency>
        <groupId>org.openpnp</groupId>
        <artifactId>opencv</artifactId>
        <version>4.5.5-1</version>
    </dependency>
    
    <!-- Jackson JSON -->
    <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
    </dependency>
</dependencies>
```

### 配置文件

```yaml
spring:
  application:
    name: paddleocr-service
  
server:
  port: 8080

paddleocr:
  model-dir: classpath:models/
  det-model: ch_PP-OCRv3_det_infer
  rec-model: ch_PP-OCRv3_rec_infer
  cls-model: ch_PP-OCRv3_cls_infer
  use-gpu: false
  gpu-memory: 4000
```

*图：OCR 识别请求处理链路（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 410" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="150" y="16" width="420" height="42" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="42" text-anchor="middle" font-size="14" fill="#1e293b">客户端请求（Base64 图片 / 图片 URL）</text>
  <line x1="360" y1="58" x2="360" y2="80" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="180" y="82" width="360" height="42" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="108" text-anchor="middle" font-size="14" fill="#1e293b">OCRController（HTTP 接口）</text>
  <line x1="360" y1="124" x2="360" y2="146" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="250" y="148" width="220" height="42" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="174" text-anchor="middle" font-size="14" fill="#1e293b">OCRService</text>
  <line x1="360" y1="190" x2="360" y2="202" stroke="#94a3b8" stroke-width="1.5"/>
  <line x1="230" y1="202" x2="490" y2="202" stroke="#94a3b8" stroke-width="1.5"/>
  <line x1="230" y1="202" x2="230" y2="212" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="490" y1="202" x2="490" y2="212" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="120" y="214" width="220" height="42" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="230" y="231" text-anchor="middle" font-size="13" fill="#1e293b">IDCardRecognizer</text>
  <text x="230" y="247" text-anchor="middle" font-size="12" fill="#475569">身份证识别</text>
  <rect x="380" y="214" width="220" height="42" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="490" y="231" text-anchor="middle" font-size="13" fill="#1e293b">BankCardRecognizer</text>
  <text x="490" y="247" text-anchor="middle" font-size="12" fill="#475569">银行卡识别</text>
  <line x1="250" y1="256" x2="322" y2="276" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="470" y1="256" x2="398" y2="276" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="180" y="278" width="360" height="42" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="360" y="304" text-anchor="middle" font-size="14" fill="#1e293b">PaddleOCR 模型推理（det / rec / cls）</text>
  <line x1="360" y1="320" x2="360" y2="342" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="150" y="344" width="420" height="42" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="360" y="370" text-anchor="middle" font-size="14" fill="#1e293b">返回 JSON 识别结果</text>
</svg>

## 部署方式

### 本地部署

1. 克隆项目代码
2. 下载PaddleOCR模型文件到 `src/main/resources/models/` 目录
3. 执行 `mvn clean package` 构建项目
4. 运行 `java -jar target/paddleocr-service.jar` 启动服务

### Docker部署

```dockerfile
FROM openjdk:8-jdk-alpine

WORKDIR /app

COPY target/paddleocr-service.jar app.jar
COPY src/main/resources/models/ models/

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
```

构建和运行：

```bash
docker build -t paddleocr-service .
docker run -p 8080:8080 paddleocr-service
```

## 接口说明

### 身份证识别接口

- **URL**: `/api/ocr/idcard`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "image": "base64编码的图片数据",
    "imageUrl": "图片URL（可选）"
  }
  ```
- **Response**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "name": "张三",
      "gender": "男",
      "nation": "汉",
      "birth": "19900101",
      "address": "北京市朝阳区",
      "idNumber": "110101199001011234"
    }
  }
  ```

### 银行卡识别接口

- **URL**: `/api/ocr/bankcard`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "image": "base64编码的图片数据",
    "imageUrl": "图片URL（可选）"
  }
  ```
- **Response**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "cardNumber": "6222021234567890123",
      "bankName": "中国工商银行",
      "cardType": "借记卡"
    }
  }
  ```

## 性能优化

1. **模型优化**：使用轻量级模型，如PP-OCRv3的移动端模型
2. **并发处理**：使用线程池处理OCR请求
3. **缓存机制**：对相同图片的识别结果进行缓存
4. **批处理**：支持批量图片识别
5. **硬件加速**：在支持GPU的环境中启用GPU加速

## 安全性

1. **输入验证**：对上传的图片进行大小和格式验证
2. **防止恶意请求**：实现请求频率限制
3. **数据脱敏**：对识别结果中的敏感信息进行脱敏处理
4. **HTTPS**：使用HTTPS协议传输数据
5. **权限控制**：对接口访问进行权限控制

## 扩展与维护

1. **模型更新**：定期更新PaddleOCR模型以提高识别准确率
2. **支持更多证件类型**：可扩展支持其他类型的证件识别
3. **多语言支持**：可扩展支持多语言文字识别
4. **监控与告警**：实现服务监控和异常告警机制
5. **日志记录**：记录识别请求和结果，便于问题排查
