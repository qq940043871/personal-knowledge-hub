# Kubernetes实战 - 架构师学习笔记

Kubernetes是容器编排的**事实标准**，掌握Kubernetes实战技能对于构建和管理大规模容器化应用至关重要。

Kubernetes提供了自动化的容器部署、扩展和管理功能，是**云原生应用的核心基础设施**。

## Kubernetes核心概念

### Pod

- Kubernetes中**最小的部署单元**，可以包含一个或多个容器，共享网络和存储资源。

### Deployment

- 用于管理Pod的**声明式更新**，支持滚动更新、回滚等操作。

### Service

- 为Pod提供**稳定的网络访问入口**，实现服务发现和负载均衡。

### Volume

- 为Pod提供**持久化存储**，支持多种存储类型。

*图：Deployment、Pod、Service、Volume 的对象关系（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 210" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="40" y="78" width="150" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="115" y="105" text-anchor="middle" font-size="14" fill="#1e293b">Deployment</text>
  <line x1="190" y1="100" x2="288" y2="100" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="239" y="90" text-anchor="middle" font-size="12" fill="#475569">声明式更新</text>
  <rect x="290" y="78" width="140" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="360" y="105" text-anchor="middle" font-size="14" fill="#1e293b">Pod</text>
  <line x1="530" y1="100" x2="432" y2="100" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="481" y="90" text-anchor="middle" font-size="12" fill="#475569">服务发现/负载均衡</text>
  <rect x="530" y="78" width="150" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="605" y="105" text-anchor="middle" font-size="14" fill="#1e293b">Service</text>
  <line x1="360" y1="122" x2="360" y2="148" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="372" y="140" text-anchor="start" font-size="12" fill="#475569">持久化存储</text>
  <rect x="290" y="150" width="140" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="177" text-anchor="middle" font-size="14" fill="#1e293b">Volume</text>
</svg>

## 常用kubectl命令

### 资源管理

```bash
# 创建资源
kubectl apply -f deployment.yaml

# 获取资源信息
kubectl get pods
kubectl get deployments
kubectl get services

# 查看资源详情
kubectl describe pod <pod-name>

# 删除资源
kubectl delete -f deployment.yaml
kubectl delete pod <pod-name>
```

### Pod操作

```bash
# 进入Pod容器
kubectl exec -it <pod-name> -- /bin/bash

# 查看Pod日志
kubectl logs <pod-name>
kubectl logs -f <pod-name>

# 复制文件到Pod
kubectl cp <local-file> <pod-name>:<container-path>

# 重启Pod
kubectl delete pod <pod-name>
```

### 配置和上下文

```bash
# 查看当前上下文
kubectl config current-context

# 切换上下文
kubectl config use-context <context-name>

# 查看集群信息
kubectl cluster-info

# 查看节点信息
kubectl get nodes
```

## Deployment配置示例

### 基础Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.21
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m"
```

这是一个简单的Nginx Deployment配置示例。

### 带健康检查的Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: springboot-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: springboot
  template:
    metadata:
      labels:
        app: springboot
    spec:
      containers:
      - name: app
        image: myapp:latest
        ports:
        - containerPort: 8080
        livenessProbe:
          httpGet:
            path: /actuator/health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /actuator/health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 5
```

添加**健康检查**可以确保应用的高可用性。

## Service配置示例

### ClusterIP Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  selector:
    app: nginx
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
```

**ClusterIP是默认的Service类型**，只能在集群内部访问。

### NodePort Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-nodeport
spec:
  type: NodePort
  selector:
    app: nginx
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
      nodePort: 30080
```

**NodePort类型**的Service可以通过节点IP和指定端口从外部访问。

## ConfigMap和Secret

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  application.properties: |
    server.port=8080
    spring.datasource.url=jdbc:mysql://mysql:3306/mydb
    spring.datasource.username=user
    spring.datasource.password=password
```

**ConfigMap用于存储非敏感的配置数据**。

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
data:
  username: dXNlcg==  # base64编码的"user"
  password: cGFzc3dvcmQ=  # base64编码的"password"
```

**Secret用于存储敏感信息**，如密码、密钥等。

## Kubernetes最佳实践

- 为资源设置合适的**requests和limits**
- 使用**标签和注解**组织和管理资源
- 实施**健康检查**确保应用可用性
- 使用**命名空间**隔离不同环境
- 定期备份**etcd**数据
- 监控集群状态和资源使用情况
