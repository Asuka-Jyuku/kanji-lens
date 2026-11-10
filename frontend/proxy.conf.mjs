// Development only (`ng serve`): /api goes to the API, so the page and the API share one origin.
// No CORS, and a phone on the LAN reaches the API through this server while the API itself
// stays on 127.0.0.1 (ARCHITECTURE.md, section 6.1; docs/SECURITY.md). KANJILENS_API_URL points
// it elsewhere, such as an API on another port.
const target = process.env['KANJILENS_API_URL'] ?? 'http://127.0.0.1:8000';

export default {
  '/api': { target },
};
