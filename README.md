# claude-code-mercury

**A universal upgrade layer for model tool calling, adapted for Inception Labs' Mercury 2 diffusion LLM.**

Claude Code runs natively on Mercury 2 through bidirectional protocol translation and structured tool enrichment. The same enrichment applied to any model -- including Claude itself -- measurably improves tool calling accuracy.

Built on the [Agentic API Standard](https://github.com/nexus-marbell/agentic-api-standard): 20 design patterns for self-describing, machine-first interfaces.

Adapted from [claude-code-xai](https://github.com/vantasnerdan/claude-code-xai) -- the original Grok bridge that proved the "universal upgrade layer" thesis.

---

## What is Mercury 2?

Mercury 2 is a **diffusion large language model (dLLM)** by [Inception Labs](https://www.inceptionlabs.ai/). Unlike autoregressive models (GPT, Claude, Grok) that generate tokens one at a time left-to-right, Mercury uses discrete diffusion to refine multiple text blocks simultaneously -- comparable to an editor revising an entire draft at once rather than writing word by word.

Key characteristics:

| Property | Value |
|----------|-------|
| **Architecture** | Diffusion LLM (dLLM) -- parallel token generation |
| **Context Window** | 128K tokens |
| **Max Output** | 16,384 tokens |
| **Speed** | ~1,000 tokens/second on Blackwell GPUs |
| **Reasoning** | Tunable via `reasoning_effort` (instant / low / medium / high) |
| **Function Calling** | Supported (OpenAI tool/function format) |
| **Streaming** | Simulated -- generates full response block, then streams tokens |
| **API Format** | OpenAI Chat Completions compatible (drop-in) |
| **Pricing** | $0.25/MTok input, $0.75/MTok output |

Mercury 2 benchmarks competitively with Claude 4.5 Haiku and GPT 5.2 Mini on reasoning tasks (GPQA Diamond: 74, AIME: 91) while being 5x faster and significantly cheaper.

## The Problem

Large language models learn tool calling through reinforcement learning. The learned behaviors are implicit -- baked into weights, not visible in the API. When a model encounters a new tool ecosystem, it has no training signal to draw on. Tool definitions ship as minimal JSON Schema: a name, a description, a parameter list. No sequencing rules. No failure modes. No context about when to use one tool over another.

This creates two problems:

1. **Cross-model tool calling is blind.** Mercury has never seen Claude Code's tools. It does not know that `Read` should come before `Edit`, that `Grep` replaces `bash grep`, or that force-pushing will destroy work. Without this knowledge, tool calling degrades to guesswork.

2. **Even trained models underperform.** Claude's RL training encodes tool usage patterns, but the tool definitions themselves remain sparse. The model works *despite* the schema, not *because* of it. Richer definitions would make the implicit explicit -- and measurably improve accuracy.

## Architecture

```
Claude Code (Anthropic Messages API)
       |
       v
+-----------------------------------------+
|       claude-code-mercury               |
|                                         |
|  +-----------------------------------+  |
|  |    System Preamble Injection      |  |
|  |  6 behavioral areas from CC       |  |
|  |  training: tool preference,       |  |
|  |  sequencing, chaining,            |  |
|  |  parallelism, safety, output      |  |
|  +----------------+------------------+  |
|                   |                     |
|  +----------------v------------------+  |
|  |     Tool Enrichment Engine        |  |
|  |                                   |  |
|  |  Layer 1: 8 Structural            |  |
|  |  patterns from the standard       |  |
|  |                                   |  |
|  |  Layer 2: 3 Behavioral            |  |
|  |  dimensions (WHAT/WHY/WHEN)       |  |
|  |  for 9 Claude Code tools          |  |
|  +----------------+------------------+  |
|                   |                     |
|  +----------------v------------------+  |
|  |   Protocol Translation Layer      |  |
|  |                                   |  |
|  |  Forward:  Messages -> Chat       |  |
|  |  Reverse:  Chat -> Messages       |  |
|  |  Streaming: SSE <-> SSE           |  |
|  |  Tools: tool_use <-> functions    |  |
|  +----------------+------------------+  |
|                   |                     |
+-----------------------------------------+
                    |
                    v
      Mercury API (Inception Labs)
      api.inceptionlabs.ai/v1
```

Every request flows through three stages: behavioral context injection, tool definition enrichment, and protocol translation. Responses flow back through the reverse path. Streaming is supported (see Porting Notes for Mercury-specific behavior).

## Quickstart

### Prerequisites

- Python 3.11+
- A Mercury API key from [platform.inceptionlabs.ai](https://platform.inceptionlabs.ai/dashboard/api-keys)
- Claude Code installed (`npm install -g @anthropic-ai/claude-code`)

### Setup

```bash
git clone https://github.com/nexus-marbell/claude-code-mercury.git
cd claude-code-mercury

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env: set INCEPTION_API_KEY=your-key-here

# Start the bridge
python main.py
# Bridge running on http://localhost:4000
```

### Connect Claude Code

```bash
ANTHROPIC_BASE_URL=http://localhost:4000 claude
```

Claude Code now routes through the bridge. Tool definitions are enriched with the Agentic API Standard before reaching Mercury. Responses are translated back to Anthropic format transparently.

### Docker

```bash
docker compose up -d
ANTHROPIC_BASE_URL=http://localhost:4000 claude
```

### Run Tests

```bash
pytest                          # All tests (no API key required)
pytest -m "not live"            # Unit/integration only
INCEPTION_API_KEY=sk-... pytest   # Include live API tests
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `INCEPTION_API_KEY` | -- | Your Inception Labs API key (required) |
| `MERCURY_MODEL` | `mercury-2` | Mercury model to use |
| `MERCURY_REASONING_EFFORT` | `high` | Reasoning depth: `instant` / `low` / `medium` / `high` |
| `ENRICHMENT_MODE` | `full` | `passthrough` / `structural` / `full` |
| `PREAMBLE_ENABLED` | `true` | System prompt behavioral injection |
| `IDENTITY_ENABLED` | `true` | Mercury identity assertion + Claude stripping |
| `STRUCTURE_DIR` | `./structure` | Path to enrichment YAML definitions |
| `HOST` | `0.0.0.0` | Bridge listen address |
| `PORT` | `4000` | Bridge listen port |

### Enrichment Modes

- **`passthrough`** -- No enrichment. Raw tool definitions forwarded as-is. Use for A/B benchmarking.
- **`structural`** -- API Standard patterns only. Self-describing schemas, error formats, HATEOAS navigation. No behavioral knowledge.
- **`full`** -- Structural + behavioral. Complete WHAT/WHY/WHEN training transfer. Gold standard compliance.

## Standard Compliance

Built against the [Agentic API Standard](https://github.com/nexus-marbell/agentic-api-standard) compliance tiers:

| Tier | Patterns | Status |
|------|----------|--------|
| **Bronze** | P1 (Manifest), P3 (Errors), P4 (HTTP Status), P9 (Infrastructure Errors), P10 (Content Negotiation) | Implemented |
| **Silver** | Bronze + P2 (HATEOAS), P6 (Self-Describing), P7 (Canonical Naming), P11 (Rate Limits) | Implemented |
| **Gold** | All 20 patterns | Target |

## Porting Notes: Mercury vs Grok

This bridge was adapted from [claude-code-xai](https://github.com/vantasnerdan/claude-code-xai). The following differences between Mercury and Grok informed the adaptation:

### Fully Portable (no changes needed)

- **Protocol format**: Both use OpenAI Chat Completions API. The entire translation layer (forward, reverse, tools, streaming adapter) works unchanged.
- **Function calling**: Mercury supports the same OpenAI function/tool calling schema. No format changes needed.
- **Error format**: Mercury returns standard OpenAI error responses. The error translation layer works as-is.
- **Enrichment engine**: All structural and behavioral enrichment is model-agnostic. The entire `enrichment/` package works unchanged.

### Adapted

| Area | Grok Behavior | Mercury Behavior | Bridge Handling |
|------|--------------|-------------------|-----------------|
| **API endpoint** | `api.x.ai/v1` | `api.inceptionlabs.ai/v1` | Updated base URL |
| **Auth env var** | `XAI_API_KEY` | `INCEPTION_API_KEY` | Renamed |
| **Model names** | `grok-4`, `grok-4-1-fast-reasoning` | `mercury-2` | Updated MODEL_MAP |
| **Model env var** | `GROK_MODEL` | `MERCURY_MODEL` | Renamed |
| **Identity preamble** | "You are Grok (xAI)" | "You are Mercury 2 (Inception Labs)" | Updated |
| **Thinking/reasoning** | Grok reasons internally, no control | Mercury has `reasoning_effort` param | Claude's `thinking` stripped; Mercury's `reasoning_effort` injected (default: `high`) |

### Mercury-Specific Behavior to Be Aware Of

**Simulated Streaming**: Mercury's diffusion architecture generates the full response block, then streams tokens to the client. This means:
- Time-to-first-token (TTFT) may be higher than autoregressive models (~12s measured)
- Once streaming begins, throughput is extremely fast (~1,000+ tok/s)
- The bridge's streaming adapter handles this transparently -- the SSE event format is the same
- Clients expecting low TTFT for perceived responsiveness should be aware of this trade-off

**Reasoning Effort**: Mercury supports a `reasoning_effort` parameter with four levels: `instant`, `low`, `medium`, `high`. The bridge injects `reasoning_effort` (default: `high`) and `reasoning_summary: true` into every request. Anthropic's `thinking` param is stripped and mapped to Mercury's native reasoning. Override via `MERCURY_REASONING_EFFORT` env var.

**Max Output Tokens**: Mercury 2 supports up to 16,384 output tokens. Requests with `max_tokens` above this may be silently capped by the API. The bridge passes `max_tokens` through unchanged.

**Temperature**: Mercury 2 supports temperatures in the range 0.5-1.0. The bridge clamps values outside this range automatically (with debug logging). Temperatures below 0.5 are clamped to 0.5; above 1.0 are clamped to 1.0.

**Vision**: Mercury 2 is text-only (no image input). The bridge already rejects image content blocks with a clear error message, same as the Grok bridge.

### Not Yet Implemented

- **Diffusion visualization**: Mercury's `diffusing` parameter (streams noisy tokens that refine into the final output) is not exposed through the bridge
- **Mercury-edit model**: The `mercury-edit` model (code editing specialist for FIM/apply-edit) is not integrated -- the bridge always routes to `mercury-2`

## Project Structure

```
claude-code-mercury/
+-- main.py                  # FastAPI bridge application
+-- manifest.json            # Agentic API Standard manifest (Pattern 1)
+-- translation/             # Bidirectional protocol translation
|   +-- forward.py           # Anthropic Messages -> OpenAI Chat
|   +-- reverse.py           # OpenAI Chat -> Anthropic Messages
|   +-- streaming.py         # SSE event stream adaptation
|   +-- tools.py             # Tool schema conversion + enrichment hooks
|   +-- config.py            # Model mapping, feature flags
+-- enrichment/              # Two-layer tool enrichment engine
|   +-- engine.py            # Pipeline orchestrator
|   +-- factory.py           # Configured enricher creation
|   +-- config.py            # Mode selection (passthrough/structural/full)
|   +-- system_preamble.py   # Behavioral conventions injection
|   +-- structural/          # Layer 1: API Standard patterns
|   +-- behavioral/          # Layer 2: Training transfer
+-- structure/               # Editable enrichment definitions (YAML)
|   +-- manifest.yaml        # Master index
|   +-- behavioral/          # WHAT/WHY/WHEN per tool
|   +-- structural/          # API Standard patterns per tool
|   +-- preamble/            # Identity and conventions
+-- bridge/                  # Infrastructure (logging, token tracking)
+-- benchmarks/              # Deterministic quality measurement
+-- tests/                   # 490+ tests
+-- docker-compose.yml       # One-command deployment
```

## Attribution

This project is adapted from [claude-code-xai](https://github.com/vantasnerdan/claude-code-xai) by the same team. The original bridge proved the "universal upgrade layer" thesis with Grok. This adaptation validates that the enrichment architecture is truly model-agnostic by porting it to a fundamentally different model architecture (diffusion vs autoregressive).

Built on the [Agentic API Standard](https://github.com/nexus-marbell/agentic-api-standard): 20 design patterns for agent-friendly interfaces.

## License

MIT
