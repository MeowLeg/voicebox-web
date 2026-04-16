const voiceboxHost = 'http://61.153.213.238'
const voiceboxPort = '17493'
const articlesHost = process.env.VUE_APP_ARTICLES_HOST || 'http://61.153.213.238'
const articlesPort = process.env.VUE_APP_ARTICLES_PORT || '4029'

const voiceboxTarget = `${voiceboxHost}:${voiceboxPort}`
const articlesTarget = `${articlesHost}:${articlesPort}`

module.exports = {
  lintOnSave: false,
  publicPath: '/voicebox-web/',
  devServer: {
    port: 3000,
    proxy: {
      '/voicebox-web/articles': {
        target: articlesTarget,
        changeOrigin: true,
        onProxyReq: (proxyReq, req) => {
          proxyReq.path = req.url.replace(/^\/voicebox-web\/articles/, '');
        }
      },
      '/voicebox-web': {
        target: voiceboxTarget,
        changeOrigin: true,
        onProxyReq: (proxyReq, req) => {
          proxyReq.path = req.url.replace(/^\/voicebox-web/, '');
        }
      }
    }
  }
}