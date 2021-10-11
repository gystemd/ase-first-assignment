from flakon import JsonBlueprint
from flask import abort, jsonify, request

from bedrock_a_party.classes.party import CannotPartyAloneError, \
    ItemAlreadyInsertedByUser, NotExistingFoodError, \
    NotInvitedGuestError, Party

parties = JsonBlueprint('parties', __name__)

_LOADED_PARTIES = {}  # dict of available parties
_PARTY_NUMBER = 0  # index of the last created party


@parties.route("/parties", methods=['GET', 'POST'])
def all_parties():
    """
        method = POST: Creates a new party and gets the party identifier back.
        method = GET: Retrieves all scheduled parties.
    """
    result = None

    if request.method == 'POST':
        try:
            result = create_party(request)
        except CannotPartyAloneError:
            abort(400)

    elif request.method == 'GET':
        result = get_all_parties()

    return result


@parties.route("/parties/loaded", methods=['GET'])
def loaded_parties():
    """ Returns the number of parties currently loaded in the system """

    return {'loaded_parties': len(_LOADED_PARTIES)}


@parties.route("/party/<id>", methods=['GET', 'DELETE'])
def single_party(id):
    """
        method = GET: Retrieves the party identified by <id>.
        method = DELETE: Deletes the party identified by <id> from the system
    """

    global _LOADED_PARTIES
    result = ""

    exists_party(id)

    if request.method == 'GET':
        result = _LOADED_PARTIES.get(id).serialize()

    elif request.method == 'DELETE':
        _LOADED_PARTIES.pop(id)
        result = ('', 200)

    return result


@parties.route("/party/<id>/foodlist", methods=['GET'])
def get_foodlist(id):
    """Retrieves the current foodlist of the party identified by <id>."""

    global _LOADED_PARTIES
    result = ""

    exists_party(id)

    result = jsonify({
        "foodlist": _LOADED_PARTIES.get(id).food_list.serialize()
    })

    return result


@parties.route("/party/<id>/foodlist/<user>/<item>",
               methods=['POST', 'DELETE'])
def edit_foodlist(id, user, item):
    """
        method = POST: Adds the <item> brought by <user> to the food-list of
        the party <id>.
        method = DELETE: Removes the given <item> brought by <user> from the
        food-list of the party <id>.
        Only people invited to the party can add and remove food items from
        the party list.
    """

    global _LOADED_PARTIES

    exists_party(id)
    party = _LOADED_PARTIES.get(id)
    result = ""

    if request.method == 'POST':
        try:
            result = jsonify(party.add_to_food_list(item, user).serialize())
        except NotInvitedGuestError:
            abort(401)
        except ItemAlreadyInsertedByUser:
            abort(400)

    if request.method == 'DELETE':
        try:
            party.remove_from_food_list(item, user)
            result = jsonify({"msg": "Food deleted!"})
        except NotExistingFoodError:
            abort(400)

    return result

#
# These are utility functions. Use them, DON'T CHANGE THEM!!
#


def create_party(req):
    global _LOADED_PARTIES, _PARTY_NUMBER

    # get data from request
    json_data = req.get_json()

    # list of guests
    try:
        guests = json_data['guests']
    except:
        raise CannotPartyAloneError("you cannot party alone!")

    # add party to the loaded parties lists
    _LOADED_PARTIES[str(_PARTY_NUMBER)] = Party(_PARTY_NUMBER, guests)
    _PARTY_NUMBER += 1

    return jsonify({'party_number': _PARTY_NUMBER - 1})


def get_all_parties():
    global _LOADED_PARTIES

    return jsonify(loaded_parties=[party.serialize()
                                   for party in _LOADED_PARTIES.values()])


def exists_party(_id):
    global _PARTY_NUMBER
    global _LOADED_PARTIES

    if int(_id) > _PARTY_NUMBER:
        # error 404: Not Found, i.e. wrong URL, resource does not exist
        abort(404)
    elif not(_id in _LOADED_PARTIES):
        # error 410: Gone, i.e. it existed but it's not there anymore
        abort(410)