from constants import *
from pulp import LpStatus
from itertools import groupby
from operator import itemgetter
from add_remove_constraints import *

def total_marks_helper(marks):
    if marks % 10 == 0:
        return marks // 2
    else:
        return (marks // 2) + 5
    
def solve_recursive(problem, questions_list, question_vars, constraints, chapter_weights, nearby_data, removed_constraints):
        if LpStatus[problem.status] == "Optimal":
            return successMsg(questions_list, question_vars, chapter_weights, nearby_data, removed_constraints)
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
                return solve_recursive(problem, questions_list, question_vars, constraints, chapter_weights, nearby_data, removed_constraints)
            else:
                return errorMsg()
        else:
            print("No optimal solution found.")

def successMsg(questions_list, question_vars, chapter_weights, nearby_data, removed_constraints=[]):
    properties = {}
    properties["STATUS"] = "Optimal"
        
    selected_questions = [
        q for q in questions_list if question_vars[q["_id"]].value() == 1
    ]

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
    total_marks = sum([q['marks'] for q in selected_questions])
    properties['NUMBER OF QUESTIONS'] = len(selected_questions)
    properties['TOTAL MARKS'] = total_marks
    properties['MARKS PER BLOOM'] = marks_per_bloom
    properties['MARKS PER DIFFICULTY'] = marks_per_difficulty
    properties['MARKS PER QUESTION TYPE'] = marks_per_type
    properties['MARKS PER CHAPTER'] = marks_per_chapter
    properties['MARKS PER TOPIC'] = marks_per_topic
    properties['AVERAGE DIFFICULTY'] = avg_diff
    properties['NEARBY BLOOMS COUNT'] = nearby_data['bloom']
    properties['NEARBY DIFFICULTY COUNT'] = nearby_data['difficulty']
    properties['NEARBY QUESTION TYPE COUNT'] = nearby_data['question_type']
    properties['NEARBY CHAPTER COUNT'] = nearby_data['chapter']
    
    if removed_constraints:
        properties['REMOVED CONSTRAINTS'] = removed_constraints
    return properties, selected_questions, False

def errorMsg():
    properties = {}
    properties["STATUS"] = "Non Feasible"
    return properties, {}, False
