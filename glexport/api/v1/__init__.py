"""Module containing Glexport API resources."""


from flask_restful import Api
from glexport.api.v1.shipments import Shipments


api = Api()


api.add_resource(Shipments, '/api/v1/shipments')
## add more API resources below
pass
