# paddle离线安装

## Docker环境部署

1. **docker启动容器**
    1. docker安装测试 docker run -d --name centos7 -i -t (j镜像ID) /bin/bash
    2. --net none 关闭网络

2. **升级openssl版本到1.1.1**
    1. wget --no-check-certificate  https://www.openssl.org/source/openssl-1.1.1a.tar.gz

```bash
# 1.下载openssl
wget https://www.openssl.org/source/openssl-1.1.1a.tar.gz
tar -zxvf openssl-1.1.1a.tar.gz
cd openssl-1.1.1a
# 2.编译安装
./config --prefix=/usr/local/openssl no-zlib #不需要zlib
make
make install
# 3.备份原配置
mv /usr/bin/openssl /usr/bin/openssl.bak
mv /usr/include/openssl/ /usr/include/openssl.bak
# 4.新版配置
ln -s /usr/local/openssl/include/openssl /usr/include/openssl
ln -s /usr/local/openssl/lib/libssl.so.1.1 /usr/local/lib64/libssl.so
ln -s /usr/local/openssl/bin/openssl /usr/bin/openssl
# 5.修改系统配置
## 写入openssl库文件的搜索路径
echo "/usr/local/openssl/lib" >> /etc/ld.so.conf
## 使修改后的/etc/ld.so.conf生效 
ldconfig -v
# 6.查看openssl版本
openssl version
```

3. **安装python3时候报错，提示没有zlib，需要安装zlib**
    1. ./configure  make && make install

4. **安装python3.10版本，需要源码编译**

```bash
pip install（whl 包的名字）--force-reinstall
pip3 install opencv_python_headless
# 编译安装
./configure prefix=/usr/local/python3 --with-openssl=/usr/local/openssl
make && make install
# 编译完成后，创建软链接文件到执行文件路径：
ln -s /usr/local/python3/bin/python3 /usr/bin/python3
ln -s /usr/local/python3/bin/pip3 /usr/bin/pip3
# 我们可以清除之前编译的可执行文件及配置文件 && 清除所有生成的文件：
make clean && make distclean
```

5. **联网环境下安装paddle和paddleocr**
    1. export PATH=$PATH:/usr/local/python3/bin #处理环境变量

```plain
yum install libjpeg zlib libtiff
错误：The headers or library files could not be found for jpeg
yum -y install libjpeg-turbo-devel
```

**多镜像源**

> 1. https://pypi.tuna.tsinghua.edu.cn/simple 提示找不到pillow
> 2. https://mirrors.aliyun.com/pypi/simple/ 可以正常安装
> 3. https://pypi.douban.com/simple/

```shell
python3 -m pip install paddlepaddle==2.3.2 -i https://pypi.tuna.tsinghua.edu.cn/simple
python3 -m pip install paddleocr==2.7.0.0 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

6. **替换动态库(libstdc++.so.6.0.26)，解决找不到CXXABI的问题**
    1. strings /lib64/libstdc++.so.6 | grep CXXABI
    2. find / -name "libstdc++.so*"
    3. rm libstdc++.so.6
    4. ln -s libstdc++.so.6.0.26 libstdc++.so.6

7. **导出当前环境的python依赖**

```bash
# 在当前的目录下新建一个requirements.txt,里面存放着所有的依赖
pip3 freeze >requirements.txt 
# 联网环境下，在目标及其执行此语句即可
pip install -r requirements.txt
# 离线环境下，需要先下载所有依赖
pip3 download -r requirements.txt -d /home/study/packages
# 压缩所有的依赖包
tar -zcvf requirements.tar.gz ./*
# 然后将dataException.tar.gz和requirement.txt放到目标机器
# 目标机器下执行语句 安装依赖 
pip install --no-index --find-links=./  -r requirements.txt

```

8. **导出docker镜像**

```bash
docker save d4c3cafb11d5> /opt/mysql-8.0.22..tar
docker load < /opt/mysql-8.0.22.tar
```

9. **下载paddleocr的模型**
