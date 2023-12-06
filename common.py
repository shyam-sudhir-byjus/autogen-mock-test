from constants import *
from pulp import LpStatus
from itertools import groupby
from operator import itemgetter
from add_remove_constraints import *
import ast
import re

def total_marks_helper(marks):
    if marks % 10 == 0:
        return marks // 2
    else:
        return (marks // 2) + 5
    
def solve_recursive(problem, questions_list, question_vars, constraints, chapter_weights, nearby_data, most_frequent_questions, removed_constraints):
        if LpStatus[problem.status] == "Optimal":
            return successMsg(questions_list, question_vars, chapter_weights, nearby_data, most_frequent_questions, removed_constraints)
        elif LpStatus[problem.status] == "Infeasible":
            if constraints:
                constraint_type, percentages = constraints.pop(0)
                print(f"No feasible solution found. Removing {constraint_type} constraint.")
                removed_constraints.append(constraint_type)
                if constraint_type == 'most_frequent_question':
                    remove_frequency_constraint(problem, question_vars, percentages)
                elif constraint_type in ['Average_Difficulty_Lower_Constraint']:
                    remove_average_difficulty_constraint(problem, constraint_type)
                elif constraint_type == 'AtLeastOneQuestionInChapter':
                    remove_at_least_one_question_constraint(problem, percentages)
                else:
                    remove_constraints(problem, constraint_type, percentages)
                problem.solve()
                return solve_recursive(problem, questions_list, question_vars, constraints, chapter_weights, nearby_data, most_frequent_questions, removed_constraints)
            else:
                return errorMsg()
        else:
            print("No optimal solution found.")

def successMsg(questions_list, question_vars, chapter_weights, nearby_data, most_frequent_questions, removed_constraints=[]):
    properties = {}
    properties["STATUS"] = "Optimal"
        
    selected_questions = [
        q for q in questions_list if question_vars[q["_id"]].value() == 1
    ]

    selected_questions = sorted(selected_questions, key=lambda x: float(x['marks']))

    for select_ques in selected_questions:
        select_ques["frequency"] = get_frequency(str(select_ques["_id"]), most_frequent_questions)
        select_ques["options"] = format_options(select_ques["options"])

    grouped_by_bloom = groupby(sorted(selected_questions, key=itemgetter('bloom')), key=itemgetter('bloom'))
    grouped_by_difficulty = groupby(sorted(selected_questions, key=itemgetter('difficulty')), key=itemgetter('difficulty'))
    grouped_by_type = groupby(sorted(selected_questions, key=itemgetter('type')), key=itemgetter('type'))
    grouped_by_chapter = groupby(sorted(selected_questions, key=itemgetter('chapter')), key=itemgetter('chapter'))
    grouped_by_topic = groupby(sorted(selected_questions, key=itemgetter('topic')), key=itemgetter('topic'))
    
    marks_per_bloom = {key: sum(item['marks'] for item in group) for key, group in grouped_by_bloom}
    marks_per_difficulty = {key: sum(item['marks'] for item in group) for key, group in grouped_by_difficulty}
    marks_per_type = {key: sum(item['marks'] for item in group) for key, group in grouped_by_type}
    marks_per_chapter = {key: sum(item['marks'] for item in group) for key, group in grouped_by_chapter}
    marks_per_topic = {key: sum(item['marks'] for item in group) for key, group in grouped_by_topic}
    
    avg_diff = sum([difficulty_mapper_dict[q['difficulty']] for q in selected_questions]) / len(selected_questions)
    difficulty_level = "easy" if 2 <= avg_diff <= 4 else ("medium" if 4 < avg_diff <= 6 else "hard")
    total_marks = sum([q['marks'] for q in selected_questions])
    properties['number_of_questions'] = len(selected_questions)
    properties['total_marks'] = total_marks
    properties['bloom_distribution'] = marks_per_bloom
    properties['difficulty_distribution'] = marks_per_difficulty
    properties['question_type_distribution'] = marks_per_type
    properties['chapter_distribution'] = marks_per_chapter
    properties['topic_distribution'] = marks_per_topic
    properties['average_difficulty'] = avg_diff
    properties['average_difficulty_string'] = difficulty_level
    properties['blooms_from_nearby_school'] = nearby_data['bloom']
    properties['difficulty_from_school_nearby'] = nearby_data['difficulty']
    properties['question_type_from_school_nearby'] = nearby_data['question_type']
    properties['chapters_from_school_nearby'] = nearby_data['chapter']
    properties['school_count'] = nearby_data['school_count']
    
    if removed_constraints:
        properties['removed_constraints'] = removed_constraints
    return properties, selected_questions, False

def errorMsg():
    properties = {}
    properties["STATUS"] = "Non Feasible"
    return properties, {}, False

def get_frequency(question_id, data):
    frequency_mapping = {item['question_id']: item['frequency'] for item in data}
    return frequency_mapping.get(question_id, 0)

def format_options(options):
    if options == "" or options == {}:
        return []
    try:
        if isinstance(options, list):
            options_list = options
        else:
            options_list = ast.literal_eval(options)
        cleaned_options_list = [re.sub(r'^(\([a-zA-Z]\)|^[a-zA-Z0-9]+\.)|^[a-zA-Z0-9]+\.|^[a-zA-Z0-9]+\)', '', option).strip() for option in options_list]
        return cleaned_options_list
    except:
        return options