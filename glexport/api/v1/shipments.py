"""Shipments API."""


from flask import abort, make_response, jsonify, Response
from flask_restful import fields, marshal_with, reqparse, Resource
from glexport.database import get_db


PRODUCT_FIELDS = {
  'id': fields.Integer,
  'quantity': fields.Integer,
  'sku': fields.String,
  'description': fields.String,
  'active_shipment_count': fields. Integer
}

SHIPMENT_FIELDS = {
  'id': fields.Integer,
  'name': fields.String,
  'products': fields.List(fields.Nested(PRODUCT_FIELDS))
}

RESPONSE_FIELDS = {
  'records': fields.List(fields.Nested(SHIPMENT_FIELDS))
}


class Shipments(Resource):
  """Flask-RESTful resource for shipments API."""

  VALID_GET_REQUEST_ARGS = [
    ('company_id', int),
    ('international_transportation_mode', str),
    ('sort', str),
    ('direction', str),
    ('page', int),
    ('per', int)
  ]
  VALID_SORTS = {
    'id',
    'international_departure_date'
  }
  VALID_DIRECTIONS = {
    'asc',
    'desc'
  }

  SHIPMENT_QUERY_TEMPLATE = """
    SELECT id, name
    FROM shipments
    WHERE company_id={company_id}
    {filter_by}
    {order_by}
    {paginate};
  """
  ACTIVE_SHIPMENT_QUERY = """
    SELECT product_id, COUNT(shipment_id) AS active_shipment_count
    FROM shipment_products
    GROUP BY product_id
  """
  PRODUCT_QUERY_TEMPLATE = """
    SELECT products.id, sku, description, quantity, active_shipment_count
    FROM products, shipment_products, ({active_shipment_query}) AS active_shipments
    WHERE products.id=shipment_products.product_id AND
      active_shipments.product_id=shipment_products.product_id AND
      shipment_id={shipment_id}
  """

  def __init__(self):
    """Constructor for shipments API."""
    self._get_parser = reqparse.RequestParser()
    for arg_name, arg_type in self.VALID_GET_REQUEST_ARGS:
      self._get_parser.add_argument(arg_name, type=arg_type, location='values')

    ## create parsers for other request methods below
    pass

  def _validate_get_request(self):
    """Ensures a HTTP GET request is valid

    Raises:
      HTTPException: aborts with status code 422 if company_id is not given.
    """
    error_list = []

    ## validate company_id
    company_id = self._args.get('company_id')
    if not company_id:
      error_list.append('company_id is required')

    ## validate other args below
    pass

    if len(error_list) > 0:
      abort(make_response(jsonify(
        errors=error_list
      ), 422))

  def _set_get_defaults(self):
    """Sets default arguments if they are not given."""
    sort_column = self._args.get('sort')
    if not sort_column or sort_column not in self.VALID_SORTS:
      sort_column = 'id'
    self._args['sort'] = sort_column

    direction = self._args.get('direction')
    if not direction or direction not in self.VALID_DIRECTIONS:
      direction = 'asc'
    self._args['direction'] = direction

    page = self._args.get('page')
    if not page or page < 1:
      page = 1
    self._args['page'] = page

    per = self._args.get('per')
    if not per or per < 1:
      per = 4
    self._args['per'] = per

  def _get_shipment_query(self):
    """Constructs a query to the shipments table.

    Returns:
      A string containing the shipments query.
    """
    ## Filter by company id
    company_id = self._args.get('company_id')

    ## Filter by international transportation mode
    intl_transp_mode = self._args.get('international_transportation_mode')
    filter_by = ''
    if intl_transp_mode:
       filter_by = 'AND international_transportation_mode=\'{}\''.format(
        intl_transp_mode)

    ## Sort
    sort_column = self._args.get('sort')
    direction = self._args.get('direction')
    order_by = 'ORDER BY {} {}'.format(
      sort_column,
      direction
    )

    ## Paginate
    page = self._args.get('page')
    per = self._args.get('per')
    paginate = 'LIMIT {limit} OFFSET {offset}'.format(
      limit=per,
      offset=(page-1)*per
    )

    shipment_query = self.SHIPMENT_QUERY_TEMPLATE.format(
      company_id=company_id,
      filter_by=filter_by,
      order_by=order_by,
      paginate=paginate
    )

    return shipment_query

  def _get_product_queries(self, shipments):
    """Constructs product queries for each shipment.

    Args:
      shipments: A list of shipment data.

    Returns:
      A list of product queries for each shipment as strings.
    """
    product_queries = []

    for shipment in shipments:
      shipment_id = shipment[0]
      product_query = self.PRODUCT_QUERY_TEMPLATE.format(
        active_shipment_query=self.ACTIVE_SHIPMENT_QUERY,
        shipment_id=shipment_id
      )
      product_queries.append(product_query)

    return product_queries

  def _query_shipments(self, shipment_query):
    """Fetches shipment data from the glexport_development database.

    Args:
      shipment_query: A string to be executed as a Postgres query.

    Returns:
      A list of shipment data in the form of tuples: (id, name)
    """
    db = get_db()
    db.execute(shipment_query)
    shipments = db.fetchall()

    return shipments

  def _query_products(self, product_queries):
    """Fetches product data from the glexport_development database.

    Args:
      product_queries: A list of strings to be executed as Postgres queries.

    Returns:
      A list of product data in the form of tuples:
        (id, sku, description, quantity, active_shipment_count)
    """
    products = []
    db = get_db()

    for product_query in product_queries:
      db.execute(product_query)
      products.append(db.fetchall())

    return products

  @marshal_with(RESPONSE_FIELDS)
  def _marshal_shipments(self, shipments, products):
    """Marshals the GET response for Shipments API.

    Args:
      shipments: A list of shipment data.
      products: A list of product data.

    Returns:
      JSON response data containing shipment records.
    """
    shipment_records = []
    for shipment, product_list in zip(shipments, products):
      record = {
        'id': shipment[0],
        'name': shipment[1],
        'products': []
      }
      for product in product_list:
        record['products'].append({
          'id': product[0],
          'sku': product[1],
          'description': product[2],
          'quantity': product[3],
          'active_shipment_count': product[4]
        })
      shipment_records.append(record)

    return {'records': shipment_records}

  def get(self):
    """Handler for HTTP GET requests for the shipments API.

    Returns:
      A list of shipment records.
    """
    self._args = self._get_parser.parse_args()
    self._validate_get_request()
    self._set_get_defaults()

    shipment_query = self._get_shipment_query()
    shipments = self._query_shipments(shipment_query)
    product_queries = self._get_product_queries(shipments)
    products = self._query_products(product_queries)

    return self._marshal_shipments(shipments, products)
