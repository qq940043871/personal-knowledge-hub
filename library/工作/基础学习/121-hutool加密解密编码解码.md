# hutool加密解密编码解码

## [加密解密概述](https://www.hutool.cn/docs/#/crypto/%E6%A6%82%E8%BF%B0?id=%e6%a6%82%e8%bf%b0)
## [国密算法工具-SmUtil](https://www.hutool.cn/docs/#/crypto/国密算法工具-SmUtil?id=%e5%9b%bd%e5%af%86%e7%ae%97%e6%b3%95%e5%b7%a5%e5%85%b7-smutil)
### [介绍](https://www.hutool.cn/docs/#/crypto/国密算法工具-SmUtil?id=%e4%bb%8b%e7%bb%8d)
Hutool针对**Bouncy Castle**做了简化包装，用于实现国密算法中的SM2、SM3、SM4。

国密算法工具封装包括：

+ 非对称加密和签名：SM2
+ 摘要签名算法：SM3
+ 对称加密：SM4

国密算法需要引入**Bouncy Castle**库的依赖。

### [使用](https://www.hutool.cn/docs/#/crypto/国密算法工具-SmUtil?id=%e4%bd%bf%e7%94%a8)
#### [引入Bouncy Castle依赖](https://www.hutool.cn/docs/#/crypto/国密算法工具-SmUtil?id=%e5%bc%95%e5%85%a5bouncy-castle%e4%be%9d%e8%b5%96)
```xml
<dependency>
  <groupId>org.bouncycastle</groupId>
  <artifactId>bcprov-jdk15to18</artifactId>
  <version>1.69</version>
</dependency>
```

**说明**** ****bcprov-jdk15to18****的版本请前往Maven中央库搜索，查找对应JDK的最新版本。**

#### [非对称加密SM2](https://www.hutool.cn/docs/#/crypto/国密算法工具-SmUtil?id=%e9%9d%9e%e5%af%b9%e7%a7%b0%e5%8a%a0%e5%af%86sm2)
1. 使用随机生成的密钥对加密或解密

```java
String text = "我是一段测试aaaa";

SM2 sm2 = SmUtil.sm2();
// 公钥加密，私钥解密
String encryptStr = sm2.encryptBcd(text, KeyType.PublicKey);
String decryptStr = StrUtil.utf8Str(sm2.decryptFromBcd(encryptStr, KeyType.PrivateKey));
```

1. 使用自定义密钥对加密或解密

```java
String text = "我是一段测试aaaa";

KeyPair pair = SecureUtil.generateKeyPair("SM2");
byte[] privateKey = pair.getPrivate().getEncoded();
byte[] publicKey = pair.getPublic().getEncoded();

SM2 sm2 = SmUtil.sm2(privateKey, publicKey);
// 公钥加密，私钥解密
String encryptStr = sm2.encryptBcd(text, KeyType.PublicKey);
String decryptStr = StrUtil.utf8Str(sm2.decryptFromBcd(encryptStr, KeyType.PrivateKey));
```

1. SM2签名和验签

```java
String content = "我是Hanley.";
final SM2 sm2 = SmUtil.sm2();
String sign = sm2.signHex(HexUtil.encodeHexStr(content));

// true
boolean verify = sm2.verifyHex(HexUtil.encodeHexStr(content), sign);
```

当然，也可以自定义密钥对：

```java
String content = "我是Hanley.";
KeyPair pair = SecureUtil.generateKeyPair("SM2");
final SM2 sm2 = new SM2(pair.getPrivate(), pair.getPublic());

byte[] sign = sm2.sign(content.getBytes());

// true
boolean verify = sm2.verify(content.getBytes(), sign);
```

1. 使用SM2曲线点构建SM2

