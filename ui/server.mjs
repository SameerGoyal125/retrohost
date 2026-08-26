import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PORT = process.env.PORT || 8123;
const API_TARGET = "http://localhost:8790";
const HTML_PATH = join(__dirname, "index.html");

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

const server = createServer(async (req, res) => {
  // Preflight
  if (req.method === "OPTIONS") {
    res.writeHead(204, CORS);
    return res.end();
  }

  // Serve index.html
  if (req.url === "/" || req.url === "/index.html") {
    try {
      const html = await readFile(HTML_PATH, "utf-8");
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8", ...CORS });
      return res.end(html);
    } catch {
      res.writeHead(500, CORS);
      return res.end("Failed to read index.html");
    }
  }

  // Proxy /api/*
  if (req.url.startsWith("/api")) {
    const target = API_TARGET + req.url;
    try {
      const upstream = await fetch(target, { method: req.method, headers: req.headers });
      res.writeHead(upstream.status, {
        ...Object.fromEntries(upstream.headers),
        ...CORS,
      });
      const body = await upstream.arrayBuffer();
      return res.end(Buffer.from(body));
    } catch {
      res.writeHead(502, CORS);
      return res.end("Backend unreachable");
    }
  }

  res.writeHead(404, CORS);
  res.end("Not found");
});

server.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
