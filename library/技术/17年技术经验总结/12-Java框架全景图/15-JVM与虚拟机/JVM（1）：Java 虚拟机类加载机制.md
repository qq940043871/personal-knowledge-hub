# JVM（1）：Java 虚拟机类加载机制

> ⚠️ 本篇为为知笔记导出存档，导出时丢失了部分数字，代码不可直接复制执行，仅作思路与步骤参考。
> 2026-11-08：可按定义/上下文确定的数字已修复（标注"修复值"处，如生命周期7阶段、连接3部分、0xCAFEBABE、四条指令、5种初始化场景）；示例代码中的赋值数字无法推断，以占位标注，未编造数值。
>
> 来源：朱小厮（ImportNew），原文：blog.csdn.net/u/article/details/

## 引子

看到这个题目，很多人会觉得我写我的java代码，至于类，JVM爱怎么加载就怎么加载，博主有很长一段时间也是这么认为的。随着编程经验的日积月累，越来越感觉到了解虚拟机相关要领的重要性。闲话不多说，老规矩，先来一段代码吊吊胃口。

```java
public class SSClass
{
    static
    {
        System.out.println("SSClass");
    }
}

public class SuperClass extends SSClass
{
    static
    {
        System.out.println("SuperClass init!");
    }

    public static int value = 123; // 注：原导出数字缺失，123 仅为占位示例值，原文或不同

    public SuperClass()
    {
        System.out.println("init SuperClass");
    }
}

public class SubClass extends SuperClass
{
    static
    {
        System.out.println("SubClass init");
    }

    static int a;

    public SubClass()
    {
        System.out.println("init SubClass");
    }
}

public class NotInitialization
{
    public static void main(String[] args)
    {
        System.out.println(SubClass.value);
    }
}
```

运行结果：

```text
SSClass
SuperClass init!
```

答案答对了嚒？

也许有人会疑问：为什么没有输出SubClass init。ok~解释一下：对于静态字段，只有直接定义这个字段的类才会被初始化，因此通过其子类来引用父类中定义的静态字段，只会触发父类的初始化而不会触发子类的初始化。

上面就牵涉到了虚拟机类加载机制。如果有兴趣，可以继续看下去。

## 类加载过程

类从被加载到虚拟机内存中开始，到卸载出内存为止，它的整个生命周期包括：加载（Loading）、验证（Verification）、准备(Preparation)、解析(Resolution)、初始化(Initialization)、使用(Using)和卸载(Unloading)7个阶段（注：原导出数字缺失，按所列7个阶段修复，此处为修复值）。其中准备、验证、解析3个部分统称为连接（Linking）（注：同上，按所列3个部分修复）。如图所示。

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 620" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="320" y="34" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">类加载生命周期示意</text>
  <rect x="180" y="58" width="280" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="320" y="86" text-anchor="middle" font-size="13" fill="#1e293b">加载：读取字节流，生成 Class 对象</text>
  <line x1="320" y1="104" x2="320" y2="132" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="180" y="134" width="280" height="46" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="320" y="162" text-anchor="middle" font-size="13" fill="#1e293b">验证：格式/元数据/字节码/符号引用</text>
  <line x1="320" y1="180" x2="320" y2="208" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="180" y="210" width="280" height="46" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="320" y="238" text-anchor="middle" font-size="13" fill="#1e293b">准备：静态变量分配内存并设零值</text>
  <line x1="320" y1="256" x2="320" y2="284" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="180" y="286" width="280" height="46" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="320" y="314" text-anchor="middle" font-size="13" fill="#1e293b">解析：符号引用替换为直接引用</text>
  <line x1="320" y1="332" x2="320" y2="360" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="180" y="362" width="280" height="46" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="320" y="390" text-anchor="middle" font-size="13" fill="#1e293b">初始化：执行 &lt;clinit&gt;() 方法</text>
  <line x1="320" y1="408" x2="320" y2="436" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="180" y="438" width="280" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="320" y="466" text-anchor="middle" font-size="13" fill="#1e293b">使用：程序正常运行</text>
  <line x1="320" y1="484" x2="320" y2="512" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="180" y="514" width="280" height="46" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="320" y="542" text-anchor="middle" font-size="13" fill="#1e293b">卸载：类从方法区移除</text>
  <line x1="495" y1="134" x2="495" y2="332" stroke="#64748b" stroke-width="1"/>
  <line x1="487" y1="134" x2="495" y2="134" stroke="#64748b" stroke-width="1"/>
  <line x1="487" y1="332" x2="495" y2="332" stroke="#64748b" stroke-width="1"/>
  <text x="515" y="237" text-anchor="start" font-size="12" fill="#475569">连接 Linking</text>
  <text x="320" y="592" text-anchor="middle" font-size="12" fill="#475569">注：解析可在初始化之后开始，以支持运行时动态绑定</text>
