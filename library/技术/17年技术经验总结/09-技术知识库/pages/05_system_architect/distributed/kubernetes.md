# Kubernetes - 架构师学习笔记

Kubernetes（简称K8s）是Google开源的**容器编排平台**，用于自动化部署、扩展和管理容器化应用程序。它提供了服务发现、负载均衡、存储编排、自动部署和回滚、自动装箱、自我修复、密钥与配置管理等功能。

## Kubernetes核心概念

### Pod

Kubernetes中**最小的可部署单元**，可以包含一个或多个容器，共享网络和存储资源。

- 最小部署单元
- 共享网络和存储
- 生命周期短暂

### Service

为一组Pod提供**稳定的网络访问入口**，实现服务发现和负载均衡。

- 稳定访问入口
- 负载均衡
- 服务发现

### Deployment

用于管理Pod和ReplicaSet，提供**声明式的更新和部署**能力。

- 声明式部署
- 滚动更新
- 回滚支持

### Volume

为Pod提供**持久化存储**，支持多种存储类型。

- 持久化存储
- 多种存储类型
- 数据共享

## Kubernetes架构

### 控制平面组件

| 组件 | 功能 |
|------|------|
| kube-apiserver | 集群控制的前端，提供REST API |
| etcd | 分布式键值存储，保存集群状态 |
| kube-scheduler | 负责Pod调度到合适的节点 |
| kube-controller-manager | 运行控制器进程 |
| cloud-controller-manager | 与云提供商交互的控制器 |

### 节点组件

| 组件 | 功能 |
|------|------|
| kubelet | 负责节点上的Pod管理 |
| kube-proxy | 实现服务网络代理和负载均衡 |
| 容器运行时 | 负责运行容器（如Docker、containerd） |

*图：Kubernetes 控制平面与节点组件（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 270" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="20" y="36" width="680" height="114" rx="10" fill="#f8fafc" stroke="#cbd5e1" stroke-dasharray="4 3"/>
  <text x="36" y="60" font-size="14" font-weight="bold" fill="#1e293b">控制平面组件</text>
  <rect x="33" y="76" width="126" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="96" y="101" text-anchor="middle" font-size="12" fill="#1e293b">kube-apiserver</text>
  <rect x="165" y="76" width="126" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="228" y="101" text-anchor="middle" font-size="12" fill="#1e293b">etcd</text>
  <rect x="297" y="76" width="126" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="101" text-anchor="middle" font-size="12" fill="#1e293b">kube-scheduler</text>
  <rect x="429" y="76" width="126" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="492" y="93" text-anchor="middle" font-size="12" fill="#1e293b">kube-controller</text>
  <text x="492" y="109" text-anchor="middle" font-size="12" fill="#1e293b">-manager</text>
  <rect x="561" y="76" width="126" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="624" y="93" text-anchor="middle" font-size="12" fill="#1e293b">cloud-controller</text>
  <text x="624" y="109" text-anchor="middle" font-size="12" fill="#1e293b">-manager</text>
  <line x1="360" y1="150" x2="360" y2="168" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="372" y="163" text-anchor="start" font-size="12" fill="#475569">调度Pod到节点</text>
  <rect x="20" y="170" width="680" height="86" rx="10" fill="#f8fafc" stroke="#cbd5e1" stroke-dasharray="4 3"/>
  <text x="36" y="192" font-size="14" font-weight="bold" fill="#1e293b">节点组件</text>
  <rect x="40" y="200" width="200" height="40" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="140" y="225" text-anchor="middle" font-size="13" fill="#1e293b">kubelet</text>
  <rect x="260" y="200" width="200" height="40" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="360" y="225" text-anchor="middle" font-size="13" fill="#1e293b">kube-proxy</text>
  <rect x="480" y="200" width="200" height="40" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="580" y="225" text-anchor="middle" font-size="13" fill="#1e293b">容器运行时</text>
</svg>

## 常用kubectl命令

### 资源管理

```bash
# 创建资源
kubectl apply -f deployment.yaml

# 删除资源
kubectl delete deployment myapp

# 查看资源
kubectl get pods
kubectl get deployments
kubectl get services

# 查看资源详情
kubectl describe pod pod-name
```

### Pod操作

```bash
# 进入Pod
kubectl exec -it pod-name -- /bin/bash

# 查看日志
kubectl logs pod-name

# 复制文件到Pod
kubectl cp local-file pod-name:/path/to/file

# 端口转发
kubectl port-forward pod-name 8080:80
```

## Deployment示例

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx
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
        image: nginx:1.14.2
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

## Service示例

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
  type: LoadBalancer
```

## 存储管理

### PersistentVolume

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-volume
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  hostPath:
    path: "/mnt/data"
```

### PersistentVolumeClaim

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pv-claim
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 3Gi
```

## 配置管理

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  database_url: postgresql://localhost:5432/mydb
  log_level: INFO
```

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
data:
  username: bXl1c2Vy
  password: bXlwYXNzd29yZA==
```

## Kubernetes网络

### 网络模型

- **Pod间通信**：所有Pod都在一个可以直接连通的、扁平的网络空间中
- **Pod与Service通信**：通过Service的ClusterIP实现
- **外部与Service通信**：通过NodePort、LoadBalancer或Ingress实现

### Ingress示例

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: example-ingress
spec:
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myapp-service
            port:
              number: 80
```

## Kubernetes最佳实践

- 合理设置**资源请求和限制**，避免资源浪费
- 使用**健康检查**（liveness和readiness probes）确保应用健康
- 实施**标签和注解策略**，便于资源管理和查询
- 使用**命名空间**隔离不同环境和团队的资源
- 定期备份**etcd**数据，确保集群状态可恢复
- 实施**安全策略**，如RBAC、网络策略等
- **监控和日志收集**，使用Prometheus、Grafana等工具
