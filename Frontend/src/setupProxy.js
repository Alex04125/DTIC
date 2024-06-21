// src/setupProxy.js

const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api', // This is the prefix for the API endpoint
    createProxyMiddleware({
      target: 'http://127.0.0.1', // Backend server
      changeOrigin: true,
      pathRewrite: {
        '^/api': '', // Remove /api prefix when forwarding the request
      },
    })
  );
};