</svg>
*图：类加载生命周期示意（据原文重绘）*

加载、验证、准备、初始化和卸载这个阶段的顺序是确定的，类的加载过程必须按照这种顺序按部就班地开始，而解析阶段则不一定：它在某些情况下可以在初始化阶段之后再开始，这是为了支持Java语言的运行时绑定（也称为动态绑定或晚期绑定）。以下陈述的内容都已HotSpot为基准。

### 加载

在加载阶段（可以参考java.lang.ClassLoader的loadClass()方法），虚拟机需要完成以下件事情：

1. 通过一个类的全限定名来获取定义此类的二进制字节流（并没有指明要从一个Class文件中获取，可以从其他渠道，譬如：网络、动态生成、数据库等）；
2. 将这个字节流所代表的静态存储结构转化为方法区的运行时数据结构；
3. 在内存中生成一个代表这个类的java.lang.Class对象，作为方法区这个类的各种数据的访问入口；

加载阶段和连接阶段（Linking）的部分内容（如一部分字节码文件格式验证动作）是交叉进行的，加载阶段尚未完成，连接阶段可能已经开始，但这些夹在加载阶段之中进行的动作，仍然属于连接阶段的内容，这两个阶段的开始时间仍然保持着固定的先后顺序。

### 验证

验证是连接阶段的第一步，这一阶段的目的是为了确保Class文件的字节流中包含的信息符合当前虚拟机的要求，并且不会危害虚拟机自身的安全。

验证阶段大致会完成个阶段的检验动作：

- 文件格式验证：验证字节流是否符合Class文件格式的规范；例如：是否以魔术0xCAFEBABE开头（注：原导出前缀缺失，0xCAFEBABE 为 JVM 规范规定的魔数，此处为修复值）、主次版本号是否在当前虚拟机的处理范围之内、常量池中的常量是否有不被支持的类型。
- 元数据验证：对字节码描述的信息进行语义分析（注意：对比javac编译阶段的语义分析），以保证其描述的信息符合Java语言规范的要求；例如：这个类是否有父类，除了java.lang.Object之外。
- 字节码验证：通过数据流和控制流分析，确定程序语义是合法的、符合逻辑的。
- 符号引用验证：确保解析动作能正确执行。

验证阶段是非常重要的，但不是必须的，它对程序运行期没有影响，如果所引用的类经过反复验证，那么可以考虑采用-Xverifynone参数来关闭大部分的类验证措施，以缩短虚拟机类加载的时间。

### 准备

准备阶段是正式为类变量分配内存并设置类变量初始值的阶段，这些变量所使用的内存都将在方法区中进行分配。这时候进行内存分配的仅包括类变量（被static修饰的变量），而不包括实例变量，实例变量将会在对象实例化时随着对象一起分配在堆中。其次，这里所说的初始值“通常情况”下是数据类型的零值，假设一个类变量的定义为：

```java
public static int value = 123; // 注：原导出数字缺失，123 仅为占位示例值，原文或不同
```

那变量value在准备阶段过后的初始值为0（即数据类型的零值）而不是123（123即上文所赋的示例值，原数值已丢失），因为这时候尚未开始执行任何java方法，而把value赋值为123的putstatic指令是程序被编译后，存放于类构造器`<clinit>()`方法（注：按"类构造器"定义修复补全）之中，所以把value赋值为123的动作将在初始化阶段才会执行。

