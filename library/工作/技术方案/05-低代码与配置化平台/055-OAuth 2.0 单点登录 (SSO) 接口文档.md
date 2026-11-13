# OAuth 2.0 单点登录 (SSO) 接口文档

## 变更记录
| **序号** | **编写人** | **编写日期** | **版本号** | **变更内容描述** | **备注** |
| :--- | --- | :--- | :--- | :--- | :--- |
| 1 |  | 2025-08-16 | V0.1.0 | 初稿 |  |
| 2 |  |  |  |  |  |
| 3 |  |  |  |  |  |
| 4 |  |  |  |  |  |
| 5 |  |  |  |  |  |
| 6 |  |  |  |  |  |
| 7 |  |  |  |  |  |
| 8 |  |  |  |  |  |
| 9 |  |  |  |  |  |
| 10 |  |  |  |  |  |

## 1. 文档概述
本文档详细描述了基于 OAuth 2.0 协议实现的单点登录 (SSO) 系统接口规范，包括认证流程、各端点的请求与响应格式、错误码及安全注意事项。

### 1.1. 流程示意图
![](images/1755303906668-ed9a5359-f81c-477e-b5b2-7c2e1763c7a0-fe26aa83.png)

## 2. 术语与定义
+ **客户端 (Client)**: 接入 SSO 系统的第三方应用
+ **资源所有者 (Resource Owner)**: 拥有账号信息的用户
+ **授权服务器 (Authorization Server)**: 负责认证用户并颁发令牌的服务器
+ **资源服务器 (Resource Server)**: 存储用户资源的服务器，本文档中主要指用户信息服务
+ **令牌 (Token)**: 授权凭证，包括访问令牌和刷新令牌
+ **回调 URI (Redirect URI)**: 授权完成后跳转的客户端地址

## 3. 认证流程概述
本系统采用 OAuth 2.0 授权码模式 (Authorization Code Flow) 实现单点登录，流程如下：

1. 客户端引导用户到授权服务器
2. 用户在授权服务器进行身份认证并授权
3. 授权服务器返回授权码给客户端
4. 客户端使用授权码向授权服务器请求令牌
5. 授权服务器验证授权码并颁发令牌
6. 客户端使用访问令牌请求用户信息
7. 资源服务器验证令牌并返回用户信息

## 4. 接口详情
### 4.1 获取授权码
#### 4.1.1 功能描述
引导用户进行身份认证并获取授权，成功后返回授权码。

#### 4.1.2 请求信息
+ **URL**: `https://sso.example.com/oauth/authorize`
+ **方法**: GET
+ **参数**:

| **参数名** | **类型** | **必选** | **描述** |
| :--- | :--- | :--- | :--- |
| response_type | string | 是 | 固定值 "code"，表示采用授权码模式 |
| client_id | string | 是 | 客户端唯一标识，由系统分配 |
| redirect_uri | string | 是 | 授权完成后的回调地址，必须与客户端注册的地址一致 |
| state | string | 否 | 客户端生成的随机字符串，用于防止 CSRF 攻击，服务器会原样返回 |

#### 4.1.3 响应信息
成功时将用户重定向到`redirect_uri`，并附加以下参数：

+ **code**: 授权码，有效期 5 分钟
+ **state**: 客户端传入的 state 参数

示例：

```plain
https://client.example.com/callback?code=AUTHORIZATION_CODE&state=STATE_VALUE
```

#### 4.1.4 错误响应
授权失败时将用户重定向到`redirect_uri`，并附加以下参数：

+ **error**: 错误代码
+ **error_description**: 错误描述
+ **state**: 客户端传入的 state 参数

示例：

**plaintext**

```plain
https://client.example.com/callback?error=access_denied&error_description=User+denied+access&state=STATE_VALUE
```

### 4.2 获取访问令牌
#### 4.2.1 功能描述
使用授权码换取访问令牌和刷新令牌。

#### 4.2.2 请求信息
+ **URL**: `https://sso.example.com/oauth/token`
+ **方法**: POST
+ **Content-Type**: application/x-www-form-urlencoded
+ **请求头**:
    - Authorization: Basic Base64(client_id:client_secret)
+ **参数**:

| **参数名** | **类型** | **必选** | **描述** |
| :--- | :--- | :--- | :--- |
| grant_type | string | 是 | 固定值 "authorization_code" |
| code | string | 是 | 从授权端点获取的授权码 |
| redirect_uri | string | 是 | 必须与获取授权码时使用的 redirect_uri 一致 |

#### 4.2.3 响应信息
+ **Content-Type**: application/json
+ 成功响应示例

**json**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "def50200a56a1f1...",
  "scope": "userinfo"
}
```

| **参数名** | **类型** | **描述** |
| :--- | :--- | :--- |
| access_token | string | 访问令牌 |
| token_type | string | 令牌类型，固定为 "bearer" |
| expires_in | integer | 访问令牌有效期，单位：秒 |
| refresh_token | string | 刷新令牌，用于获取新的访问令牌 |
| scope | string | 实际授予的权限范围 |

#### 4.2.4 错误响应
+ **Content-Type**: application/json
+ 错误响应示例：

**json**

```json
{
  "error": "invalid_grant",
  "error_description": "Invalid authorization code"
}
```

### 4.3 刷新令牌
#### 4.3.1 功能描述
使用刷新令牌获取新的访问令牌。

#### 4.3.2 请求信息
+ **URL**: `https://sso.example.com/oauth/refresh_token`
+ **方法**: POST
+ **Content-Type**: application/x-www-form-urlencoded
+ **请求头**:
    - Authorization: Basic Base64(client_id:client_secret)
