## Docker环境部署

1. **docker启动容器**docker安装测试 docker run -d --name centos7 -i -t (j镜像ID) /bin/bash
1. --net none 关闭网络
1. **升级openssl版本到1.1.1**wget --no-check-certificate  [https://www.openssl.org/source/openssl-1.1.1a.tar.gz](https://www.openssl.org/source/openssl-1.1.1a.tar.gz)

```
<code># 1.下载openssl<br/>wget https://www.openssl.org/source/openssl-1.1.1a.tar.gz<br/>tar -zxvf openssl-1.1.1a.tar.gz<br/>cd openssl-1.1.1a<br/># 2.编译安装<br/>./config --prefix=/usr/local/openssl no-zlib #不需要zlib<br/>make<br/>make install<br/># 3.备份原配置<br/>mv /usr/bin/openssl /usr/bin/openssl.bak<br/>mv /usr/include/openssl/ /usr/include/openssl.bak<br/># 4.新版配置<br/>ln -s /usr/local/openssl/include/openssl /usr/include/openssl<br/>ln -s /usr/local/openssl/lib/libssl.so.1.1 /usr/local/lib64/libssl.so<br/>ln -s /usr/local/openssl/bin/openssl /usr/bin/openssl<br/># 5.修改系统配置<br/>## 写入openssl库文件的搜索路径<br/>echo "/usr/local/openssl/lib" &gt;&gt; /etc/ld.so.conf<br/>## 使修改后的/etc/ld.so.conf生效 <br/>ldconfig -v<br/># 6.查看openssl版本<br/>openssl version</code>
```

1. **安装python3时候报错，提示没有zlib，需要安装zlib**./configure  make && make install
1. **安装python3.10版本，需要源码编译**

```
<code>pip install（whl 包的名字）--force-reinstall<br/>pip3 install opencv_python_headless<br/># 编译安装<br/>./configure prefix=/usr/local/python3 --with-openssl=/usr/local/openssl<br/>make &amp;&amp; make install<br/># 编译完成后，创建软链接文件到执行文件路径：<br/>ln -s /usr/local/python3/bin/python3 /usr/bin/python3<br/>ln -s /usr/local/python3/bin/pip3 /usr/bin/pip3<br/># 我们可以清除之前编译的可执行文件及配置文件 &amp;&amp; 清除所有生成的文件：<br/>make clean &amp;&amp; make distclean</code>
```

1. **联网环境下安装paddle和paddleocr**export PATH=$PATH:/usr/local/python3/bin #处理环境变量

```
<code>yum install libjpeg zlib libtiff<br/>错误：The headers or library files could not be found for jpeg<br/>yum -y install libjpeg-turbo-devel</code>
```

**多镜像源**

> [https://pypi.tuna.tsinghua.edu.cn/simple](https://pypi.tuna.tsinghua.edu.cn/simple) 提示找不到pillow[https://mirrors.aliyun.com/pypi/simple/](https://mirrors.aliyun.com/pypi/simple/) 可以正常安装[https://pypi.douban.com/simple/](https://pypi.douban.com/simple/)

```
<code>python3 -m pip install paddlepaddle==2.3.2 -i https://pypi.tuna.tsinghua.edu.cn/simple<br/>python3 -m pip install paddleocr==2.7.0.0 -i https://pypi.tuna.tsinghua.edu.cn/simple</code>
```

1. **替换动态库(libstdc++.so.6.0.26)，解决找不到CXXABI的问题**strings /lib64/libstdc++.so.6 | grep CXXABI
1. find / -name "libstdc++.so*"
1. rm libstdc++.so.6
1. ln -s libstdc++.so.6.0.26 libstdc++.so.6
1. **导出当前环境的python依赖**

```
<code># 在当前的目录下新建一个requirements.txt,里面存放着所有的依赖<br/>pip3 freeze &gt;requirements.txt <br/># 联网环境下，在目标及其执行此语句即可<br/>pip install -r requirements.txt<br/># 离线环境下，需要先下载所有依赖<br/>pip3 download -r requirements.txt -d /home/study/packages<br/># 压缩所有的依赖包<br/>tar -zcvf requirements.tar.gz ./*<br/># 然后将dataException.tar.gz和requirement.txt放到目标机器<br/># 目标机器下执行语句 安装依赖 <br/>pip install --no-index --find-links=./  -r requirements.txt<br/></code>
```

1. **导出docker镜像**

```
<code>docker save d4c3cafb11d5&gt; /opt/mysql-8.0.22..tar<br/>docker load &lt; /opt/mysql-8.0.22.tar</code>
```

1. **下载paddleocr的模型**