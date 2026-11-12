# Java-集合

关键操作：初始化、新增、删除、底层（链表、索引、树、图）

| 名称 | 是否允许空 | 是否允许重复数据 | 是否有序 | 是否线程安全  | 备注 |
| --- | --- | --- | --- | --- | --- |
| ArrayList | 允许 | 允许 | 有序 | 否 | |
| LinkedList | 允许 | 允许 | 有序 | 否 | |
| CopyOnWriteArrayList | 允许 | 允许 | 有序 | 是 | |
| HashMap | Key和value都允许 | Key会覆盖，value重复 | 无序 | 否 | |
| LinkedHashMap | Key和value都允许 | Key会覆盖，value重复 | 有序 | 否 | |
| 红黑树 | Key不允许，value允许 | Key会覆盖，value重复 | 有序 | 否 | |
| 优先队列 | | | | | |
| 阻塞队列 | | | | | |

## 什么时候用LinkedList，什么时候用ArrayList？

![](images/1665570148499-728eb0a4-9108-42a7-8530-e1d8b51a4c85-668a1e88.png)

## 如何边遍历边移除Collection中的元素

![](images/1665570159126-e8decea1-e064-49c5-a3a5-ad6cda0f572e-899f1c2d.png)

## 如何将List转化成int[]？

![](images/1665570174330-2d08688f-0bc6-4c0e-804c-d31b1c0c42af-df62144a.png)

## 如何将int[]转化成List？

![](images/1665570187423-fdfb8b76-5484-442c-bc09-f377aaab8381-fa6d045c.png)

![](images/1665570196691-80dad8de-9d0c-449c-9704-8c07f53ca89b-f1524140.png)

## 过滤一个Collection最好的方法是什么？

![](images/1665570206193-366b1898-4d96-4bc2-9012-d5e176afff67-0e47ea82.png)

## 将List转化成Set最简单的方法？

![](images/1665570214473-5657c440-0c10-49a5-b215-86f6ea17f9ad-9e48675b.png)

## 如何删除ArrayList中重复的元素？

![](images/1665570221973-32675f88-fc1b-4275-a9b8-f2e4bc2bfe48-5df493ad.png)

## 有序的collection

![](images/1665570230165-57dc3e61-8e92-4956-a597-48c89a007048-28803a40.png)

## 拷贝list

![](images/1665570239820-3000eb88-c7a5-4785-b14b-865cdca3302e-ba01490a.png)
