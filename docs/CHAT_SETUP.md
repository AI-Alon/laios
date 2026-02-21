# 🚀 Quick Setup Guide - Getting Chat Working

## Step-by-Step Setup

### 1. Install Ollama

Choose your platform:

**macOS**:
```bash
curl https://ollama.ai/install.sh | sh
```

**Linux**:
```bash
curl https://ollama.ai/install.sh | sh
```

**Windows**:
- Download installer from: https://ollama.ai/download
- Run the installer
- Ollama will start automatically

### 2. Start Ollama (if not already running)

```bash
ollama serve
```

Leave this running in a terminal window.

### 3. Pull a Model

In a **new terminal**:

```bash
# Recommended: Llama 2 (good balance of speed and quality)
ollama pull llama2

# This will download ~3.8GB
# Takes 5-10 minutes depending on your internet
```

**Alternative models**:
```bash
ollama pull mistral       # 4.1GB - Great quality
ollama pull phi           # 1.6GB - Fast, smaller
ollama pull codellama     # 3.8GB - Better at code
ollama pull llama2:13b    # 7.3GB - More capable
```

### 4. Verify Ollama Works

```bash
# List installed models
ollama list

# Test the model
ollama run llama2 "Hello, how are you?"
```

You should see a response from the model.

### 5. Run LAIOS Chat

```bash
laios chat
```

You should see:

```
╭─────────────────────────────────────╮
│   LAIOS Interactive Chat            │
│ Type 'exit' or 'quit' to end        │
╰─────────────────────────────────────╯

Session ID: abc-123...

You: 
```

### 6. Test the Chat

Try these messages:

```
You: Hello! What can you do?

You: What tools do you have access to?

You: Can you explain what an autonomous agent is?

You: What's 2+2?

You: Tell me about yourself
```

Type `exit` or `quit` to end the session.

## Troubleshooting

### Problem: "LLM client not initialized"

**Cause**: Ollama not running or model not available

**Fix**:
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Check models
ollama list

# If no models, pull one
ollama pull llama2
```

### Problem: "Connection refused"

**Cause**: Ollama not accessible

**Fix**:
```bash
# Check Ollama status
curl http://localhost:11434/api/version

# Should return: {"version":"..."}
```

### Problem: Very slow responses

**Cause**: Model too large for your hardware

**Fix**:
```bash
# Use smaller model
ollama pull phi

# Update config to use phi
# Edit config/default.yaml
llm:
  model: "phi"
```

### Problem: "ollama package not installed"

**Fix**:
```bash
pip install ollama
```

## Next Steps

Once chat is working:

1. **Try different models**:
   ```bash
   ollama pull mistral
   # Edit config/default.yaml to use "mistral"
   laios chat
   ```

2. **Run the example**:
   ```bash
   python examples/chat_example.py
   ```

3. **Explore tools**:
   ```bash
   laios tools list
   laios tools run filesystem.read_file --params '{"path": "README.md"}'
   ```

## System Requirements

- **RAM**: 8GB minimum (16GB recommended)
- **Disk**: 5-10GB for models
- **CPU**: Modern multi-core (Apple Silicon works great!)
- **GPU**: Optional but helpful

## Model Recommendations

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| phi | 1.6GB | ⚡⚡⚡ | ⭐⭐ | Quick tests, low-resource |
| llama2 | 3.8GB | ⚡⚡ | ⭐⭐⭐ | General use (recommended) |
| mistral | 4.1GB | ⚡⚡ | ⭐⭐⭐⭐ | Better quality |
| llama2:13b | 7.3GB | ⚡ | ⭐⭐⭐⭐⭐ | Maximum quality |
| codellama | 3.8GB | ⚡⚡ | ⭐⭐⭐ | Coding tasks |

---

**You're ready!** Start chatting with LAIOS: `laios chat` 🎉
