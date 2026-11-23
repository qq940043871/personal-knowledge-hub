# RAG与Long-Context之争—没必要争

👨🏻 作者：刘聪NLP📃 作者介绍：AIGC前沿知识分享&落地经验总结🛖 知乎主页：https://www.zhihu.com/people/LiuCongNLP⏰ 收录时间：2024-05-23 11:28:42🔗 原文链接：[https://mp.weixin.qq.com/s/IecOYCNM...](https://mp.weixin.qq.com/s/IecOYCNMIOd5xoMSbmYNKw)（原图见飞书文档，本地未能获取）关注作者公众号，获取更多AI知识

## **写在前面**

大家好，我是刘聪NLP。

随着大模型可以支持的上下文(Context)长度越来越长，网上（好几个群里都在聊这个话题，也来聊几句）竟然出现了RAG与Long-Context之争，是真没必要。。。主要是两者不冲突，并不是非A即B、非B即A的关系。

个人观点： **如果类比做检索系统的话，RAG应该算作粗排，而Long-Context可以算是精排。**RAG的本质是通过用户问题从数据库/知识库中找到相关片段内容，再利用大模型查找或总结出答案。Long-Context的本质是将所有文本内容全部灌入到大模型中，用户问一个问题，再利用大模型查找或总结出答案。

本质区别在于外部知识如何给到大模型，以及给多少到大模型。

这也是大家的所“争”之处，因为大模型可以接受的长度越长，那么检索的重要性就会降低， **对检索效果的依赖就会降低**，也就是为什么有人持观点，未来没有RAG，只有Long-Context。但大模型随着输入长度越长， **KV Cache所占资源就越多**，成本也会剧增，这也是为什么有人持观点，未来也会有RAG。

那么未来是多远呢？如果未来只是5年，我觉得RAG一定会存在；如果未来是AGI，那么也许不需要RAG。

## **为什么RAG是粗排，Long-Context是精排**

**从计算量角度来看**，目前RAG是靠检索系统来进行相关内容过滤，一般采用ES、向量匹配等方法，可以理解计算量较小，也就是文本之间交互较少；而Long-Context相当于用户Query与文本交互时，利用了整个大模型参数，即通过Transformer的每一层Attention来定位相关文本片段。

**从文本选择角度来看**，Long-Context可以类比成人为已经确定了问题的相关内容，而RAG需要借助检索手段来确定问题所涉及的相关内容，有一定的信息损失。

## **大模型上下文支持的越长，对RAG越友好**

RAG是目前大模型落地最快速、最有效、最安全的方式。但RAG依然存在很多问题，例如：文档在切段的过程中会将文本原始语义切割、检索匹配存在准确率的问题。但当大模型Context可以支持更长时，RAG可以对文档不切割甚至少切割，检索可以召回更多内容，Top10不够用我们就来Top100。

那么，

- 如果你站边RAG，那么大模型即使支持了Long-Context，它也是大模型；
- 如果你站边Long-Context，那么RAG就是在大模型支持无限Context前的过滤手段。

争与不争的核心问题在于数据库/知识库中内容长度是否会超出大模型所能支持的最大长度。

但检索越好、大模型支持长度越长，对于目前大模型落地、大模型可持续发展都是必不可少的， **we are famlily**！！！

## **Long-Context会打击到一些RAG的场景，但不是全部**

不可否认，Long-Context会打击到一些RAG的场景。

主要就是数据库/知识库内容不超过大模型最大长度的场景，例如：涉及场景中仅有几篇文档作为参考资料，完全不需要检索， **直接暴力解法都给大模型就完事儿了**。

但如果超出大模型最大长度的内容，不用检索过滤，请问阁下如何应对。

很多极端的人说可能就不存在领域大模型了，但仔细想想，即使Gemini支持1M Token、Kimi-Chat支持200w字，也就是400多个PDF(假设一个PDF平均有5k字)，垂直领域(不抬杠，这里特指一些大领域)数据何至于此呀。

