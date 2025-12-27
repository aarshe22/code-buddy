/**
 * VS Code Extension Server
 * Provides Language Server Protocol (LSP) and extension API for AI features
 */
const express = require('express');
const WebSocket = require('ws');
const axios = require('axios');

const app = express();
app.use(express.json());

const OLLAMA_HOST = process.env.OLLAMA_HOST || 'http://host.docker.internal:11434';
const AGENT_ORCHESTRATOR_URL = process.env.AGENT_ORCHESTRATOR_URL || 'http://agent-orchestrator:8000';
const RAG_CHAT_URL = process.env.RAG_CHAT_URL || 'http://rag-chat:8003';

// WebSocket server for real-time features
const wss = new WebSocket.Server({ port: 3004 });

// Code completion endpoint
app.post('/api/completion', async (req, res) => {
  try {
    const { file_path, content, cursor_position, language } = req.body;
    
    // Get context from RAG
    const contextResponse = await axios.post(`${RAG_CHAT_URL}/search`, {
      query: content.slice(Math.max(0, cursor_position - 200), cursor_position),
      limit: 3
    });
    
    const context = contextResponse.data.results.map(r => r.content).join('\n');
    
    // Generate completion using Ollama
    const completionResponse = await axios.post(`${OLLAMA_HOST}/api/generate`, {
      model: 'deepseek-coder:33b',
      prompt: `Complete this ${language} code. Use the following context:\n\n${context}\n\nCode to complete:\n${content.slice(Math.max(0, cursor_position - 100), cursor_position)}\n\nProvide only the completion, no explanation:`,
      stream: false,
      options: {
        temperature: 0.3,
        num_predict: 100
      }
    });
    
    const completion = completionResponse.data.response.trim();
    
    res.json({
      completions: [{
        text: completion,
        range: {
          start: { line: 0, character: cursor_position },
          end: { line: 0, character: cursor_position }
        }
      }]
    });
  } catch (error) {
    console.error('Completion error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Code explanation endpoint
app.post('/api/explain', async (req, res) => {
  try {
    const { code, language, file_path } = req.body;
    
    const response = await axios.post(`${AGENT_ORCHESTRATOR_URL}/task`, {
      task: `Explain this ${language} code in detail: ${code}`,
      context: { file_path, code }
    });
    
    res.json({
      explanation: response.data.result,
      language: language
    });
  } catch (error) {
    console.error('Explain error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Error explanation endpoint
app.post('/api/explain-error', async (req, res) => {
  try {
    const { error_message, code, language, file_path } = req.body;
    
    const response = await axios.post(`${AGENT_ORCHESTRATOR_URL}/debug`, {
      file_path: file_path,
      error_message: error_message,
      context: { code, language }
    });
    
    res.json({
      explanation: response.data.explanation,
      fixes: response.data.fixes,
      root_cause: response.data.root_cause
    });
  } catch (error) {
    console.error('Error explanation error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Test generation endpoint
app.post('/api/generate-tests', async (req, res) => {
  try {
    const { code, language, file_path, test_framework } = req.body;
    
    const response = await axios.post(`${AGENT_ORCHESTRATOR_URL}/generate`, {
      prompt: `Generate comprehensive unit tests for this ${language} code using ${test_framework || 'pytest'}. Include edge cases and error handling.`,
      language: language,
      context_files: [file_path],
      output_path: file_path.replace(/\.(py|js|ts)$/, '_test.$1')
    });
    
    res.json({
      tests: response.data.code,
      file_path: response.data.file_path,
      explanation: response.data.explanation
    });
  } catch (error) {
    console.error('Test generation error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Documentation generation endpoint
app.post('/api/generate-docs', async (req, res) => {
  try {
    const { code, language, file_path, doc_format } = req.body;
    
    const response = await axios.post(`${AGENT_ORCHESTRATOR_URL}/task`, {
      task: `Generate ${doc_format || 'docstring'} documentation for this ${language} code. Include parameter descriptions, return values, and usage examples.`,
      context: { code, language, file_path }
    });
    
    res.json({
      documentation: response.data.result,
      format: doc_format || 'docstring'
    });
  } catch (error) {
    console.error('Documentation generation error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Inline edit endpoint
app.post('/api/inline-edit', async (req, res) => {
  try {
    const { file_path, selection, instruction, language } = req.body;
    
    const response = await axios.post(`${AGENT_ORCHESTRATOR_URL}/task`, {
      task: `Edit the selected code: ${instruction}`,
      context: {
        file_path: file_path,
        selection: selection,
        language: language
      }
    });
    
    res.json({
      edited_code: response.data.result,
      changes: response.data.changes || []
    });
  } catch (error) {
    console.error('Inline edit error:', error);
    res.status(500).json({ error: error.message });
  }
});

// WebSocket for real-time features
wss.on('connection', (ws) => {
  console.log('Client connected');
  
  ws.on('message', async (message) => {
    try {
      const data = JSON.parse(message);
      
      if (data.type === 'completion') {
        // Real-time completion streaming
        const response = await axios.post(`${OLLAMA_HOST}/api/generate`, {
          model: 'deepseek-coder:33b',
          prompt: data.prompt,
          stream: true
        }, {
          responseType: 'stream'
        });
        
        response.data.on('data', (chunk) => {
          const lines = chunk.toString().split('\n').filter(l => l);
          for (const line of lines) {
            try {
              const parsed = JSON.parse(line);
              if (parsed.response) {
                ws.send(JSON.stringify({
                  type: 'completion',
                  text: parsed.response
                }));
              }
            } catch (e) {
              // Ignore parse errors
            }
          }
        });
      }
    } catch (error) {
      ws.send(JSON.stringify({
        type: 'error',
        message: error.message
      }));
    }
  });
  
  ws.on('close', () => {
    console.log('Client disconnected');
  });
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'vscode-extension-server' });
});

const PORT = process.env.PORT || 3003;
app.listen(PORT, () => {
  console.log(`VS Code Extension Server running on port ${PORT}`);
  console.log(`WebSocket server running on port 3004`);
});

