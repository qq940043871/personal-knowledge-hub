# WAIT过多、参数调整

配置文件 `sysctl.conf`：

```conf
# Controls IP packet forwarding
net.ipv4.ip_forward = 0
net.ipv4.tcp_fin_timeout = 10
net.ipv4.tcp_window.scaling = 0
net.ipv4.tcp_sack = 0

# Controls the use of TCP synccookies
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_tw_recycle = 1
net.ipv4.ip_local_port_range = 1024
```
