import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // backend/.env 파일 읽기
  const env = loadEnv(mode, path.resolve(__dirname, '../backend'), '')

  console.log('[Vite] MORALIS_API_KEY 로드됨:', env.MORALIS_API_KEY ? '✓' : '✗')

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    // backend/.env의 변수를 VITE_ 접두사로 매핑
    define: {
      'import.meta.env.VITE_MORALIS_API_KEY': JSON.stringify(env.MORALIS_API_KEY || ''),
      'import.meta.env.VITE_COINGECKO_API_KEY': JSON.stringify(env.COINGECKO_API_KEY || ''),
    },
  }
})
