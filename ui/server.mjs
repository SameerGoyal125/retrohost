import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PORT = process.env.PORT || 8123;
const API_TARGET = "http://localhost:8790";
const HTML_PATH = join(__dirname, "index.html");

const server = createServer(async (req, res) => {
  // Serve index.html (same-origin — no CORS headers needed)
  if (req.url === "/" || req.url === "/index.html") {
    try {
      const html = await readFile(HTML_PATH, "utf-8");
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      return res.end(html);
    } catch {
      res.writeHead(500);
      return res.end("Failed to read index.html");
    }
  }

  // Proxy /api/*
  if (req.url.startsWith("/api")) {
    const target = API_TARGET + req.url;
    try {
      // Read the request body for methods that carry one
      let body = null;
      if (req.method === "POST" || req.method === "PUT" || req.method === "PATCH") {
        body = await new Promise((resolve, reject) => {
          const chunks = [];
          req.on("data", (c) => chunks.push(c));
          req.on("end", () => resolve(Buffer.concat(chunks)));
          req.on("error", reject);
        });
      }

      // Forward headers, minus hop-by-hop ones fetch manages itself
      const headers = { ...req.headers };
      delete headers.host;
      delete headers["content-length"];
      if (body && body.length) headers["content-length"] = body.length;

      const upstream = await fetch(target, {
        method: req.method,
        headers,
        body: body && body.length ? body : undefined,
      });
      res.writeHead(upstream.status, Object.fromEntries(upstream.headers));
      const upstreamBody = await upstream.arrayBuffer();
      return res.end(Buffer.from(upstreamBody));
    } catch {
      res.writeHead(502);
      return res.end("Backend unreachable");
    }
  }

  res.writeHead(404);
  res.end("Not found");
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
