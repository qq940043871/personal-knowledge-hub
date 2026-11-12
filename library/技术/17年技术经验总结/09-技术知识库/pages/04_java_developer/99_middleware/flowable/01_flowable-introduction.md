# Flowable 概述

## 什么是 Flowable

### Flowable 的历史背景

Flowable 是一个轻量级的、开源的、基于 Java 的业务流程管理（BPM）和工作流引擎。它由 Activiti 5.x 的原班团队于 2016 年 10 月创建，旨在提供一个更加现代化、高性能和易于使用的工作流解决方案。

### Flowable 与 Activiti 的关系

- **历史渊源**：Flowable 是 Activiti 5.x 的一个分支，由 Tijs Rademakers 和 Joram Barrez 等核心开发人员创建
- **技术演进**：Flowable 在 Activiti 5.x 的基础上进行了重大改进和重构
- **兼容性**：Flowable 与 Activiti 5.x 的流程定义和 API 保持高度兼容

### Flowable 的核心优势

1. **轻量级设计**：核心引擎体积小，依赖少，易于集成
2. **高性能**：优化的数据库操作和缓存机制，支持高并发场景
3. **模块化架构**：各个功能模块独立，可以按需使用
4. **丰富的 API**：提供全面的 Java API 和 REST API
5. **活跃的社区**：拥有活跃的开发者社区和持续的更新维护

## Flowable 的特点

### 轻量级、高性能

- 核心引擎 JAR 包大小仅几兆字节
- 启动速度快，内存占用低
- 优化的数据库查询和事务管理
- 支持批量操作和异步执行

### 支持 BPMN 2.0 标准

- 完全支持 BPMN 2.0 规范
- 支持所有标准 BPMN 元素
- 提供可视化流程设计器
- 支持流程版本管理

### 灵活的扩展性

- 支持自定义服务任务
- 支持自定义监听器
- 支持自定义表达式
- 支持自定义表单类型

### 丰富的 API 接口

Flowable 对外提供 8 大核心 Service，覆盖从部署、运行到历史查询的完整生命周期：

- RepositoryService：流程定义和部署管理
- RuntimeService：流程实例和执行管理
- TaskService：任务管理
- HistoryService：历史数据查询
- IdentityService：用户和组管理
- ManagementService：引擎管理和作业管理
- FormService：表单管理
- DynamicBpmnService：动态流程修改

*图：Flowable 八大核心服务与引擎的关系（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 300" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="200" y="14" width="320" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="39" text-anchor="middle" font-size="14" fill="#1e293b">统一接入：Java API / REST API</text>
  <line x1="360" y1="54" x2="360" y2="76" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="30" y="80" width="660" height="136" rx="10" fill="none" stroke="#94a3b8" stroke-width="1.2" stroke-dasharray="4 4"/>
  <text x="46" y="100" font-size="13" fill="#475569">核心服务层（8 大 Service）</text>
  <rect x="47" y="108" width="146" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="120" y="125" text-anchor="middle" font-size="13" fill="#1e293b">RepositoryService</text>
  <text x="120" y="141" text-anchor="middle" font-size="12" fill="#475569">流程定义与部署管理</text>
  <rect x="207" y="108" width="146" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="280" y="125" text-anchor="middle" font-size="13" fill="#1e293b">RuntimeService</text>
  <text x="280" y="141" text-anchor="middle" font-size="12" fill="#475569">流程实例与执行管理</text>
  <rect x="367" y="108" width="146" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="440" y="125" text-anchor="middle" font-size="13" fill="#1e293b">TaskService</text>
  <text x="440" y="141" text-anchor="middle" font-size="12" fill="#475569">任务管理</text>
  <rect x="527" y="108" width="146" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="600" y="125" text-anchor="middle" font-size="13" fill="#1e293b">HistoryService</text>
  <text x="600" y="141" text-anchor="middle" font-size="12" fill="#475569">历史数据查询</text>
  <rect x="47" y="164" width="146" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="120" y="181" text-anchor="middle" font-size="13" fill="#1e293b">IdentityService</text>
  <text x="120" y="197" text-anchor="middle" font-size="12" fill="#475569">用户与组管理</text>
  <rect x="207" y="164" width="146" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="280" y="181" text-anchor="middle" font-size="13" fill="#1e293b">ManagementService</text>
  <text x="280" y="197" text-anchor="middle" font-size="12" fill="#475569">引擎与作业管理</text>
  <rect x="367" y="164" width="146" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="440" y="181" text-anchor="middle" font-size="13" fill="#1e293b">FormService</text>
  <text x="440" y="197" text-anchor="middle" font-size="12" fill="#475569">表单管理</text>
  <rect x="527" y="164" width="146" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="600" y="181" text-anchor="middle" font-size="13" fill="#1e293b">DynamicBpmnService</text>
  <text x="600" y="197" text-anchor="middle" font-size="12" fill="#475569">动态流程修改</text>
  <line x1="360" y1="216" x2="360" y2="238" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="220" y="240" width="280" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="360" y="267" text-anchor="middle" font-size="14" fill="#1e293b">Flowable 引擎（BPMN 2.0 执行核心）</text>
</svg>

## 适用场景

### 审批流程

- 请假审批
- 报销审批
- 合同审批
- 采购审批
- 项目审批

### 订单处理

- 电商订单处理
- 金融订单处理
- 物流订单处理
- 服务订单处理

### 工作流编排

- 数据处理流程
- 文件处理流程
- 批量任务处理
- 多系统协作流程

### 业务流程管理

- 客户服务流程
- 生产制造流程
- 人力资源流程
- 财务管理流程

## Flowable 与其他工作流引擎对比

| 特性 | Flowable | Activiti | Camunda | JBPM |
|------|----------|----------|---------|------|
| 轻量级 | 是 | 是 | 否 | 否 |
| BPMN 2.0 支持 | 完整 | 完整 | 完整 | 部分 |
| 性能 | 高 | 中 | 中 | 低 |
| 易用性 | 高 | 中 | 中 | 低 |
| 社区活跃 | 高 | 中 | 高 | 低 |
| 文档完善 | 高 | 中 | 高 | 中 |

## 总结：Flowable 的定位与优势

Flowable 是一个功能强大、性能优异、易于使用的工作流引擎，**特别适合需要与 Java 业务系统深度集成的场景**。它的轻量级设计和丰富的 API 使其能够灵活地适应各种业务流程需求。
