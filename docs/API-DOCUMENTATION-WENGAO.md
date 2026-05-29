# 文稿API接口文档

> 基于 Voicebox 后端 API，直接访问底层接口（非代理转发）

**基础URL**: `http://61.153.213.238:4029`（文稿服务）

---

## 目录

1. [报纸新闻](#1-报纸新闻)
2. [电视新闻](#2-电视新闻)

---

## 1. 报纸新闻

### 1.1 获取报纸文章列表

获取指定日期范围内的报纸文章列表。

**请求**

```
GET /articles/get_paper_articles
```

**查询参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| siteId | string | 是 | 站点ID |
| docstatus | string | 是 | 文档状态 |
| beginDate | string | 否 | 开始日期，格式：`YYYY-MM-DD` |
| endDate | string | 否 | 结束日期，格式：`YYYY-MM-DD` |

**请求示例**

```bash
curl -X GET "http://localhost:17493/articles/get_paper_articles?siteId=xxx&docstatus=published&beginDate=2026-04-20&endDate=2026-04-24"
```

**响应示例**

```json
{
  "data": [
    {
      "AUTHOR": "记者姓名",
      "CHNLDESC": "频道描述",
      "DOCSTATUS": 1,
      "DOCTYPE": 1,
      "METADATAID": 123456,
      "PUBDATE": "2026-04-24",
      "TITLE": "新闻标题"
    }
  ]
}
```

**响应字段说明**

| 字段 | 类型 | 描述 |
|------|------|------|
| METADATAID | number | 文章元数据ID，用于获取详情 |
| TITLE | string | 文章标题 |
| AUTHOR | string | 作者 |
| PUBDATE | string | 发布日期 |
| CHNLDESC | string | 频道描述 |
| DOCSTATUS | number | 文档状态 |
| DOCTYPE | number | 文档类型 |

---

### 1.2 获取报纸文章详情

根据 METADATAID 获取单篇文章的完整内容。

**请求**

```
GET /articles/get_paper_article_detail
```

**查询参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| metadataId | string | 是 | 文章的 METADATAID |

**请求示例**

```bash
curl -X GET "http://localhost:17493/articles/get_paper_article_detail?metadataId=123456"
```

**响应示例**

```json
{
  "metadataId": 123456,
  "title": "新闻标题",
  "content": "文章正文内容...",
  "author": "记者姓名",
  "publishDate": "2026-04-24",
  "source": "来源",
  "attachments": []
}
```

---

## 2. 电视新闻

### 2.1 获取电视新闻列表

获取指定时间范围和栏目的电视新闻列表。

**请求**

```
GET /articles/get_tv_newslists
```

**查询参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| startTime | string | 是 | 开始时间，格式：`YYYY-MM-DD HH:mm:ss` |
| endTime | string | 是 | 结束时间，格式：`YYYY-MM-DD HH:mm:ss` |
| columnId | string | 是 | 栏目ID |

**请求示例**

```bash
curl -X GET "http://localhost:17493/articles/get_tv_newslists?startTime=2026-04-20%2000:00:00&endTime=2026-04-24%2023:59:59&columnId=xxx"
```

**响应示例**

```json
{
  "data": [
    {
      "docid": "doc_12345",
      "llistid": "list_123",
      "title": "新闻标题",
      "publishTime": "2026-04-24 19:00:00",
      "duration": 1800,
      "columnName": "新闻联播"
    }
  ]
}
```

---

### 2.2 获取电视新闻列表详情

根据 llistid 获取电视新闻列表的详细信息。

**请求**

```
GET /articles/get_tv_newslist_detail
```

**查询参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| llistid | string | 是 | 列表ID |

**请求示例**

```bash
curl -X GET "http://localhost:17493/articles/get_tv_newslist_detail?llistid=list_123"
```

**响应示例**

```json
{
  "llistid": "list_123",
  "title": "新闻联播",
  "publishTime": "2026-04-24 19:00:00",
  "items": [
    {
      "docid": "doc_12345",
      "title": "新闻项目标题",
      "segmentIndex": 1,
      "duration": 120
    }
  ]
}
```

---

### 2.3 获取电视新闻文章

根据 docid 获取电视新闻的完整文稿内容。

**请求**

```
GET /articles/get_tv_article
```

**查询参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| docid | string | 是 | 文档ID |

**请求示例**

```bash
curl -X GET "http://localhost:17493/articles/get_tv_article?docid=doc_12345"
```

**响应示例**

```json
{
  "docid": "doc_12345",
  "title": "新闻标题",
  "segments": [
    {
      "type": "content",
      "label": "口播",
      "text": "各位观众晚上好..."
    },
    {
      "type": "content",
      "label": "画外音",
      "text": "今天上午..."
    },
    {
      "type": "interview",
      "label": "采访",
      "text": "我觉得..."
    }
  ],
  "duration": 1800,
  "publishTime": "2026-04-24 19:00:00"
}
```

**响应字段说明**

| 字段 | 类型 | 描述 |
|------|------|------|
| segments | array | 文稿段落数组 |
| segments[].type | string | 段落类型：`content`(内容)、`interview`(采访) |
| segments[].label | string | 标签：如 `口播`、`画外音`、`采访` |
| segments[].text | string | 文本内容 |

---

## 错误响应

所有API在出错时返回标准HTTP状态码：

| 状态码 | 描述 |
|--------|------|
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

错误响应示例：

```json
{
  "error": "Invalid parameter",
  "message": "siteId is required"
}
```

---

## 使用场景

| 场景 | 使用的API |
|------|----------|
| 获取某天报纸头条 | `get_paper_articles` + `get_paper_article_detail` |
| 获取新闻联播节目单 | `get_tv_newslists` + `get_tv_newslist_detail` |
| 获取单条电视新闻文稿 | `get_tv_article` |