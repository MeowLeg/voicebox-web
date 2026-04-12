# Voicebox Web - 舟传媒科技部TTS

基于 Vue 3 + TypeScript + Tailwind CSS 的语音合成应用。

## 功能特性

- 语音配置文件管理（创建、删除）
- 文本转语音合成
- 报纸/电视新闻获取
- 生成历史记录
- 模型管理
- 多语言支持

## 技术栈

- Vue 3 (Composition API)
- TypeScript
- Vue Router
- Tailwind CSS
- Vue CLI

## 跨域解决方案

使用 Vue CLI 的 devServer proxy 配置解决开发环境跨域问题：

```javascript
// vue.config.js
devServer: {
  proxy: {
    '/voicebox-web': {
      target: 'http://localhost:17493',
      changeOrigin: true,
      pathRewrite: {
        '^/voicebox-web': ''
      }
    }
  }
}
```

所有 `/voicebox-web` 开头的 API 请求会被代理到后端服务器 (localhost:17493)。

## 开发环境

### 前置要求

- Node.js 16+
- 后端服务器运行在 http://localhost:17493

### 启动开发服务器

```bash
npm install
npm run serve
```

访问 http://localhost:3000/voicebox-web

### 生产构建

```bash
npm run build
```

构建产物在 `dist/` 目录，可部署到任意静态服务器或 Nginx。

### Nginx 部署配置

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/dist;
    
    # API 代理
    location /voicebox-web/ {
        proxy_pass http://localhost:17493/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 项目结构

```
src/
├── api/          # API 调用封装
├── assets/       # 静态资源
├── components/   # 公共组件
├── router/       # 路由配置
├── views/        # 页面组件
├── App.vue       # 根组件
└── main.ts       # 入口文件
```

## API 代理说明

开发环境使用 Vue CLI proxy，生产环境使用 Nginx 代理。

- 开发环境: `http://localhost:3000/voicebox-web/api` → `http://localhost:17493/api`
- 生产环境: `http://your-domain.com/voicebox-web/api` → `http://localhost:17493/api`

## License

MIT