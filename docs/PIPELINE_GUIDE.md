# 🚀 Pipeline & Execution Guide

This guide explains how to execute, customize, and extend the multi-agent research pipeline programmatically or via interfaces.

---

## 💻 Running the Pipeline

### 1. Interactive Web Dashboard (Streamlit)
The recommended interface for user-friendly research:

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```
Or with activated venv:
```powershell
streamlit run app.py
```
- Open your browser at `http://localhost:8501`.
- Enter any topic or click one of the quick-starter suggestion chips.
- Watch live agent status updates as they search, scrape, write, and critique.
- Download reports as `.md` or copy to clipboard.

---

### 2. Command-Line Interface (`main.py`)
Run a research topic directly from PowerShell:

```powershell
python main.py
```
To change the topic, edit [main.py](file:///c:/new/multi-agent-research/main.py):
```python
from src.pipelines.pipeline import run_research_pipeline

topic = "The impact of quantum computing on modern cryptography in 2026"
result = run_research_pipeline(topic)
```

---

## 🧩 Programmatic API Usage

You can import and call `run_research_pipeline` anywhere in your Python code:

```python
from src.pipelines.pipeline import run_research_pipeline

def my_callback(step_num: int, step_name: str, status: str, data: any):
    print(f"[{status.upper()}] Step {step_num}: {step_name}")

result = run_research_pipeline(
    topic="Advances in Solid-State Batteries 2026",
    model_name="gemini-3.1-flash-lite",
    temperature=0.2,
    status_callback=my_callback
)

print(result["report"])
print(result["feedback"])
```

### Callback Parameters
- `step_num` (`int`): Step index `1` to `4`.
- `step_name` (`str`): Human-readable name of the step.
- `status` (`str`): Either `"running"` or `"done"`.
- `data` (`any`): Intermediate output returned upon step completion (e.g. search string, scraped text, report string).

---

## 🛠️ Customizing Agent Behaviors

### 1. Adjusting Writer Output Format
In [src/agents/agents.py](file:///c:/new/multi-agent-research/src/agents/agents.py#L35-L53), customize `writer_prompt` to change report sections, depth, tone, or word counts.

### 2. Customizing Critic Criteria
In [src/agents/agents.py](file:///c:/new/multi-agent-research/src/agents/agents.py#L58-L78), edit `critic_prompt` to introduce custom metrics (e.g., commercial feasibility, risk assessment, methodology rigor).

### 3. Adding New Tools to Agents
Tools can be added by passing them to `tools=[...]` in `build_search_agent` or `build_reader_agent`:
```python
@tool
def my_custom_tool(param: str) -> str:
    """Description for the agent to know when to call this tool."""
    return "result"

def build_search_agent(model_llm=None):
    return create_agent(
        model=model_llm or llm,
        tools=[web_search, my_custom_tool],
    )
```

---

## ⚠️ Troubleshooting & FAQ

### 1. `RateLimitError` or `429 RESOURCE_EXHAUSTED`
- If you hit rate limits on `gemini-3.8-flash` (free tier limit of 20 requests/day), switch to **`gemini-3.1-flash-lite`** in the UI sidebar dropdown or set `GEMINI_MODEL=gemini-3.1-flash-lite` in `.env`.

### 2. `ModuleNotFoundError`
- Ensure you are running within the project's virtual environment:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```

### 3. Scraping Fails on Protected Pages
- Certain websites implement Cloudflare bot protections or CAPTCHAs. The scraper will fall back through Trafilatura ➔ Readability ➔ BeautifulSoup. If all tiers fail, it returns an informative error string so the writer agent can proceed using remaining search snippets.