还有，在场景中针对权限的判定，没必要用大模型来判断，完全可以进行域隔离就行，那么也无需将所有文本给到大模型（节省计算资源）。

PS: 说个题外话，貌似人一辈子也就产生0.3B左右的Tokens（之前群友讨论过这个话题），是不是当模型支持最大长度达到300M时，可以快速复制一个人了。不用微调，直接给库。

## **你能部署1M Token的大模型服务吗**

KV Cache的计算方式是4*Batch Size*模型层数L*注意力维度H*KV Cache长度，要硬支持1M长度的话，确实有些可怕。

当然目前有一些优化方法，滑动窗口、Cache量化等等等（欢迎大家补充），但即使这样由于大模型参数规模较大，显存占用也是很可怕的。并且滑动窗口貌似与感觉与retrieval差不多，都是有损失的。那么若可以接受损失，那么为什么不能接受retrieval。

当然前面聊的内容都没有考虑成本问题，但回归现实，请问有哪些厂家有能力部署支持1M Token的大模型模型服务，或者说部署这样一个模型的性价比如何？

对于ToC，大模型服务由大模型公司进行部署，成本由大模型公司承担，那么考虑的就是如何盈利的问题（当然可以为了梦想不考虑）。

对于ToB，会遇到一个很现实的问题，用了这么多显卡，能来什么？Long-Context相较于RAG来说，能否带来精度的提高，可以带来多少提高，是否会增加延迟，相同显卡情况下部署更大的模型+RAG是否更有性价比。

如果你遇到一个1张T4部署大模型的需求，就知道显示是多么残酷。 **并不是抬杠，只是我在路上走，目标活下去。**

## **如果你相信AGI，Cache所有文本就不是梦**

在技术飞速发展的时代，那么未来有一天，用较小的代价来Cache所有的文本也许不是梦。

但真的有必要吗？

Long-Context和RAG本质是都是让大模型找到更好的答案，真正智能还是要靠模型本身。接受更长的上下文可以侧面反应模型的智能，但模型的智能并不仅仅是接受更长的上下文。

## **写在最后**

做人不用太极端，世界上也并非是非黑即白，条条大路都通AGI。

往期推荐：

