from constants import *
from utils.db_utils import *
from lp_constraints import pulp_solver
from google_locations_api import get_location_name
from common import total_marks_helper


def chapter_utils(input_data):
    grade, subject, curriculum = input_data['grade'], input_data['subject'], input_data['curriculum']
    return get_chapter_list(grade, subject, curriculum)


def questions_utils(input_data):
    chapters = input_data['chapter']
    seen = set()
    chapters = [item for item in chapters if item.lower() not in seen and not seen.add(item.lower())]

    '''
      Get input parameters to pass onto the PULP Optimisation Solver
    '''

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
    messages, res, rerun = pulp_solver(questions_list, similar_questions_list, input_data, most_frequent_questions, user_difficulty, total_marks)
    # if rerun:
    #     total_marks = total_marks_helper(total_marks)
    #     messages, res, rerun = pulp_solver(questions_list, similar_questions_list, input_data, most_frequent_questions, user_difficulty, total_marks)
    
    return messages, res

if __name__ == "__main__":
    inputs = {
        "curriculum": "ICSE",
      "chapter": [
        "Probability",
        "Sets",
        "Numbers",
        "Integers",
        "Algebra",
        "Statistics",
        "Ratios and Proportions",
        "Decimals"
      ],
      "difficulty_level": "medium",
      "subject": "Mathematics",
      "grade": "Standard VII",
      "total_marks": 10,
      "city": "Chennai"
    }
    print(questions_utils(inputs))


    

