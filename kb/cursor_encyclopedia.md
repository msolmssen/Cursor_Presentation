# Cursor Technical & Competitive Encyclopedia

## Core Technical Theses
### 1. Context Windows vs. Fine-Tuning
- **Thesis**: Long context windows paired with high-precision retrieval outperform fine-tuning for high-velocity teams.
- **The "Why"**: Fine-tuning is a dead end; by the time a model is trained on a codebase, the code has changed.
- **The Solution**: Cursor "feeds" the model the most relevant, up-to-date dependencies across the entire monolith in real-time. This provides the "ground truth" of the latest commit.
- **Impact**: Superior understanding of complex, dynamic code structures without the artificial limitations of fine-tuning.

### 2. Multi-Model Task Optimization
- **Thesis**: One model cannot do everything. Cursor uses a system of specialized, purpose-built models.
- **The Architecture**:
  - **Tab**: In-house model optimized for predictive code completion and "Ghost Text."
  - **Apply**: Specialized model for applying AI-generated code changes to the codebase.
  - **Composer**: Orchestrates multi-file edits.

### 3. Synchronicity & Engineering Modalities
- **Thesis**: Seamlessly transitioning between real-time background AI assistance (Tab) and active agents (Composer) allows for different modalities of work in one platform.

## Product Features & "Aha!" Moments
- **IDE-Native vs. Extension**: Built into the core logic of the editor, not a "shallow" plugin.
- **Vector Indexing**: Cursor builds a permanent mathematical map (vector index) of local files for lower latency and "Flow State."
- **Ghost Text**: Predicts not just the next word, but the next *edit location* (e.g., changing a React component and predicting the change in the corresponding file).
- **Model Neutrality**: Access to OpenAI, Anthropic, Google, and in-house models. No vendor lock-in; users get the best price/performance.
- **Security**: SOC 2 Type II. "Privacy Mode" guarantees code is never stored or used for training.

## Competitive Takedowns
### VS Code Copilot (The Extension Problem)
- **Shallow Awareness**: Limited by the VS Code API; cannot "connect the dots" across a large codebase as effectively as Cursor's native indexing.
- **Platform vs. Product**: Microsoft prioritizes stability for a mass platform; Cursor prioritizes speed and UI innovation for developers.
- **Lock-in**: Pushes OpenAI/Azure; not model agnostic.

### Claude Code (The Terminal Problem)
- **The Black Box**: Agents present a plan and apply a diff in a terminal. If there is a logic error, you don't see it until the code runs.
- **Context Blindness**: It can read files, but it doesn't "see" what the dev is looking at or where the cursor is positioned.
- **Feedback Loop**: Slower than Cursor's real-time streaming into the file.
