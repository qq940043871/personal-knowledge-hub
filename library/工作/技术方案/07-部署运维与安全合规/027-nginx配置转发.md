# nginx配置转发

此处为截取请求地址中 bimg4 之后的路径，并赋给转发地址：

```nginx
location ^~ /bimg4/ {
  if ($request_uri ~ /bimg4/(.*)) {
    set $bucketid $1;
  }
  proxy_pass http://$bucketid;
}
```
