---
title: Skincare Evidence MCP
emoji: 🧴
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
short_description: MCP server that searches clinical studies on skincare
tags:
  - mcp-server
---

# Skincare Evidence MCP

A remote [MCP](https://modelcontextprotocol.io) server with one tool, `search_studies`. It finds published clinical studies (PubMed, via Europe PMC) about a skincare ingredient, optionally for a skin concern. It returns study type, year, a short abstract and a link to cite.

**Endpoint:** `https://<this-space-subdomain>.hf.space/mcp` (Streamable HTTP, no auth)

Add it to Claude Code:

```sh
claude mcp add --transport http skincare-evidence https://<this-space-subdomain>.hf.space/mcp
```

Or in claude.ai: Settings → Connectors → Add custom connector, and paste the same URL.

The Space sleeps when idle, so the first call can take a minute.

> General educational information only, not medical advice.

Source: [aristidesz/skincare-evidence-advisor](https://github.com/aristidesz/skincare-evidence-advisor)
