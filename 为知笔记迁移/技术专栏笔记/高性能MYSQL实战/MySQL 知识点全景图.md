# MySQL 知识点全景图

另外，为了帮助大家理清学习思路，我整理了一个比较全面的 MySQL 知识点全景图如下，包括系统、网络、硬件、到性能优化、高可用、架构设计等等方面，这些知识点会贯穿整个课程。

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 440" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <text x="320" y="32" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">MySQL 知识点全景导图</text>
  <line x1="235" y1="212" x2="220" y2="90" stroke="#64748b" stroke-width="1.5"/>
  <line x1="235" y1="220" x2="220" y2="220" stroke="#64748b" stroke-width="1.5"/>
  <line x1="235" y1="228" x2="220" y2="350" stroke="#64748b" stroke-width="1.5"/>
  <line x1="405" y1="212" x2="420" y2="90" stroke="#64748b" stroke-width="1.5"/>
  <line x1="405" y1="220" x2="420" y2="220" stroke="#64748b" stroke-width="1.5"/>
  <line x1="405" y1="228" x2="420" y2="350" stroke="#64748b" stroke-width="1.5"/>
  <rect x="235" y="195" width="170" height="50" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="320" y="225" text-anchor="middle" font-size="13" fill="#1e293b">MySQL 知识点全景</text>
  <rect x="30" y="70" width="190" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="125" y="95" text-anchor="middle" font-size="13" fill="#1e293b">系统·网络·硬件</text>
  <rect x="30" y="200" width="190" height="40" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="125" y="217" text-anchor="middle" font-size="13" fill="#1e293b">性能优化</text>
  <text x="125" y="235" text-anchor="middle" font-size="12" fill="#475569">系统/参数/SQL/业务</text>
  <rect x="30" y="330" width="190" height="40" rx="8" fill="#f5f3ff" stroke="#7c3aed" stroke-width="1.5"/>
  <text x="125" y="355" text-anchor="middle" font-size="13" fill="#1e293b">MySQL 复制（原理/类型）</text>
  <rect x="420" y="70" width="190" height="40" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="515" y="95" text-anchor="middle" font-size="13" fill="#1e293b">InnoDB 技术焦点</text>
  <rect x="420" y="200" width="190" height="40" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="515" y="225" text-anchor="middle" font-size="13" fill="#1e293b">高可用架构</text>
  <rect x="420" y="330" width="190" height="40" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="515" y="355" text-anchor="middle" font-size="13" fill="#1e293b">容量规划与生态</text>
</svg>

*图：MySQL 知识点全景导图（据原文重绘）*

比如，优化包括数据库针对系统的优化，针对数据库本身参数的优化，针对SQL的优化，针对业务的优化等等。还有一个比较关键的点——InnoDB，因为一般使用 MySQL 都会使用 InnoDB 作为存储引擎，所以 InnoDB 有很多技术焦点和特性，需要你去学习和了解。另外就是数据库的复制、MySQL Replication，这也是经常会被面试官所考察的，包括复制的原理、复制的类型、各种复制之间的差异等等。还有就是从顶层来看，数据库的容量规划这么多，数据库的生态体系该怎么掌握，或者是怎么学习？等等，就不一一列举了。
