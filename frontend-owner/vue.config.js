module.exports = {
  // 生产环境的基础路径（用于Nginx部署）
  publicPath: process.env.NODE_ENV === 'production' ? '/owner/' : '/',
  
  devServer: {
    port: 8081,
    allowedHosts: 'all',  // 允许通过内网穿透域名访问
    proxy: {
      '/api': {
        target: 'http://localhost:8088',
        changeOrigin: true
      }
    }
  },
  
  // PWA配置
  pwa: {
    name: '智慧物业',
    shortName: '物业系统',
    themeColor: '#4DBA87',
    msTileColor: '#000000',
    appleMobileWebAppCapable: 'yes',
    appleMobileWebAppStatusBarStyle: 'black',
    
    // 开发模式也生成完整manifest
    workboxPluginMode: 'GenerateSW',
    
    // manifest.json配置
    manifestOptions: {
      name: '智慧物业管理系统',
      short_name: '物业系统',
      description: '便捷的物业管理服务平台',
      start_url: process.env.NODE_ENV === 'production' ? '/owner/' : '/',
      display: 'standalone',
      background_color: '#ffffff',
      theme_color: '#4DBA87',
      icons: [
        {
          src: '/img/icons/android-chrome-192x192.png',
          sizes: '192x192',
          type: 'image/png'
        },
        {
          src: '/img/icons/android-chrome-512x512.png',
          sizes: '512x512',
          type: 'image/png'
        },
        {
          src: '/img/icons/android-chrome-maskable-192x192.png',
          sizes: '192x192',
          type: 'image/png',
          purpose: 'maskable'
        },
        {
          src: '/img/icons/apple-touch-icon.png',
          sizes: '180x180',
          type: 'image/png'
        }
      ]
    },
    
    // Service Worker配置
    workboxOptions: {
      // 缓存策略
      runtimeCaching: [
        {
          urlPattern: /^https:\/\/api\.deepseek\.com\//,
          handler: 'NetworkFirst',
          options: {
            networkTimeoutSeconds: 10,
            cacheName: 'deepseek-api',
            expiration: {
              maxEntries: 50,
              maxAgeSeconds: 300
            }
          }
        },
        {
          urlPattern: /\/api\//,
          handler: 'NetworkFirst',
          options: {
            networkTimeoutSeconds: 10,
            cacheName: 'api-cache',
            expiration: {
              maxEntries: 100,
              maxAgeSeconds: 300
            }
          }
        },
        {
          urlPattern: /\.(?:png|jpg|jpeg|svg|gif)$/,
          handler: 'CacheFirst',
          options: {
            cacheName: 'images-cache',
            expiration: {
              maxEntries: 100,
              maxAgeSeconds: 30 * 24 * 60 * 60
            }
          }
        }
      ]
    }
  }
}
