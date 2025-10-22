# 循環インポートを避けるため、遅延インポートを使用
def __getattr__(name):
    if name == "create_family_session":
        from .entrypoints import create_family_session
        return create_family_session
    elif name == "root_agent":
        from .root_agent import root_agent
        return root_agent
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    "create_family_session",
    "root_agent",
]
