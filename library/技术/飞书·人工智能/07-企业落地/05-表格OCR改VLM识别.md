# pipeline表格ocr识别调整vlm识别

## Pipeline处理流程

![图片展示了Pipeline处理流程。从docx_analyze开始，依次进行Collect Page Info、batch_image_analyze、ModelSingleton等操作，最终进入Batch Processing。Batch Processing分为Memory-based Batch和OCR Batch Processing两部分，Memory-based Batch下有SortBlocksByBlock、DocLayoutHQLMModel等步骤，OCR Batch Processing下有PaddedOCR、YOLOWHModel等步骤。该图与上下文紧密相关，直观呈现了文档处理的各环节及流程。](https://feishu.cn/file/MY64btNYOoY5sMxaI9dcUixdnj8)

![图片展示了AtomModelSingleton获取原子模型的流程图。从AtomModelSingleton开始，通过get_atom_model()方法，根据Model Type（OCR、layout、formula、table）选择不同模型。OCR对应OCR Model，layout对应Layout Model，formula对应Formula Model，table对应Table Model，其中Table Model下有RapidTable。各模型间存在Model Cache的关联。该图与文档中Pipeline处理流程相关，直观呈现了模型选择与获取的逻辑关系。](https://feishu.cn/file/DNVNbaJLNo66pzxetw9cOEr6nOd)

## 修改目标

从使用基于OCR的 `RapidTableModel` 改为使用VLM预测器。

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

### 4.注意事项

1. **VLM输出格式解析**：需要根据实际的VLM输出格式实现 `extract_table_from_vlm_output` 和 `convert_vlm_table_to_html` 方法。
