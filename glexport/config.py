"""Configuration module for glexport-flask."""


class Config(object):
  """Flask configuration class."""

  SITE_NAME = 'Glexport Flask'

  SERVER_NAME = 'localhost:3000'

  POSTGRES_USER     = 'jason'
  POSTGRES_PASSWORD = ''
  POSTGRES_HOST     = 'localhost'
  POSTGRES_PORT     = '5432'
  POSTGRES_DB       = 'glexport_development'
  POSTGRES_URI_TEMPLATE = 'postgresql:///{dbname}'

  SQLALCHEMY_DATABASE_URI = POSTGRES_URI_TEMPLATE.format(
    user     = POSTGRES_USER,
    password = POSTGRES_PASSWORD,
    host     = POSTGRES_HOST,
    port     = POSTGRES_PORT,
    dbname   = POSTGRES_DB
  )
  SQLALCHEMY_TRACK_MODIFICATIONS = False
