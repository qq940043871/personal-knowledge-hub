# ECS架构

> 模块：实体组件系统
> 更新时间：2026-03-29

---

## 一、ECS概述

```
ECS三要素：
  1. Entity（实体）
     - 唯一ID
     - 无数据，只有组件容器
     
  2. Component（组件）
     - 数据容器
     - 无逻辑
     
  3. System（系统）
     - 处理逻辑
     - 操作特定组件组合

优势：
  - 数据局部性好，缓存友好
  - 组合优于继承
  - 并行处理简单
```

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 390" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="360" y="32" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">ECS三要素</text>
  <rect x="275" y="70" width="170" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="103" text-anchor="middle" font-size="14" fill="#1e293b">ECS架构</text>
  <path d="M360,126 V160 H130 V196" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <path d="M360,126 V196" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <path d="M360,126 V160 H610 V196" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="30" y="200" width="200" height="80" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="130" y="230" text-anchor="middle" font-size="13" fill="#1e293b">Entity 实体</text>
  <text x="130" y="252" text-anchor="middle" font-size="12" fill="#475569">唯一ID·组件容器</text>
  <rect x="260" y="200" width="200" height="80" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="360" y="230" text-anchor="middle" font-size="13" fill="#1e293b">Component 组件</text>
  <text x="360" y="252" text-anchor="middle" font-size="12" fill="#475569">纯数据·无逻辑</text>
  <rect x="490" y="200" width="200" height="80" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="610" y="230" text-anchor="middle" font-size="13" fill="#1e293b">System 系统</text>
  <text x="610" y="252" text-anchor="middle" font-size="12" fill="#475569">处理逻辑·操作组件组合</text>
  <text x="360" y="330" text-anchor="middle" font-size="13" fill="#475569">组合优于继承，缓存友好，易并行</text>
  <text x="360" y="356" text-anchor="middle" font-size="13" fill="#475569">System遍历组件数组批量处理</text>
</svg>

*图：ECS三要素关系示意（依正文整理）*

---

## 二、C++实现

```cpp
// 实体：只是一个ID
using Entity = uint32_t;
const Entity INVALID_ENTITY = 0;

// 组件基类
struct IComponent {
    virtual ~IComponent() = default;
    static ComponentType getStaticType() { return -1; }
};

// 实体管理器
class EntityManager {
private:
    std::vector<Entity> entities;
    std::queue<Entity> available;
    size_t entityCount = 0;
    
public:
    Entity create() {
        if (!available.empty()) {
            Entity e = available.front();
            available.pop();
            return e;
        }
        return ++entityCount;
    }
    
    void destroy(Entity e) {
        available.push(e);
    }
};

// 组件数组（稀疏集）
template<typename T>
class ComponentArray {
private:
    std::unordered_map<Entity, T> components;
    
public:
    void insert(Entity e, const T& component) {
        components[e] = component;
    }
    
    void remove(Entity e) {
        components.erase(e);
    }
    
    T* get(Entity e) {
        auto it = components.find(e);
        return it != components.end() ? &it->second : nullptr;
    }
    
    bool has(Entity e) {
        return components.find(e) != components.end();
    }
};
```

---

## 三、World管理器

```cpp
class ECSWorld {
private:
    EntityManager entityManager;
    
    // 所有组件数组
    ComponentArray<TransformComponent> transforms;
    ComponentArray<RenderComponent> renders;
    ComponentArray<RigidBodyComponent> rigidBodies;
    ComponentArray<ColliderComponent> colliders;
    
    // 系统列表
    std::vector<ISystem*> systems;
    
public:
    // 实体操作
    Entity createEntity() {
        return entityManager.create();
    }
    
    void destroyEntity(Entity e) {
        entityManager.destroy(e);
        transforms.remove(e);
        renders.remove(e);
        rigidBodies.remove(e);
        colliders.remove(e);
    }
    
    // 组件操作
    template<typename T>
    T* addComponent(Entity e, const T& component) {
        auto& arr = getComponentArray<T>();
        arr.insert(e, component);
        return &arr.get(e);
    }
    
    template<typename T>
    T* getComponent(Entity e) {
        return getComponentArray<T>().get(e);
    }
    
    // 系统更新
    void update(double dt) {
        for (auto* system : systems) {
            system->update(this, dt);
        }
    }
};
```

---

*下一步：实体管理*