至于“特殊情况”是指：public static final int value=123（占位示例值同上），即当类字段的字段属性是ConstantValue时，会在准备阶段初始化为指定的值，所以标注为final之后，value的值在准备阶段初始化为123而非0

### 解析

解析阶段是虚拟机将常量池内的符号引用替换为直接引用的过程。解析动作主要针对类或接口、字段、类方法、接口方法、方法类型、方法句柄和调用点限定符类符号引用进行。

### 初始化

类初始化阶段是类加载过程的最后一步，到了初始化阶段，才真正开始执行类中定义的java程序代码。在准备极端，变量已经付过一次系统要求的初始值，而在初始化阶段，则根据程序猿通过程序制定的主管计划去初始化类变量和其他资源，或者说：初始化阶段是执行类构造器<clinit>()方法的过程.

`<clinit>()`方法是由编译器自动收集类中的所有类变量的赋值动作和静态语句块static{}中的语句合并产生的，编译器收集的顺序是由语句在源文件中出现的顺序所决定的，静态语句块只能访问到定义在静态语句块之前的变量，定义在它之后的变量，在前面的静态语句块可以赋值，但是不能访问。如下：

```java
public class Test
{
    static
    {
        i=0; // 注：原导出数字缺失，0 为占位示例值，原文或不同
        System.out.println(i); // 这句编译器会报错：Cannot reference a field before it is defined（非法向前应用）
    }

    static int i=0; // 注：占位示例值同上
}
```

`<clinit>()`方法与实例构造器`<init>()`方法不同，它不需要显示地调用父类构造器，虚拟机会保证在子类`<init>()`方法执行之前，父类的`<clinit>()`方法方法已经执行完毕，回到本文开篇的举例代码中，结果会打印输出：SSClass就是这个道理。

由于父类的`<clinit>()`方法先执行，也就意味着父类中定义的静态语句块要优先于子类的变量赋值操作。

`<clinit>()`方法对于类或者接口来说并不是必需的，如果一个类中没有静态语句块，也没有对变量的赋值操作，那么编译器可以不为这个类生产`<clinit>()`方法。

接口中不能使用静态语句块，但仍然有变量初始化的赋值操作，因此接口与类一样都会生成`<clinit>()`方法。但接口与类不同的是，执行接口的`<clinit>()`方法不需要先执行父接口的`<clinit>()`方法。只有当父接口中定义的变量使用时，父接口才会初始化。另外，接口的实现类在初始化时也一样不会执行接口的`<clinit>()`方法。

虚拟机会保证一个类的`<clinit>()`方法在多线程环境中被正确的加锁、同步，如果多个线程同时去初始化一个类，那么只会有一个线程去执行这个类的`<clinit>()`方法，其他线程都需要阻塞等待，直到活动线程执行`<clinit>()`方法完毕。如果在一个类的`<clinit>()`方法中有好事很长的操作，就可能造成多个线程阻塞，在实际应用中这种阻塞往往是隐藏的。

```java
package jvm.classload;

public class DealLoopTest
{
    static class DeadLoopClass
    {
        static
        {
            if(true)
            {
                System.out.println(Thread.currentThread()+"init DeadLoopClass");
                while(true)
                {
                }
            }
        }
    }

    public static void main(String[] args)
    {
        Runnable script = new Runnable(){
            public void run()
            {
                System.out.println(Thread.currentThread()+" start");
                DeadLoopClass dlc = new DeadLoopClass();
                System.out.println(Thread.currentThread()+" run over");
            }
        };

        Thread thread = new Thread(script);
        Thread thread = new Thread(script);

        threadstart();
        threadstart();
    }
}
```

运行结果：（即一条线程在死循环以模拟长时间操作，另一条线程在阻塞等待）

```text
Thread[Thread-<编号>,<优先级>,main] start（注：原导出数字缺失，线程名编号与优先级为占位）
Thread[Thread-<编号>,<优先级>,main] start
Thread[Thread-<编号>,<优先级>,main]init DeadLoopClass
```

