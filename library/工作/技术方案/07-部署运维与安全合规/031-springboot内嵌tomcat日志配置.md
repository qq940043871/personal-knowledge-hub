# springboot内嵌tomcat日志配置

```yaml
server:
  port: 8082
  tomcat:
    accesslog:
      buffered: true
      directory: E:/logs
      enabled: true
      file-date-format: .yyyy-MM-dd
      pattern: common
      prefix: access_log
      rename-on-rotate: false
      request-attributes-enabled: false
      rotate: true
      suffix: .log
```
