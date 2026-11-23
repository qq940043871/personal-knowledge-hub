# CentOS6.4安装paddle

1. 虚拟机模拟内网环境centos6.4  gcc4.4.7
1. gcc支持的C++标准
1. 经过多次折腾后发现在gcc4.4.7下进行安装实在过于困难，因此决定升级gcc4.8.5
1. 升级准备：下载gcc源码，下载g++编译相关 yumdownloader
1. 升级过程中遇到错误：

Fatal error: gnu/stubs-32.h: No such file or directory

```
<code>yum -y install glibc-devel.i686</code>
```

1. 编译python
1. 下载paddle相关依赖
1. 下载paddleocr相关依赖
1. [https://mirrors.aliyun.com/centos/7/os/x86_64/](https://mirrors.aliyun.com/centos/7/os/x86_64/)  安装CentOS7的基础软件安装源