# 🛠️ Tools & API Reference

This document provides a technical reference for the tools, models, and environment variables used by the agents.

---

## 🔧 Agent Tools (`src/tools/tools.py`)

### 1. `web_search(query: str) -> str`
Wrapped with `@tool` from `langchain.tools`.

- **Engine**: Tavily Search API (`tavily-python`).
- **Signature**:
  ```python
  def web_search(query: str) -> str
  ```
- **Behavior**:
  - Sends query to `tavily.search(query=query, max_results=5)`.
  - Formats results into structured blocks:
    - `Title`: Document title
    - `URL`: Web link
    - `Content`: First 300 characters of relevance preview
  - Handles network timeouts and returns error messages gracefully if the API fails.

---

### 2. `scrape_url(url: str) -> str`
Wrapped with `@tool` from `langchain.tools`.

- **Strategy**: Multi-tier extraction with automatic fallback.
- **Signature**:
  ```python
  def scrape_url(url: str) -> str
  ```
- **Fallback Pipeline**:
  ```mermaid
  flowchart TD
      URL[Target URL] --> HTTP[requests.get with Browser User-Agent]
      HTTP --> Tier1{Tier 1: Trafilatura}
      Tier1 -->|Success| Clean[Regex Spacing & Line Sanitation]
      Tier1 -->|Empty / Failed| Tier2{Tier 2: Readability-lxml}
      Tier2 -->|Success| Clean
      Tier2 -->|Empty / Failed| Tier3[Tier 3: BeautifulSoup DOM Strip]
      Tier3 --> Clean
      Clean --> Output[Truncate to 15,000 chars & Return]
  ```
- **Key Details**:
  - **Headers**: Spoofs standard modern desktop Chrome `User-Agent`.
  - **Timeout**: 15 seconds.
  - **Sanitization**: Decomposes `<script>`, `<style>`, `<nav>`, `<footer>`, and `<header>` tags. Collapses whitespace with regex.
  - **Limits**: Returns up to 15,000 characters to prevent context-window blowup while preserving complete article substance.

---

## 🧠 LLM Engines & Providers (`src/agents/agents.py`)

### Google Gemini (Default & Recommended)
- **Library**: `langchain-google-genai`
- **Supported Models**:
  - `gemini-3.1-flash-lite` *(Default)*: Extremely high token throughput, ideal for free-tier development.
  - `gemini-3.8-flash`: Cutting-edge reasoning and speed.
  - `gemini-flash-latest`: Automatically tracks latest stable flash release.
- **Config**:
  ```python
  llm = ChatGoogleGenerativeAI(
      model=model_name,
      temperature=0.3,
      api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
  )
  ```

---

## 🔐 Environment Variables (`.env`)

| Variable | Required | Description | Example |
| :--- | :--- | :--- | :--- |
| `GEMINI_API_KEY` | **Yes** (or `GOOGLE_API_KEY`) | Google AI Studio API key | `AQ.Ab8RN6...` |
| `TAVILY_API_KEY` | **Yes** | Tavily search API key | `tvly-dev-37y...` |
| `OPENAI_API_KEY` | *Optional* | OpenAI API key (if switching to GPT models) | `sk-proj-...` |
| `GEMINI_MODEL` | *Optional* | Default model override | `gemini-3.1-flash-lite` |
