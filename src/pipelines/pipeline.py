from src.agents.agents import (
    build_search_agent,
    build_reader_agent,
    get_writer_chain,
    get_critic_chain,
    get_llm,
)

def extract_text(content) -> str:
    """Helper to ensure agent message content is cleanly converted to string."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
            elif hasattr(item, "text"):
                parts.append(getattr(item, "text"))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)

def run_research_pipeline(
    topic: str,
    model_name: str = None,
    temperature: float = 0.3,
    status_callback = None,
) -> dict:
    """Execute the 4-step autonomous research pipeline.
    
    Args:
        topic: The research topic query.
        model_name: Optional Gemini model name override.
        temperature: LLM sampling temperature.
        status_callback: Optional callable(step_num, step_name, status, data) for UI updates.
        
    Returns:
        dict containing search_results, scraped_content, report, and feedback.
    """
    state = {}
    llm_instance = get_llm(model=model_name, temperature=temperature)
    writer_c = get_writer_chain(llm_instance)
    critic_c = get_critic_chain(llm_instance)

    # Step 1 - Search agent
    if status_callback:
        status_callback(1, "Searching the Web", "running", None)
    print("\n" + " ="*50)
    print("step 1 - search agent is working ...")
    print("="*50)

    search_agent = build_search_agent(model_llm=llm_instance)
    search_result = search_agent.invoke({
        "messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]
    })
    raw_search = search_result['messages'][-1].content
    state["search_results"] = extract_text(raw_search)

    if status_callback:
        status_callback(1, "Web Search Completed", "done", state["search_results"])
    print("\n search result ", state['search_results'])

    # Step 2 - Reader agent
    if status_callback:
        status_callback(2, "Scraping Top Resources", "running", None)
    print("\n" + " ="*50)
    print("step 2 - Reader agent is scraping top resources ...")
    print("="*50)

    reader_agent = build_reader_agent(model_llm=llm_instance)
    reader_result = reader_agent.invoke({
        "messages": [("user",
            f"Based on the following search results about '{topic}', "
            f"pick the most relevant URL and scrape it for deeper content.\n\n"
            f"Search Results:\n{state['search_results'][:1500]}"
        )]
    })
    raw_scrape = reader_result['messages'][-1].content
    state['scraped_content'] = extract_text(raw_scrape)

    if status_callback:
        status_callback(2, "Deep Reading Completed", "done", state["scraped_content"])
    print("\nscraped content: \n", state['scraped_content'])

    # Step 3 - Writer chain
    if status_callback:
        status_callback(3, "Drafting Comprehensive Report", "running", None)
    print("\n" + " ="*50)
    print("step 3 - Writer is drafting the report ...")
    print("="*50)

    research_combined = (
        f"SEARCH RESULTS:\n{state['search_results']}\n\n"
        f"DETAILED SCRAPED CONTENT:\n{state['scraped_content']}"
    )

    state["report"] = writer_c.invoke({
        "topic": topic,
        "research": research_combined,
    })

    if status_callback:
        status_callback(3, "Report Drafted", "done", state["report"])
    print("\n Final Report\n", state['report'])

    # Step 4 - Critic chain
    if status_callback:
        status_callback(4, "Critic Reviewing Report", "running", None)
    print("\n" + " ="*50)
    print("step 4 - critic is reviewing the report ")
    print("="*50)

    state["feedback"] = critic_c.invoke({
        "report": state['report']
    })

    if status_callback:
        status_callback(4, "Review Complete", "done", state["feedback"])
    print("\n critic report \n", state['feedback'])

    return state