# Java 如何通过 DSL 语言实现合同流程编排

在Java中通过DSL实现合同流程编排，可结合**内部DSL**（基于Java语法）和**工作流引擎**的思想，设计一套声明式的合同流程描述语言。下面介绍具体实现方案：

## 一、设计合同流程DSL的核心概念
合同流程通常包含：

+ **节点**：流程中的步骤（如合同起草、审批、签署、归档）
+ **流转规则**：节点间的跳转条件（如“审批通过→签署”）
+ **数据上下文**：流程中传递的数据（如合同金额、签署日期）
+ **参与者**：执行节点的角色或用户

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 420" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="350" y="40" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">合同流程 DSL 核心概念</text>
  <rect x="265" y="184" width="170" height="52" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="350" y="215" text-anchor="middle" font-size="13" fill="#1e293b">合同流程 DSL</text>
  <rect x="30" y="96" width="210" height="52" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="135" y="118" text-anchor="middle" font-size="13" fill="#1e293b">节点：流程步骤</text>
  <text x="135" y="138" text-anchor="middle" font-size="12" fill="#475569">起草·审批·签署·归档</text>
  <rect x="30" y="272" width="210" height="52" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="135" y="294" text-anchor="middle" font-size="13" fill="#1e293b">参与者：执行角色</text>
  <text x="135" y="314" text-anchor="middle" font-size="12" fill="#475569">执行节点的角色或用户</text>
  <rect x="460" y="96" width="210" height="52" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="565" y="118" text-anchor="middle" font-size="13" fill="#1e293b">流转规则：跳转条件</text>
  <text x="565" y="138" text-anchor="middle" font-size="12" fill="#475569">如：审批通过 → 签署</text>
  <rect x="460" y="272" width="210" height="52" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="565" y="294" text-anchor="middle" font-size="13" fill="#1e293b">数据上下文：传递数据</text>
  <text x="565" y="314" text-anchor="middle" font-size="12" fill="#475569">合同金额·签署日期</text>
  <line x1="265" y1="200" x2="244" y2="126" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <line x1="265" y1="220" x2="244" y2="294" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <line x1="435" y1="200" x2="456" y2="126" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <line x1="435" y1="220" x2="456" y2="294" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
</svg>

*图：合同流程 DSL 四类核心概念示意（依正文整理）*

## 二、基于Java的内部DSL实现
### 1. 定义核心模型
```java
// 合同流程模型
public class ContractProcess {
    private String id;
    private String name;
    private List<Node> nodes = new ArrayList<>();
    private Map<String, Transition> transitions = new HashMap<>();
    
    // 流程构建器（DSL入口）
    public static ContractProcessBuilder define(String id, String name) {
        return new ContractProcessBuilder(id, name);
    }
    
    // 执行流程
    public void execute(ContractContext context) {
        // 流程执行逻辑...
    }
}

// 节点模型
public class Node {
    private String id;
    private String name;
    private NodeType type;
    private Consumer<ContractContext> action;
    
    // 节点类型枚举
    public enum NodeType {
        START, END, TASK, DECISION
    }
}

// 流转规则
public class Transition {
    private String sourceNodeId;
    private String targetNodeId;
    private Predicate<ContractContext> condition;
}

// 上下文数据
public class ContractContext {
    private Map<String, Object> data = new HashMap<>();
    
    public <T> T get(String key) { return (T) data.get(key); }
    public void put(String key, Object value) { data.put(key, value); }
}
```

### 2. 构建DSL语法
使用流式API和Lambda表达式实现连贯的流程定义：

```java
public class ContractProcessBuilder {
    private final ContractProcess process;
    private Node currentNode;
    
    public ContractProcessBuilder(String id, String name) {
        this.process = new ContractProcess();
        this.process.setId(id);
        this.process.setName(name);
    }
    
    // 定义开始节点
    public ContractProcessBuilder start(String nodeId, String nodeName) {
        Node startNode = new Node();
        startNode.setId(nodeId);
        startNode.setName(nodeName);
        startNode.setType(Node.NodeType.START);
        process.getNodes().add(startNode);
        this.currentNode = startNode;
        return this;
    }
    
    // 定义任务节点
    public ContractProcessBuilder task(String nodeId, String nodeName, Consumer<ContractContext> action) {
        Node taskNode = new Node();
        taskNode.setId(nodeId);
        taskNode.setName(nodeName);
        taskNode.setType(Node.NodeType.TASK);
        taskNode.setAction(action);
        process.getNodes().add(taskNode);
        
        // 默认添加从上一节点到当前节点的流转
        addTransition(currentNode.getId(), nodeId, ctx -> true);
        this.currentNode = taskNode;
        return this;
    }
    
    // 定义决策节点
    public ContractProcessBuilder decision(String nodeId, String nodeName, 
                                          Map<Predicate<ContractContext>, String> conditions) {
        Node decisionNode = new Node();
        decisionNode.setId(nodeId);
        decisionNode.setName(nodeName);
        decisionNode.setType(Node.NodeType.DECISION);
        process.getNodes().add(decisionNode);
        
        // 添加从上一节点到决策节点的流转
        addTransition(currentNode.getId(), nodeId, ctx -> true);
        
        // 为决策节点添加多个出口流转
        conditions.forEach((condition, targetNodeId) -> {
            addTransition(nodeId, targetNodeId, condition);
        });
        
        this.currentNode = decisionNode;
        return this;
    }
    
    // 定义结束节点
    public ContractProcessBuilder end(String nodeId, String nodeName) {
        Node endNode = new Node();
        endNode.setId(nodeId);
        endNode.setName(nodeName);
        endNode.setType(Node.NodeType.END);
        process.getNodes().add(endNode);
        
        // 添加从上一节点到结束节点的流转
        addTransition(currentNode.getId(), nodeId, ctx -> true);
        return this;
    }
    
    // 添加自定义流转规则
    private void addTransition(String sourceNodeId, String targetNodeId, 
                              Predicate<ContractContext> condition) {
        Transition transition = new Transition();
        transition.setSourceNodeId(sourceNodeId);
        transition.setTargetNodeId(targetNodeId);
        transition.setCondition(condition);
        process.getTransitions().put(sourceNodeId + "->" + targetNodeId, transition);
    }
    
    // 构建流程
    public ContractProcess build() {
        return process;
    }
}
```

