from typing import Any

from flask import render_template as flask_render_template

from frontstage.common.session import Session


def render_template(template: str, session: Session = None, **kwargs: Any) -> str:
    session_expires_at = session.get_formatted_expires_in() if session else None
    return flask_render_template(template, session_expires_at=session_expires_at, **kwargs)
