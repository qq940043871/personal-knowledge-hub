# 表格OCR改VLM识别

## 修改目标

从使用基于OCR的 `RapidTableModel` 改为使用VLM预测器。

*图：表格识别双路径——VLM 与原 OCR（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 340" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="270" y="16" width="180" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="41" text-anchor="middle" font-size="14" fill="#1e293b">表格识别（table_enable）</text>
  <line x1="360" y1="56" x2="360" y2="80" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="280" y="84" width="160" height="40" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="360" y="109" text-anchor="middle" font-size="14" fill="#1e293b">use_vlm_table ?</text>
  <line x1="310" y1="124" x2="210" y2="156" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="410" y1="124" x2="510" y2="156" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <text x="230" y="140" text-anchor="middle" font-size="13" fill="#475569">true</text>
  <text x="490" y="140" text-anchor="middle" font-size="13" fill="#475569">false</text>
  <rect x="90" y="160" width="240" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="210" y="183" text-anchor="middle" font-size="14" fill="#1e293b">VLM：表格图转 base64</text>
  <text x="210" y="203" text-anchor="middle" font-size="13" fill="#475569">batch_predict 逐表预测</text>
  <rect x="390" y="160" width="240" height="56" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="510" y="183" text-anchor="middle" font-size="14" fill="#1e293b">OCR：get_atom_model('table')</text>
  <text x="510" y="203" text-anchor="middle" font-size="13" fill="#475569">table_model.predict</text>
  <line x1="210" y1="216" x2="320" y2="248" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="510" y1="216" x2="400" y2="248" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="160" y="252" width="400" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="360" y="279" text-anchor="middle" font-size="13" fill="#1e293b">校验以 &lt;/html&gt; 或 &lt;/table&gt; 结尾，写入 table_res['html']</text>
  <text x="360" y="322" text-anchor="middle" font-size="12" fill="#475569">VLM 路径异常：logger.error 后 continue（可回退 OCR 或跳过）；OCR 失败仅告警</text>
</svg>

## 详细修改

> 涉及的修改：mineru/backend/pipeline/batch_analyze.py

### 1. 修改 BatchAnalyze 类的初始化

首先在 `BatchAnalyze` 类中添加VLM预测器支持：

```Python
class BatchAnalyze:
    def __init__(self, model_manager, batch_ratio: int, formula_enable, table_enable, enable_ocr_det_batch: bool = True, use_vlm_table: bool = False):
        self.batch_ratio = batch_ratio
        self.formula_enable = get_formula_enable(formula_enable)
        self.table_enable = get_table_enable(table_enable)
        self.model_manager = model_manager
        self.enable_ocr_det_batch = enable_ocr_det_batch
        self.use_vlm_table = use_vlm_table  # 新增VLM表格识别开关
        
        # 如果启用VLM表格识别，初始化VLM预测器
        if self.use_vlm_table and self.table_enable:
            from mineru.backend.vlm.vlm_analyze import ModelSingleton
            self.vlm_model_singleton = ModelSingleton()
            self.vlm_predictor = None  # 延迟初始化
```

### 2. 添加VLM预测器获取方法

