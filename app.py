import ssl
import json
import urllib.request

from uuid import uuid4
from datetime import datetime

import flask
import isodate
import amadeus

import utils

FLIGHT_CHARTS = {}
AIRPORTS = {}

def ssl_disabled_urlopen(endpoint):
    context = ssl._create_unverified_context()
    return urllib.request.urlopen(endpoint, context=context)

app = flask.Flask(__name__)
app.secret_key = uuid4().bytes
client = amadeus.Client(http = ssl_disabled_urlopen)

@app.template_filter()
def parse_duration(deltastr):
    return isodate.parse_duration(deltastr)
@app.template_filter()
def parse_datetime(datetimestr):
    return isodate.parse_datetime(datetimestr)
@app.template_filter()
def format_duration(delta, fmtstr):
    return fmtstr.format(utils.Duration(int(delta.total_seconds())))
@app.template_filter()
def strftime(timestamp, formatstr):
    return timestamp.strftime(formatstr)

@app.route("/")
def index():
    return flask.render_template(
        "base.html.jinja",
        title = "Book Flights like never before",
        today = datetime.now().strftime("%Y-%m-%d")
    )

@app.route("/flights/")
@app.route("/flights/<sort_by>")
def flights(sort_by = "price-wise"):
    if "from" in flask.request.args:
        params = {
            "originLocationCode"     : flask.request.args["from"],
            "destinationLocationCode": flask.request.args["to"],
            "departureDate"          : flask.request.args["depart_on"],
            "adults"                 : flask.request.args.get("adults", 1),
            "children"               : flask.request.args.get("children", 0),
            "infants"                : flask.request.args.get("infants", 0),
            "travelClass"            : flask.request.args.get("class", "ECONOMY"),
            "currencyCode"           : "INR"
        }
        if "return_on" in flask.request.args:
            params |= { "returnDate": flask.request.args["return_on"] }
        flask.session["params"] = params | {
            "originLocation"     : flask.request.args["from_location"],
            "destinationLocation": flask.request.args["to_location"],
        }
        flask.session["flights"] = str(uuid4())
        FLIGHT_CHARTS[flask.session["flights"]] = client.shopping.flight_offers_search.get(**params).result
        return flask.redirect(flask.request.path)

    # params = {
    #     "originLocationCode"     : "DEL",
    #     "destinationLocationCode": "FRA",
    #     "departureDate"          : "2021-09-21",
    #     "returnDate"             : "2021-09-26",
    #     "adults"                 : 1,
    #     "children"               : 0,
    #     "infants"                : 0,
    #     "travelClass"            : "ECONOMY",
    #     "currencyCode"           : "INR",
    #     "max"                    : 20
    # }
    # flask.session["params"] = params | {
    #     "originLocation"     : "DEL, Indira Gandhi Intl Airport - Delhi",
    #     "destinationLocation": "FRA, Frankfurt Intl Airport - Frankfurt",
    # }
    # with open("static/assets/flight_offers_del_fra.json", "r+") as file:
    #     offers = json.load(file)
    #     offers["data"] = utils.unique_objects(offers["data"])
    #     flask.session["flights"] = offers

    origin      = flask.session['params']['originLocationCode']
    destination = flask.session['params']['destinationLocationCode']
    return flask.render_template(
        "flights.html.jinja",
        params = flask.session["params"],
        flights = FLIGHT_CHARTS[flask.session["flights"]],
        title = f"Cheapest flights from {origin} to {destination}",
        today = datetime.now().strftime("%Y-%m-%d")
    )

@app.route("/airlinecodes/")
def airlinecodes():
    data = client.reference_data.airlines.get(
        airlineCodes = ','.join(flask.request.args.getlist("airlines"))
    ).data
    for airline in data:
        airline["businessName"] = airline["businessName"].title()
        airline["commonName"  ] = airline["commonName"  ].title()
    return flask.jsonify(data)

@app.route("/iatacodes/")
def iatacodes():
    # return jsonify(utils.get_airport_codes(request.args["query"]))
    data = client.reference_data.locations.get(**{
        "keyword": flask.request.args["query"],
        "subType": amadeus.Location.AIRPORT,
        "view": "LIGHT", "page[limit]": 5
    }).data
    for location in data:
        location["name"] = location["name"].title()
        location["address"]["cityName"] = location["address"]["cityName"].title()
        location["address"]["countryName"] = location["address"]["countryName"].title()
        del location["self"]
    return flask.jsonify(data)