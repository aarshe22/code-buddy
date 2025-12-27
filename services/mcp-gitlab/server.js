/**
 * MCP GitLab Server - Provides GitLab repository access via MCP
 */
const express = require('express');
const axios = require('axios');
const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');

const app = express();
app.use(express.json());

const GITLAB_TOKEN = process.env.GITLAB_TOKEN || '';
const GITLAB_URL = process.env.GITLAB_URL || 'https://gitlab.com';
const GITLAB_API_BASE = `${GITLAB_URL}/api/v4`;

// Helper to encode project path
function encodeProjectPath(path) {
  return encodeURIComponent(path);
}

// HTTP API endpoints for agent-orchestrator
app.get('/api/repo/info', async (req, res) => {
  try {
    const repo = req.query.repo;
    if (!repo) {
      return res.status(400).json({ error: 'repo parameter required' });
    }

    const encodedPath = encodeProjectPath(repo);
    const response = await axios.get(
      `${GITLAB_API_BASE}/projects/${encodedPath}`,
      {
        headers: {
          'PRIVATE-TOKEN': GITLAB_TOKEN,
        },
      }
    );

    res.json({
      name: response.data.name,
      full_name: response.data.path_with_namespace,
      description: response.data.description,
      default_branch: response.data.default_branch,
      url: response.data.web_url,
      visibility: response.data.visibility,
    });
  } catch (error) {
    console.error('GitLab API error:', error.message);
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/repo/file', async (req, res) => {
  try {
    const repo = req.query.repo;
    const path = req.query.path;
    
    if (!repo || !path) {
      return res.status(400).json({ error: 'repo and path parameters required' });
    }

    const encodedPath = encodeProjectPath(repo);
    const branch = req.query.branch || 'main';
    
    const response = await axios.get(
      `${GITLAB_API_BASE}/projects/${encodedPath}/repository/files/${encodeURIComponent(path)}/raw?ref=${branch}`,
      {
        headers: {
          'PRIVATE-TOKEN': GITLAB_TOKEN,
        },
      }
    );

    res.json({
      path: path,
      content: response.data,
      branch: branch,
    });
  } catch (error) {
    console.error('GitLab API error:', error.message);
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/repo/tree', async (req, res) => {
  try {
    const repo = req.query.repo;
    const branch = req.query.branch || 'main';
    
    if (!repo) {
      return res.status(400).json({ error: 'repo parameter required' });
    }

    const encodedPath = encodeProjectPath(repo);
    
    const response = await axios.get(
      `${GITLAB_API_BASE}/projects/${encodedPath}/repository/tree?ref=${branch}&recursive=true`,
      {
        headers: {
          'PRIVATE-TOKEN': GITLAB_TOKEN,
        },
      }
    );

    res.json({
      tree: response.data.map(item => ({
        path: item.path,
        type: item.type,
        id: item.id,
      })),
    });
  } catch (error) {
    console.error('GitLab API error:', error.message);
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/repo/push', async (req, res) => {
  try {
    const { repo, branch, files, commit_message } = req.body;
    
    if (!repo || !branch || !files || !commit_message) {
      return res.status(400).json({ error: 'Missing required parameters' });
    }

    const encodedPath = encodeProjectPath(repo);
    
    // Prepare actions for commit
    const actions = Object.entries(files).map(([path, content]) => ({
      action: 'update',
      file_path: path,
      content: content,
    }));
    
    // Create commit
    const response = await axios.post(
      `${GITLAB_API_BASE}/projects/${encodedPath}/repository/commits`,
      {
        branch: branch,
        commit_message: commit_message,
        actions: actions,
      },
      {
        headers: {
          'PRIVATE-TOKEN': GITLAB_TOKEN,
        },
      }
    );
    
    res.json({ success: true, commit_id: response.data.id });
  } catch (error) {
    console.error('GitLab API error:', error.message);
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/repo/pull', async (req, res) => {
  try {
    const repo = req.query.repo;
    const branch = req.query.branch || 'main';
    
    if (!repo) {
      return res.status(400).json({ error: 'repo parameter required' });
    }

    const encodedPath = encodeProjectPath(repo);
    
    // Get repository tree
    const treeResponse = await axios.get(
      `${GITLAB_API_BASE}/projects/${encodedPath}/repository/tree?ref=${branch}&recursive=true`,
      {
        headers: {
          'PRIVATE-TOKEN': GITLAB_TOKEN,
        },
      }
    );

    // Get file contents
    const files = {};
    for (const item of treeResponse.data) {
      if (item.type === 'blob') {
        try {
          const fileResponse = await axios.get(
            `${GITLAB_API_BASE}/projects/${encodedPath}/repository/files/${encodeURIComponent(item.path)}/raw?ref=${branch}`,
            {
              headers: {
                'PRIVATE-TOKEN': GITLAB_TOKEN,
              },
            }
          );
          files[item.path] = fileResponse.data;
        } catch (err) {
          console.warn(`Failed to fetch ${item.path}:`, err.message);
        }
      }
    }
    
    res.json({ files, branch });
  } catch (error) {
    console.error('GitLab API error:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'mcp-gitlab' });
});

const PORT = process.env.MCP_PORT || 3002;
app.listen(PORT, () => {
  console.log(`MCP GitLab Server running on port ${PORT}`);
});

// Also start MCP stdio server for direct MCP protocol
if (process.env.MCP_STDIO === 'true') {
  async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.log('MCP stdio server connected');
  }
  main().catch(console.error);
}

