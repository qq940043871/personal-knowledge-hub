# Token识别实现

> 模块：词法分析器
> 更新时间：2026-03-29

---

## 一、词法分析器实现

```java
public class Lexer {
    private String input;
    private int position = 0;
    private int line = 1;
    private int column = 1;
    private List<Token> tokens = new ArrayList<>();
    
    public Lexer(String input) {
        this.input = input;
    }
    
    public List<Token> tokenize() {
        while (position < input.length()) {
            skipWhitespace();
            if (position >= input.length()) break;
            
            char c = peek();
            
            if (Character.isLetter(c) || c == '_') {
                tokens.add(scanIdentifier());
            } else if (Character.isDigit(c)) {
                tokens.add(scanNumber());
            } else if (c == '\'' || c == '"') {
                tokens.add(scanString());
            } else if (c == '-') {
                tokens.add(scanComment());
            } else {
                tokens.add(scanOperator());
            }
        }
        
        tokens.add(new Token(Token.Type.EOF, "", position, line, column));
        return tokens;
    }
    
    private Token scanIdentifier() {
        int start = position;
        int startLine = line;
        int startColumn = column;
        
        StringBuilder sb = new StringBuilder();
        while (position < input.length()) {
            char c = peek();
            if (Character.isLetterOrDigit(c) || c == '_') {
                sb.append(c);
                advance();
            } else {
                break;
            }
        }
        
        String word = sb.toString();
        Token.Type type = getKeywordType(word);
        
        return new Token(type, word, start, startLine, startColumn);
    }
    
    private Token scanNumber() {
        int start = position;
        StringBuilder sb = new StringBuilder();
        
        while (position < input.length()) {
            char c = peek();
            if (Character.isDigit(c) || c == '.') {
                sb.append(c);
                advance();
            } else {
                break;
            }
        }
        
        String num = sb.toString();
        Token.Type type = num.contains(".") ? Token.Type.FLOAT : Token.Type.INTEGER;
        
        return new Token(type, num, start, line, column);
    }
    
    private Token scanString() {
        int start = position;
        char quote = peek();
        advance();
        
        StringBuilder sb = new StringBuilder();
        while (position < input.length() && peek() != quote) {
            if (peek() == '\\') {
                advance();
                char escaped = peek();
                switch (escaped) {
                    case 'n': sb.append('\n'); break;
                    case 't': sb.append('\t'); break;
                    case 'r': sb.append('\r'); break;
                    case '\\': sb.append('\\'); break;
                    case '\'': sb.append('\''); break;
                    case '"': sb.append('"'); break;
                    default: sb.append(escaped); break;
                }
            } else {
                sb.append(peek());
            }
            advance();
        }
        
        advance(); // 跳过结束引号
        
        return new Token(Token.Type.STRING, sb.toString(), start, line, column);
    }
    
    private Token scanComment() {
        int start = position;
        advance(); // 跳过 -
        
        if (peek() == '-') {
            advance();
            while (position < input.length() && peek() != '\n') {
                advance();
            }
            return new Token(Token.Type.EOF, "", start, line, column);
        }
        
        return new Token(Token.Type.MINUS, "-", start, line, column);
    }
    
    private Token scanOperator() {
        int start = position;
        char c = peek();
        advance();
        
        switch (c) {
            case '+': return new Token(Token.Type.PLUS, "+", start, line, column);
            case '-': return new Token(Token.Type.MINUS, "-", start, line, column);
            case '*': return new Token(Token.Type.STAR, "*", start, line, column);
            case '/': return new Token(Token.Type.SLASH, "/", start, line, column);
            case '%': return new Token(Token.Type.PERCENT, "%", start, line, column);
            case '(': return new Token(Token.Type.LPAREN, "(", start, line, column);
            case ')': return new Token(Token.Type.RPAREN, ")", start, line, column);
            case ',': return new Token(Token.Type.COMMA, ",", start, line, column);
            case '.': return new Token(Token.Type.DOT, ".", start, line, column);
            case ';': return new Token(Token.Type.SEMICOLON, ";", start, line, column);
            case '=': return new Token(Token.Type.EQ, "=", start, line, column);
            
            case '<':
                if (peek() == '=') { advance(); return new Token(Token.Type.LE, "<=", start, line, column); }
                if (peek() == '>') { advance(); return new Token(Token.Type.NE, "<>", start, line, column); }
                return new Token(Token.Type.LT, "<", start, line, column);
                
            case '>':
                if (peek() == '=') { advance(); return new Token(Token.Type.GE, ">=", start, line, column); }
                return new Token(Token.Type.GT, ">", start, line, column);
                
            case '!':
                if (peek() == '=') { advance(); return new Token(Token.Type.NE, "!=", start, line, column); }
                return new Token(Token.Type.ERROR, "!", start, line, column);
                
            default:
                return new Token(Token.Type.ERROR, String.valueOf(c), start, line, column);
        }
    }
    
    private char peek() {
        return position < input.length() ? input.charAt(position) : '\0';
    }
    
    private void advance() {
        if (position < input.length()) {
            if (input.charAt(position) == '\n') {
                line++;
                column = 1;
            } else {
                column++;
            }
            position++;
        }
    }
    
    private void skipWhitespace() {
        while (position < input.length() && Character.isWhitespace(peek())) {
            advance();
        }
    }
}
```

