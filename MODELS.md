# Model Recommendations for 96GB VRAM

**Note**: Ollama runs natively on the Docker host (not in a container). Ensure Ollama is installed and running on the host system.

With your NVIDIA RTX PRO 6000 Blackwell (96GB VRAM), AMD Ryzen Threadripper PRO 7985WX (64 cores), and 256GB RAM, you can run very large models efficiently.

## Recommended Models

### Coding Models

#### deepseek-coder:33b (Recommended for Code)
- **VRAM Required**: ~20GB
- **Best for**: Code generation, completion, debugging
- **Quality**: Excellent for code
- **Speed**: Very fast

```bash
ollama pull deepseek-coder:33b
```

#### codellama:34b
- **VRAM Required**: ~20GB
- **Best for**: Code-specific tasks, Python/JavaScript focus
- **Quality**: Excellent for code
- **Speed**: Very fast

```bash
ollama pull codellama:34b
```

### Reasoning Models

#### llama3.2:90b (Recommended for Reasoning)
- **VRAM Required**: ~50GB
- **Best for**: Complex reasoning, problem-solving, architecture decisions
- **Quality**: Excellent
- **Speed**: Fast on your hardware

```bash
ollama pull llama3.2:90b
```

#### llama3.2:70b
- **VRAM Required**: ~40GB
- **Best for**: High-quality reasoning with faster inference
- **Quality**: Excellent
- **Speed**: Very fast

```bash
ollama pull llama3.2:70b
```

### Embedding Models

#### nomic-embed-text (Recommended for Embeddings)
- **Dimensions**: 768
- **VRAM Required**: ~2GB
- **Best for**: Code embeddings, semantic search, RAG
- **Quality**: Excellent for code
- **Speed**: Very fast

```bash
ollama pull nomic-embed-text
```

## Model Selection Strategy

### For Code Generation
- Primary: `llama3.2:90b` or `codellama:34b`
- Secondary: `deepseek-coder:33b`

### For Code Review
- Primary: `llama3.2:90b`
- Secondary: `llama3.2:70b`

### For Debugging
- Primary: `codellama:34b` or `deepseek-coder:33b`
- Secondary: `llama3.2:70b`

### For Refactoring
- Primary: `llama3.2:90b`
- Secondary: `codellama:34b`

## Running Multiple Models

You can run multiple models simultaneously on your powerful system:

```bash
# Pull recommended models
ollama pull deepseek-coder:33b
ollama pull llama3.2:90b
ollama pull nomic-embed-text

# List available models
ollama list
```

**Total VRAM Usage**: ~72GB (leaves 24GB headroom)

Then modify agents to use different models for different tasks.

## Model Configuration

To change the model used by agents, edit:

```python
# services/agent-orchestrator/agents/base_agent.py
self.model = "llama3.2:90b"  # Change this
```

Or set per-agent:

```python
# In specific agent classes
self.model = "codellama:34b"  # For code-specific tasks
```

## Performance Tips

1. **Keep Models Loaded**: Set `OLLAMA_KEEP_ALIVE=24h` in `.env`
2. **Batch Processing**: Process multiple requests together
3. **Model Quantization**: Use quantized versions if available (smaller, faster)
4. **GPU Memory**: Monitor with `nvidia-smi` to ensure optimal usage

## Model Information

Check model details:

```bash
# List all models
ollama list

# Show model info
ollama show llama3.2:90b
ollama show deepseek-coder:33b
ollama show nomic-embed-text
```

## Custom Models

You can also use custom models:

1. Create a Modelfile
2. Build custom model: `ollama create <name> -f Modelfile`
3. Use in agents

## Model Updates

Update models:

```bash
ollama pull llama3.2:90b
ollama pull deepseek-coder:33b
ollama pull nomic-embed-text
```

This will pull the latest version if available.

## Ollama Configuration

Ensure Ollama is configured on the host to:
- Listen on all interfaces: `OLLAMA_HOST=0.0.0.0`
- Keep models loaded for faster inference
- Use GPU acceleration (automatic with NVIDIA GPU)

See [MODEL_RECOMMENDATIONS.md](MODEL_RECOMMENDATIONS.md) for detailed recommendations based on your hardware.

