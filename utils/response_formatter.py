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
    while score < total_score:
        user_marks = get_exam_progress_in_db(exam_id)
        if user_marks != []:
            for item in user_marks:
                get_question_marks(user_marks)
                total_score += item["marks"]
                indx = start_question_answer_indexing(user_marks["question_id"])
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
    msg, feedback = get_subjective_grade_from_autogen(user_marks["question_id"])
    autogen_feedback = {
        "user_marks": feedback["Marks"],
        "feedback_provided": feedback["Summary"],
    }
    save_feeback_msg_in_db(
        msg, autogen_feedback, user_marks["question_id"], user_marks["exam_id"]
    )
    return


def start_question_answer_indexing(que_id):
    que = get_question_from_exam(que_id)
    resp = request.post(PINECONE_INDEXING_API, json=que)
    if resp.status_code == 200:
        return 1
    else:
        return -1


def get_subjective_grade_from_autogen(question_id):
    que = get_question_by_id(question_id)
    if que == {}:
        return {
            "response": {},
            "status": {"isError": True, "message": "Incorrect Question Id provided"},
        }
    if (
        hasattr(que, "question")
        and hasattr(que, "marks")
        and hasattr(que, "answer")
        and hasattr(que, "user_solution")
    ):
        url = f"{SUBJECTIVE_GRADING_API}/grade_answer/"
        payload = json.dumps(
            {
                "question_text": que["question"],
                "marks": que["marks"],
                "user_solution": que["user_solution"],
            }
        )
        if que["answer"] != "":
            payload["baseline_solution"] = que["answer"]
        headers = {"Content-Type": "application/json"}

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            msg = response.json()["response"]
            sub1 = "Here is the final feedback for the student"
            idx1 = msg.index(sub1)
            idx2 = msg.index(
                "I hope this feedback helps you to improve your performance in future assessments."
            )
            feedback = msg[idx1 + len(sub1) + 1 : idx2]
            feedback = json.loads(feedback[0])
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
