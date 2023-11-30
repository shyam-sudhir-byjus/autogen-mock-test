from pymongo import MongoClient
from get_parameters import (
    CONN_URI_SLP, DB_NAME_SLP
)

client = MongoClient(CONN_URI_SLP)

db = client[DB_NAME_SLP]

def get_questions_list_from_db(grade, chapters, subject, curriculum):
    query = {
            "chapter": {"$in": chapters},
            "grade": grade,
            "subject": subject,
            "curriculum": curriculum,
            "filter_flag_use": 1,
            "topic": {"$ne": ""}
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
    return list(dedup_collection.find({"ID1": {"$in": ids_for_dedup}},{"_id":0,"ID1":1,"ID2":1}))

def get_frequency_list(ids_for_dedup):
    frequency_collection = db['frequency_question_collection_v2']
    most_frequent_questions = list(frequency_collection.find({"question_id": {"$in": [str(i) for i in ids_for_dedup]}},{"_id":0,"question_id":1,"frequency":1}))
    most_frequent_questions.sort(key=lambda x: x['frequency'], reverse=True)
    return most_frequent_questions


def get_subject_details(subject):
    maths_list = ['Maths', 'MATHS', 'MATHEMATICS', 'Math', 'math', 'maths', 'Mathematics']
    science_list = ['SCIENCE', 'PHYSICS', 'BIOLOGY', 'CHEMISTRY', "Physics", "Biology", "Science", "Chemistry"]

    if subject in maths_list:
        return maths_list
    else :
        return science_list
    

def get_chapter_list(grade, subject, curriculum):
    subject_list = get_subject_details(subject)
    condition_for_distinct = {
        "grade":grade,
        "curriculum":curriculum,
        "subject":{"$in":subject_list},
        "filter_flag_use": 1
    }
    questions_collection = db["question_school_papers_v2"]
    chapter_list = questions_collection.distinct('chapter',condition_for_distinct)
    return chapter_list 
