# CFCA证书名称处理

1. RA系统中注销证书
2. CFCA提供pfx证书
3. keytool转换jks证书

```shell
keytool -importkeystore -srckeystore your_certificate.pfx -srcstoretype PKCS12 -destkeystore your_keystore.jks -deststoretype JKS
```

4. 替换ra系统中的jks证书
5. 如何重新申请证书（而不是自动续费）

:::info
信任度的这种表 company_info的act_status字段 帮我修改成0

修改为非激活状态下，即可默认是新颁发证书

:::

6. 信任度表结构

[zd_db.sql](https://www.yuque.com/attachments/yuque/0/2025/sql/960423/1736839971258-ed645878-5aa3-4379-b21f-162abf130197.sql)

7. 由于多颁发新证书，在信任度系统中存在多证书，需要删除原证书，保证使用到新证书

```shell
cert_info中的旧证书 需要删除
```

8. 重新两码激活
9. 针对合同签章即可
