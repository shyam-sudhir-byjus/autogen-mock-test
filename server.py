from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from pulp_main import questions_utils, chapter_utils
from utils import response_formatter
from threading import Thread
from utils.db_utils import get_last_exam_id
import time

app = Flask(__name__)
CORS(app)


@app.route("/start_grading_task/", methods=["POST"])
def get_student_grading_info():
    exam_id = get_last_exam_id()
    score = request.json.get("score", -1)
    thread = Thread(
        target=response_formatter.evaluating_student_at_runtime,
        args=(
            exam_id,
            score,
        ),
    )
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
    '''
    Returns the list of chapters for given parameters
    
    Endpoint: 
        /get_chapter_list

    Method: 
        POST
    
    Request:
        {
            "subject": String,
            "grade": String,
            "curriculum": String
        }
    
    Response: 
        List of Chapter Names (String)
    '''
    request_data = request.get_json()
    chapters = chapter_utils(request_data)
    return jsonify({"chapters": chapters})


@app.route("/get_questions/", methods=["POST"])
def get_questions():
    """
    Returns dictionary of optimised questions, with their properties
    
    Endpoint: 
        /get_questions

    Method: 
        POST
    
    Request:
        {
            "city": String ,
            "curriculum": String,
            "chapter": List[String],
            "difficulty_level" : String,
            "subject": String,
            "grade": String,
            "total_marks": Float
        }
    
    Response: 
        Dict of Optimisd Questions with Properties [Dict]
    """
    request_data = request.get_json()
    messages, res = questions_utils(request_data)
    for data in res:
        data["_id"] = str(data["_id"])
        data["marks"] = str(data["marks"])
    return jsonify({"questions": res, "properties": messages})


@app.route("/save_question_progress/", methods=["POST"])
def save_question_progress():
    request.exam_id = request.json.get("exam_id")
    request.question_id = request.json.get("question_id")
    request.user_answer = request.json.get("user_answer")
    response_formatter.save_exam_progress_response_fromatter(request.exam_id ,request.question_id, request.user_answer )
    return {
        "response": "question_response_save_in_db",
        "status": {"isError": False, "message": "API call sucessful"},
    }


@app.route("/grading_status_stream/", methods=['GET'])
def grading_status_stream():
    print('entering')
    score = int(request.args.get("score"))
    exam_id = int(request.args.get("exam_id"))

    def generate(exam_id, score):
        while not response_formatter.are_all_questions_graded(
            exam_id, score
        ):
            yield "data: {}\n\n".format("waiting")
            time.sleep(50)  # Check every 5 seconds
        yield "data: {}\n\n".format("done")

    val  =Response(generate(exam_id, score), mimetype="text/event-stream")
    print(val)
    return val

@app.route("/show_user_marks/", methods=['GET'])
def show_user_marks():
    exam_id = int(request.args.get('exam_id'))
    val = response_formatter.get_question_marks_response_formatter(exam_id)
    return {
        "response": val ,
        "status":{
            "isError":False,
            "message":"Api call successfully"
        }
    }

@app.route('/get_my_image_solution/',methods=["POST"])
def get_my_image_solution():
    request.base64_image = request.json.get('base64_image')
    content = response_formatter.perform_ocr(request.base64_image)
    content_2 = response_formatter.getGoogleOCR(request.base64_image.split(',')[1])
    final_response = response_formatter.chat_gpt_decision(content, content_2)
    # final_response = final_response.replace('{','')
    # final_response = final_response.replace('}','')

    return {
        "response":{"mathpix":content,"google_vision":content_2,'openai_identified':final_response['Answer']},
        "status":{
            "isError": False,
            "message": "Api call successful"
        }
    }

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8509)