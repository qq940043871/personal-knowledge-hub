## 📋 概述

GPUStack 是一个用于管理本地 GPU 资源的平台，支持多 GPU 调度和管理。

## 🏗️ 架构设计

```
<code>┌─────────────────────────────────────────┐<br/>│            GPUStack Platform            │<br/>├─────────────────────────────────────────┤<br/>│  Web UI  │  API Server  │  Scheduler    │<br/>├─────────────────────────────────────────┤<br/>│        GPU Resource Manager             │<br/>├─────────────────────────────────────────┤<br/>│   GPU 1    │   GPU 2    │   GPU N      │<br/>└─────────────────────────────────────────┘</code>
```

## 🚀 快速开始

### 1. 安装

```
<code># 使用 pip 安装<br/>pip install gpustack<br/><br/># 或者使用 Docker<br/>docker pull gpustack/gpustack</code>
```

### 2. 配置

创建配置文件 `config.yaml`:

```
<code>server:<br/>  host: "0.0.0.0"<br/>  port: 8000<br/><br/>gpus:<br/>  - name: "gpu-0"<br/>    type: "NVIDIA"<br/>    memory: "16GB"</code>
```

### 3. 启动服务

```
<code>gpustack start --config config.yaml</code>
```

## ⚙️ 核心功能

### GPU 管理

```
<code>from gpustack import GPUManager<br/><br/># 初始化GPU管理器<br/>gpu_manager = GPUManager()<br/><br/># 获取可用GPU列表<br/>available_gpus = gpu_manager.list_gpus()<br/>print(f"可用GPU数量: {len(available_gpus)}")<br/><br/># 获取特定GPU信息<br/>gpu_info = gpu_manager.get_gpu(0)<br/>print(f"GPU名称: {gpu_info.name}")<br/>print(f"GPU内存: {gpu_info.memory}")</code>
```

### 任务调度

```
<code>from gpustack import TaskScheduler<br/><br/>scheduler = TaskScheduler()<br/><br/># 提交GPU任务<br/>task_id = scheduler.submit_task(<br/>    name="model_inference",<br/>    gpu_required=True,<br/>    memory_required="8GB",<br/>    command="python inference.py"<br/>)<br/><br/># 查询任务状态<br/>status = scheduler.get_task_status(task_id)<br/>print(f"任务状态: {status}")</code>
```

### 资源监控

```
<code>from gpustack import Monitor<br/><br/>monitor = Monitor()<br/><br/># 获取实时GPU指标<br/>metrics = monitor.get_gpu_metrics(gpu_id=0)<br/>print(f"GPU使用率: {metrics.utilization}%")<br/>print(f"显存使用: {metrics.memory_used}/{metrics.memory_total}")</code>
```

## 💡 最佳实践

### 1. 多GPU负载均衡

```
<code>from gpustack import LoadBalancer<br/><br/>lb = LoadBalancer(strategy="round_robin")<br/><br/># 注册多个GPU<br/>lb.add_gpu(0)<br/>lb.add_gpu(1)<br/>lb.add_gpu(2)<br/><br/># 获取下一个可用GPU<br/>selected_gpu = lb.select_gpu()</code>
```

### 2. 任务优先级

```
<code>scheduler.submit_task(<br/>    name="high_priority_task",<br/>    priority=10,<br/>    gpu_required=True<br/>)<br/><br/>scheduler.submit_task(<br/>    name="low_priority_task",<br/>    priority=1,<br/>    gpu_required=False  # 可以使用CPU<br/>)</code>
```

### 3. 资源限制

```
<code># config.yaml<br/>limits:<br/>  max_concurrent_tasks: 4<br/>  max_memory_per_task: "8GB"<br/>  timeout_seconds: 3600</code>
```

## 🔧 API 参考

### 基础 API

| th | th | th |
| --- | --- | --- |
| td | td | td |
| td | td | td |
| td | td | td |
| td | td | td |
| td | td | td |

### 使用示例

```
<code># 获取GPU列表<br/>curl http://localhost:8000/api/gpus<br/><br/># 提交任务<br/>curl -X POST http://localhost:8000/api/tasks \<br/>  -H "Content-Type: application/json" \<br/>  -d '{"name": "test", "command": "nvidia-smi"}'</code>
```

## 📊 监控面板

访问 `http://localhost:8000` 查看 Web UI，可以实时看到：

- GPU 利用率图表
- 显存使用情况
- 任务队列状态
- 系统资源汇总

## 🐛 常见问题

### Q: GPU 未被识别？

```
<code># 检查 NVIDIA 驱动<br/>nvidia-smi<br/><br/># 确认 CUDA 版本<br/>nvcc --version</code>
```

### Q: 如何设置默认 GPU？

```
<code># config.yaml<br/>default_gpu: 0</code>
```

### Q: 任务超时如何处理？

```
<code>scheduler.submit_task(<br/>    name="long_task",<br/>    timeout_seconds=7200,  # 2小时<br/>    retry_on_failure=True<br/>)</code>
```

## 📚 相关资源

- 官方文档: [https://gpustack.readthedocs.io](https://gpustack.readthedocs.io)
- GitHub: [https://github.com/gpustack/gpustack](https://github.com/gpustack/gpustack)
- 社区论坛: [https://discuss.gpustack.io](https://discuss.gpustack.io)