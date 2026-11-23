# Dify数据标准思路

## 数据处理

1. mineru把PDF文档转化为md文档
2. md文档中处理空行数据
3. md文档中追加合适的父段落!@!分割，确保父分段大小不超过2000
4. md文档根据标题追加!@!分割（程序化）
5. md文档在!@!的符号上追加标题和第几部分（程序化）
6. md文档在所有3.2.1类似这种数据上增加@@的分隔符，用来区分子段（程序化）重要重要
7. 解析md文档，按照!@!分割，调用dify的创建分段接口（程序化）

*图：MinerU 到 Dify 分段的数据处理流水线（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 170" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="60" y="24" width="100" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="110" y="50" text-anchor="middle" font-size="13" fill="#1e293b">PDF 文档</text>
  <line x1="162" y1="46" x2="188" y2="46" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="190" y="24" width="130" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="255" y="50" text-anchor="middle" font-size="13" fill="#1e293b">MinerU 转 md</text>
  <line x1="322" y1="46" x2="348" y2="46" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="350" y="24" width="130" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="415" y="50" text-anchor="middle" font-size="13" fill="#1e293b">处理空行数据</text>
  <line x1="482" y1="46" x2="508" y2="46" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="510" y="24" width="150" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="585" y="44" text-anchor="middle" font-size="13" fill="#1e293b">父段落 !@! 分割</text>
  <text x="585" y="62" text-anchor="middle" font-size="11" fill="#475569">大小不超过 2000</text>
  <path d="M585,70 L585,88 L75,88 L75,110" fill="none" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="10" y="112" width="130" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="75" y="138" text-anchor="middle" font-size="13" fill="#1e293b">按标题追加 !@!</text>
  <line x1="142" y1="134" x2="168" y2="134" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="170" y="112" width="160" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="250" y="138" text-anchor="middle" font-size="13" fill="#1e293b">标注标题和第几部分</text>
  <line x1="332" y1="134" x2="358" y2="134" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="360" y="112" width="150" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="435" y="134" text-anchor="middle" font-size="13" fill="#1e293b">3.2.1 加 @@ 分隔</text>
  <text x="435" y="152" text-anchor="middle" font-size="11" fill="#475569">区分子段</text>
  <line x1="512" y1="134" x2="538" y2="134" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="540" y="112" width="170" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="625" y="138" text-anchor="middle" font-size="13" fill="#1e293b">调用 dify 创建分段接口</text>
</svg>

### 备注

1. 文档切分时，一定要特别注意父分段和子分段之间的大小，绝对不能超过，否则会导致召回测试完全出问题。
2. 子分段应该尽量小，这样才能确保搜索的足够精准

### 父子分段大小必须设置合适（非常重要）

父子分段的段大小必须设置合适，不然召回测试结果非常查

其他分段方式需要再次测试

## 调用dify接口

1. 查询知识库列表(浏览器路径中直接获取文件id)
2. 根据知识库获取文档
3. 文档可以通过多次方式上传都可以（空文档也不影响）
4. ~~必须通过手动上传文档，再删除分段的内容，目前才能召回，通过接口的方式目前有问题~~
5. ~~（特别注意，不能上传空文档再处理分段，文档内容必须包含分段内容）~~
6. 根据文档ID上传根据自己规则划分好的分段
7. ~~处理完以后必须再多上传一个文档，触发下该知识库的向量化检索才准确~~，可能子分段问题导致的，暂时忽略

### 问题

1. 如何获取一共多少个父分段
2. 如何获取一共多少个1级题目
3. 如何获取一共多少个2级题目
4. 如何获取一共多少个3级题目
