import { defineConfig } from 'vite';
export default defineConfig({
  base: process.env.BASE_PATH || '/',
  server: { port: 5173, fs: { allow: ['..'] } },
  build: { outDir: 'dist', emptyOutDir: true, assetsInlineLimit: 0 },
});
