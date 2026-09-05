import { defineConfig } from 'vite';

// Development/visual QA only. GitHub Pages continues serving the static files.
export default defineConfig({
  appType: 'mpa',
  server: { host: '0.0.0.0', allowedHosts: ['terminal.local'] }
});
