from pymongo import MongoClient
from get_parameters import CONN_URI_SLP, DB_NAME_SLP

client = MongoClient(CONN_URI_SLP)

db = client[DB_NAME_SLP]


def get_questions_list_from_db(grade, chapters, subject, curriculum):
    query = {
        "chapter": {"$in": chapters},
        "grade": grade,
        "subject": subject,
        "curriculum": curriculum,
        "filter_flag_use": 1,
        "topic": {"$ne": ""},
    }

    projection = {
        "ID": 1,
        "question": 1,
        "chapter": 1,
        "topic": 1,
        "bloom": 1,
        "difficulty": 1,
        "type": 1,
        "options": 1,
        "marks": 1,
    }

    questions_collection = db["question_school_papers_v2"]
    questions_list = list(questions_collection.find(query, projection))
    return questions_list


def get_dedup_list(ids_for_dedup):
    dedup_collection = db["question_dedup"]
    return list(
        dedup_collection.find(
            {"ID1": {"$in": ids_for_dedup}}, {"_id": 0, "ID1": 1, "ID2": 1}
        )
    )


def get_frequency_list(ids_for_dedup):
    frequency_collection = db["frequency_question_collection_v2"]
    most_frequent_questions = list(
        frequency_collection.find(
            {"question_id": {"$in": [str(i) for i in ids_for_dedup]}},
            {"_id": 0, "question_id": 1, "frequency": 1},
        )
    )
    most_frequent_questions.sort(key=lambda x: x["frequency"], reverse=True)
    return most_frequent_questions


def get_subject_details(subject):
    maths_list = [
        "Maths",
        "MATHS",
        "MATHEMATICS",
        "Math",
        "math",
        "maths",
        "Mathematics",
    ]
    science_list = [
        "SCIENCE",
        "PHYSICS",
        "BIOLOGY",
        "CHEMISTRY",
        "Physics",
        "Biology",
        "Science",
        "Chemistry",
    ]

    if subject in maths_list:
        return maths_list
    else:
        return science_list


def get_chapter_list(grade, subject, curriculum):
    subject_list = get_subject_details(subject)
    condition_for_distinct = {
        "grade": grade,
        "curriculum": curriculum,
        "subject": {"$in": subject_list},
        "filter_flag_use": 1,
    }
    questions_collection = db["question_school_papers_v2"]
    chapter_list = questions_collection.distinct("chapter", condition_for_distinct)
    return chapter_list


def get_question_by_id(id):
    que = db.question_school_papers_v2.find_one(
        {"ID": id}, {"_id": 0, "question": 1, "answer": 1, "marks": 1}
    )
    return que


def get_last_exam_id():
    que = list(db.student_exam_questions.find({}).sort("_id", -1).limit(1))
    if que == []:
        return 1
    return que["exam_id"] + 1


def get_available_student_id():
    student = list(
        db.mock_exam_available_students.find({"isActive": 0}).sort("_id", -1).limit(1)
    )
    if student == []:
        return -1
    return student[0]["exam_id"]


def save_exam_progress_in_db( exam_id, que_id, user_answer):
    que = db.question_school_papers_v2.find_one(
        {"ID": que_id},
        {
            "_id": 0,
            "marks": 1,
            "baseline_solution": "$answer",
            "concept": 1,
            "subject": 1,
            "grade": 1,
            "chapter": 1,
            "subtopic": "$topic",
        },
    )
    doc = {
        "question_id": que_id,
        "exam_id": exam_id,
        "user_solution": user_answer,
        "is_pinecone_indexed": 0,
        "solution_generated": 0**que,
    }
    inserted_id = db.student_exam_questions.insert_one(doc)
    return inserted_id


def get_exam_progress_in_db(exam_id):
    exam_response = list(
        db.student_exam_questions.find(
            {"exam_id": exam_id, "solution_generated": 0}
        ).sort({"_id": 1})
    )
    return exam_response


def save_feeback_msg_in_db(msg, feedback, question_id, exam_id):
    exam_response_id = db.student_exam_questions.update_one(
        {"exam_id": exam_id, "question_id": question_id},
        {"$set": {"chat_msg": msg, **feedback}},
    )
    return exam_response_id


def get_question_from_exam(question_id, exam_id):
    # ['exam_id','question','question_id','marks','user_solution','baseline_solution','marks_given',
    #              'feedback_provided','subject','subtopic','grade','chapter_name']
    exam_que = db.student_exam_question.find_one(
        {"exam_id": exam_id, "question_id": question_id},
        {
            "question": 1,
            "question_id": 1,
            "marks": 1,
            "user_solution": 1,
            "baseline_solution": 1,
            "user_marks": 1,
            "feedback_provided": 1,
            "subject": 1,
            "subtopic": 1,
            "grade": 1,
            "chapter_name": 1,
        },
    )
    return exam_que


def get_exam_score_progress(exam_id,score):
    exams = list(db.student_exam_question.find({"exam_id":exam_id}))
    if exams ==[]:
        return False 
    score_cal = 0
    for item in exams : 
        score_cal+= item['marks']
    if score==score_cal:
        return True 
    return False
