from flask import request
from get_parameters import (
    SUBJECTIVE_GRADING_API,
    PINECONE_INDEXING_API,
    OPENAI_KEY,
    MATHPIX_APP_KEY,
    MATHPIX_APP_ID,
    GOOGLE_API_KEY,
    CHAT_COMPLETION_MODEL,
    OPENAI_API_KEY,
    OPENAI_API_TYPE,
    OPENAI_BASE_KEY,
    OPENAI_API_VERSION
)
import requests
import json
from utils.db_utils import *
import time
import base64
from google.cloud import vision
import openai


SYS_PROMPTS = '''
 You are an intelligent student for grade VI to grade XII . You have been topper in all subjects and have scored extraordinarily well. 
 You will be given two version of the answer for a question.You will are given two versions of OCR. So pick out the best version of answer which makes sense and is coherent in read. 
 If it is a math question. Please take a extra care of equations and symbols while deciding best answer version.
 Your output should have  best version identified should come as json doc with key as answer: 
 Sample Output :
    "{Answer: best version answer}"

'''



def evaluating_student_at_runtime(exam_id, score):
    # get the exam Id
    # after every delay of 50 seconds call api and get the result
    # incase nothing is available then again wait for 50 seconds
    total_score = 0
    count = 0
    print("thread started")
    while total_score <= score:
        user_marks = get_exam_progress_in_db(exam_id)
        if user_marks != []:
            for item in user_marks:
                get_question_marks(item)
                total_score += item["marks"]
                indx = start_question_answer_indexing(
                    item["question_id"], item["exam_id"]
                )
                if indx == -1:
                    print("Indexing Failed")
        time.sleep(30)
        count += 1
        if count == 60:
            break
    return


def are_all_questions_graded(exam_id, score):
    return get_exam_score_progress(exam_id, score)


def get_question_marks(user_marks):
    print(user_marks)
    msg, feedback = get_subjective_grade_from_autogen(
        user_marks["question_id"], user_marks["exam_id"]
    )
    print(msg, feedback)
    autogen_feedback = {
        "user_marks": feedback["Marks"],
        "feedback_provided": "Explanation "
        + json.dumps(feedback["Marks Explanation"])
        + " \nSummary"
        + json.dumps(feedback["Summary"]),
    }
    save_feeback_msg_in_db(
        msg, autogen_feedback, user_marks["question_id"], user_marks["exam_id"]
    )
    return


def start_question_answer_indexing(que_id, exam_id):
    print("Entering the indexing function")
    que = get_question_from_exam(que_id, exam_id)
    url = PINECONE_INDEXING_API + "/save_que_marks_index/"
    headers = {"Content-Type": "application/json"}
    que = json.dumps({"mock_response": que})
    resp = requests.post(url, headers=headers, data=que)
    if resp.status_code == 200:
        resp = resp.json()
        if resp["status"]["isError"]:
            print(resp["status"])
        return 1
    else:
        return -1


def get_subjective_grade_from_autogen(question_id, exam_id):
    que = get_question_by_id(question_id, exam_id)
    if que == {}:
        return {
            "response": {},
            "status": {"isError": True, "message": "Incorrect Question Id provided"},
        }
    if (
        "question" in que
        and "marks" in que
        and "answer" in que
        and "user_solution" in que
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
        print(f"this is response status {response.status_code}")
        if response.status_code == 200:
            response = response.json()
            return response["response"]["msg"], response["response"]["feedback"]

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


def perform_ocr(base64_encoded_image):
    response = requests.post(
        "https://api.mathpix.com/v3/text",
        json={
            "src": base64_encoded_image,
            "rm_fonts": True,
            "math_display_delimiters": ["\\(", "\\)"],
            "formats": ["text", "data", "latex_simplified"],
            "data_options": {"include_asciimath": True},
        },
        headers={
            "app_id": MATHPIX_APP_ID,
            "app_key": MATHPIX_APP_KEY,
            "Content-type": "application/json",
        },
        timeout=5,
    )

    mathpix_response = response.json()
    print(mathpix_response)
    return {"text": mathpix_response["text"], "isError": False}


def getGoogleOCR(image_base64):
    url = "https://vision.googleapis.com/v1/images:annotate?key={}".format(GOOGLE_API_KEY)
    headers = {"Content-Type": "application/json"}
    payload = {
        "requests": [
            {
                "image": {"content": image_base64},
                "features": [{"type": "TEXT_DETECTION"}],
            }
        ]
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    print(response)
    if response.status_code == 200:
        result = response.json()
        if "textAnnotations" in result["responses"][0]:
            detected_text = result["responses"][0]["textAnnotations"][0]["description"]
            #  return detected_text
            return {"text": detected_text, "isError": False}
        return None
    else:
        return None


def detect_text(base64_image):
    client = vision.ImageAnnotatorClient()

    image_bytes = base64.b64decode(base64_image)
    image = vision.Image(content=image_bytes)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    for text in texts:
        print('\n"{}"'.format(text.description))

        vertices = [
            "({},{})".format(vertex.x, vertex.y)
            for vertex in text.bounding_poly.vertices
        ]

        text += "bounds:", ",".join(vertices)

    if response.error.message:
        raise Exception(
            "{}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
        )

    return {"text": text, "isError": False}

def chat_gpt_decision(mathpix_answer, google_ocr_version):
    prompts = f'Answer Version 1 {google_ocr_version}. Answer Version 2 {mathpix_answer}'
    messages = [
        {"role": "system", "content": SYS_PROMPTS},
        {"role": "user", "content": prompts},
    ]
    gpt_response = openai.ChatCompletion.create(
        api_type=OPENAI_API_TYPE,
        api_version=OPENAI_API_VERSION,
        api_base=OPENAI_BASE_KEY,
        api_key=OPENAI_API_KEY,
        engine=CHAT_COMPLETION_MODEL,
        messages=messages,
        max_tokens=4000,
        temperature=0,
    )

    gpt_response = gpt_response["choices"][0]["message"]["content"]
    #print(completion)
    return json.loads(gpt_response)


## Uncommet below for  GPT4 Vision Preview  .
# headers = {
#     "Content-Type": "application/json",
#     "Authorization": f"Bearer {OPENAI_KEY}",
# }

# payload = {
#     "model": "gpt-4-vision-preview",
#     "messages": [
#         {
#             "role": "user",
#             "content": [
#                 {
#                     "type": "text",
#                     "text": "Step 1: Conduct OCR of provided image. Ensure that you do not miss any line, word, letter \
#                 even if you've low confidence. \
#                 Step 2: Provide the OCR output based on step 1. Strictly ensure no other text is there in output \
#                 than the required OCR output in text format.",
#                 },
#                 {
#                     "type": "image_url",
#                     "image_url": {"url": f"data:image/jpeg;base64,{base64_encoded_image}"},
#                 },
#             ],
#         }
#     ],
#     "max_tokens": 300,
# }

# response = requests.post(
#     "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
# )
# data = response.json()
# content = data["choices"][0]["message"]["content"]

# return content
