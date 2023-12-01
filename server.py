from flask import Flask, request, jsonify
from flask_cors import CORS
from pulp_main import questions_utils, chapter_utils
from utils import response_formatter
from threading import Thread
from utils.db_utils import get_last_exam_id

app = Flask(__name__)
CORS(app)


@app.route("/start_grading_task/", methods=["POST"])
def get_student_grading_info():
    exam_id = get_last_exam_id()
    score = request.json.get('score',-1)
    thread = Thread(target=response_formatter.evaluating_student_at_runtime,args=(exam_id,score,))
    thread.start()
    return {
        "response": {"exam_id": exam_id},
        "status": {"isError": False, "message": "Api call successful"},
    }


@app.route("/health", methods=["GET"])
def get_check():
    return jsonify({"message": "Working!"})


@app.route("/get_chapters/", methods=["POST"])
def get_chapters():
    request_data = request.get_json()
    chapters = chapter_utils(request_data)
    return jsonify({"chapters": chapters})


@app.route("/get_questions/", methods=["POST"])
def get_questions():
    request_data = request.get_json()
    messages, res = questions_utils(request_data)
    for data in res:
        data["_id"] = str(data["_id"])
        data["marks"] = str(data["marks"])
    return jsonify({"questions": res, "properties": messages})


@app.route('/save_question_progress/', methods=['POST'])
def save_question_progress():
    request.exam_id = request.json.get('exam_id')
    request.question_id = request.json.get('question_id')
    request.user_answer = request.json.get('user_answer')
    response_formatter.save_exam_progress_response_fromatter()
    return {
        "response":"question_response_save_in_db",
        "status":{
            "isError": False, 
            "message":"API call sucessful"
        }
    }

# @app.after_request
# def logging_mock_test_exam()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=7002)
