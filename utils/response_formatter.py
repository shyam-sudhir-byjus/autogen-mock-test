from flask import request
from get_parameters import SUBJECTIVE_GRADING_API, PINECONE_INDEXING_API
import requests
import json
from utils.db_utils import *
import time


def evaluating_student_at_runtime(exam_id, score):
    # get the exam Id
    # after every delay of 50 seconds call api and get the result
    # incase nothing is available then again wait for 50 seconds
    total_score = 0
    count = 0
    print('thread started')
    while  total_score<=score :
        user_marks = get_exam_progress_in_db(exam_id)
        if user_marks != []:
            for item in user_marks:
                get_question_marks(item)
                total_score += item["marks"]
                indx = start_question_answer_indexing(item["question_id"], item['exam_id'])
                if indx == -1:
                    print("Indexing Failed")
        time.sleep(60)
        count+=1
        if count ==30:
            break
    return


def are_all_questions_graded(exam_id, score):
        return get_exam_score_progress(exam_id, score)


def get_question_marks(user_marks):
    print(user_marks)
    msg, feedback = get_subjective_grade_from_autogen(user_marks["question_id"],user_marks['exam_id'])
    print(msg, feedback)
    autogen_feedback = {
        "user_marks": feedback["Marks"],
        "feedback_provided": "Explanation "+json.dumps(feedback["Marks Explanation"])+" \nSummary" +json.dumps(feedback["Summary"]),
    }
    save_feeback_msg_in_db(
        msg, autogen_feedback, user_marks["question_id"], user_marks["exam_id"]
    )
    return


def start_question_answer_indexing(que_id,exam_id):
    print('Entering the indexing function')
    que = get_question_from_exam(que_id,exam_id)
    url = PINECONE_INDEXING_API+"/save_que_marks_index/"
    headers = {
  'Content-Type': 'application/json'
        }
    que = json.dumps({"mock_response":que})
    resp = requests.post(url, headers= headers,data=que)
    if resp.status_code == 200:
        resp = resp.json()
        if resp['status']['isError']:
            print(resp['status'])
        return 1
    else:
        return -1


def get_subjective_grade_from_autogen(question_id,exam_id):
    que = get_question_by_id(question_id,exam_id)
    if que == {}:
        return {
            "response": {},
            "status": {"isError": True, "message": "Incorrect Question Id provided"},
        }
    if (
        "question" in que and 
       "marks" in que  and 
       "answer" in que and
       "user_solution" in que  
    ):
        url = f"{SUBJECTIVE_GRADING_API}/grade_answer/"
        payload = {
                "question_text": que["question"],
                "marks": que["marks"],
                "user_solution": que["user_solution"],
            }
        
        if que["answer"] != "":
            payload["baseline_solution"] = que["answer"]
        headers = {"Content-Type": "application/json"}
        payload = json.dumps(payload)
        response = requests.post(url, headers=headers, data=payload)
        print(f'this is response status {response.status_code}')
        if response.status_code == 200:
            msg = response.json()["response"]
            feedback_msg = msg.split('feedback (to chat_manager)')[-1]
            feedback_msg = feedback_msg.replace("\n","")
            feedback_msg = feedback_msg.split('--------------------------------------------------------------------------------')[0]
            start = feedback_msg.find('{')
            end = feedback_msg.rfind('}')

            if start != -1 and end != -1 and end > start:
                feedback=  feedback_msg[start:end+1]
            feedback = json.loads(feedback)
            return msg, feedback

        else:
            return {
                "response": {},
                "status": {
                    "isError": True,
                    "Message": f"Error in calling Subjective Grading. API returns :{response.status_code}",
                },
            }
    else:
        return {
            "response": {},
            "status": {
                "isError": True,
                "message": "Question info missing either question, marks  or baseline solution (answer)",
            },
        }


def save_exam_progress_response_fromatter(exam_id, que_id, user_answer):
    id = save_exam_progress_in_db(exam_id, que_id, user_answer)
    return id


def get_question_marks_response_formatter(exam_id):
    return get_user_marks_from_exam(exam_id)