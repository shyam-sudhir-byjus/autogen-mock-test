from constants import *
from db_utils import *
from lp_constraints import pulp_solver
from bson import ObjectId
from google_locations_api import get_location_name

def questions_utils(input_data):
    chapters = input_data['chapter']
    grade = input_data['grade']
    subject = input_data['subject']
    curriculum = input_data['curriculum']
    user_difficulty = difficulty_mapper_dict[input_data['difficulty_level']]
    total_marks = input_data['total_marks']
    mapquest_res = get_location_name(input_data["city"])
    input_data["location"] = {"latitude": None, "longitude": None}
    input_data["location"]["latitude"], input_data["location"]["longitude"] = mapquest_res['lat'], mapquest_res['lng']

    questions_list = get_questions_list_from_db(grade, chapters, subject, curriculum)
    ids_for_dedup = [q['_id'] for q in questions_list]
    similar_questions_list = get_dedup_list(ids_for_dedup)
    most_frequent_questions = get_frequency_list(ids_for_dedup)
    messages, res = pulp_solver(questions_list, similar_questions_list, input_data, most_frequent_questions, user_difficulty, total_marks)
    return messages, res

if __name__ == "__main__":
    inputs = {
        "difficulty_level" : "medium",
        "total_marks" : 40,
        "chapter" : [
            "Cell Structure and Function",
            "Chemical Effects of Electric Current",
            "Coal and Petroleum",
            "Combustion and Flame",
        ],
        "grade" : "Standard VIII",
        "subject" : "Science",
        "curriculum" : "CBSE",
        "location": {
            "latitude": 12.96614, 
            "longitude": 77.58694
        }
    }
    print(questions_utils(inputs))


    