+ **参数**:

| **参数名** | **类型** | **必选** | **描述** |
| :--- | :--- | :--- | :--- |
| grant_type | string | 是 | 固定值 "refresh_token" |
| refresh_token | string | 是 | 从令牌端点获取的刷新令牌 |
| scope | string | 否 | 请求的权限范围，不能超出原授权范围 |

#### 4.3.3 响应信息
与令牌端点的成功响应格式相同，可能会返回新的刷新令牌。

### 4.4 用户信息
#### 4.4.1 功能描述
使用访问令牌获取用户基本信息。

#### 4.4.2 请求信息
+ **URL**: `https://sso.example.com/oauth/userinfo`
+ **方法**: GET
+ **请求头**:
    - Authorization: Bearer {access_token}

#### 4.4.3 响应信息
+ **Content-Type**: application/json
+ 成功响应示例：

**json**

```json
{
  "userid": "客户唯一编号",
  "username": "客户姓名",
  "parentMerchantNo": "平台的商户编号",
  "merchantNo": "境内买家的商户编号",
  "payerAccountName": "付款方名称",
  "payerAccountNo": "付款方账号"
}
```

### 4.5 注销
#### 4.5.1 功能描述
使令牌失效，实现单点登出。

#### 4.5.2 请求信息
+ **URL**: `https://sso.example.com/oauth/revoke`
+ **方法**: POST
+ **Content-Type**: application/x-www-form-urlencoded
+ **请求头**:
    - Authorization: Basic Base64(client_id:client_secret)
+ **参数**:

| **参数名** | **类型** | **必选** | **描述** |
| :--- | :--- | :--- | :--- |
| token | string | 是 | 要撤销的令牌（访问令牌或刷新令牌） |
| token_type_hint | string | 否 | 令牌类型，可选值：access_token、refresh_token |

#### 4.5.3 响应信息
+ 成功：HTTP 200 OK，无响应体
+ 失败：返回错误信息，格式同令牌端点的错误响应

## 5. 错误码说明
| **错误码** | **描述** | **常见场景** |
| :--- | :--- | :--- |
| invalid_request | 请求参数缺失或无效 | 缺少必要参数、参数格式错误 |
| unauthorized_client | 客户端未被授权 | 客户端 ID 无效、未注册 |
| access_denied | 访问被拒绝 | 用户拒绝授权、客户端权限不足 |
| unsupported_response_type | 不支持的响应类型 | response_type 值不正确 |
| invalid_scope | 无效的权限范围 | 请求的 scope 不存在或不被支持 |
| server_error | 服务器内部错误 | 服务器处理请求时发生错误 |
| temporarily_unavailable | 服务暂时不可用 | 服务器暂时无法处理请求 |
| invalid_grant | 无效的授权凭证 | 授权码已过期或被使用、刷新令牌无效 |
| invalid_client | 客户端认证失败 | client_id 或 client_secret 错误 |

## 6. 安全注意事项
1. 所有接口必须使用 HTTPS 协议传输
2. 客户端应妥善保管 client_secret，不得在前端代码中暴露
3. state 参数必须使用随机字符串，并在回调时验证，防止 CSRF 攻击
4. 授权码和令牌应视为敏感信息，不得在日志中明文记录
5. 建议客户端实现令牌轮换机制，定期使用刷新令牌获取新的访问令牌
6. 客户端应在访问令牌过期前主动使用刷新令牌获取新令牌
7. 用户登出时，客户端应调用注销接口使令牌失效

## 7. 完整流程示例
1. **客户端引导用户到授权服务器**

```plain
GET https://sso.example.com/oauth/authorize?
  response_type=code&
  client_id=CLIENT_ID&
  redirect_uri=https%3A%2F%2Fclient.example.com%2Fcallback&
  scope=userinfo&
  state=random_state_value
```

2. **用户认证授权后，授权服务器重定向到回调地址**

```plain
GET https://client.example.com/callback?
  code=AUTHORIZATION_CODE&
  state=random_state_value
```

3. **客户端使用授权码换取令牌**

```plain
POST https://sso.example.com/oauth/token
Content-Type: application/x-www-form-urlencoded
Authorization: Basic Base64(CLIENT_ID:CLIENT_SECRET)

grant_type=authorization_code&
code=AUTHORIZATION_CODE&
redirect_uri=https%3A%2F%2Fclient.example.com%2Fcallback
```

4. **授权服务器返回令牌**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "def50200a56a1f1...",
  "scope": "userinfo"
}
```

5. **客户端获取用户信息**

```plain
GET https://sso.example.com/oauth/userinfo
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

6. **客户端获取用户信息成功**

```json
{
  "userid": "客户唯一编号",
  "username": "客户姓名",
  "parentMerchantNo": "平台的商户编号",
  "merchantNo": "境内买家的商户编号",
  "payerAccountName": "付款方名称",
  "payerAccountNo": "付款方账号"
}
```

7. **用户登出，客户端撤销令牌**

```plain
POST https://sso.example.com/oauth/revoke
Content-Type: application/x-www-form-urlencoded
Authorization: Basic Base64(CLIENT_ID:CLIENT_SECRET)

token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...&
token_type_hint=access_token
```

---
