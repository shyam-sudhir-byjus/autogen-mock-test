from pulp import lpSum
from constants import bloom_mapper_dict

def add_constraints_bloom(problem, question_vars, questions_list, percentages, tolerance, total_marks):

    for constraint_param, weight in percentages.items():
        problem += (
                (weight - tolerance) * total_marks <=
                lpSum([q["marks"] * question_vars[q["_id"]] for q in questions_list if q["bloom"] in bloom_mapper_dict[constraint_param]]) 
                <= (weight + tolerance) * total_marks,
                f"Bloom_Constraint_{constraint_param}",
            )
    
def add_constraints_difficult(problem, question_vars, questions_list, percentages, tolerance, total_marks):

    for constraint_param, weight in percentages.items():
        problem += (
                (weight - tolerance) * total_marks <=
                lpSum([q["marks"] * question_vars[q["_id"]] for q in questions_list if q["difficulty"] == constraint_param])
                <= (weight + tolerance) * total_marks,
                f"Difficulty_Constraint_{constraint_param}",
            )
    
def add_constraints_question_type(problem, question_vars, questions_list, percentages, tolerance, total_marks):

    for constraint_param, weight in percentages.items():
        problem += (
                (weight - tolerance) * total_marks <=
                lpSum([q["marks"] * question_vars[q["_id"]] for q in questions_list if q["type"] == constraint_param])
                <= (weight + tolerance) * total_marks,
                f"QuestionType_Constraint_{constraint_param}",
            )

def add_constraints_chapter(problem, question_vars, questions_list, percentages, tolerance, total_marks):

    for constraint_param, weight in percentages.items():
        try:
            problem += (
                    (weight - tolerance) * total_marks <=lpSum([q["marks"] * question_vars[q["_id"]] for q in questions_list if q["chapter"] == constraint_param])
                    <= (weight + tolerance) * total_marks,
                    f"Chapter_Constraint_{constraint_param}",
                )
        except:
            continue

def add_constraints_topic(problem, question_vars, questions_list, percentages, tolerance, total_marks):

    for constraint_param, weight in percentages.items():
        try:
            problem += (
                    (weight - tolerance) * total_marks <=
                    lpSum([q["marks"] * question_vars[q["_id"]] for q in questions_list if q["topic"] == constraint_param]) 
                    <= (weight + tolerance) * total_marks,
                    f"Topic_Distribution_Constraint_{constraint_param}",
                )
        except:
            continue