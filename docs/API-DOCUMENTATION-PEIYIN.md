# 配音API接口文档

> 基于 Voicebox 后端 API，直接访问底层接口（非代理转发）

**基础URL**: `http://61.153.213.238:17493`（配音服务）

---

## 目录

1. [音色管理](#1-音色管理)
2. [语音合成](#2-语音合成)
3. [生成状态](#3-生成状态)
4. [音频获取](#4-音频获取)
5. [历史记录](#5-历史记录)
6. [模型管理](#6-模型管理)
7. [效果配置](#7-效果配置)

---

## 1. 音色管理

### 1.1 获取音色列表

获取所有已创建的音色配置文件。

**请求**

```
GET /profiles
```

**请求示例**

```bash
curl -X GET "http://localhost:17493/profiles"
```

**响应示例**

```json
[
  {
    "id": "uuid-xxx-xxx",
    "name": "主播音色",
    "language": "zh",
    "description": "新闻播报音色",
    "created_at": "2026-04-20T10:30:00Z"
  }
]
```

**响应字段说明**

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 音色配置ID |
| name | string | 音色名称 |
| language | string | 语言代码：`zh`(中文)、`en`(英文) |
| description | string | 描述信息 |
| created_at | string | 创建时间（ISO 8601格式） |

---

### 1.2 创建音色配置

创建新的音色配置文件。

**请求**

```
POST /profiles
Content-Type: application/json
```

**请求体**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| name | string | 是 | 音色名称 |
| description | string | 否 | 描述信息 |
| language | string | 否 | 语言代码，默认为 `zh` |
| voice_type | string | 否 | 音色类型：`cloned`(克隆)、`preset`(预设)、`designed`(设计) |
| preset_engine | string | 否 | 预设引擎（当 voice_type 为 `preset` 时必填） |
| preset_voice_id | string | 否 | 预设音色ID |

**请求示例**

```bash
curl -X POST "http://localhost:17493/profiles" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "新闻主播",
    "description": "用于新闻播报",
    "language": "zh"
  }'
```

**响应示例**

```json
{
  "id": "uuid-xxx-xxx",
  "name": "新闻主播",
  "language": "zh",
  "description": "用于新闻播报",
  "created_at": "2026-04-24T15:30:00Z"
}
```

---

### 1.3 上传音色样本

上传音频样本用于音色克隆。

**请求**

```
POST /profiles/{profileId}/samples
Content-Type: multipart/form-data
```

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| profileId | string | 音色配置ID |

**表单字段**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| file | file | 是 | 音频文件（支持 WAV、MP3、M4A、FLAC） |
| reference_text | string | 是 | 音频对应的文本内容 |

**请求示例**

```bash
curl -X POST "http://localhost:17493/profiles/uuid-xxx-xxx/samples" \
  -F "file=@sample.wav" \
  -F "reference_text=这是一段用于克隆音色的参考音频"
```

**响应**

```
HTTP/1.1 204 No Content
```

---

### 1.4 删除音色配置

删除指定的音色配置文件。

**请求**

```
DELETE /profiles/{profileId}
```

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| profileId | string | 音色配置ID |

**请求示例**

```bash
curl -X DELETE "http://localhost:17493/profiles/uuid-xxx-xxx"
```

**响应**

```
HTTP/1.1 204 No Content
```

---

### 1.5 获取预设音色列表

获取指定引擎的预设音色。

**请求**

```
GET /profiles/presets/{engine}
```

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| engine | string | 引擎名称：`qwen`、`qwen_custom_voice`、`luxtts`、`chatterbox`、`chatterbox_turbo`、`tada`、`kokoro` |

**请求示例**

```bash
curl -X GET "http://localhost:17493/profiles/presets/qwen"
```

**响应示例**

```json
{
  "engine": "qwen",
  "voices": [
    {
      "voice_id": "female_young",
      "name": "年轻女性",
      "gender": "female",
      "language": "zh"
    },
    {
      "voice_id": "male_middle",
      "name": "中年男性",
      "gender": "male",
      "language": "zh"
    }
  ]
}
```

---

## 2. 语音合成

### 2.1 发起语音生成

提交文本并开始语音合成。

**请求**

```
POST /generate
Content-Type: application/json
```

**请求体**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| profile_id | string | 否* | 音色配置ID（使用克隆音色时必填） |
| voice_id | string | 否* | 预设音色ID（使用预设音色时必填） |
| text | string | 是 | 要合成的文本内容 |
| language | string | 否 | 语言代码，默认 `zh` |
| seed | number | 否 | 随机种子，用于复现结果 |
| instruct | string | 否 | 指令提示（如 "播音腔"、"新闻播报"） |
| engine | string | 否 | 引擎名称，覆盖默认设置 |
| model_size | string | 否 | 模型大小（如 `1.7B`、`0.6B`） |
| max_chunk_chars | number | 否 | 单段最大字符数，默认 500 |
| speed | number | 否 | 语速倍率，默认 1.0 |

> **注意**: `profile_id` 和 `voice_id` 至少需要一个。

**请求示例**

```bash
curl -X POST "http://localhost:17493/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "uuid-xxx-xxx",
    "text": "各位观众晚上好，欢迎收看新闻联播节目。",
    "language": "zh",
    "seed": 42,
    "instruct": "新闻播报",
    "max_chunk_chars": 500,
    "speed": 1.0
  }'
```

**响应示例**

```json
{
  "id": "gen-xxx-xxx",
  "profile_id": "uuid-xxx-xxx",
  "text": "各位观众晚上好，欢迎收看新闻联播节目。",
  "language": "zh",
  "audio_path": null,
  "duration": null,
  "seed": 42,
  "instruct": "新闻播报",
  "model_size": "1.7B",
  "status": "pending",
  "error": null,
  "created_at": "2026-04-24T15:30:00Z",
  "active_version_id": null
}
```

**响应字段说明**

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 生成任务ID |
| status | string | 状态：`pending`(等待中)、`processing`(处理中)、`completed`(完成)、`failed`(失败) |
| audio_path | string \| null | 音频文件路径（完成后返回） |
| duration | number \| null | 音频时长（秒，完成后返回） |
| error | string \| null | 错误信息（失败时返回） |

---

## 3. 生成状态

### 3.1 查询生成状态

查询语音生成任务的当前状态。

**请求**

```
GET /generate/{id}/status
```

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| id | string | 生成任务ID |

**请求示例**

```bash
curl -X GET "http://localhost:17493/generate/gen-xxx-xxx/status"
```

**响应示例（处理中）**

```json
{
  "id": "gen-xxx-xxx",
  "profile_id": "uuid-xxx-xxx",
  "text": "各位观众晚上好...",
  "language": "zh",
  "audio_path": null,
  "duration": null,
  "status": "processing",
  "error": null,
  "created_at": "2026-04-24T15:30:00Z"
}
```

**响应示例（已完成）**

```json
{
  "id": "gen-xxx-xxx",
  "profile_id": "uuid-xxx-xxx",
  "text": "各位观众晚上好...",
  "language": "zh",
  "audio_path": "/path/to/audio.wav",
  "duration": 5.2,
  "status": "completed",
  "error": null,
  "created_at": "2026-04-24T15:30:00Z"
}
```

**响应示例（失败）**

```json
{
  "id": "gen-xxx-xxx",
  "profile_id": "uuid-xxx-xxx",
  "text": "各位观众晚上好...",
  "language": "zh",
  "audio_path": null,
  "duration": null,
  "status": "failed",
  "error": "Model not loaded",
  "created_at": "2026-04-24T15:30:00Z"
}
```

---

## 4. 音频获取

### 4.1 获取生成的音频

获取已完成的音频文件。

**请求**

```
GET /audio/{id}
```

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| id | string | 生成任务ID或版本ID |

**请求示例**

```bash
curl -X GET "http://localhost:17493/audio/gen-xxx-xxx" -o audio.wav
```

**响应**

```
HTTP/1.1 200 OK
Content-Type: audio/wav

[binary audio data]
```

---

## 5. 历史记录

### 5.1 获取生成历史

获取语音生成的历史记录。

**请求**

```
GET /history?limit={limit}
```

**查询参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| limit | number | 否 | 返回记录数量上限，默认 50 |

**请求示例**

```bash
curl -X GET "http://localhost:17493/history?limit=100"
```

**响应示例**

```json
{
  "items": [
    {
      "id": "gen-xxx-xxx",
      "profile_id": "uuid-xxx-xxx",
      "profile_name": "新闻主播",
      "text": "各位观众晚上好...",
      "language": "zh",
      "audio_path": "/path/to/audio.wav",
      "duration": 5.2,
      "status": "completed",
      "error": null,
      "created_at": "2026-04-24T15:30:00Z",
      "versions": [
        {
          "id": "ver-xxx-xxx",
          "audio_path": "/path/to/audio.wav",
          "is_default": true
        }
      ],
      "active_version_id": "ver-xxx-xxx"
    }
  ]
}
```

---

### 5.2 删除历史记录

删除指定的历史记录。

**请求**

```
DELETE /history/{id}
```

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| id | string | 历史记录ID |

**请求示例**

```bash
curl -X DELETE "http://localhost:17493/history/gen-xxx-xxx"
```

**响应**

```
HTTP/1.1 204 No Content
```

---

## 6. 模型管理

### 6.1 获取模型状态列表

获取所有可用模型的状态信息。

**请求**

```
GET /models/status
```

**请求示例**

```bash
curl -X GET "http://localhost:17493/models/status"
```

**响应示例**

```json
{
  "models": [
    {
      "model_name": "qwen-tts-1.7B",
      "display_name": "Qwen-TTS 1.7B",
      "hf_repo_id": "舟传媒/qwen-tts-1.7B",
      "downloaded": true,
      "downloading": false,
      "size_mb": 3500000,
      "loaded": true,
      "supports_clone": true
    },
    {
      "model_name": "kokoro",
      "display_name": "Kokoro",
      "hf_repo_id": "舟传媒/kokoro",
      "downloaded": true,
      "downloading": false,
      "size_mb": 50000,
      "loaded": true,
      "supports_clone": false
    }
  ]
}
```

**响应字段说明**

| 字段 | 类型 | 描述 |
|------|------|------|
| model_name | string | 模型标识名 |
| display_name | string | 显示名称 |
| hf_repo_id | string | Hugging Face 仓库ID |
| downloaded | boolean | 是否已下载 |
| downloading | boolean | 是否正在下载 |
| size_mb | number \| null | 模型大小（MB） |
| loaded | boolean | 是否已加载到内存 |
| supports_clone | boolean | 是否支持音色克隆 |

---

### 6.2 下载模型

下载指定的模型到本地。

**请求**

```
POST /models/download
Content-Type: application/json
```

**请求体**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|
| model_name | string | 是 | 模型标识名 |

**请求示例**

```bash
curl -X POST "http://localhost:17493/models/download" \
  -H "Content-Type: application/json" \
  -d '{"model_name": "qwen-tts-0.6B"}'
```

**响应**

```
HTTP/1.1 204 No Content
```

---

### 6.3 加载模型

将模型加载到内存中以准备进行语音合成。

**请求**

```
POST /models/load?model_name={model_name}
```

**查询参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|
| model_name | string | 是 | 模型标识名 |

**请求示例**

```bash
curl -X POST "http://localhost:17493/models/load?model_name=qwen-tts-1.7B"
```

**响应**

```
HTTP/1.1 204 No Content
```

---

## 7. 效果配置

### 7.1 获取可用效果列表

获取所有可用的音频效果。

**请求**

```
GET /effects/available
```

**请求示例**

```bash
curl -X GET "http://localhost:17493/effects/available"
```

**响应示例**

```json
{
  "effects": [
    {
      "type": "reverb",
      "label": "混响",
      "description": "为音频添加空间混响效果",
      "params": {
        "room_size": {
          "default": 0.5,
          "min": 0,
          "max": 1,
          "step": 0.01,
          "description": "房间大小"
        },
        "damping": {
          "default": 0.5,
          "min": 0,
          "max": 1,
          "step": 0.01,
          "description": "阻尼"
        },
        "wet_level": {
          "default": 0.3,
          "min": 0,
          "max": 1,
          "step": 0.01,
          "description": "混响电平"
        },
        "dry_level": {
          "default": 0.7,
          "min": 0,
          "max": 1,
          "step": 0.01,
          "description": "干声电平"
        },
        "width": {
          "default": 1,
          "min": 0,
          "max": 1,
          "step": 0.01,
          "description": "宽度"
        }
      }
    },
    {
      "type": "pitch_shift",
      "label": "音调调整",
      "description": "调整音频的音调",
      "params": {
        "semitones": {
          "default": 0,
          "min": -12,
          "max": 12,
          "step": 0.1,
          "description": "半音程"
        }
      }
    },
    {
      "type": "speed",
      "label": "语速",
      "description": "调整播放速度",
      "params": {
        "speed": {
          "default": 1.0,
          "min": 0.5,
          "max": 2.0,
          "step": 0.05,
          "description": "倍率"
        },
        "algorithm": {
          "default": "high",
          "options": ["high", "low"],
          "description": "算法"
        }
      }
    }
  ]
}
```

**可用效果类型**

| 类型 | 描述 | 参数 |
|------|------|------|
| chorus | 合唱/镶边 | rate_hz, depth, feedback, centre_delay_ms, mix |
| reverb | 混响 | room_size, damping, wet_level, dry_level, width |
| delay | 延迟 | delay_seconds, feedback, mix |
| compressor | 压缩器 | threshold_db, ratio, attack_ms, release_ms |
| gain | 增益 | gain_db |
| highpass | 高通滤波 | cutoff_frequency_hz |
| lowpass | 低通滤波 | cutoff_frequency_hz |
| pitch_shift | 音调调整 | semitones |
| speed | 语速 | speed, algorithm |

---

### 7.2 获取音色效果配置

获取指定音色的效果链配置。

**请求**

```
GET /profiles/{profileId}
```

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| profileId | string | 音色配置ID |

**请求示例**

```bash
curl -X GET "http://localhost:17493/profiles/uuid-xxx-xxx"
```

**响应示例**

```json
{
  "id": "uuid-xxx-xxx",
  "name": "新闻主播",
  "language": "zh",
  "effects_chain": [
    {
      "type": "reverb",
      "enabled": true,
      "params": {
        "room_size": 0.3,
        "damping": 0.5,
        "wet_level": 0.2,
        "dry_level": 0.8,
        "width": 1
      }
    }
  ]
}
```

---

### 7.3 更新音色效果配置

更新指定音色的效果链配置。

**请求**

```
PUT /profiles/{profileId}/effects
Content-Type: application/json
```

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| profileId | string | 音色配置ID |

**请求体**

| 字段 | 类型 | 描述 |
|------|------|------|
| effects_chain | array \| null | 效果链配置数组，传入 `null` 重置效果 |

**效果配置对象**

| 字段 | 类型 | 描述 |
|------|------|------|
| type | string | 效果类型 |
| enabled | boolean | 是否启用（可选） |
| params | object | 效果参数 |

**请求示例**

```bash
curl -X PUT "http://localhost:17493/profiles/uuid-xxx-xxx/effects" \
  -H "Content-Type: application/json" \
  -d '{
    "effects_chain": [
      {
        "type": "reverb",
        "params": {
          "room_size": 0.3,
          "damping": 0.5,
          "wet_level": 0.2,
          "dry_level": 0.8,
          "width": 1
        }
      },
      {
        "type": "speed",
        "params": {
          "speed": 1.0,
          "algorithm": "high"
        }
      }
    ]
  }'
```

**响应示例**

```json
{
  "id": "uuid-xxx-xxx",
  "name": "新闻主播",
  "language": "zh",
  "effects_chain": [
    {
      "type": "reverb",
      "params": {
        "room_size": 0.3,
        "damping": 0.5,
        "wet_level": 0.2,
        "dry_level": 0.8,
        "width": 1
      }
    }
  ]
}
```

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
  "message": "profile_id is required"
}
```

---

## 使用场景

| 场景 | 使用的API |
|------|----------|
| 创建音色并上传样本 | `POST /profiles` → `POST /profiles/{id}/samples` |
| 使用克隆音色生成语音 | `POST /generate` → `GET /generate/{id}/status` → `GET /audio/{id}` |
| 使用预设音色生成语音 | `GET /profiles/presets/{engine}` → `POST /generate` |
| 配置音频效果 | `GET /effects/available` → `PUT /profiles/{id}/effects` |
| 管理模型 | `GET /models/status` → `POST /models/download` → `POST /models/load` |