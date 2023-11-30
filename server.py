from flask import Flask, request, jsonify
from flask_cors import CORS
from pulp_main import questions_utils, chapter_utils

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def get_check():
    return jsonify({"message": "Working!"})


@app.route('/get_chapters/', methods=['POST'])
def get_chapters():
    request_data = request.get_json()
    chapters = chapter_utils(request_data)
    return jsonify({"chapters": chapters})   


@app.route('/get_questions/', methods=['POST'])
def get_questions():
    request_data = request.get_json()
    messages, res = questions_utils(request_data)
    for data in res:
        data['_id'] = str(data['_id'])
        data['marks'] = str(data['marks'])
    return jsonify({"questions":res,"properties": messages})

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=7002)
