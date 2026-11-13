# Skill架构

> 模块：Skill系统
> 更新时间：2026-03-29

## Skill 定义：基类、SkillContext 与 SkillResult

> Skill 基类持有 name、description、version、**enabled 开关**与 **permission_level**；`execute()` 由子类实现，`get_schema()` 返回 OpenAPI schema；SkillContext 携带 user_id、session_id、messages、parameters、metadata，SkillResult 用 success + output/error 表达结果。

```python
class Skill:
    """Skill基类"""
    
    def __init__(self, name: str, description: str, version: str = "1.0.0"):
        self.name = name
        self.description = description
        self.version = version
        self.enabled = True
        self.permission_level = PermissionLevel.USER
    
    async def execute(self, context: SkillContext) -> SkillResult:
        """执行Skill"""
        raise NotImplementedError
    
    def get_schema(self) -> Dict:
        """返回OpenAPI schema"""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "parameters": self.get_parameters()
        }
    
    def get_parameters(self) -> Dict:
        """返回参数定义"""
        return {}


@dataclass
class SkillContext:
    """Skill执行上下文"""
    user_id: str
    session_id: str
    messages: List[Dict]
    parameters: Dict
    metadata: Dict


@dataclass
class SkillResult:
    """Skill执行结果"""
    success: bool
    output: Any = None
    error: str = None
    metadata: Dict = None
```

## Skill 管理器：注册查重与带守卫的执行链路

> 注册时**重名抛 ValueError**；执行时**未找到、未启用、抛异常**三种情况都返回 `SkillResult(success=False, error=...)`。

*图：SkillManager 执行链路的守卫检查（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 210" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="15" y="30" width="165" height="64" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="97" y="57" text-anchor="middle" font-size="14" font-weight="bold" fill="#1e293b">查找 Skill</text>
  <text x="97" y="79" text-anchor="middle" font-size="12" fill="#475569">skills.get(skill_name)</text>
  <line x1="180" y1="62" x2="188" y2="62" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="190" y="30" width="165" height="64" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="272" y="57" text-anchor="middle" font-size="14" font-weight="bold" fill="#1e293b">检查 enabled</text>
  <text x="272" y="79" text-anchor="middle" font-size="12" fill="#475569">未启用则失败返回</text>
  <line x1="355" y1="62" x2="363" y2="62" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="365" y="30" width="165" height="64" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="447" y="57" text-anchor="middle" font-size="14" font-weight="bold" fill="#1e293b">执行 Skill</text>
  <text x="447" y="79" text-anchor="middle" font-size="12" fill="#475569">await skill.execute(...)</text>
  <line x1="530" y1="62" x2="538" y2="62" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="540" y="30" width="165" height="64" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="622" y="57" text-anchor="middle" font-size="14" font-weight="bold" fill="#1e293b">返回 SkillResult</text>
  <text x="622" y="79" text-anchor="middle" font-size="12" fill="#475569">success / output / error</text>
  <line x1="97" y1="94" x2="97" y2="128" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="5,4" marker-end="url(#arw)"/>
  <line x1="272" y1="94" x2="272" y2="128" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="5,4" marker-end="url(#arw)"/>
  <line x1="447" y1="94" x2="447" y2="128" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="5,4" marker-end="url(#arw)"/>
  <rect x="95" y="130" width="530" height="48" rx="8" fill="#fef2f2" stroke="#dc2626" stroke-width="1.5"/>
  <text x="360" y="159" text-anchor="middle" font-size="13" fill="#1e293b">未找到 / 未启用 / 抛出异常 → SkillResult(success=False, error=...)</text>
</svg>

```python
class SkillManager:
    """Skill管理器"""
    
    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self.registries: List[SkillRegistry] = []
    
    def register(self, skill: Skill):
        """注册Skill"""
        if skill.name in self.skills:
            raise ValueError(f"Skill {skill.name} already registered")
        self.skills[skill.name] = skill
    
    async def execute(self, skill_name: str, context: SkillContext) -> SkillResult:
        """执行Skill"""
        skill = self.skills.get(skill_name)
        if not skill:
            return SkillResult(success=False, error=f"Skill {skill_name} not found")
        
        if not skill.enabled:
            return SkillResult(success=False, error=f"Skill {skill_name} is disabled")
        
        try:
            result = await skill.execute(context)
            return result
        except Exception as e:
            return SkillResult(success=False, error=str(e))
    
    def get_skill(self, name: str) -> Skill:
        return self.skills.get(name)
    
    def list_skills(self) -> List[Dict]:
        return [
            {
                "name": s.name,
                "description": s.description,
                "version": s.version,
                "enabled": s.enabled
            }
            for s in self.skills.values()
        ]
```

*下一步：Skill注册*
