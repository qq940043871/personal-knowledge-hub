# Jvm常用命令

> 注：原为知导出时丢失了部分数字参数，已按运维常识修复可推断项（修复处均已标注）；无法唯一推断的以 N / [pid] 占位，请按需填写。

* jvm内存使用情况

* jmap -histo pid | head -n N 查看前N位（注：原导出参数缺失，N为占位名次）
* jmap -histo pid | sort -k2 -g -r 查看对象数最多的对象，按降序输出（注：原导出参数缺失，jmap -histo 第2列为对象实例数，此处为修复值）
* jmap -histo pid | sort -k3 -g -r 查看内存的对象，按降序输出（注：原导出参数缺失，jmap -histo 第3列为内存字节数，此处为修复值）
* jmap -dump:format=b,file=heap.hprof [pid]（注：原导出参数缺失，[pid]为占位）
* jmap -heap [pid]:查看jvm空间分布

* jstat：Java虚拟机统计工具，可以用于监视JVM各种堆和非堆内存大小和使用量

* jstat -class pid：输出加载类的数量及所占空间信息
* jstat -gc pid：输出gc信息，包括gc次数和时间，内存使用状况（可带时间和显示条目参数）

* jstack

* jstack pid jvm线程情况

* jstat

* jstat -gcutil
* vi

* 显示行号 :set number
* 跳转到最后一行 :$
* 跳转到第一行 :1（注：原导出参数缺失，"跳转到第一行"即 :1，此处为修复值） 跳转到任一行 :行号 $表示跳转到行尾
