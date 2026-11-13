# iframe跨域问题解决

Chrome浏览器对于跨域问题校验比较严格：

业务场景：第三方需要通过iframe嵌入我方一个页面

:::info
1. 设置nginx配置，允许嵌入Iframe中
2. 服务应答response，设置cookie允许，SameSite=None,secure,httponly
3. 替换前端操作cookie的代码（不能出现前端设置cookie的情况，会导致cookie无法设置，同时获取不到）

:::

:::info
nginx中配置

1. proxy_set_header 是设置的请求头
2. add_header才是设置的应答头
3. proxy_cookie_path是为了转换cookie的路径而已

:::

简简单单一个问题：排查花费时长7个小时

1. iframe问题解决思路：

:::info
1. 通过window.open跳转的方式打开页面，避免使用iframe
2. 采用火狐浏览器进行演示
3. 修改代码，确保服务端和前端都支持跨域

:::

:::info
accept:*/*|accept-encoding:gzip, deflate, br, zstd|accept-language:zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6|cache-control:no-cache|connection:keep-alive|host:vod.duanshu.com|origin:https://ayaqh.duanshu.com|pragma:no-cache|referer:https://ayaqh.duanshu.com/|sec-ch-ua:"Microsoft Edge";v="129", "Not=A?Brand";v="8", "Chromium";v="129"|sec-ch-ua-mobile:?0|sec-ch-ua-platform:"Windows"|sec-fetch-dest:empty|sec-fetch-mode:cors|sec-fetch-site:same-site|user-agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0

:::