```Python
def get_vlm_predictor(self):
    """获取VLM预测器"""
    if self.vlm_predictor is None:
        self.vlm_predictor = self.vlm_model_singleton.get_model(
            backend="transformers",
            model_path=None,
            server_url=None
        )
    return self.vlm_predictor

def image_to_base64(self, pil_image):
    """将PIL图像转换为base64字符串"""
    import base64
    from io import BytesIO
    
    buffer = BytesIO()
    pil_image.save(buffer, format='PNG')
    img_bytes = buffer.getvalue()
    return base64.b64encode(img_bytes).decode('utf-8')

# 从VLM输出中提取表格HTML
def extract_table_from_vlm_output(self, vlm_result,table_img):
    """从VLM输出中提取表格HTML"""
    try:
        # 解析VLM token输出，提取表格内容
        from mineru.backend.vlm.vlm_magic_model import MagicModel

        # 假设vlm_result是token字符串，需要解析出表格部分
        # 这里需要根据实际VLM输出格式进行调整
        print('vlm_result', vlm_result)
        magic_model = MagicModel(vlm_result, 1000, 1000)  # 使用标准化尺寸
        table_blocks = magic_model.get_table_blocks()
        print('table_blocks',table_blocks)
        if table_blocks:
            # 提取第一个表格块的内容并转换为HTML
            table_block = table_blocks[0]
            # 这里需要实现从VLM表格块到HTML的转换逻辑
            # 具体实现取决于VLM输出的表格格式
            return self.convert_vlm_table_to_html(table_block)

        return None
    except Exception as e:
        logger.warning(f"Failed to extract table from VLM output: {e}")
        return None

# 将VLM表格块转换为HTML格式
def convert_vlm_table_to_html(self, para_block):
    """将VLM表格块转换为HTML格式"""
    # 这里需要根据VLM表格块的具体格式实现转换逻辑
    # 参考VLM后端的表格处理方式
    try:
        # 假设table_block包含表格的结构化信息
        # 需要将其转换为HTML表格格式
        html_content = "<table>"

        # 这里需要根据实际的table_block结构进行实现
        # 示例代码，需要根据实际情况调整
        from mineru.utils.enum_class import MakeMode, BlockType, ContentType
        para_type = para_block['type']
        if para_type == BlockType.TABLE:
            for block in para_block['blocks']:  # 2nd.拼table_body
                if block['type'] == BlockType.TABLE_BODY:
                    for line in block['lines']:
                        for span in line['spans']:
                            if span['type'] == ContentType.TABLE:
                                # if processed by table model
                                if span.get('html', ''):
                                    html_content += span.get('html', '')
        html_content += "</table>"
        return html_content
    except Exception as e:
        logger.warning(f"Failed to convert VLM table to HTML: {e}")
        return None
```

### 3. 替换表格识别逻辑

表格识别代码替换为VLM：

```Python
# 表格识别 table recognition
if self.table_enable:
    if self.use_vlm_table:
        # 使用VLM进行表格识别
        vlm_predictor = self.get_vlm_predictor()
        
        for table_res_dict in tqdm(table_res_list_all_page, desc="VLM Table Predict"):
            table_img = table_res_dict['table_img']
            
            try:
                # 将表格图像转换为base64
                table_base64 = self.image_to_base64(table_img)
                
                # 使用VLM预测
                vlm_results = vlm_predictor.batch_predict(images=[table_base64])
                
                if vlm_results and len(vlm_results) > 0:
                    # 解析VLM输出中的表格内容
                    html_code = self.extract_table_from_vlm_output(vlm_results[0],table_img)
                    
                    if html_code:
                        expected_ending = html_code.strip().endswith('</html>') or html_code.strip().endswith('</table>')
                        if expected_ending:
                            table_res_dict['table_res']['html'] = html_code
                        else:
                            logger.warning('VLM table recognition processing fails, not found expected HTML table end')
                    else:
                        logger.warning('VLM table recognition processing fails, not get html return')
                else:
                    logger.warning('VLM table recognition processing fails, no results returned')
                    
            except Exception as e:
                logger.error(f"VLM table recognition failed: {e}")
                # 可以选择回退到OCR方式或跳过
                continue
    else:
        # 原有的OCR表格识别逻辑
        for table_res_dict in tqdm(table_res_list_all_page, desc="Table Predict"):
            _lang = table_res_dict['lang']
            table_model = atom_model_manager.get_atom_model(
                atom_model_name='table',
                lang=_lang,
            )
            html_code, table_cell_bboxes, logic_points, elapse = table_model.predict(table_res_dict['table_img'])
            # 判断是否返回正常
            if html_code:
                expected_ending = html_code.strip().endswith('</html>') or html_code.strip().endswith('</table>')
                if expected_ending:
                    table_res_dict['table_res']['html'] = html_code
                else:
                    logger.warning(
                        'table recognition processing fails, not found expected HTML table end'
                    )
            else:
                logger.warning(
                    'table recognition processing fails, not get html return'
                )
```

### 4. 注意事项

1. **VLM输出格式解析**：需要根据实际的VLM输出格式实现 `extract_table_from_vlm_output` 和 `convert_vlm_table_to_html` 方法。