需要注意的是，其他线程虽然会被阻塞，但如果执行`<clinit>()`方法的那条线程退出`<clinit>()`方法后，其他线程唤醒之后不会再次进入`<clinit>()`方法。同一个类加载器下，一个类型只会初始化一次。

将上面代码中的静态块替换如下：

```java
static
{
    System.out.println(Thread.currentThread() + "init DeadLoopClass");
    try
    {
        TimeUnit.SECONDS.sleep(5); // 注：原导出数字缺失，5 为占位示例值，原文或不同
    }
    catch (InterruptedException e)
    {
        e.printStackTrace();
    }
}
```

运行结果：

```text
Thread[Thread-<编号>,<优先级>,main] start
Thread[Thread-<编号>,<优先级>,main] start
Thread[Thread-<编号>,<优先级>,main]init DeadLoopClass (之后sleep 5 s，占位同上)
Thread[Thread-<编号>,<优先级>,main] run over
Thread[Thread-<编号>,<优先级>,main] run over
```

虚拟机规范严格规定了有且只有5种情况（jdk1.7）（注：原导出数字缺失，5按下文所列5种情况修复、1.7 按第5条 MethodHandle 动态语言支持自 JDK 1.7 引入推定，均为修复值）必须对类进行“初始化”（而加载、验证、准备自然需要在此之前开始）：

1. 遇到new,getstatic,putstatic,invokestatic这四条字节码指令时（注：原导出数字缺失，按所列4个指令修复，此处为修复值），如果类没有进行过初始化，则需要先触发其初始化。生成这条指令的最常见的Java代码场景是：使用new关键字实例化对象的时候、读取或设置一个类的静态字段（被final修饰、已在编译器把结果放入常量池的静态字段除外）的时候，以及调用一个类的静态方法的时候。
2. 使用java.lang.reflect包的方法对类进行反射调用的时候，如果类没有进行过初始化，则需要先触发其初始化。
3. 当初始化一个类的时候，如果发现其父类还没有进行过初始化，则需要先触发其父类的初始化。
4. 当虚拟机启动时，用户需要指定一个要执行的主类（包含main()方法的那个类），虚拟机会先初始化这个主类。
5. 当使用jdk动态语言支持时，如果一个java.lang.invoke.MethodHandle实例最后的解析结果REF_getstatic,REF_putstatic,REF_invokeStatic的方法句柄，并且这个方法句柄所对应的类没有进行初始化，则需要先出触发其初始化。

开篇已经举了一个范例：通过子类引用父类的静态字段（注：按上文"通过其子类来引用父类中定义的静态字段"修复），不会导致子类初始化。

这里再举两个例子。

1. 通过数组定义来引用类，不会触发此类的初始化：（SuperClass类已在本文开篇定义）

```java
public class NotInitialization
{
    public static void main(String[] args)
    {
        SuperClass[] sca = new SuperClass[];
    }
}
```

运行结果：（无）

2. 常量在编译阶段会存入调用类的常量池中，本质上并没有直接引用到定义常量的类，因此不会触发定义常量的类的初始化：

```java
public class ConstClass
{
    static
    {
        System.out.println("ConstClass init!");
    }

    public static final String HELLOWORLD = "hello world";
}

public class NotInitialization
{
    public static void main(String[] args)
    {
        System.out.println(ConstClass.HELLOWORLD);
    }
}
```

运行结果：hello world

附：昨天从论坛上看到一个例子，很有意思，如下：

```java
package jvm.classload;

public class StaticTest
{
    public static void main(String[] args)
    {
        staticFunction();
    }

    static StaticTest st = new StaticTest();

    static
    {
        System.out.println("");
    }

    {
        System.out.println("");
    }

    StaticTest()
    {
        System.out.println("");
        System.out.println("a="+a+",b="+b);
    }

    public static void staticFunction(){
        System.out.println("");
    }

    int a=;

    static int b =;
}
```

问题是：请问输出是什么？

程序跑一下就知道结果，如果想知道为什么，请在下方留言~~

## 参考文献

- 《深入理解java虚拟机》周志明 著.