- [**角色扮演大模型的碎碎念**](https://mp.weixin.qq.com/s?__biz=Mzg5MTU1NTE1OQ==&mid=2247488277&idx=1&sn=eb1b190b527f15e2cba0c59af4d91199&scene=21#wechat_redirect)
- [**自我蒸馏方法-减轻大模型微调过程中的灾难性遗忘**](https://mp.weixin.qq.com/s?__biz=Mzg5MTU1NTE1OQ==&mid=2247488268&idx=1&sn=b4b0d165fab9b546ef543b597dac6b14&scene=21#wechat_redirect)
- [**Yi技术报告细节分享**](https://mp.weixin.qq.com/s?__biz=Mzg5MTU1NTE1OQ==&mid=2247488248&idx=1&sn=da8b5d9b5aa374d56f1641a1e4938283&scene=21#wechat_redirect)
- [**大模型增量预训练新技巧-解决灾难性遗忘**](https://mp.weixin.qq.com/s?__biz=Mzg5MTU1NTE1OQ==&mid=2247488117&idx=1&sn=674e8e4b93773d03e7f1d659cb5ac070&scene=21#wechat_redirect)
- [**如何提高LLMs的文本表征(Text Embedding)能力?**](https://mp.weixin.qq.com/s?__biz=Mzg5MTU1NTE1OQ==&mid=2247487965&idx=1&sn=88cb466344722f4d027390b107f4290a&scene=21#wechat_redirect)
- [**DEITA-大模型指令微调的数据高效筛选方法**](https://mp.weixin.qq.com/s?__biz=Mzg5MTU1NTE1OQ==&mid=2247487947&idx=1&sn=0b23e924df987565c4808f74dbf79ddd&scene=21#wechat_redirect)
- [**大模型微调技巧 | 高质量指令数据筛选方法-MoDS**](https://mp.weixin.qq.com/s?__biz=Mzg5MTU1NTE1OQ==&mid=2247487747&idx=1&sn=f11dafe28e8ceb0faa38c9d55a262633&scene=21#wechat_redirect)
- [**辟谣！微软撤回声称ChatGPT为20B参数的论文，并给出解释。**](https://mp.weixin.qq.com/s?__biz=Mzg5MTU1NTE1OQ==&mid=2247487334&idx=1&sn=610b8af83bb7002dffe6805f1874f962&scene=21#wechat_redirect)
- [**如何看待微软论文声称 ChatGPT 是 20B (200亿) 参数量的模型？**](https://mp.weixin.qq.com/s?__biz=Mzg5MTU1NTE1OQ==&mid=2247487327&idx=1&sn=593923b9ca8fd01a58e769b52d002884&scene=21#wechat_redirect)
- [**大模型微调技巧-在Embeeding上加入噪音提高指令微调效果**](https://mp.weixin.qq.com/s?__biz=Mzg5MTU1NTE1OQ==&mid=2247487123&idx=1&sn=b337c8a718c7998e507004ff189483ca&scene=21#wechat_redirect)
- [**如何从数据集中自动识别高质量的指令数据**](https://mp.weixin.qq.com/s?__biz=Mzg5MTU1NTE1OQ==&mid=2247486951&idx=1&sn=e4bd058dbe9c191ecfeec3c75e8bff06&scene=21#wechat_redirect)
- [**BaiChuan2技术报告细节分享&个人想法**](https://mp.weixin.qq.com/s?__biz=Mzg5MTU1NTE1OQ==&mid=2247486892&idx=1&sn=d5ce452857d4c0facad23ce5d11c7a5b&scene=21#wechat_redirect)
- [**大模型LLM微调经验总结&项目更新**](https://mp.weixin.qq.com/s?__biz=Mzg5MTU1NTE1OQ==&mid=2247486639&idx=1&sn=ce712cf3d28d9c2f73cfa2a6430a3c60&scene=21#wechat_redirect)
- [**打造LLM界的Web UI**](https://mp.weixin.qq.com/s?__biz=Mzg5MTU1NTE1OQ==&mid=2247486578&idx=1&sn=8fc505e81e2a479bfaf9b5b15d120808&scene=21#wechat_redirect)
- [**是我们在训练大模型，还是大模型在训练我们？**](https://mp.weixin.qq.com/s?__biz=Mzg5MTU1NTE1OQ==&mid=2247486542&idx=1&sn=7b499f03dffb9c0954423bfc33b686af&scene=21#wechat_redirect)
- [**Llama2技术细节&开源影响**](https://mp.weixin.qq.com/s?__biz=Mzg5MTU1NTE1OQ==&mid=2247486512&idx=1&sn=73d2b6dd73051e85bf6b9f630919f3d9&scene=21#wechat_redirect)
- [**大模型时代-行业落地再思考**](https://mp.weixin.qq.com/s?__biz=Mzg5MTU1NTE1OQ==&mid=2247486493&idx=1&sn=d58830d103a21e141a20d308f2ad3a83&scene=21#wechat_redirect)
- [**垂直领域大模型的一些思考及开源模型汇总**](https://mp.weixin.qq.com/s?__biz=Mzg5MTU1NTE1OQ==&mid=2247486425&idx=1&sn=3838157c39962946702c85faea61ccc0&scene=21#wechat_redirect)
- [**如何评估大模型-LLMs的好坏？**](https://mp.weixin.qq.com/s?__biz=Mzg5MTU1NTE1OQ==&mid=2247486414&idx=1&sn=013cf0a463dc22ddaa9fde69aeeb2e8b&scene=21#wechat_redirect)
- [**总结|Prompt在NER场景的应用**](https://mp.weixin.qq.com/s?__biz=Mzg5MTU1NTE1OQ==&mid=2247485753&idx=1&sn=dc46fcdf332b52be8233f4992c6fd0df&scene=21#wechat_redirect)