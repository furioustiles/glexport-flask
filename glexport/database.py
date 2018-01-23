"""Psycopg2 database."""


from flask import g
import psycopg2 as psql


POSTGRES_DB = 'glexport_development'


def get_db():
  """Returns a cursor from the psycop2 client."""
  if not hasattr(g, 'pg_cur'):
    g.pg_conn = psql.connect("dbname='{dbname}'".format(
      dbname=POSTGRES_DB
    ))
    g.pg_cur = g.pg_conn.cursor()
  return g.pg_cur
