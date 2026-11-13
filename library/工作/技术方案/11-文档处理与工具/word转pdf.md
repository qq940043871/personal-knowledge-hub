# word转pdf

iText主要用于PDF文档的创建和处理，**原生并不直接支持Word转PDF**。不过，你可以通过以下几种方式实现Word到PDF的转换：

## **一、使用iText结合Apache POI（推荐方案）**

**思路**：先用Apache POI读取Word文档内容，再用iText将内容写入PDF。

### **依赖配置**

```XML
<!-- Apache POI for Word处理 -->
<dependency>
    <groupId>org.apache.poi</groupId>
    <artifactId>poi-ooxml</artifactId>
    <version>5.2.3</version>
</dependency>

<!-- iText for PDF生成 -->
<dependency>
    <groupId>com.itextpdf</groupId>
    <artifactId>itextpdf</artifactId>
    <version>5.5.13.3</version>
</dependency>
```

#### **示例代码**

```Java
import org.apache.poi.xwpf.usermodel.*;
import com.itextpdf.text.*;
import com.itextpdf.text.pdf.*;

import java.io.*;

public class WordToPdfConverter {
    public static void convert(String docxPath, String pdfPath) throws Exception {
        // 读取Word文档
        try (FileInputStream fis = new FileInputStream(docxPath);
             XWPFDocument doc = new XWPFDocument(fis);
             FileOutputStream fos = new FileOutputStream(pdfPath)) {
            
            // 创建PDF文档
            Document pdfDoc = new Document(PageSize.A4);
            PdfWriter writer = PdfWriter.getInstance(pdfDoc, fos);
            pdfDoc.open();
            
            // 处理Word文档中的段落
            for (XWPFParagraph para : doc.getParagraphs()) {
                // 创建PDF段落
                Paragraph pdfPara = new Paragraph();
                
                // 处理段落中的每个文本运行
                for (XWPFRun run : para.getRuns()) {
                    // 获取文本和格式
                    String text = run.getText(0);
                    if (text != null) {
                        Font font = new Font();
                        
                        // 设置字体大小
                        if (run.getFontSize() > 0) {
                            font.setSize(run.getFontSize());
                        }
                        
                        // 设置字体样式（粗体、斜体等）
                        if (run.isBold()) {
                            font.setStyle(Font.BOLD);
                        }
                        if (run.isItalic()) {
                            font.setStyle(Font.ITALIC);
                        }
                        
                        // 添加到PDF段落
                        pdfPara.add(new Chunk(text, font));
                    }
                }
                
                // 添加段落间距
                pdfPara.setSpacingAfter(10);
                
                // 添加到PDF文档
                pdfDoc.add(pdfPara);
            }
            
            // 关闭PDF文档
            pdfDoc.close();
        }
    }

    public static void main(String[] args) {
        try {
            convert("input.docx", "output.pdf");
            System.out.println("转换完成！");
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```

### **二、使用iText 7的docx4j集成（更现代的方案）**

iText 7提供了对docx4j的集成支持，可更方便地处理Word转PDF。

#### **依赖配置**

```XML
<!-- iText 7 Core -->
<dependency>
    <groupId>com.itextpdf</groupId>
    <artifactId>itext7-core</artifactId>
    <version>7.2.5</version>
    <type>pom</type>
</dependency>

<!-- iText 7 docx4j扩展 -->
<dependency>
    <groupId>com.itextpdf</groupId>
    <artifactId>itext7-docx4j</artifactId>
    <version>7.2.5</version>
</dependency>
```

#### **示例代码**

```Java
import com.itextpdf.docx4j.Docx4JConverter;
import com.itextpdf.kernel.pdf.PdfDocument;
import com.itextpdf.kernel.pdf.PdfWriter;

import java.io.File;
import java.io.IOException;

public class WordToPdfConverter7 {
    public static void convert(String docxPath, String pdfPath) throws IOException {
        try (PdfDocument pdfDoc = new PdfDocument(new PdfWriter(pdfPath))) {
            // 使用docx4j转换器
            Docx4JConverter.convert(new File(docxPath), pdfDoc);
        }
    }

    public static void main(String[] args) {
        try {
            convert("input.docx", "output.pdf");
            System.out.println("转换完成！");
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
```

### **三、使用商业库（如Aspose.Words）**

如果需要更高质量的转换（特别是复杂格式），可考虑商业库Aspose.Words：

#### **依赖配置**

```XML
<dependency>
    <groupId>com.aspose</groupId>
    <artifactId>aspose-words</artifactId>
    <version>23.11</version>
</dependency>
```

#### **示例代码**

```Java
import com.aspose.words.Document;
import com.aspose.words.SaveFormat;

import java.io.FileOutputStream;
import java.io.IOException;

public class WordToPdfConverterAspose {
    public static void convert(String docxPath, String pdfPath) throws Exception {
        // 加载Word文档
        Document doc = new Document(docxPath);
        
        // 保存为PDF
        doc.save(new FileOutputStream(pdfPath), SaveFormat.PDF);
    }

    public static void main(String[] args) {
        try {
            convert("input.docx", "output.pdf");
            System.out.println("转换完成！");
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```

### **四、各方案对比**

| **方案** | **优点** | **缺点** |
|-|-|-|
| **iText + Apache POI** | 开源免费，可控性高 | 需手动处理复杂格式（如表格、图片） |
| **iText 7 + docx4j** | 集成度高，支持更多Word特性 | 仍有格式丢失风险，需额外依赖 |
| **Aspose.Words** | 转换质量极高，支持复杂文档 | 商业软件，需购买许可证 |

### **五、注意事项**

1. **格式限制**：

   - 纯文本Word文档转换效果较好，复杂格式（如嵌套表格、自定义样式）可能丢失。
   - 中文支持需确保使用包含中文字体的Font（如`STSong-Light`）。

1. **性能考虑**：

   - Apache POI解析大文档时可能较慢，可考虑分块处理或使用SAX模式。

1. **字体依赖**：

   - iText默认不包含中文字体，需手动指定或嵌入字体（如使用`BaseFont.createFont()`）。

1. **商业许可**：

   - Aspose.Words等商业库需购买许可证，否则生成的PDF会包含水印。

### **总结**

- **简单需求**：使用iText + Apache POI组合，适合纯文本或简单格式的Word文档。
- **复杂需求**：优先考虑Aspose.Words，可获得接近原生的转换效果。
- **现代Java**：iText 7 + docx4j是不错的选择，提供更简洁的API和更好的兼容性。
