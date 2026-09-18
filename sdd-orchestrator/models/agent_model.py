from dataclasses import dataclass, field
from typing import List, Optional

from models.cli_discovery_model import CLIInfo

@dataclass
class AgentConfig:
    """Configuration of an AI agent, derived from a discovered CLI."""
    cli_key: str
    display_name: str
    model_name: str
    extra_args: list[str] = field(default_factory=list)
    cli_type: str = ""

class AgentModel:
    """Model for configuring available and active AI agents."""
    def __init__(self):
        self._active_agent: Optional[AgentConfig] = None
        self._available_agents: List[AgentConfig] = []

    def get_available_agents(self, found_clis: List[CLIInfo]) -> List[AgentConfig]:
        """Converts discovered CLIs into available agent configurations."""
        self._available_agents = []
        for cli in found_clis:
            if cli.found:
                # For now we use a default placeholder model based on the CLI,
                # e.g., we could map it in the future.
                model_name = "default"
                if cli.key == "claude":
                    model_name = "claude-3-7-sonnet-20250219"
                elif cli.key == "gemini":
                    model_name = "gemini-2.5-pro"
                elif cli.key == "codex":
                    model_name = "gpt-4o"
                
                config = AgentConfig(
                    cli_key=cli.key,
                    display_name=cli.display_name,
                    model_name=model_name,
                    cli_type=cli.cli_type
                )
                self._available_agents.append(config)
        return self._available_agents

    def set_active_agent(self, agent_config: AgentConfig) -> None:
        """Sets the active agent."""
        self._active_agent = agent_config

    def get_active_agent(self) -> Optional[AgentConfig]:
        """Returns the active agent."""
        return self._active_agent
