# Skill执行

> 模块：Skill系统
> 更新时间：2026-03-29

---

Skill 执行的核心是两个组件：**SkillExecutor** 负责执行流程（参数验证、构建上下文、带超时执行），**PermissionGuard** 负责权限控制。

## 一、执行流程

> `SkillExecutor.execute` 按三步执行单个 Skill：**参数验证 → 构建上下文 → 带超时执行**，执行结果写入 `execution_history`，超时则返回失败结果。

*图：Skill 执行流程（示意）*

```html
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 350" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="250" y="20" width="220" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="47" text-anchor="middle" font-size="14" fill="#1e293b">接收执行请求</text>
  <line x1="360" y1="64" x2="360" y2="80" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="250" y="84" width="220" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="111" text-anchor="middle" font-size="14" fill="#1e293b">1. 参数验证</text>
  <text x="575" y="111" text-anchor="middle" font-size="13" fill="#475569">缺必填参数则抛 ValueError</text>
  <line x1="360" y1="128" x2="360" y2="144" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="250" y="148" width="220" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="175" text-anchor="middle" font-size="14" fill="#1e293b">2. 构建 SkillContext</text>
  <line x1="360" y1="192" x2="360" y2="208" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="250" y="212" width="220" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="239" text-anchor="middle" font-size="14" fill="#1e293b">3. 带超时执行 wait_for</text>
  <line x1="360" y1="256" x2="240" y2="276" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="360" y1="256" x2="480" y2="276" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="130" y="278" width="220" height="52" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="240" y="299" text-anchor="middle" font-size="14" fill="#1e293b">执行成功</text>
  <text x="240" y="317" text-anchor="middle" font-size="13" fill="#1e293b">记录 execution_history 并返回</text>
  <rect x="370" y="278" width="220" height="52" rx="8" fill="#fef2f2" stroke="#dc2626" stroke-width="1.5"/>
  <text x="480" y="299" text-anchor="middle" font-size="14" fill="#1e293b">执行超时</text>
  <text x="480" y="317" text-anchor="middle" font-size="13" fill="#1e293b">SkillResult(success=False)</text>
</svg>
```

```python
class SkillExecutor:
    """Skill执行器"""
    
    def __init__(self, skill_manager: SkillManager, 
                 timeout: float = 30.0):
        self.skill_manager = skill_manager
        self.timeout = timeout
        self.execution_history = []
    
    async def execute(self, skill_name: str, 
                    parameters: Dict,
                    context: Dict) -> SkillResult:
        """执行单个Skill"""
        
        # 1. 参数验证
        skill = self.skill_manager.get_skill(skill_name)
        validated_params = self.validate_parameters(skill, parameters)
        
        # 2. 构建上下文
        skill_context = SkillContext(
            user_id=context.get("user_id"),
            session_id=context.get("session_id"),
            messages=context.get("messages", []),
            parameters=validated_params,
            metadata=context.get("metadata", {})
        )
        
        # 3. 执行（带超时）
        try:
            result = await asyncio.wait_for(
                self.skill_manager.execute(skill_name, skill_context),
                timeout=self.timeout
            )
            
            self.execution_history.append({
                "skill": skill_name,
                "params": validated_params,
                "success": result.success,
                "duration": result.metadata.get("duration", 0)
            })
            
            return result
            
        except asyncio.TimeoutError:
            return SkillResult(
                success=False,
                error=f"Skill execution timeout after {self.timeout}s"
            )
    
    def validate_parameters(self, skill: Skill, parameters: Dict) -> Dict:
        """参数验证"""
        schema = skill.get_parameters()
        validated = {}
        
        for param in schema:
            name = param["name"]
            required = param.get("required", False)
            
            if name in parameters:
                validated[name] = parameters[name]
            elif "default" in param:
                validated[name] = param["default"]
            elif required:
                raise ValueError(f"Missing required parameter: {name}")
        
        return validated
```

---

## 二、权限控制

> `PermissionGuard` 按 `PermissionLevel` 数值比较权限：**用户级（1）／管理员级（2）／系统级（3）**，用户级别低于 Skill 所需级别时抛出 `PermissionError`。

```python
class PermissionLevel(Enum):
    USER = 1      # 用户级
    ADMIN = 2       # 管理员级
    SYSTEM = 3      # 系统级

class PermissionGuard:
    """权限守卫"""
    
    @staticmethod
    def check_permission(user_level: PermissionLevel, 
                         skill_level: PermissionLevel) -> bool:
        return user_level.value >= skill_level.value
    
    def require_permission(self, required_level: PermissionLevel):
        def decorator(func):
            @wraps(func)
            async def wrapper(self, context, *args, **kwargs):
                if not self.check_permission(context.user_level, required_level):
                    raise PermissionError(
                        f"Permission denied: requires level {required_level}"
                    )
                return await func(self, context, *args, **kwargs)
            return wrapper
        return decorator
```

---

*下一步：MCP协议概述*
