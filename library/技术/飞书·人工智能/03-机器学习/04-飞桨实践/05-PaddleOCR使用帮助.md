# PaddleOCR使用帮助

| **字段** | **说明** | **默认值** |
| :--- | :--- | :--- |
| use_gpu | 是否使用GPU | TRUE |
| gpu_mem | 初始化占用的GPU内存大小 | 8000M |
| image_dir | 通过命令行调用时执行预测的图片或文件夹路径 | |
| page_num | 当输入类型为pdf文件时有效，指定预测前面page_num页，默认预测所有页 | 0 |
| det_algorithm | 使用的检测算法类型 | DB |
| det_model_dir | 检测模型所在文件夹。传参方式有两种，1. None: 自动下载内置模型到 ~/.paddleocr/det；2.自己转换好的inference模型路径，模型路径下必须包含model和params文件 | None |
| det_max_side_len | 检测算法前向时图片长边的最大尺寸，当长边超出这个值时会将长边resize到这个大小，短边等比例缩放 | 960 |
| det_db_thresh | DB模型输出预测图的二值化阈值 | 0.3 |
| det_db_box_thresh | DB模型输出框的阈值，低于此值的预测框会被丢弃 | 0.5 |
| det_db_unclip_ratio | DB模型输出框扩大的比例 | 2 |
| det_db_score_mode | 计算检测框score的方式，有'fast'和'slow'，如果要检测的文字有弯曲，建议用'slow'，'slow'模式计算的box的score偏大，box不容易被过滤掉 | 'fast' |
| det_east_score_thresh | EAST模型输出预测图的二值化阈值 | 0.8 |
| det_east_cover_thresh | EAST模型输出框的阈值，低于此值的预测框会被丢弃 | 0.1 |
| det_east_nms_thresh | EAST模型输出框NMS的阈值 | 0.2 |
| rec_algorithm | 使用的识别算法类型 | CRNN |
| rec_model_dir | 识别模型所在文件夹。传参方式有两种，1. None: 自动下载内置模型到 ~/.paddleocr/rec；2.自己转换好的inference模型路径，模型路径下必须包含model和params文件 | None |
| rec_image_shape | 识别算法的输入图片尺寸 | "3,32,320" |
| rec_batch_num | 进行识别时，同时前向的图片数 | 30 |
| max_text_length | 识别算法能识别的最大文字长度 | 25 |
| rec_char_dict_path | 识别模型字典路径，当rec_model_dir使用方式2传参时需要修改为自己的字典路径 | ./ppocr/utils/ppocr_keys_v1.txt |
| use_space_char | 是否识别空格 | TRUE |
| drop_score | 对输出按照分数(来自于识别模型)进行过滤，低于此分数的不返回 | 0.5 |
| use_angle_cls | 是否加载分类模型 | FALSE |
| cls_model_dir | 分类模型所在文件夹。传参方式有两种，1. None: 自动下载内置模型到 ~/.paddleocr/cls；2.自己转换好的inference模型路径，模型路径下必须包含model和params文件 | None |
| cls_image_shape | 分类算法的输入图片尺寸 | "3, 48, 192" |
| label_list | 分类算法的标签列表 | ['0', '180'] |
| cls_batch_num | 进行分类时，同时前向的图片数 | 30 |
| enable_mkldnn | 是否启用mkldnn | FALSE |
| use_zero_copy_run | 是否通过zero_copy_run的方式进行前向 | FALSE |
| lang | 模型语言类型,目前支持 目前支持中英文(ch)、英文(en)、法语(french)、德语(german)、韩语(korean)、日语(japan) | ch |
| det | 前向时使用启动检测 | TRUE |
| rec | 前向时是否启动识别 | TRUE |
| cls | 前向时是否启动分类 (命令行模式下使用use_angle_cls控制前向是否启动分类) | FALSE |
| show_log | 是否打印logger信息 | FALSE |
| type | 执行ocr或者表格结构化, 值可选['ocr','structure'] | ocr |
| ocr_version | OCR模型版本，可选PP-OCRv3, PP-OCRv2, PP-OCR。PP-OCRv3 支持中、英文的检测、识别、多语种识别，方向分类器等模型；PP-OCRv2 目前仅支持中文的检测和识别模型；PP-OCR支持中文的检测，识别，多语种识别，方向分类器等模型 | PP-OCRv3 |
