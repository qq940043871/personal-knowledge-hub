# SpringDataJPA详解

> 模块：数据访问框架
> 更新时间：2026-03-29

---

## 一、框架介绍

Spring Data JPA是Spring Data系列的一部分，对JPA（Java Persistence API）进行了封装，提供 Repository 抽象层。

**核心特性**：
- 自动生成CRUD方法
- 自动实现分页和排序
- 自定义查询方法命名规则
- 支持@Query自定义SQL

*图：Spring Data JPA 分层封装关系（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 180" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="20" y="60" width="150" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="95" y="87" text-anchor="middle" font-size="14" fill="#1e293b">业务代码</text>
  <line x1="170" y1="82" x2="200" y2="82" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="205" y="60" width="150" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="280" y="87" text-anchor="middle" font-size="14" fill="#1e293b">Repository 接口</text>
  <line x1="355" y1="82" x2="385" y2="82" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="390" y="60" width="150" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="465" y="87" text-anchor="middle" font-size="14" fill="#1e293b">Spring Data JPA</text>
  <line x1="540" y1="82" x2="570" y2="82" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="575" y="60" width="125" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="637" y="87" text-anchor="middle" font-size="14" fill="#1e293b">数据库（JPA）</text>
  <text x="360" y="150" text-anchor="middle" font-size="13" fill="#475569">Repository 抽象层封装 JPA，自动生成 CRUD 与分页排序</text>
</svg>

---

## 二、实际业务应用场景

### 场景1：Repository定义

```java
// 1. 定义Repository
public interface UserRepository extends JpaRepository<User, Long> {
    
    // 方法命名查询 - 自动实现
    Optional<User> findByUsername(String username);
    
    List<User> findByEmailContaining(String email);
    
    List<User> findByAgeBetween(Integer minAge, Integer maxAge);
    
    @Query("SELECT u FROM User u WHERE u.status = :status ORDER BY u.createTime DESC")
    List<User> findByStatus(@Param("status") Integer status);
    
    @Query(value = "SELECT * FROM t_user WHERE age > :age LIMIT :limit", 
           nativeQuery = true)
    List<User> findByAgeLimit(@Param("age") Integer age, @Param("limit") Integer limit);
}

// 2. 分页查询
@Service
public class UserService {
    
    @Autowired
    private UserRepository userRepository;
    
    public Page<User> getUserPage(Integer page, Integer size, String keyword) {
        Pageable pageable = PageRequest.of(page - 1, size, 
            Sort.by(Sort.Direction.DESC, "createTime"));
        
        if (StringUtils.hasText(keyword)) {
            return userRepository.findByEmailContaining(keyword, pageable);
        }
        
        return userRepository.findAll(pageable);
    }
}
```

### 场景2：复杂查询Specification

```java
public Specification<User> buildSpecification(UserQuery query) {
    return (root, criteriaQuery, criteriaBuilder) -> {
        List<Predicate> predicates = new ArrayList<>();
        
        if (StringUtils.hasText(query.getName())) {
            predicates.add(criteriaBuilder.like(root.get("name"), 
                "%" + query.getName() + "%"));
        }
        
        if (query.getMinAge() != null) {
            predicates.add(criteriaBuilder.ge(root.get("age"), query.getMinAge()));
        }
        
        if (query.getStatus() != null) {
            predicates.add(criteriaBuilder.equal(root.get("status"), query.getStatus()));
        }
        
        return criteriaBuilder.and(predicates.toArray(new Predicate[0]));
    };
}

public List<User> searchUsers(UserQuery query) {
    Specification<User> spec = buildSpecification(query);
    return userRepository.findAll(spec);
}
```

---

## 三、总结与选型对比

**Spring Data JPA适合快速开发**，但**MyBatis在复杂业务场景下更灵活**。

---

*下一步：Hibernate ORM*
