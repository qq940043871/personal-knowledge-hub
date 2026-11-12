# WebApp类加载器

> 模块：类加载器
> 更新时间：2026-03-29

---

## 一、Tomcat类加载器层次

```
Bootstrap
    │
    ▼
System
    │
    ▼
Common
    │
    ├──► WebApp ClassLoader (应用1)
    │         │
    │         ▼
    │      WebApp/WEB-INF/classes
    │      WebApp/WEB-INF/lib/*.jar
    │
    └──► WebApp ClassLoader (应用2)
              │
              ▼
           WebApp/WEB-INF/classes
           WebApp/WEB-INF/lib/*.jar

特点：
  - 每个WebApp有独立的ClassLoader
  - WebApp优先加载自己的类
  - 实现应用隔离
```

---

## 二、WebAppClassLoader实现：类加载的五步流程

`WebAppClassLoader` 继承 URLClassLoader，构造时把 `WEB-INF/classes` 目录与 `WEB-INF/lib` 下的 jar 加入搜索路径；loadClass 按五步走：**查缓存 → findLoadedClass → 核心类（java. / javax.servlet）委托父加载器 → 自己 findClass → 失败再委托父加载器**。

```java
public class WebAppClassLoader extends URLClassLoader {
    private File classesDir;
    private File libDir;
    private Map<String, Class<?>> cache = new ConcurrentHashMap<>();
    
    public WebAppClassLoader(ClassLoader parent, Context context) {
        super(new URL[0], parent);
        
        String docBase = context.getDocBase();
        this.classesDir = new File(docBase, "WEB-INF/classes");
        this.libDir = new File(docBase, "WEB-INF/lib");
        
        // 添加classes目录
        if (classesDir.exists()) {
            addURL(classesDir.toURI());
        }
        
        // 添加lib目录下的jar包
        if (libDir.exists()) {
            File[] jars = libDir.listFiles((dir, name) -> name.endsWith(".jar"));
            if (jars != null) {
                for (File jar : jars) {
                    addURL(jar.toURI());
                }
            }
        }
    }
    
    @Override
    protected Class<?> loadClass(String name, boolean resolve) 
        throws ClassNotFoundException {
        
        // 1. 检查缓存
        Class<?> clazz = cache.get(name);
        if (clazz != null) {
            return clazz;
        }
        
        // 2. 检查是否已加载
        clazz = findLoadedClass(name);
        if (clazz != null) {
            return clazz;
        }
        
        // 3. 核心类委托给父加载器
        if (name.startsWith("java.") || name.startsWith("javax.servlet")) {
            return super.loadClass(name, resolve);
        }
        
        // 4. 尝试自己加载
        try {
            clazz = findClass(name);
            cache.put(name, clazz);
            return clazz;
        } catch (ClassNotFoundException e) {
            // 5. 委托给父加载器
            return super.loadClass(name, resolve);
        }
    }
    
    @Override
    public URL findResource(String name) {
        // 优先从自己找
        URL url = findResource(name);
        if (url != null) {
            return url;
        }
        return super.findResource(name);
    }
}
```

*图：loadClass 的五步加载流程（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 360" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="180" y="20" width="360" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="47" text-anchor="middle" font-size="14" fill="#1e293b">1. 检查缓存：cache.get(name)</text>
  <line x1="360" y1="64" x2="360" y2="84" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="180" y="88" width="360" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="115" text-anchor="middle" font-size="14" fill="#1e293b">2. 检查是否已加载：findLoadedClass(name)</text>
  <line x1="360" y1="132" x2="360" y2="152" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="180" y="156" width="360" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="360" y="183" text-anchor="middle" font-size="14" fill="#1e293b">3. java. / javax.servlet 开头：委托父加载器</text>
  <line x1="360" y1="200" x2="360" y2="220" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="180" y="224" width="360" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="360" y="251" text-anchor="middle" font-size="14" fill="#1e293b">4. 尝试自己加载：findClass(name)</text>
  <line x1="360" y1="268" x2="360" y2="288" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="180" y="292" width="360" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="360" y="319" text-anchor="middle" font-size="14" fill="#1e293b">5. 加载失败：委托给父加载器 super.loadClass()</text>
</svg>

---

*下一步：类隔离与热部署*
