// import { defineConfig } from 'vite'
// import react from '@vitejs/plugin-react'

// // https://vite.dev/config/
// export default defineConfig({
//   plugins: [react()],
//   server: {
//     host: true,
//     port: 5173,
//     allowedHosts: ['9900donut.me', 'www.9900donut.me'],
//     hmr: {
//       overlay: false, // disable error overlay to avoid webview script conflicts
//     },
//     proxy: {
//       '/api': {
//         target: 'http://127.0.0.1:8000', // Django 后端
//         changeOrigin: true,
//       },
//       '/task': {
//         target: 'http://127.0.0.1:8000', // 
//         changeOrigin: true,
//       },
//       '/material': {
//         target: 'http://127.0.0.1:8000',
//         changeOrigin: true,
//       },
//       '/media': {
//         target: 'http://127.0.0.1:8000',
//         changeOrigin: true,
//       },
//     }
//   },
// })
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // 读取环境变量（Vite 只认以 VITE_ 开头的）
  const env = loadEnv(mode, process.cwd(), '')

  // 如果没有配置 VITE_API_PROXY_TARGET，就用本地默认 127.0.0.1:8000
  const apiTarget = env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000'

  return {
    plugins: [react()],
    server: {
      host: true,
      port: 5173,
      allowedHosts: ['9900donut.me', 'www.9900donut.me'],
      hmr: {
        overlay: false, // disable error overlay to avoid webview script conflicts
      },
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
        },
        '/task': {
          target: apiTarget,
          changeOrigin: true,
        },
        '/material': {
          target: apiTarget,
          changeOrigin: true,
        },
        '/media': {
          target: apiTarget,
          changeOrigin: true,
        },
      }
    },
  }
})
