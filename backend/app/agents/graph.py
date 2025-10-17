import time
import logging
from langgraph.graph import StateGraph, END
from .state import AgentState
from .router import RouterAgent
from .researcher import ResearcherAgent
from .analyzer import AnalyzerAgent
from .composer import ComposerAgent

logger = logging.getLogger(__name__)


def route_after_router(state: AgentState) -> str:
    """Determine the next node based on research necessity"""
    if state.get("needs_research", False):
        return "researcher"
    else:
        return "composer"


def create_timed_wrapper(agent_name: str, execute_func):
    """Create a wrapper function that logs execution time and adds it to step_history"""
    async def wrapper(state: AgentState) -> AgentState:
        start_time = time.time()
        logger.info(f"[{agent_name}] Starting execution...")

        result = await execute_func(state)

        elapsed = round(time.time() - start_time, 1)
        logger.info(f"[{agent_name}] Completed in {elapsed}s")

        # Add elapsed time to the most recent step for this agent
        if result.get("step_history"):
            for step in reversed(result["step_history"]):
                if step["agent"] == agent_name and "elapsed_time" not in step:
                    step["elapsed_time"] = elapsed
                    break

        return result

    return wrapper


def create_agent_graph():
    """Create and configure the LangGraph agent workflow"""

    # Initialize agents
    router = RouterAgent()
    researcher = ResearcherAgent()
    analyzer = AnalyzerAgent()
    composer = ComposerAgent()

    # Create the graph
    workflow = StateGraph(AgentState)

    # Add nodes for each agent with timing wrappers
    workflow.add_node("router", create_timed_wrapper("Router", router.execute))
    workflow.add_node("researcher", create_timed_wrapper("Researcher", researcher.execute))
    workflow.add_node("analyzer", create_timed_wrapper("Analyzer", analyzer.execute))
    workflow.add_node("composer", create_timed_wrapper("Composer", composer.execute))

    # Define the workflow edges
    workflow.set_entry_point("router")

    # Conditional edge: route to researcher or composer based on needs_research flag
    workflow.add_conditional_edges(
        "router",
        route_after_router,
        {
            "researcher": "researcher",
            "composer": "composer"
        }
    )

    # Research path: researcher -> analyzer -> composer
    workflow.add_edge("researcher", "analyzer")
    workflow.add_edge("analyzer", "composer")

    # Both paths end at composer
    workflow.add_edge("composer", END)

    # Compile the graph
    app = workflow.compile()

    return app
