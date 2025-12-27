# Model Recommendations for Your Hardware

## Your System Specifications

- **GPU**: NVIDIA RTX PRO 6000 Blackwell (96GB VRAM)
- **CPU**: AMD Ryzen Threadripper PRO 7985WX (64 cores)
- **RAM**: 256GB
- **OS**: Ubuntu

Your system is exceptionally powerful and can run the largest available models efficiently.

## Model Categories

### 1. Coding Models

These models are optimized for code generation, completion, and understanding.

#### Recommended: **deepseek-coder:33b**
- **VRAM Required**: ~20GB
- **Best For**: Code generation, completion, debugging
- **Strengths**: 
  - Excellent code understanding
  - Strong multi-language support
  - Great at following patterns
  - Fast inference
- **Pull Command**: `ollama pull deepseek-coder:33b`

#### Alternative: **codellama:34b**
- **VRAM Required**: ~20GB
- **Best For**: Code generation, Python/JavaScript focus
- **Strengths**:
  - Strong Python support
  - Good for refactoring
  - Fast inference
- **Pull Command**: `ollama pull codellama:34b`

#### Alternative: **qwen2.5-coder:32b**
- **VRAM Required**: ~20GB
- **Best For**: Multi-language code generation
- **Strengths**:
  - Excellent multilingual support
  - Good code quality
- **Pull Command**: `ollama pull qwen2.5-coder:32b`

### 2. Reasoning Models

These models excel at complex reasoning, problem-solving, and multi-step thinking.

#### Recommended: **llama3.2:90b**
- **VRAM Required**: ~50GB
- **Best For**: Complex reasoning, problem-solving, architecture decisions
- **Strengths**:
  - Best reasoning capabilities
  - Excellent for chain-of-thought
  - Great for system design
  - Handles complex multi-step tasks
- **Pull Command**: `ollama pull llama3.2:90b`

#### Alternative: **llama3.2:70b**
- **VRAM Required**: ~40GB
- **Best For**: High-quality reasoning with faster inference
- **Strengths**:
  - Excellent reasoning
  - Faster than 90b
  - Still very capable
- **Pull Command**: `ollama pull llama3.2:70b`

#### Alternative: **qwen2.5:72b**
- **VRAM Required**: ~40GB
- **Best For**: Complex reasoning, multilingual tasks
- **Strengths**:
  - Strong reasoning
  - Multilingual capabilities
- **Pull Command**: `ollama pull qwen2.5:72b`

### 3. Embedding Models

These models generate vector embeddings for RAG and semantic search.

#### Recommended: **nomic-embed-text**
- **Dimensions**: 768
- **VRAM Required**: ~2GB
- **Best For**: Code embeddings, semantic search
- **Strengths**:
  - Excellent for code
  - Fast inference
  - Good quality embeddings
  - Optimized for code understanding
- **Pull Command**: `ollama pull nomic-embed-text`

#### Alternative: **mxbai-embed-large**
- **Dimensions**: 1024
- **VRAM Required**: ~3GB
- **Best For**: High-quality embeddings
- **Strengths**:
  - Higher dimensional embeddings
  - Very high quality
  - Good for complex queries
- **Pull Command**: `ollama pull mxbai-embed-large`

## Recommended Model Setup

### Primary Setup (Recommended)

For your 96GB VRAM system, you can run multiple models simultaneously:

```bash
# Coding model
ollama pull deepseek-coder:33b

# Reasoning model
ollama pull llama3.2:90b

# Embedding model
ollama pull nomic-embed-text
```

**Total VRAM Usage**: ~72GB (leaves 24GB headroom)

### Alternative Setup (Faster Inference)

If you prefer faster inference over maximum quality:

```bash
# Coding model
ollama pull codellama:34b

# Reasoning model
ollama pull llama3.2:70b

# Embedding model
ollama pull nomic-embed-text
```

**Total VRAM Usage**: ~62GB (leaves 34GB headroom)