### 3. 使用DSL定义合同流程
```java
public class ContractProcessExample {
    public static void main(String[] args) {
        // 定义合同审批流程
        ContractProcess process = ContractProcess.define("contractApproval", "合同审批流程")
            .start("start", "开始")
            .task("draft", "合同起草", ctx -> {
                System.out.println("起草合同...");
                ctx.put("contractAmount", 100000); // 设置合同金额
                ctx.put("contractType", "销售合同");
            })
            .task("deptManagerApproval", "部门经理审批", ctx -> {
                System.out.println("部门经理审批合同...");
                boolean approved = (Integer) ctx.get("contractAmount") < 200000;
                ctx.put("deptApproved", approved);
            })
            .decision("approvalDecision", "审批决策", Map.of(
                ctx -> (Boolean) ctx.get("deptApproved"), "legalReview",
                ctx -> !(Boolean) ctx.get("deptApproved"), "reject"
            ))
            .task("legalReview", "法务审核", ctx -> {
                System.out.println("法务审核合同...");
                ctx.put("legalApproved", true);
            })
            .task("sign", "合同签署", ctx -> {
                System.out.println("签署合同...");
                ctx.put("signed", true);
            })
            .task("reject", "合同驳回", ctx -> {
                System.out.println("合同已驳回");
                ctx.put("rejected", true);
            })
            .end("end", "结束")
            .build();
        
        // 执行流程
        ContractContext context = new ContractContext();
        process.execute(context);
    }
}
```

## 三、扩展功能
### 1. 持久化流程定义
将DSL定义的流程保存为JSON/XML，便于存储和复用：

```java
public class ProcessSerializer {
    public static String toJson(ContractProcess process) {
        // 使用Jackson/Gson将流程对象转换为JSON
        // ...
        return jsonString;
    }
    
    public static ContractProcess fromJson(String json) {
        // 从JSON恢复流程对象
        // ...
        return process;
    }
}
```

### 2. 集成外部系统
在节点中调用外部服务（如审批系统、电子签系统）：

```java
.task("electronicSign", "电子签署", ctx -> {
    // 调用电子签API
    ElectronicSignService.sign(
        ctx.get("contractId"), 
        ctx.get("signerId")
    );
    ctx.put("signed", true);
})
```

### 3. 添加监听器
监听流程事件（如节点完成、流转发生）：

```java
public class ProcessListener {
    public void onNodeCompleted(String nodeId, ContractContext ctx) {
        System.out.println("节点[" + nodeId + "]已完成");
    }
    
    public void onTransition(String fromNodeId, String toNodeId, ContractContext ctx) {
        System.out.println("从节点[" + fromNodeId + "]流转到[" + toNodeId + "]");
    }
}
```

## 四、实际应用建议
1. **使用成熟工作流引擎**：若需求复杂，可集成Activiti/Camunda，通过Java API操作。
2. **数据库存储流程实例**：用关系型数据库跟踪每个合同的流程状态。
3. **可视化流程设计器**：结合前端工具（如bpmn-js）提供图形化流程设计界面。
4. **权限控制**：在节点执行前校验用户权限，确保只有授权用户可操作。

## 五、开源库推荐
1. **Flowable**：轻量级工作流引擎，提供Java API和BPMN 2.0支持。
2. **Easy Rules**：简单的规则引擎，可用于流转条件判断。
3. **Camunda**：企业级工作流平台，支持可视化设计和复杂流程。

通过这种方式，你可以在Java中实现灵活、可扩展的合同流程编排DSL，让非技术人员也能理解和维护流程逻辑。