使用曲线点构建中的点生成和验证见：[https://i.goto327.top/CryptTools/SM2.aspx?tdsourcetag=s_pctim_aiomsg](https://i.goto327.top/CryptTools/SM2.aspx?tdsourcetag=s_pctim_aiomsg)

```java
String privateKeyHex = "FAB8BBE670FAE338C9E9382B9FB6485225C11A3ECB84C938F10F20A93B6215F0";
String x = "9EF573019D9A03B16B0BE44FC8A5B4E8E098F56034C97B312282DD0B4810AFC3";
String y = "CC759673ED0FC9B9DC7E6FA38F0E2B121E02654BF37EA6B63FAF2A0D6013EADF";

// 数据和ID此处使用16进制表示
String data = "434477813974bf58f94bcf760833c2b40f77a5fc360485b0b9ed1bd9682edb45";
String id = "31323334353637383132333435363738";

final SM2 sm2 = new SM2(privateKeyHex, x, y);
// 生成的签名是64位
sm2.usePlainEncoding();

final String sign = sm2.signHex(data, id);
// true
boolean verify = sm2.verifyHex(data, sign)
```

1. 使用私钥D值签名

```java
//需要签名的明文,得到明文对应的字节数组
byte[] dataBytes = "我是一段测试aaaa".getBytes();
//指定的私钥
String privateKeyHex = "1ebf8b341c695ee456fd1a41b82645724bc25d79935437d30e7e4b0a554baa5e";

// 此构造从5.5.9开始可使用
final SM2 sm2 = new SM2(privateKeyHex, null, null);
sm2.usePlainEncoding();
byte[] sign = sm2.sign(dataBytes, null);
```

1. 使用公钥Q值验证签名

```java
//指定的公钥
String publicKeyHex ="04db9629dd33ba568e9507add5df6587a0998361a03d3321948b448c653c2c1b7056434884ab6f3d1c529501f166a336e86f045cea10dffe58aa82ea13d725363";
//需要加密的明文,得到明文对应的字节数组
byte[] dataBytes = "我是一段测试aaaa".getBytes();
//签名值
String signHex ="2881346e038d2ed706ccdd025f2b1dafa7377d5cf090134b98756fafe084dddbcdba0ab00b5348ed48025195af3f1dda29e819bb66aa9d4d088050ff148482a";

final SM2 sm2 = new SM2(null, ECKeyUtil.toSm2PublicParams(publicKeyHex));
sm2.usePlainEncoding();

// true
boolean verify = sm2.verify(dataBytes, HexUtil.decodeHex(signHex));
```

1. 其他格式的密钥

在SM2算法中，密钥的格式分以下几种：

私钥：

+ D值 一般为硬件直接生成的值
+ PKCS#8 JDK默认生成的私钥格式
+ PKCS#1 一般为OpenSSL生成的的EC密钥格式

公钥：

+ Q值 一般为硬件直接生成的值
+ X.509 JDK默认生成的公钥格式
+ PKCS#1 一般为OpenSSL生成的的EC密钥格式

在新版本的Hutool中，SM2的构造方法对这几类的密钥都做了兼容，即用户无需关注密钥类型：

#### [摘要加密算法SM3](https://www.hutool.cn/docs/#/crypto/国密算法工具-SmUtil?id=%e6%91%98%e8%a6%81%e5%8a%a0%e5%af%86%e7%ae%97%e6%b3%95sm3)
```java
//结果为：136ce3c86e4ed909b76082055a61586af20b4dab674732ebd4b599eef080c9be
String digestHex = SmUtil.sm3("aaaaa");
```

#### [对称加密SM4](https://www.hutool.cn/docs/#/crypto/国密算法工具-SmUtil?id=%e5%af%b9%e7%a7%b0%e5%8a%a0%e5%af%86sm4)
```java
String content = "test中文";
SymmetricCrypto sm4 = SmUtil.sm4();

String encryptHex = sm4.encryptHex(content);
String decryptStr = sm4.decryptStr(encryptHex, CharsetUtil.CHARSET_UTF_8);
```

## [Base64编码解码-Base64](https://www.hutool.cn/docs/#/core/Codec编码/Base64编码解码-Base64?id=base64%e7%bc%96%e7%a0%81%e8%a7%a3%e7%a0%81-base64)
### [介绍](https://www.hutool.cn/docs/#/core/Codec编码/Base64编码解码-Base64?id=%e4%bb%8b%e7%bb%8d)
Base64编码是用64（2的6次方）个ASCII字符来表示256（2的8次方）个ASCII字符，也就是三位二进制数组经过编码后变为四位的ASCII字符显示，长度比原来增加1/3。

### [使用](https://www.hutool.cn/docs/#/core/Codec编码/Base64编码解码-Base64?id=%e4%bd%bf%e7%94%a8)
```java
String a = "伦家是一个非常长的字符串";
//5Lym5a625piv5LiA5Liq6Z2e5bi46ZW/55qE5a2X56ym5Liy
String encode = Base64.encode(a);

// 还原为a
String decodeStr = Base64.decodeStr(encode);
```

## [16进制工具-HexUtil](https://www.hutool.cn/docs/#/core/工具类/16进制工具-HexUtil?id=_16%e8%bf%9b%e5%88%b6%e5%b7%a5%e5%85%b7-hexutil)
### [介绍](https://www.hutool.cn/docs/#/core/工具类/16进制工具-HexUtil?id=%e4%bb%8b%e7%bb%8d)
十六进制（简写为hex或下标16）在数学中是一种逢16进1的进位制，一般用数字0到9和字母A到F表示（其中:A~~F即10~~15）。例如十进制数57，在二进制写作111001，在16进制写作39。

像java,c这样的语言为了区分十六进制和十进制数值,会在十六进制数的前面加上 0x,比如0x20是十进制的32,而不是十进制的20。**HexUtil**就是将字符串或byte数组与16进制表示转换的工具类。

### [用于](https://www.hutool.cn/docs/#/core/工具类/16进制工具-HexUtil?id=%e7%94%a8%e4%ba%8e)
16进制一般针对无法显示的一些二进制进行显示，常用于： 1、图片的字符串表现形式 2、加密解密 3、编码转换

### [使用](https://www.hutool.cn/docs/#/core/工具类/16进制工具-HexUtil?id=%e4%bd%bf%e7%94%a8)
**HexUtil**主要以**encodeHex**和**decodeHex**两个方法为核心，提供一些针对字符串的重载方法。

```java
String str = "我是一个字符串";

String hex = HexUtil.encodeHexStr(str, CharsetUtil.CHARSET_UTF_8);

//hex是：
//e68891e698afe4b880e4b8aae5ad97e7aca6e4b8b2

String decodedStr = HexUtil.decodeHexStr(hex);

//解码后与str相同
```

## [二进码十进数-BCD](https://www.hutool.cn/docs/#/core/语言特性/二进码十进数-BCD?id=%e4%ba%8c%e8%bf%9b%e7%a0%81%e5%8d%81%e8%bf%9b%e6%95%b0-bcd)
### [介绍](https://www.hutool.cn/docs/#/core/语言特性/二进码十进数-BCD?id=%e4%bb%8b%e7%bb%8d)
BCD码（Binary-Coded Decimal‎）亦称二进码十进数或二-十进制代码，BCD码这种编码形式利用了四个位元来储存一个十进制的数码，使二进制和十进制之间的转换得以快捷的进行。

这种编码技巧最常用于会计系统的设计里，因为会计制度经常需要对很长的数字串作准确的计算。相对于一般的浮点式记数法，采用BCD码，既可保存数值的精确度，又可免却使电脑作浮点运算时所耗费的时间。此外，对于其他需要高精确度的计算，BCD编码亦很常用。

BCD码是四位二进制码, 也就是将十进制的数字转化为二进制, 但是和普通的转化有一点不同, 每一个十进制的数字0-9都对应着一个四位的二进制码,对应关系如下: 十进制0 对应 二进制0000 ;十进制1 对应二进制0001 ....... 9 1001 接下来的10就有两个上述的码来表示 10 表示为00010000 也就是BCD码是遇见1001就产生进位,不象普通的二进制码,到1111才产生进位10000

### [方法](https://www.hutool.cn/docs/#/core/语言特性/二进码十进数-BCD?id=%e6%96%b9%e6%b3%95)
```java
String strForTest = "123456ABCDEF";
        
//转BCD
byte[] bcd = BCD.strToBcd(strForTest);
//解码BCD
String str = BCD.bcdToStr(bcd);
Assert.assertEquals(strForTest, str);
```
