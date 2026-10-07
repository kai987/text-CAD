import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { releaseBuildDefinitions } from './scripts/release-build-meta.mjs';

export default defineConfig({
  base: '/text-CAD/',
  plugins: [react()],
  define: releaseBuildDefinitions(),
});
