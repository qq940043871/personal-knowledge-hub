# 郑大信息-Api网关

网关作用：

> 对外：提供统一的流量入口，针对请求进行参数校验、IP限流
>
> 对内：提供安全认证，日志监控，限流熔断，敏感协议脱敏，关键业务校验，可视化协议编排等功能

功能：

>  过滤：网关需要检测一些异常访问，过滤掉这些请求
>
>  校验：关键业务逻辑判断（认证级别、协议签订、会员有效期、脱敏处理、资金密码校验、黑白名单）
>
>  转发：请求转发和协议转换

    灰度发布：网关完全可以做到对相同服务不同版本的实例进行导流，还可以收集相关的数据

    API聚合：使用网关可以将多个单独请求聚合成一个请求

    服务治理：限流、降级、熔断、负载均衡等

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 470" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="320" y="30" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">API网关架构示意</text>
  <rect x="210" y="52" width="220" height="36" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="320" y="74" text-anchor="middle" font-size="13" fill="#1e293b">客户端/外部请求</text>
  <line x1="320" y1="90" x2="320" y2="108" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="30" y="112" width="580" height="70" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="44" y="130" text-anchor="start" font-size="13" font-weight="bold" fill="#1e293b">对外：统一流量入口</text>
  <rect x="230" y="138" width="84" height="34" rx="6" fill="#ffffff" stroke="#2563eb" stroke-width="1.2"/>
  <text x="272" y="160" text-anchor="middle" font-size="13" fill="#1e293b">参数校验</text>
  <rect x="326" y="138" width="84" height="34" rx="6" fill="#ffffff" stroke="#2563eb" stroke-width="1.2"/>
  <text x="368" y="160" text-anchor="middle" font-size="13" fill="#1e293b">IP限流</text>
  <line x1="320" y1="184" x2="320" y2="202" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="30" y="206" width="580" height="70" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="44" y="224" text-anchor="start" font-size="13" font-weight="bold" fill="#1e293b">核心功能：过滤·校验·转发</text>
  <rect x="53" y="232" width="170" height="34" rx="6" fill="#ffffff" stroke="#d97706" stroke-width="1.2"/>
  <text x="138" y="254" text-anchor="middle" font-size="13" fill="#1e293b">过滤：拦截异常访问</text>
  <rect x="235" y="232" width="170" height="34" rx="6" fill="#ffffff" stroke="#d97706" stroke-width="1.2"/>
  <text x="320" y="254" text-anchor="middle" font-size="13" fill="#1e293b">校验：认证·黑白名单</text>
  <rect x="417" y="232" width="170" height="34" rx="6" fill="#ffffff" stroke="#d97706" stroke-width="1.2"/>
  <text x="502" y="254" text-anchor="middle" font-size="13" fill="#1e293b">转发：请求与协议转换</text>
  <line x1="320" y1="278" x2="320" y2="296" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="30" y="300" width="580" height="70" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="44" y="318" text-anchor="start" font-size="13" font-weight="bold" fill="#1e293b">对内：认证·监控·脱敏</text>
  <rect x="117" y="326" width="84" height="34" rx="6" fill="#ffffff" stroke="#16a34a" stroke-width="1.2"/>
  <text x="159" y="348" text-anchor="middle" font-size="13" fill="#1e293b">灰度发布</text>
  <rect x="213" y="326" width="84" height="34" rx="6" fill="#ffffff" stroke="#16a34a" stroke-width="1.2"/>
  <text x="255" y="348" text-anchor="middle" font-size="13" fill="#1e293b">API聚合</text>
  <rect x="309" y="326" width="214" height="34" rx="6" fill="#ffffff" stroke="#16a34a" stroke-width="1.2"/>
  <text x="416" y="348" text-anchor="middle" font-size="13" fill="#1e293b">服务治理：限流·熔断·负载均衡</text>
  <line x1="320" y1="372" x2="320" y2="390" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="210" y="394" width="220" height="36" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="320" y="416" text-anchor="middle" font-size="13" fill="#1e293b">内部服务（多版本实例）</text>
</svg>

*图：API网关架构与功能分层示意（据原文重绘）*
