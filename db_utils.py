from pymongo import MongoClient

client = MongoClient(
    "mongodb://questiondb:d5a8c07f243ec9e54c18729a3bf91029d9250f1k@3.110.82.242:27017/questiondb"
)

db = client["questiondb"]
questions_collection = db["question_school_papers_v2"]
dedup_collection = db["question_dedup"]
frequency_collection = db['frequency_question_collection_v2']
city_school_question_tags_collection = db['city_school_question_tags_v2']
city_school_location = db['city_school_location_v2']

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

    questions_list = list(questions_collection.find(query, projection))
    return questions_list

def get_dedup_list(ids_for_dedup):
    return list(dedup_collection.find({"ID1": {"$in": ids_for_dedup}},{"_id":0,"ID1":1,"ID2":1}))

def get_frequency_list(ids_for_dedup):
    most_frequent_questions = list(frequency_collection.find({"question_id": {"$in": [str(i) for i in ids_for_dedup]}},{"_id":0,"question_id":1,"frequency":1}))
    most_frequent_questions.sort(key=lambda x: x['frequency'], reverse=True)
    return most_frequent_questions
