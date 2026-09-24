"""
API package for researchloop-ai.
"""


def get_app():
    from backend.api.main import app
    return app


__all__ = ["get_app"]
