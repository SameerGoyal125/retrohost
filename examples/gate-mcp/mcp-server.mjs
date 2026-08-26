#!/usr/bin/env node
// Minimal MCP server with one WRITE tool, to validate TrueForge's approval gate.
// Uses node:http directly (no express) to avoid import issues.
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { z } from "zod";
import { randomUUID } from "crypto";
import http from "node:http";

const sessions = new Map();
const IDLE_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes

function removeSession(id) {
  const entry = sessions.get(id);
  if (!entry) return;
  sessions.delete(id);
  console.log(`Session ${id} removed (${sessions.size} active)`);
}

function touchSession(id) {
  const entry = sessions.get(id);
  if (!entry) return;
  clearTimeout(entry.timer);
  entry.timer = setTimeout(() => removeSession(id), IDLE_TIMEOUT_MS);
}

function getOrCreateSession() {
  const id = randomUUID();
  const server = new McpServer({ name: "retrohost-gate", version: "1.0.0" });
  server.tool(
    "publish_report",
    "Publishes a reproduction report. This is a write/destructive action that should require human approval.",
    { report: z.string().describe("The report body to publish") },
    async ({ report }) => ({
      content: [{ type: "text", text: `PUBLISHED: ${report}` }],
    })
  );
  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: () => id,
    onclose: () => removeSession(id),
  });
  const timer = setTimeout(() => removeSession(id), IDLE_TIMEOUT_MS);
  const entry = { server, transport, id, timer };
  sessions.set(id, entry);
  return entry;
}

async function collectBody(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  return JSON.parse(Buffer.concat(chunks).toString());
}

const httpServer = http.createServer(async (req, res) => {
  if (req.url === "/mcp") {
    try {
      if (req.method === "POST") {
        const body = await collectBody(req);
        const isInit = body?.method === "initialize";
        const sessionId = req.headers["mcp-session-id"];

        if (isInit) {
          const { server, transport } = getOrCreateSession();
          await server.connect(transport);
          await transport.handleRequest(req, res, body);
        } else if (sessionId && sessions.has(sessionId)) {
          touchSession(sessionId);
          const { transport } = sessions.get(sessionId);
          await transport.handleRequest(req, res, body);
        } else {
          res.writeHead(400, { "Content-Type": "application/json" });
          res.end(JSON.stringify({ error: "Missing or invalid session" }));
        }
      } else if (req.method === "DELETE") {
        const sessionId = req.headers["mcp-session-id"];
        if (sessionId && sessions.has(sessionId)) {
          const { transport } = sessions.get(sessionId);
          await transport.close();
          removeSession(sessionId);
          res.writeHead(200);
          res.end();
        } else {
          res.writeHead(400, { "Content-Type": "application/json" });
          res.end(JSON.stringify({ error: "Missing or invalid session" }));
        }
      } else {
        res.writeHead(405);
        res.end("Method not allowed");
      }
    } catch (err) {
      console.error("MCP error:", err);
      res.writeHead(500, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: String(err) }));
    }
  } else {
    res.writeHead(404);
    res.end("Not found");
  }
});

const PORT = process.env.PORT || 8941;

// Prevent crashes on unhandled errors
process.on("uncaughtException", (err) => {
  console.error("Uncaught exception:", err);
});

httpServer.listen(PORT, "0.0.0.0", () => {
  console.log(`gate-mcp listening on 0.0.0.0:${PORT}`);
});
