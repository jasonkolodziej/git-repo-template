# MCP

> [!NOTE]
> see: `https://github.com/<ORG>/<REPO>/settings/copilot/coding_agent`
>
> [Documentation:](https://docs.github.com/en/enterprise-cloud@latest/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/extend-cloud-agent-with-mcp)

```jsonl
 {
   "mcpServers": {
     "github-mcp-server": {
       "type": "http",
       // Remove "/readonly" to enable wider access to all tools.
       // Then, use the "X-MCP-Toolsets" header to specify which toolsets you'd like to include.
       // Use the "tools" field to select individual tools from the toolsets.
       "url": "https://api.githubcopilot.com/mcp/readonly",
       "tools": ["*"],
       "headers": {
         "X-MCP-Toolsets": "repos,issues,users,pull_requests,code_security,secret_protection,actions,web_search"
       }
     },
		"io.github.upstash/context7": {
			"type": "stdio",
			"command": "npx",
			"args": ["@upstash/context7-mcp@1.0.31"],
			"env": {
				"CONTEXT7_API_KEY": "$COPILOT_MCP_CONTEXT7_API_KEY"
			},
			"gallery": "https://api.mcp.github.com",
			"version": "1.0.31"
		},
   }
 }
```
