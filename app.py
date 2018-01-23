#!/usr/bin/env python3
"""Binary file that runs the glexport-flask server."""


from flask import Flask, g
from glexport.api.v1 import api
from glexport.config import Config


def create_app(config):
  """Flask application factory.

  Args:
    config: Configuration object to be applied to Flask application.

  Returns:
    Flask application object for Glexport with all applied extensions.
  """
  app = Flask(__name__)

  app.config.from_object(config)
  api.init_app(app)

  @app.teardown_appcontext
  def close_db(error):
    """Closes database connection after request."""
    if hasattr(g, 'pg_cur'):
      g.pg_cur.close()
      g.pg_conn.close()

  return app


if __name__ == '__main__':
  glexport_app = create_app(Config)
  glexport_app.run()
