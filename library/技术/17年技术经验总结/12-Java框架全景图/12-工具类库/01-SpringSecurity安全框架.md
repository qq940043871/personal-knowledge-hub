# Spring Security

> 模块：安全框架
> 更新时间：2026-03-29

---

## 一、框架介绍

**Spring Security是Spring生态中最专业的安全框架**，提供了**认证（Authentication）和授权（Authorization）两大核心功能**，支持OAuth2、JWT等现代认证协议。

**官网**：[https://spring.io/projects/spring-security](https://spring.io/projects/spring-security)

**核心功能**：
- 用户认证（用户名密码、OAuth、JWT）
- 权限授权（基于角色、基于资源）
- CSRF防护
- Session管理
- 密码加密

---

## 二、快速开始

### 1. Maven依赖

```xml
<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-security</artifactId>
    </dependency>
</dependencies>
```

### 2. 基础配置

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf.disable())  // 前后端分离项目通常关闭CSRF
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/public/**", "/login").permitAll()
                .requestMatchers("/admin/**").hasRole("ADMIN")
                .requestMatchers("/user/**").hasAnyRole("USER", "ADMIN")
                .anyRequest().authenticated()
            )
            .formLogin(form -> form
                .loginProcessingUrl("/login")
                .successHandler((request, response, authentication) -> {
                    response.getWriter().write("登录成功");
                })
                .failureHandler((request, response, exception) -> {
                    response.getWriter().write("登录失败");
                })
            )
            .logout(logout -> logout
                .logoutUrl("/logout")
                .logoutSuccessHandler((request, response, authentication) -> {
                    response.getWriter().write("退出成功");
                })
            )
            .sessionManagement(session -> session
                .maximumSessions(1)  // 最大会话数
            );
        
        return http.build();
    }
    
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
```

---

## 三、实际业务应用场景

### 场景1：JWT认证

```java
// 1. JWT工具类
@Component
public class JwtUtils {
    
    @Value("${jwt.secret}")
    private String secret;
    
    @Value("${jwt.expiration}")
    private Long expiration;
    
    public String generateToken(UserDetails user) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("roles", user.getAuthorities().stream()
            .map(GrantedAuthority::getAuthority)
            .collect(Collectors.toList()));
        
        return Jwts.builder()
            .claims(claims)
            .subject(user.getUsername())
            .issuedAt(new Date())
            .expiration(new Date(System.currentTimeMillis() + expiration))
            .signWith(Keys.hmacShaKeyFor(secret.getBytes()))
            .compact();
    }
    
    public String getUsernameFromToken(String token) {
        return Jwts.parser()
            .verifyWith(Keys.hmacShaKeyFor(secret.getBytes()))
            .build()
            .parseSignedClaims(token)
            .getPayload()
            .getSubject();
    }
    
    public boolean validateToken(String token) {
        try {
            Jwts.parser()
                .verifyWith(Keys.hmacShaKeyFor(secret.getBytes()))
                .build()
                .parseSignedClaims(token);
            return true;
        } catch (JwtException e) {
            return false;
        }
    }
}

// 2. JWT认证过滤器
@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {
    
    @Autowired
    private JwtUtils jwtUtils;
    
    @Autowired
    private UserDetailsService userDetailsService;
    
    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                   HttpServletResponse response,
                                   FilterChain chain) throws Exception {
        String token = request.getHeader("Authorization");
        
        if (token != null && token.startsWith("Bearer ")) {
            token = token.substring(7);
            
            if (jwtUtils.validateToken(token)) {
                String username = jwtUtils.getUsernameFromToken(token);
                UserDetails userDetails = userDetailsService.loadUserByUsername(username);
                
                UsernamePasswordAuthenticationToken authentication =
                    new UsernamePasswordAuthenticationToken(
                        userDetails, null, userDetails.getAuthorities());
                authentication.setDetails(
                    new WebAuthenticationDetailsSource().buildDetails(request));
                
                SecurityContextHolder.getContext().setAuthentication(authentication);
            }
        }
        
        chain.doFilter(request, response);
    }
}

// 3. 配置JWT过滤器
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    
    @Autowired
    private JwtAuthenticationFilter jwtFilter;
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf.disable())
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/auth/**", "/public/**").permitAll()
                .anyRequest().authenticated()
            )
            .addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class);
        
        return http.build();
    }
}
```

*图：JWT 认证过滤器处理流程（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 350" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="230" y="20" width="260" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="38" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">客户端请求</text>
  <text x="360" y="56" text-anchor="middle" font-size="12" fill="#475569">Authorization: Bearer token</text>
  <line x1="360" y1="64" x2="360" y2="84" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="230" y="88" width="260" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="106" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">JwtAuthenticationFilter</text>
  <text x="360" y="124" text-anchor="middle" font-size="12" fill="#475569">doFilterInternal 拦截</text>
  <line x1="360" y1="132" x2="360" y2="152" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="230" y="156" width="260" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="174" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">validateToken 校验</text>
  <text x="360" y="192" text-anchor="middle" font-size="12" fill="#475569">解析并校验 token</text>
  <line x1="490" y1="178" x2="503" y2="178" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="505" y="156" width="185" height="44" rx="8" fill="#fef2f2" stroke="#dc2626" stroke-width="1.5"/>
  <text x="597" y="174" text-anchor="middle" font-size="13" fill="#1e293b">校验失败</text>
  <text x="597" y="192" text-anchor="middle" font-size="12" fill="#475569">不设置认证信息</text>
  <line x1="360" y1="200" x2="360" y2="220" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="230" y="224" width="260" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="242" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">SecurityContextHolder</text>
  <text x="360" y="260" text-anchor="middle" font-size="12" fill="#475569">写入 Authentication</text>
  <line x1="360" y1="268" x2="360" y2="288" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="230" y="292" width="260" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="360" y="310" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e293b">chain.doFilter 放行</text>
  <text x="360" y="328" text-anchor="middle" font-size="12" fill="#475569">到达业务接口</text>
</svg>

### 场景2：基于注解的权限控制

```java
// 1. 启用方法级安全
@Configuration
@EnableMethodSecurity
public class SecurityConfig {
}

// 2. 使用权限注解
@RestController
@RequestMapping("/api/users")
public class UserController {
    
    // 只需要认证，不需要特定权限
    @GetMapping("/{id}")
    @PreAuthorize("isAuthenticated()")
    public User getUser(@PathVariable Long id) {
        return userService.getById(id);
    }
    
    // 需要ADMIN角色
    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public Result<Void> deleteUser(@PathVariable Long id) {
        userService.deleteById(id);
        return Result.success();
    }
    
    // 需要特定权限
    @PostMapping
    @PreAuthorize("hasAuthority('USER_CREATE')")
    public Result<Long> createUser(@RequestBody User user) {
        return Result.success(userService.save(user));
    }
    
    // 自定义权限表达式
    @GetMapping("/info")
    @PreAuthorize("@userService.isOwner(#id)")
    public User getUserInfo(@PathVariable Long id) {
        return userService.getById(id);
    }
}

// 3. 自定义权限表达式
@Service("userService")
public class UserServiceImpl implements UserService {
    
    public boolean isOwner(Long userId) {
        UserDetails userDetails = 
            (UserDetails) SecurityContextHolder.getContext()
                .getAuthentication().getPrincipal();
        return userDetails.getUsername().equals(userId.toString());
    }
}
```

### 场景3：OAuth2登录

```java
// 1. 配置OAuth2登录
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .oauth2Login(oauth2 -> oauth2
                .loginPage("/login/oauth2")
                .authorizationEndpoint(authorization -> 
                    authorization.baseUri("/oauth2/authorization"))
                .redirectionEndpoint(redirection -> 
                    redirection.baseUri("/login/oauth2/code/*"))
                .defaultSuccessUrl("/loginSuccess")
            );
        
        return http.build();
    }
}

// 2. 自定义OAuth2用户信息
@Service
public class CustomOAuth2UserService extends DefaultOAuth2UserService {
    
    @Autowired
    private UserService userService;
    
    @Override
    public OAuth2User loadUser(OAuth2UserRequest request) throws OAuth2AuthenticationException {
        OAuth2User oauth2User = super.loadUser(request);
        
        // 获取第三方用户信息
        String provider = request.getClientRegistration().getRegistrationId();
        String providerId = oauth2User.getName();
        String email = oauth2User.getAttribute("email");
        String nickname = oauth2User.getAttribute("name");
        
        // 查找或创建用户
        User user = userService.findOrCreateByOAuth(provider, providerId, email, nickname);
        
        return new CustomOAuth2User(oauth2User, user);
    }
}
```

---

## 四、密码加密

```java
@Service
public class PasswordService {
    
    @Autowired
    private PasswordEncoder passwordEncoder;
    
    // 加密密码
    public String encodePassword(String rawPassword) {
        return passwordEncoder.encode(rawPassword);
    }
    
    // 验证密码
    public boolean matches(String rawPassword, String encodedPassword) {
        return passwordEncoder.matches(rawPassword, encodedPassword);
    }
}

// 注册时加密
@Service
public class UserService {
    
    @Autowired
    private PasswordEncoder passwordEncoder;
    
    public Long register(RegisterRequest request) {
        User user = new User();
        user.setUsername(request.getUsername());
        user.setPassword(passwordEncoder.encode(request.getPassword()));
        
        return userMapper.insert(user);
    }
}
```

---

## 五、总结与学习要点

**Spring Security是Java安全认证的标准解决方案**，配合JWT可以实现完整的认证授权系统。

**学习要点**：
1. 理解认证和授权的区别
2. 掌握Spring Security配置
3. 熟练使用JWT实现无状态认证
4. 理解OAuth2协议
5. 掌握基于注解的权限控制

---

*下一步：Elasticsearch搜索引擎*
