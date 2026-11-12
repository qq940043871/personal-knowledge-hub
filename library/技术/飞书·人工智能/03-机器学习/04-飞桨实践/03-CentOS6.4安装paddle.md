# CentOS6.4安装paddle

1. 虚拟机模拟内网环境centos6.4  gcc4.4.7
2. gcc支持的C++标准
3. 经过多次折腾后发现在gcc4.4.7下进行安装实在过于困难，因此决定升级gcc4.8.5
4. 升级准备：下载gcc源码，下载g++编译相关 yumdownloader
5. 升级过程中遇到错误：

Fatal error: gnu/stubs-32.h: No such file or directory

```plain
yum -y install glibc-devel.i686
```

6. 编译python
7. 下载paddle相关依赖
8. 下载paddleocr相关依赖
9. https://mirrors.aliyun.com/centos/7/os/x86_64/  安装CentOS7的基础软件安装源
