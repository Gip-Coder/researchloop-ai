"""
Prompt templates for researchloop-ai agents.
All external academic content is explicitly isolated inside security boundaries.
"""

from backend.agent.prompts.planner import PLANNER_SYSTEM_PROMPT, build_planner_prompt
from backend.agent.prompts.relevance import RELEVANCE_SYSTEM_PROMPT, build_relevance_prompt
from backend.agent.prompts.synthesis import SYNTHESIS_SYSTEM_PROMPT, build_synthesis_prompt
from backend.agent.prompts.critic import CRITIC_SYSTEM_PROMPT, build_critic_prompt
from backend.agent.prompts.replanner import REPLANNER_SYSTEM_PROMPT, build_replanner_prompt

__all__ = [
    "PLANNER_SYSTEM_PROMPT",
    "build_planner_prompt",
    "RELEVANCE_SYSTEM_PROMPT",
    "build_relevance_prompt",
    "SYNTHESIS_SYSTEM_PROMPT",
    "build_synthesis_prompt",
    "CRITIC_SYSTEM_PROMPT",
    "build_critic_prompt",
    "REPLANNER_SYSTEM_PROMPT",
    "build_replanner_prompt",
]

