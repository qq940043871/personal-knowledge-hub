# Transformer架构完全解析：从输入输出到内部数据结构变化

> 本文目标：彻底搞懂Transformer架构的每一个组件，以及输入、处理、输出全流程中的数据结构变化。所有内容都附带张量形状演示，帮助你建立清晰的数值直觉。

Transformer是2017年《Attention Is All You Need》论文中提出的序列到序列架构，完全基于自注意力机制，摒弃了传统的循环神经网络结构。它由编码器（Encoder）和解码器（Decoder）两大部分组成，通常编码器有N层，解码器也有N层（论文中N=6）。

*图：Transformer 前向数据流与论文默认参数（示意）*

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 240" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="arw1" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/>
    </marker>
  </defs>
  <rect x="20" y="25" width="150" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="95" y="52" text-anchor="middle" font-size="13" fill="#1e293b">输入文本</text>
  <line x1="170" y1="47" x2="196" y2="47" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw1)"/>
  <rect x="200" y="25" width="150" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="275" y="52" text-anchor="middle" font-size="13" fill="#1e293b">分词（Tokenization）</text>
  <line x1="350" y1="47" x2="376" y2="47" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw1)"/>
  <rect x="380" y="25" width="150" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="455" y="52" text-anchor="middle" font-size="13" fill="#1e293b">词嵌入（d_model=512）</text>
  <line x1="530" y1="47" x2="556" y2="47" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw1)"/>
  <rect x="560" y="25" width="150" height="44" rx="8" fill="#fffbeb" stroke="#d97706" stroke-width="1.5"/>
  <text x="635" y="52" text-anchor="middle" font-size="13" fill="#1e293b">⊕ 位置编码</text>
  <line x1="635" y1="69" x2="635" y2="131" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw1)"/>
  <rect x="560" y="135" width="150" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="635" y="162" text-anchor="middle" font-size="13" fill="#1e293b">Encoder × N</text>
  <line x1="560" y1="157" x2="536" y2="157" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw1)"/>
  <rect x="380" y="135" width="150" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="455" y="162" text-anchor="middle" font-size="13" fill="#1e293b">Decoder × N</text>
  <line x1="380" y1="157" x2="356" y2="157" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw1)"/>
  <rect x="200" y="135" width="150" height="44" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="275" y="162" text-anchor="middle" font-size="13" fill="#1e293b">Linear + Softmax</text>
  <line x1="200" y1="157" x2="176" y2="157" stroke="#94a3b8" stroke-width="1.5" marker-end="url(#arw1)"/>
  <rect x="20" y="135" width="150" height="44" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
  <text x="95" y="162" text-anchor="middle" font-size="13" fill="#1e293b">输出 token 概率分布</text>
  <text x="360" y="204" text-anchor="middle" font-size="12" fill="#475569">论文默认参数：N=6，d_model=512，h=8，d_k=64，d_ff=2048</text>
  <text x="360" y="226" text-anchor="middle" font-size="12" fill="#475569">每个子层均带残差连接与层归一化</text>
</svg>

## 1. 输入处理：分词、词嵌入与位置编码

输入处理是Transformer的第一步，将自然语言文本转换为模型可以处理的数值张量。这个过程包含三个主要步骤：分词（Tokenization）、词嵌入（Embedding）和位置编码（Positional Encoding）。

### 分词（Tokenization）

分词的作用是将连续的文本分割成离散的token（可以是字、词或子词），然后将每个token映射为对应的整数ID。现代Transformer通常使用子词分词算法，如BPE（Byte Pair Encoding）或WordPiece。

### 词嵌入（Embedding）

词嵌入层是一个可训练的查找表，将每个token的整数ID映射为一个d_model维的稠密向量。这个向量包含了token的语义信息。

### 位置编码（Positional Encoding）

由于Transformer没有循环结构，无法天然感知token的顺序信息，因此需要显式地加入位置编码。位置编码为每个位置生成一个d_model维的向量，与词向量相加，作为模型的最终输入。

> 论文中使用正弦余弦位置编码，公式如下：
> 其中pos是位置索引，i是维度索引。这种位置编码可以泛化到比训练时更长的序列。

## 2. 编码器：多头自注意力与前馈网络

编码器由N个相同的层堆叠而成（论文中N=6），每个编码器层包含两个子层：多头自注意力机制和前馈神经网络，每个子层周围都有残差连接和层归一化。

### 多头自注意力

自注意力机制允许模型在处理每个token时，关注序列中所有其他token的信息。多头注意力将注意力计算分成多个独立的头，每个头可以学习不同类型的注意力模式。

这是注意力的基本计算单元，通过计算Query和Key的相似度，得到权重，然后对Value进行加权求和。

> 缩放点积注意力公式：
> 除以√d_k是为了防止点积值过大导致softmax进入梯度饱和区。

多头注意力将Q、K、V通过不同的线性投影分成h个头，每个头独立计算注意力，然后将所有头的结果拼接起来，再通过一个线性层得到最终输出。

### 前馈神经网络（FFN）

每个编码器层的第二个子层是前馈神经网络，它对每个位置的表示独立地进行相同的线性变换和非线性激活。

> 前馈网络公式：
> 包含两个线性层，中间是ReLU激活函数。论文中d_ff=2048，是d_model的4倍。

## 3. 解码器与输出生成

解码器也由N个相同的层堆叠而成（论文中N=6），每个解码器层包含三个子层：掩码多头自注意力机制、多头交叉注意力机制和前馈神经网络，同样都带有残差连接和层归一化。

解码器的输出经过线性层和Softmax层，转换为每个位置上各个token的概率分布，然后通过贪心搜索或束搜索得到最终的输出文本。

## 4. 前向传播全流程的张量形状变化

下面以一个具体的例子展示Transformer完整前向传播过程中每一步的张量形状变化，使用论文中的默认参数：d_model=512, h=8, d_k=64, d_ff=2048, N=6。

## 5. 总结：自注意力是核心创新

Transformer是现代大语言模型的基础架构，其核心创新是**自注意力机制**，解决了传统RNN无法并行计算和长程依赖建模困难的问题。

> 现在你已经全面掌握了Transformer的架构原理和每个步骤的张量形状变化！这些知识是理解GPT、BERT、LLaMA等所有大语言模型的基础。