## Model Usage by Function

### Code Generation
- **Primary**: `deepseek-coder:33b`
- **Fallback**: `codellama:34b`

### Code Review
- **Primary**: `llama3.2:90b` (better reasoning for review)
- **Fallback**: `llama3.2:70b`

### Debugging
- **Primary**: `deepseek-coder:33b` (code-focused)
- **Secondary**: `llama3.2:90b` (for complex reasoning)

### Refactoring
- **Primary**: `deepseek-coder:33b`
- **Secondary**: `codellama:34b`

### Reasoning Tasks
- **Primary**: `llama3.2:90b`
- **Fallback**: `llama3.2:70b`

### Embeddings (RAG)
- **Primary**: `nomic-embed-text`
- **Alternative**: `mxbai-embed-large` (if you need higher dimensions)

## Model Configuration

### Ollama Configuration

Ensure Ollama is configured to:
- Listen on all interfaces: `OLLAMA_HOST=0.0.0.0`
- Keep models loaded: Set appropriate keep-alive times
- Use GPU: Automatically detected with NVIDIA GPU

### Keep-Alive Settings

To keep models loaded in memory for faster inference:

```bash
# Set in your Ollama environment or systemd service
export OLLAMA_KEEP_ALIVE=24h
```

Or configure per-model:

```bash
# Keep coding model loaded
ollama run deepseek-coder:33b --keep-alive 24h

# Keep reasoning model loaded  
ollama run llama3.2:90b --keep-alive 24h
```

## Performance Expectations

### With Your Hardware

- **90B Model Inference**: ~50-100 tokens/second
- **33B Model Inference**: ~150-300 tokens/second
- **Embedding Generation**: ~1000+ embeddings/second
- **Concurrent Requests**: Can handle 5-10 simultaneous requests

### Optimization Tips

1. **Keep Models Loaded**: Use keep-alive to avoid reload overhead
2. **Batch Processing**: Process multiple requests together when possible
3. **Model Selection**: Use smaller models for simple tasks, larger for complex
4. **GPU Memory**: Monitor with `nvidia-smi` to ensure optimal usage

## Installing Models

### Quick Install

```bash
# Install recommended models
ollama pull deepseek-coder:33b
ollama pull llama3.2:90b
ollama pull nomic-embed-text

# Verify installation
ollama list
```

### Model Information

```bash
# Show model details
ollama show deepseek-coder:33b
ollama show llama3.2:90b
ollama show nomic-embed-text
```

## Updating Models

```bash
# Update a model (pulls latest version)
ollama pull deepseek-coder:33b

# Remove old version if needed
ollama rm deepseek-coder:33b
```

## Model Storage

Models are stored in `~/.ollama/models/` on the host system. With your setup:
- 90B model: ~50GB
- 33B model: ~20GB
- Embedding model: ~2GB
- **Total**: ~72GB for recommended setup

## Troubleshooting

### Out of Memory

If you run out of VRAM:
1. Use smaller models (70B instead of 90B)
2. Reduce keep-alive time
3. Unload unused models: `ollama stop <model>`

### Slow Inference

1. Check GPU utilization: `nvidia-smi`
2. Ensure models are loaded (check keep-alive)
3. Verify GPU drivers are up to date
4. Check for other GPU processes

### Model Not Found

```bash
# List available models
ollama list

# Pull missing model
ollama pull <model-name>
```

## Advanced: Custom Models

You can also use custom models or fine-tuned versions:

```bash
# Create custom model from base
ollama create my-coder -f Modelfile

# Use custom model
ollama run my-coder
```

## Summary

For your powerful system, the recommended setup is:

1. **Coding**: `deepseek-coder:33b` - Best code generation
2. **Reasoning**: `llama3.2:90b` - Best reasoning capabilities  
3. **Embeddings**: `nomic-embed-text` - Excellent for code embeddings

This combination provides the best balance of quality and performance for your hardware.

