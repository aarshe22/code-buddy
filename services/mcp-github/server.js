/**
 * MCP GitHub Server - Provides GitHub repository access via MCP
 */
const express = require('express');
const axios = require('axios');
const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');

const app = express();
app.use(express.json());

const GITHUB_TOKEN = process.env.GITHUB_TOKEN || '';
const GITHUB_API_BASE = 'https://api.github.com';

// MCP Server setup
const server = new Server({
  name: 'github-mcp-server',
  version: '1.0.0',
}, {
  capabilities: {
    tools: {},
    resources: {},
  },
});

// HTTP API endpoints for agent-orchestrator
app.get('/api/repo/info', async (req, res) => {
  try {
    const repo = req.query.repo;
    if (!repo) {
      return res.status(400).json({ error: 'repo parameter required' });
    }

    const [owner, repoName] = repo.split('/');
    const response = await axios.get(
      `${GITHUB_API_BASE}/repos/${owner}/${repoName}`,
      {
        headers: {
          Authorization: `token ${GITHUB_TOKEN}`,
          Accept: 'application/vnd.github.v3+json',
        },
      }
    );

    res.json({
      name: response.data.name,
      full_name: response.data.full_name,
      description: response.data.description,
      language: response.data.language,
      stars: response.data.stargazers_count,
      forks: response.data.forks_count,
      default_branch: response.data.default_branch,
      url: response.data.html_url,
    });
  } catch (error) {
    console.error('GitHub API error:', error.message);
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

    const [owner, repoName] = repo.split('/');
    const branch = req.query.branch || 'main';
    
    const response = await axios.get(
      `${GITHUB_API_BASE}/repos/${owner}/${repoName}/contents/${path}?ref=${branch}`,
      {
        headers: {
          Authorization: `token ${GITHUB_TOKEN}`,
          Accept: 'application/vnd.github.v3+json',
        },
      }
    );

    // Decode base64 content
    const content = Buffer.from(response.data.content, 'base64').toString('utf-8');
    
    res.json({
      path: response.data.path,
      content: content,
      sha: response.data.sha,
      size: response.data.size,
    });
  } catch (error) {
    console.error('GitHub API error:', error.message);
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

    const [owner, repoName] = repo.split('/');
    
    // Get repository tree
    const repoResponse = await axios.get(
      `${GITHUB_API_BASE}/repos/${owner}/${repoName}`,
      {
        headers: {
          Authorization: `token ${GITHUB_TOKEN}`,
        },
      }
    );

    const sha = repoResponse.data.default_branch;
    const treeResponse = await axios.get(
      `${GITHUB_API_BASE}/repos/${owner}/${repoName}/git/trees/${sha}?recursive=1`,
      {
        headers: {
          Authorization: `token ${GITHUB_TOKEN}`,
        },
      }
    );

    res.json({
      tree: treeResponse.data.tree.map(item => ({
        path: item.path,
        type: item.type,
        sha: item.sha,
      })),
    });
  } catch (error) {
    console.error('GitHub API error:', error.message);
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/repo/push', async (req, res) => {
  try {
    const { repo, branch, files, commit_message } = req.body;
    
    if (!repo || !branch || !files || !commit_message) {
      return res.status(400).json({ error: 'Missing required parameters' });
    }

    const [owner, repoName] = repo.split('/');
    
    // Get current ref
    const refResponse = await axios.get(
      `${GITHUB_API_BASE}/repos/${owner}/${repoName}/git/refs/heads/${branch}`,
      {
        headers: {
          Authorization: `token ${GITHUB_TOKEN}`,
        },
      }
    );

    const baseSha = refResponse.data.object.sha;
    
    // Get base tree
    const commitResponse = await axios.get(
      `${GITHUB_API_BASE}/repos/${owner}/${repoName}/git/commits/${baseSha}`,
      {
        headers: {
          Authorization: `token ${GITHUB_TOKEN}`,
        },
      }
    );

    const baseTreeSha = commitResponse.data.tree.sha;
    
    // Create blobs for files
    const blobs = [];
    for (const [path, content] of Object.entries(files)) {
      const blobResponse = await axios.post(
        `${GITHUB_API_BASE}/repos/${owner}/${repoName}/git/blobs`,
        {
          content: Buffer.from(content).toString('base64'),
          encoding: 'base64',
        },
        {
          headers: {
            Authorization: `token ${GITHUB_TOKEN}`,
          },
        }
      );
      blobs.push({ path, sha: blobResponse.data.sha });
    }
    
    // Create tree
    const treeResponse = await axios.post(
      `${GITHUB_API_BASE}/repos/${owner}/${repoName}/git/trees`,
      {
        base_tree: baseTreeSha,
        tree: blobs.map(blob => ({
          path: blob.path,
          mode: '100644',
          type: 'blob',
          sha: blob.sha,
        })),
      },
      {
        headers: {
          Authorization: `token ${GITHUB_TOKEN}`,
        },
      }
    );
    
    // Create commit
    const newCommitResponse = await axios.post(
      `${GITHUB_API_BASE}/repos/${owner}/${repoName}/git/commits`,
      {
        message: commit_message,
        tree: treeResponse.data.sha,
        parents: [baseSha],
      },
      {
        headers: {
          Authorization: `token ${GITHUB_TOKEN}`,
        },
      }
    );
    
    // Update ref
    await axios.patch(
      `${GITHUB_API_BASE}/repos/${owner}/${repoName}/git/refs/heads/${branch}`,
      {
        sha: newCommitResponse.data.sha,
      },
      {
        headers: {
          Authorization: `token ${GITHUB_TOKEN}`,
        },
      }
    );
    
    res.json({ success: true, commit_sha: newCommitResponse.data.sha });
  } catch (error) {
    console.error('GitHub API error:', error.message);
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

    const [owner, repoName] = repo.split('/');
    
    // Get repository contents recursively
    const treeResponse = await axios.get(
      `${GITHUB_API_BASE}/repos/${owner}/${repoName}/git/trees/${branch}?recursive=1`,
      {
        headers: {
          Authorization: `token ${GITHUB_TOKEN}`,
        },
      }
    );

    // Get file contents
    const files = {};
    for (const item of treeResponse.data.tree) {
      if (item.type === 'blob') {
        try {
          const fileResponse = await axios.get(
            `${GITHUB_API_BASE}/repos/${owner}/${repoName}/contents/${item.path}?ref=${branch}`,
            {
              headers: {
                Authorization: `token ${GITHUB_TOKEN}`,
              },
            }
          );
          files[item.path] = Buffer.from(fileResponse.data.content, 'base64').toString('utf-8');
        } catch (err) {
          console.warn(`Failed to fetch ${item.path}:`, err.message);
        }
      }
    }
    
    res.json({ files, branch });
  } catch (error) {
    console.error('GitHub API error:', error.message);
    res.status(500).json({ error: error.message });
  }
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'mcp-github' });
});

const PORT = process.env.MCP_PORT || 3001;
app.listen(PORT, () => {
  console.log(`MCP GitHub Server running on port ${PORT}`);
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