*图：tokenize() 主循环的字符分发流程（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 300" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="250" y="16" width="220" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="43" text-anchor="middle" font-size="14" fill="#1e293b">tokenize()：读取当前字符</text>
  <line x1="280" y1="60" x2="79" y2="100" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="320" y1="60" x2="221" y2="100" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="360" y1="60" x2="360" y2="100" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="400" y1="60" x2="499" y2="100" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="440" y1="60" x2="641" y2="100" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="11" y="104" width="130" height="80" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="76" y="126" text-anchor="middle" font-size="13" fill="#1e293b">字母 或 _</text>
  <text x="76" y="148" text-anchor="middle" font-size="12" fill="#475569">scanIdentifier</text>
  <text x="76" y="168" text-anchor="middle" font-size="12" fill="#475569">关键字·标识符</text>
  <rect x="153" y="104" width="130" height="80" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="218" y="126" text-anchor="middle" font-size="13" fill="#1e293b">数字</text>
  <text x="218" y="148" text-anchor="middle" font-size="12" fill="#475569">scanNumber</text>
  <text x="218" y="168" text-anchor="middle" font-size="12" fill="#475569">整数·浮点数</text>
  <rect x="295" y="104" width="130" height="80" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="126" text-anchor="middle" font-size="13" fill="#1e293b">引号 ' 或 "</text>
  <text x="360" y="148" text-anchor="middle" font-size="12" fill="#475569">scanString</text>
  <text x="360" y="168" text-anchor="middle" font-size="12" fill="#475569">字符串</text>
  <rect x="437" y="104" width="130" height="80" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="502" y="126" text-anchor="middle" font-size="13" fill="#1e293b">连字符 -</text>
  <text x="502" y="148" text-anchor="middle" font-size="12" fill="#475569">scanComment</text>
  <text x="502" y="168" text-anchor="middle" font-size="12" fill="#475569">注释·减号</text>
  <rect x="579" y="104" width="130" height="80" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="644" y="126" text-anchor="middle" font-size="13" fill="#1e293b">其他字符</text>
  <text x="644" y="148" text-anchor="middle" font-size="12" fill="#475569">scanOperator</text>
  <text x="644" y="168" text-anchor="middle" font-size="12" fill="#475569">运算符·ERROR</text>
  <line x1="76" y1="184" x2="308" y2="228" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="218" y1="184" x2="334" y2="228" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="360" y1="184" x2="360" y2="228" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="502" y1="184" x2="386" y2="228" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <line x1="644" y1="184" x2="412" y2="228" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw)"/>
  <rect x="190" y="232" width="340" height="56" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="360" y="255" text-anchor="middle" font-size="14" fill="#1e293b">生成 Token 加入 tokens 列表</text>
  <text x="360" y="276" text-anchor="middle" font-size="12" fill="#475569">循环至输入结束，追加 EOF 返回</text>
</svg>

---

*下一步：词法分析器编写*
