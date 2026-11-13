# pdf增加页码

## **PdfConvert 类的页码添加实现**

要在 `PdfConvert.getInstance().convert()` 方法中添加页码功能，我们需要结合 iText 的 `PdfPageEventHelper` 监听页面事件，并在每页底部添加页码。以下是具体实现方案：

### **方案一：使用事件监听器（推荐）**

通过自定义事件监听器，在页面生成完成后自动添加页码：

```Java
import com.itextpdf.text.*;
import com.itextpdf.text.pdf.*;

import java.io.*;

public class PdfConvert {
    private static final PdfConvert instance = new PdfConvert();
    
    private PdfConvert() {}
    
    public static PdfConvert getInstance() {
        return instance;
    }
    
    // 核心转换方法
    public void convert(String srcPath, String destPath) throws IOException, DocumentException {
        // 读取源PDF
        PdfReader reader = new PdfReader(srcPath);
        int pageCount = reader.getNumberOfPages();
        
        // 创建输出文档
        Document document = new Document(reader.getPageSize(1));
        PdfWriter writer = PdfWriter.getInstance(document, new FileOutputStream(destPath));
        
        // 添加页码事件监听器
        writer.setPageEvent(new PageNumberEvent());
        
        document.open();
        
        // 复制每一页并添加内容
        for (int i = 1; i <= pageCount; i++) {
            document.newPage();
            PdfImportedPage page = writer.getImportedPage(reader, i);
            writer.getDirectContent().addTemplate(page, 0, 0);
        }
        
        document.close();
        reader.close();
    }
    
    // 自定义页码事件监听器
    private static class PageNumberEvent extends PdfPageEventHelper {
        private Font pageNumberFont;
        
        public PageNumberEvent() {
            try {
                // 创建支持中文的字体
                BaseFont bf = BaseFont.createFont(
                    BaseFont.HELVETICA, BaseFont.WINANSI, BaseFont.NOT_EMBEDDED);
                pageNumberFont = new Font(bf, 10, Font.NORMAL);
            } catch (DocumentException | IOException e) {
                e.printStackTrace();
            }
        }
        
        @Override
        public void onEndPage(PdfWriter writer, Document document) {
            // 获取当前页面尺寸
            Rectangle rect = document.getPageSize();
            
            // 计算页码位置（底部中央）
            float x = (rect.getLeft() + rect.getRight()) / 2;
            float y = rect.getBottom() + 20;
            
            // 添加页码文本
            PdfContentByte cb = writer.getDirectContent();
            Phrase footer = new Phrase(
                "第 " + writer.getPageNumber() + " 页", pageNumberFont);
            
            ColumnText.showTextAligned(
                cb, Element.ALIGN_CENTER, footer, x, y, 0);
        }
    }
}
```

### **方案二：直接操作PDF内容（无事件监听器）**

如果不想使用事件监听器，可以直接遍历页面并添加页码：

```Java
import com.itextpdf.text.*;
import com.itextpdf.text.pdf.*;

import java.io.*;

public class PdfConvert {
    private static final PdfConvert instance = new PdfConvert();
    
    private PdfConvert() {}
    
    public static PdfConvert getInstance() {
        return instance;
    }
    
    // 核心转换方法
    public void convert(String srcPath, String destPath) throws IOException, DocumentException {
        // 读取源PDF
        PdfReader reader = new PdfReader(srcPath);
        int pageCount = reader.getNumberOfPages();
        
        // 创建输出文档
        Document document = new Document(reader.getPageSize(1));
        PdfWriter writer = PdfWriter.getInstance(document, new FileOutputStream(destPath));
        document.open();
        
        // 创建页码字体
        BaseFont bf = BaseFont.createFont(
            BaseFont.HELVETICA, BaseFont.WINANSI, BaseFont.NOT_EMBEDDED);
        Font pageNumberFont = new Font(bf, 10, Font.NORMAL);
        
        // 处理每一页
        for (int i = 1; i <= pageCount; i++) {
            document.newPage();
            
            // 复制原页面内容
            PdfImportedPage page = writer.getImportedPage(reader, i);
            writer.getDirectContent().addTemplate(page, 0, 0);
            
            // 添加页码
            addPageNumber(writer, document, i, pageCount, pageNumberFont);
        }
        
        document.close();
        reader.close();
    }
    
    // 添加页码的辅助方法
    private void addPageNumber(PdfWriter writer, Document document, 
                              int pageNum, int totalPages, Font font) {
        // 获取当前页面尺寸
        Rectangle rect = document.getPageSize();
        
        // 计算页码位置（底部中央）
        float x = (rect.getLeft() + rect.getRight()) / 2;
        float y = rect.getBottom() + 20;
        
        // 添加页码文本
        PdfContentByte cb = writer.getDirectContent();
        Phrase footer = new Phrase(
            "第 " + pageNum + " 页 / 共 " + totalPages + " 页", font);
        
        ColumnText.showTextAligned(
            cb, Element.ALIGN_CENTER, footer, x, y, 0);
    }
}
```

### **使用示例**

```Java
public class Main {
    public static void main(String[] args) {
        try {
            PdfConvert.getInstance().convert("input.pdf", "output.pdf");
            System.out.println("PDF转换完成，已添加页码！");
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```

### **方案比较**

| **方案** | **优点** | **缺点** |
|-|-|-|
| **事件监听器** | 代码分离，逻辑清晰，易于扩展 | 需要了解iText事件机制 |
| **直接操作** | 简单直观，无需额外类 | 代码耦合度高，扩展性差 |

### **注意事项**

1. **中文支持**：如果需要显示中文页码，确保使用支持中文的字体（如`STSong-Light`）。

1. **页码位置**：可以通过调整`x`和`y`坐标来自定义页码位置（如顶部、底部、左侧等）。

1. **格式优化**：

   - 如需更复杂的页码格式（如"Page 1 of 10"），修改`Phrase`内容即可。
   - 可以添加页码样式（如字体颜色、大小、加粗等）。

1. **性能考虑**：对于大型PDF，可考虑使用`PdfStamper`直接在原文件上添加页码，避免创建新文档。
