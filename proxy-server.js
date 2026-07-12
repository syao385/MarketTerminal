const http = require('http');
const https = require('https');
const url = require('url');

const PORT = 3000;
const CACHE_DURATION = 120000; // 2 minutes cache duration
const cache = {}; // url -> { timestamp, data }

const server = http.createServer((req, res) => {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.statusCode = 204;
    res.end();
    return;
  }

  const parsedUrl = url.parse(req.url, true);

  // Ping endpoint for client-side auto-detection
  if (parsedUrl.pathname === '/ping') {
    res.statusCode = 200;
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify({ status: 'ok' }));
    return;
  }

  // Proxy endpoint
  if (parsedUrl.pathname === '/proxy') {
    const targetUrl = parsedUrl.query.url;
    if (!targetUrl) {
      res.statusCode = 400;
      res.setHeader('Content-Type', 'text/plain');
      res.end('Missing url query parameter.');
      return;
    }

    // Check memory cache
    const now = Date.now();
    if (cache[targetUrl] && (now - cache[targetUrl].timestamp < CACHE_DURATION)) {
      res.statusCode = 200;
      res.setHeader('Content-Type', 'application/xml; charset=utf-8');
      res.end(cache[targetUrl].data);
      return;
    }

    // Options for request
    const options = {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
      },
      rejectUnauthorized: false // Ignore SSL certificate validation warnings (essential for naaim.org/aaii.com)
    };

    https.get(targetUrl, options, (proxyRes) => {
      let body = '';
      proxyRes.on('data', chunk => body += chunk);
      proxyRes.on('end', () => {
        if (proxyRes.statusCode === 200) {
          // Cache successful response
          cache[targetUrl] = { timestamp: now, data: body };
          res.statusCode = 200;
          res.setHeader('Content-Type', 'application/xml; charset=utf-8');
          res.end(body);
        } else {
          res.statusCode = proxyRes.statusCode;
          res.setHeader('Content-Type', 'text/plain');
          res.end(`Target server returned status: ${proxyRes.statusCode}`);
        }
      });
    }).on('error', (err) => {
      console.error(`Proxy error for ${targetUrl}:`, err);
      res.statusCode = 500;
      res.setHeader('Content-Type', 'text/plain');
      res.end(`Proxy error: ${err.message}`);
    });
    return;
  }

  res.statusCode = 404;
  res.setHeader('Content-Type', 'text/plain');
  res.end('Not Found');
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`=================================================`);
  console.log(`Aether Market Terminal Local Proxy Server Active`);
  console.log(`Running at: http://localhost:${PORT}`);
  console.log(`=================================================`);
  console.log(`Routes:`);
  console.log(`  - Ping test: http://localhost:${PORT}/ping`);
  console.log(`  - Proxy RSS: http://localhost:${PORT}/proxy?url=[RSS_URL]`);
  console.log(`Keep this window open and refresh the terminal.`);
});
