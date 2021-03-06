# Copyright 2016, 2017 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Promotion API controller

Paths:
------
GET /promotions - Returns a list all of the Promotions
GET /promotions/{promotion_id} - Returns the Promotion with a given promotion_id number
POST /promotions - creates a new Promotion record
PUT /promotions/{id} - updates a Promotion record
DELETE /promotions/{id} - deletes a Promotion record
POST /promotions/{id}/redeem - redeem a Promotion record
"""

import sys
import logging
from flask import Flask, jsonify, request, url_for, make_response, abort
from flask_api import status    # HTTP Status Codes
from werkzeug.exceptions import NotFound
from app.models import Promotion, DataValidationError
from app import app

######################################################################
# Error Handlers
######################################################################


@app.errorhandler(DataValidationError)
def request_validation_error(error):
    """ Handles Value Errors from bad data """
    return bad_request(error)


@app.errorhandler(400)
def bad_request(error):
    """ Handles bad reuests with 400_BAD_REQUEST """
    message = error.message or str(error)
    app.logger.info(message)
    return jsonify(status=400, error='Bad Request', message=message), 400


@app.errorhandler(404)
def not_found(error):
    """ Handles resources not found with 404_NOT_FOUND """
    message = error.message or str(error)
    app.logger.info(message)
    return jsonify(status=404, error='Not Found', message=message), 404


@app.errorhandler(405)
def method_not_supported(error):
    """ Handles unsuppoted HTTP methods with 405_METHOD_NOT_SUPPORTED """
    message = error.message or str(error)
    app.logger.info(message)
    return jsonify(status=405, error='Method not Allowed', message=message), 405


@app.errorhandler(415)
def mediatype_not_supported(error):
    """ Handles unsuppoted media requests with 415_UNSUPPORTED_MEDIA_TYPE """
    message = error.message or str(error)
    app.logger.info(message)
    return jsonify(status=415, error='Unsupported media type', message=message), 415


@app.errorhandler(500)
def internal_server_error(error):
    """ Handles unexpected server error with 500_SERVER_ERROR """
    message = error.message or str(error)
    app.logger.info(message)
    return jsonify(status=500, error='Internal Server Error', message=message), 500


######################################################################
# GET INDEX
######################################################################
@app.route('/')
def index():
    """ Root URL response """
    return app.send_static_file('index.html')

######################################################################
# LIST ALL PROMOTIONS
######################################################################


@app.route('/promotions', methods=['GET'])
def list_promotions():
    """ Returns all of the Promotions """
    promotions = []
    promotion_id = request.args.get('promotion_id')
    name = request.args.get('name')
    product_id = request.args.get('product_id')
    discount_ratio = request.args.get('discount_ratio')
    if name:
        promotions = Promotion.find_by_name(name)
    elif product_id:
        promotions = Promotion.find_by_product_id(product_id)
    elif discount_ratio:
        promotions = Promotion.find_by_discount_ratio(discount_ratio)
    else:
        promotions = Promotion.all()

    results = [promotion.serialize() for promotion in promotions]
    return make_response(jsonify(results), status.HTTP_200_OK)


######################################################################
# RETRIEVE A PROMOTION
######################################################################


@app.route('/promotions/<int:promotion_id>', methods=['GET'])
def get_promotions(promotion_id):
    """
    Retrieve a single Promotion

    This endpoint will return a Promotion based on it's id
    """
    promotion = Promotion.find(promotion_id)
    if not promotion:
        raise NotFound("Promotion with id '{}' was not found.".format(promotion_id))
    return make_response(jsonify(promotion.serialize()), status.HTTP_200_OK)


######################################################################
# ADD A NEW PROMOTION
######################################################################


@app.route('/promotions', methods=['POST'])
def create_promotions():
    """
    Creates a Promotion
    This endpoint will create a Promotion based the data in the body that is posted
    """
    check_content_type('application/json')
    promotion = Promotion()
    promotion.deserialize(request.get_json())
    promotion.save()
    message = promotion.serialize()
    location_url = url_for('get_promotions', promotion_id=promotion.promotion_id, _external=True)
    return make_response(jsonify(message), status.HTTP_201_CREATED,
                         {
                             'Location': location_url
                         })


######################################################################
# UPDATE AN EXISTING PROMOTION
######################################################################
@app.route('/promotions/<int:promotion_id>', methods=['PUT'])
def update_promotions(promotion_id):
    """
    Update a Promotion

    This endpoint will update a Promotion based the body that is posted
    """
    check_content_type('application/json')
    promotion = Promotion.find(promotion_id)
    if not promotion:
        raise NotFound("Promotion with id '{}' was not found.".format(promotion_id))
    promotion.deserialize_partial(request.get_json())
    promotion.id = promotion_id
    promotion.save()
    return make_response(jsonify(promotion.serialize()), status.HTTP_200_OK)


######################################################################
# DELETE A PROMOTION
######################################################################
@app.route('/promotions/<int:promotion_id>', methods=['DELETE'])
def delete_promotions(promotion_id):
    """
    Delete a Promotion

    This endpoint will delete a Promotion based the id specified in the path
    """
    promotion = Promotion.find(promotion_id)
    if promotion:
        promotion.delete()
    return make_response('', status.HTTP_204_NO_CONTENT)

######################################################################
# REDEEM A PROMOTION
######################################################################
@app.route('/promotions/<int:promotion_id>/redeem', methods=['POST'])
def redeem_promotions(promotion_id):
    """
    Redeem a Promotion

    This endpoint will increment the counter of a Promotion by 1.
    """
    promotion = Promotion.redeem_promotion(promotion_id)
    return make_response(
        jsonify(promotion.serialize()),
        status.HTTP_200_OK)

######################################################################
# Reset the Database
######################################################################
@app.route('/promotions/reset', methods=['DELETE'])
def reset():
    """
    Reset the Database for test purposes
    """
    Promotion.remove_all()
    return make_response('', status.HTTP_204_NO_CONTENT)

######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def init_db():
    """ Initialies the SQLAlchemy app """
    Promotion.init_db()


def check_content_type(content_type):
    """ Checks that the media type is correct """
    if request.headers['Content-Type'] == content_type:
        return
    app.logger.error('Invalid Content-Type: %s', request.headers['Content-Type'])
    abort(415, 'Content-Type must be {}'.format(content_type))


def initialize_logging(log_level=logging.INFO):
    """ Initialized the default logging to STDOUT """
    if not app.debug:
        print 'Setting up logging...'
        # Set up default logging for submodules to use STDOUT
        # datefmt='%m/%d/%Y %I:%M:%S %p'
        fmt = '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        logging.basicConfig(stream=sys.stdout, level=log_level, format=fmt)
        # Make a new log handler that uses STDOUT
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(fmt))
        handler.setLevel(log_level)
        # Remove the Flask default handlers and use our own
        handler_list = list(app.logger.handlers)
        for log_handler in handler_list:
            app.logger.removeHandler(log_handler)
        app.logger.addHandler(handler)
        app.logger.setLevel(log_level)
        app.logger.info('Logging handler established')
