from flask import render_template as flask_render_template


def render_template(template: str, session=None, **kwargs) -> str:
    session_expires_at = session.get_formatted_expires_in() if session else None
    return flask_render_template(template, session_expires_at=session_expires_at, **kwargs)
