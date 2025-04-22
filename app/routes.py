from flask import Blueprint, jsonify

bp = Blueprint('api', __name__, url_prefix='/api/v1')

@bp.route('/test', methods=['GET'])
def test():
    return jsonify({'message': 'HELLO'})