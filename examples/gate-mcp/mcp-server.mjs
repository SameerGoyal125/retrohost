#!/usr/bin/env node
// Minimal MCP server with one WRITE tool, to validate TrueForge's approval gate.
// Uses node:http directly (no express) to avoid import issues.
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { z } from "zod";
import { randomUUID } from "crypto";
import http from "node:http";

const sessions = new Map();

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
  });
  const entry = { server, transport, id };
  sessions.set(id, entry);
  return entry;
}

const httpServer = http.createServer(async (req, res) => {
  if (req.method === "POST" && req.url === "/mcp") {
    try {
    // Collect body
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    const body = JSON.parse(Buffer.concat(chunks).toString());

    const isInit = body?.method === "initialize";
    const sessionId = req.headers["mcp-session-id"];

      if (isInit) {
        const { server, transport } = getOrCreateSession();
        await server.connect(transport);
        await transport.handleRequest(req, res, body);
      } else if (sessionId && sessions.has(sessionId)) {
        const { transport } = sessions.get(sessionId);
        await transport.handleRequest(req, res, body);
      } else {
        res.writeHead(400, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "Missing or invalid session" }));
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
