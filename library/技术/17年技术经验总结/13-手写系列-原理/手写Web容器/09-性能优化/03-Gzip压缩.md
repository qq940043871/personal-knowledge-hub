# Gzip压缩

> 模块：性能优化
> 更新时间：2026-03-29

---

## 一、Gzip压缩原理

> 优势：传输体积通常**减少 50-80%**、省带宽、加载更快；缺点：**增加 CPU 消耗**，已压缩的文件（图片、视频）不再压缩。

```
优势：
  - 减少传输大小（通常50-80%）
  - 减少带宽消耗
  - 加快页面加载

缺点：
  - 增加CPU消耗
  - 不适合已压缩的文件（图片、视频）
```

---

## 二、实现代码

> 压缩前置条件：客户端支持 gzip，且响应**不小于 1KB**、类型不是 image/video/gzip。

```java
public class GzipFilter implements Filter {
    private int minSize = 1024;  // 最小压缩大小
    
    @Override
    public void doFilter(ServletRequest request, ServletResponse response, 
                        FilterChain chain) throws IOException, ServletException {
        
        HttpServletRequest httpRequest = (HttpServletRequest) request;
        HttpServletResponse httpResponse = (HttpServletResponse) response;
        
        // 检查客户端是否支持gzip
        String acceptEncoding = httpRequest.getHeader("Accept-Encoding");
        if (acceptEncoding == null || !acceptEncoding.contains("gzip")) {
            chain.doFilter(request, response);
            return;
        }
        
        // 包装响应
        GzipResponseWrapper wrapper = new GzipResponseWrapper(httpResponse);
        
        chain.doFilter(request, wrapper);
        
        // 获取响应数据
        byte[] data = wrapper.getBuffer();
        
        // 检查是否需要压缩
        String contentType = wrapper.getContentType();
        if (shouldCompress(contentType, data.length)) {
            // 压缩数据
            byte[] compressed = compress(data);
            
            // 设置响应头
            httpResponse.setHeader("Content-Encoding", "gzip");
            httpResponse.setContentLength(compressed.length);
            
            // 写入压缩数据
            httpResponse.getOutputStream().write(compressed);
        } else {
            // 直接写入
            httpResponse.getOutputStream().write(data);
        }
    }
    
    private boolean shouldCompress(String contentType, int size) {
        if (size < minSize) {
            return false;
        }
        
        // 不压缩已压缩的文件
        if (contentType != null) {
            if (contentType.contains("image") || 
                contentType.contains("video") ||
                contentType.contains("gzip")) {
                return false;
            }
        }
        
        return true;
    }
    
    private byte[] compress(byte[] data) throws IOException {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        GZIPOutputStream gzos = new GZIPOutputStream(baos);
        gzos.write(data);
        gzos.close();
        return baos.toByteArray();
    }
}
```

*图：GzipFilter 压缩决策流程（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 240" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="20" y="24" width="150" height="48" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="95" y="53" text-anchor="middle" font-size="13" fill="#1e293b">请求进入 GzipFilter</text>
  <line x1="170" y1="48" x2="198" y2="48" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="200" y="24" width="150" height="48" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="275" y="53" text-anchor="middle" font-size="13" fill="#1e293b">客户端支持 gzip？</text>
  <text x="275" y="90" text-anchor="middle" font-size="12" fill="#475569">不支持：直接放行（chain.doFilter）</text>
  <line x1="350" y1="48" x2="378" y2="48" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="364" y="40" text-anchor="middle" font-size="12" fill="#475569">是</text>
  <rect x="380" y="24" width="110" height="48" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="435" y="53" text-anchor="middle" font-size="13" fill="#1e293b">包装响应</text>
  <line x1="490" y1="48" x2="518" y2="48" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="520" y="24" width="170" height="48" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="605" y="53" text-anchor="middle" font-size="13" fill="#1e293b">chain.doFilter 处理请求</text>
  <path d="M605,72 L605,116 L85,116 L85,146" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="20" y="150" width="130" height="48" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="85" y="179" text-anchor="middle" font-size="13" fill="#1e293b">获取响应数据</text>
  <line x1="150" y1="174" x2="178" y2="174" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="180" y="144" width="170" height="60" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="265" y="167" text-anchor="middle" font-size="13" fill="#1e293b">shouldCompress？</text>
  <text x="265" y="189" text-anchor="middle" font-size="11" fill="#475569">≥1KB 且非 image/video/gzip</text>
  <line x1="350" y1="174" x2="368" y2="174" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="359" y="166" text-anchor="middle" font-size="12" fill="#475569">是</text>
  <rect x="370" y="150" width="190" height="48" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="465" y="169" text-anchor="middle" font-size="13" fill="#1e293b">压缩并写出</text>
  <text x="465" y="187" text-anchor="middle" font-size="12" fill="#475569">Content-Encoding: gzip</text>
  <path d="M265,204 L265,224 L650,224 L650,201" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="273" y="220" font-size="12" fill="#475569">否</text>
  <rect x="590" y="150" width="120" height="48" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="650" y="179" text-anchor="middle" font-size="13" fill="#1e293b">直接写出原数据</text>
</svg>

---

*下一步：Keep-Alive长连接*
