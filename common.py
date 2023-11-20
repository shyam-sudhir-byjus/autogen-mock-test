from constants import *
from bson import ObjectId
from pulp import LpStatus
from itertools import groupby
from operator import itemgetter
from collections import defaultdict

def add_constraints(problem, weights, percentages, tolerance, constraint_type, questions_list):
    for constraint_param, weight in weights:
        if constraint_param in percentages:
            lower_bound = weight - tolerance
            upper_bound = weight + tolerance
            problem += lower_bound * len(questions_list) <= percentages[constraint_param] * len(questions_list) <= upper_bound * len(questions_list), f"{constraint_type}_Constraint_{constraint_param}"

def remove_constraints(problem, constraint_type, percentages):
    for constraint_param in percentages:
        constraint_name = f"{constraint_type}_Constraint_{constraint_param}"
        if constraint_name in problem.constraints:
            del problem.constraints[constraint_name]
            print(f"Constraint '{constraint_name}' removed.")
        else:
            print(f"Constraint '{constraint_name}' not found in the model.")

def remove_frequency_constraint(problem, question_vars, most_frequent_questions):
    for q in most_frequent_questions:
        question_id = ObjectId(q['question_id'])
        if question_id in question_vars:
            constraint_name = f"frequencyConstraint_{question_id}"
            if constraint_name in problem.constraints:
                del problem.constraints[constraint_name]
                print(f"Constraint '{constraint_name}' for question {question_id} removed.")
            else:
                print(f"Constraint '{constraint_name}' for question {question_id} not found in the model.")
        else:
            print(f"Variable for question {question_id} not found in the model.")

def remove_average_difficulty_constraint(problem):
    constraint_name = "Average_Difficulty_Constraint"
    if constraint_name in problem.constraints:
        del problem.constraints[constraint_name]
        print(f"Constraint '{constraint_name}' removed.")
    else:
        print(f"Constraint '{constraint_name}' not found in the model.")

def solve_recursive(problem, questions_list, question_vars, constraints):
        if LpStatus[problem.status] == "Optimal":
            return successMsg(questions_list, question_vars)
        elif LpStatus[problem.status] == "Infeasible":
            if constraints:
                constraint_type, percentages = constraints.pop(0)
                print(f"No feasible solution found. Removing {constraint_type} constraint.")
                remove_constraints(problem, constraint_type, percentages)
                problem.solve()
                return solve_recursive(problem, questions_list, question_vars, constraints)
            else:
                return errorMsg()
        else:
            print("No optimal solution found.")

def successMsg(questions_list, question_vars):
    properties = {}
    properties["STATUS"] = "Optimal"
        
    selected_questions = [
        q for q in questions_list if question_vars[q["_id"]].value() == 1
    ]

    grouped_by_bloom = groupby(sorted(selected_questions, key=itemgetter('bloom')), key=itemgetter('bloom'))
    grouped_by_difficulty = groupby(sorted(selected_questions, key=itemgetter('difficulty')), key=itemgetter('difficulty'))
    grouped_by_type = groupby(sorted(selected_questions, key=itemgetter('type')), key=itemgetter('type'))
    grouped_by_chapter = groupby(sorted(selected_questions, key=itemgetter('chapter')), key=itemgetter('chapter'))

    marks_per_bloom = {key: sum(item['marks'] for item in group) for key, group in grouped_by_bloom}
    marks_per_difficulty = {key: sum(item['marks'] for item in group) for key, group in grouped_by_difficulty}
    marks_per_type = {key: sum(item['marks'] for item in group) for key, group in grouped_by_type}
    questions_per_chapter = {key: len(list(group)) for key, group in grouped_by_chapter}

    # avg_diff = sum([difficulty_mapper_dict[q['difficulty']] for q in selected_questions]) / len(selected_questions)
    total_marks = sum([q['marks'] for q in selected_questions])
    properties['NUMBER OF QUESTIONS'] = len(selected_questions)
    properties['TOTAL MARKS'] = total_marks
    properties['MARKS PER BLOOM'] = marks_per_bloom
    properties['MARKS PER DIFFICULTY'] = marks_per_difficulty
    properties['MARKS PER QUESTION TYPE'] = marks_per_type
    properties['QUESTIONS PER CHAPTER'] = questions_per_chapter
    return properties, selected_questions


def errorMsg():
    properties = {}
    properties["STATUS"] = "Non Feasible"
    return properties, {}