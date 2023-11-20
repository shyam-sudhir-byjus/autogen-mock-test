from pulp import LpProblem, LpVariable, lpSum, LpMinimize, LpStatus, LpBinary
from weights import Weights
from constants import *
from db_utils import *
from bson import ObjectId
from common import *

def pulp_solver(questions_list, similar_questions_list, input_data, most_frequent_questions, user_difficulty, total_marks):

    problem = LpProblem("Question_Selection", LpMinimize)

    question_vars = {
        q["_id"]: LpVariable(f"Question_{q['_id']}", 0, 1, LpBinary) for q in questions_list
    }

    average_difficulty = LpVariable("Average_Difficulty", user_difficulty - 2, user_difficulty + 2)
    question_difficulties = lpSum([difficulty_mapper_dict[q["difficulty"]] * question_vars[q["_id"]] for q in questions_list])
    problem += (
        average_difficulty <= question_difficulties / len(questions_list),
        "Average_Difficulty_Lower_Constraint"
    )

    problem += (
        question_difficulties / len(questions_list) <= average_difficulty,
        "Average_Difficulty_Upper_Constraint"
    )

    chapter_questions = {chapter: [question_vars[q["_id"]] for q in questions_list if q["chapter"] == chapter] for chapter in set(q["chapter"] for q in questions_list)}

    for chapter, chapter_vars in chapter_questions.items():
        problem += lpSum(chapter_vars) >= 1, f"AtLeastOneQuestionInChapter_{chapter}"

    problem += (
        lpSum([q["marks"] * question_vars[q["_id"]] for q in questions_list]) == total_marks,
        "Total_Marks_Constraint",
    )

    question_vars_dict = {q["_id"]: question_vars[q["_id"]] for q in questions_list}

    for row in similar_questions_list:
        index_of_sim_pairs = [str(row["ID1"]), str(row["ID2"])]
        
        if all(ObjectId(q_id) in question_vars_dict for q_id in index_of_sim_pairs):
            name = f"similar_{index_of_sim_pairs[0]}_{index_of_sim_pairs[1]}"
            const = lpSum([question_vars_dict[ObjectId(q_id)] for q_id in index_of_sim_pairs]) <= 1
            problem += const, name

    weights_instance = Weights(city_school_question_tags_collection, city_school_location, input_data)
    bloom_weights, difficulty_weights, question_type_weights = weights_instance._get_weights()

    bloom_percentages = {bloom_type: lpSum([q["bloom"] in bloom_mapper_dict[bloom_type] for q in questions_list]) / len(questions_list) for bloom_type, _ in bloom_weights}
    difficulty_percentages = {difficulty_level: lpSum([q["difficulty"] == difficulty_level for q in questions_list]) / len(questions_list) for difficulty_level, _ in difficulty_weights}
    question_type_percentages = {q_type: lpSum([q["type"] == q_type for q in questions_list]) / len(questions_list) for q_type, _ in question_type_weights}

    tolerance = 0.3 

    add_constraints(problem, bloom_weights, bloom_percentages, tolerance, "Bloom", questions_list)
    add_constraints(problem, difficulty_weights, difficulty_percentages, tolerance, "Difficulty", questions_list)
    add_constraints(problem, question_type_weights, question_type_percentages, tolerance, "Question_Type", questions_list)

    for q in most_frequent_questions:
        question_id = ObjectId(q['question_id'])
        if question_id in question_vars:
            constraint_name = f"frequencyConstraint_{question_id}"
            problem += question_vars[question_id] <= q['frequency'], constraint_name
    
    problem.solve()

    if LpStatus[problem.status] == "Optimal":
        return successMsg(questions_list, question_vars)
    else:
        average_difficulty = LpVariable("Average_Difficulty", user_difficulty - 3, user_difficulty + 3)
    
    problem.solve()

    if LpStatus[problem.status] == "Optimal":
        return successMsg(questions_list, question_vars)

    return solve_recursive(problem, questions_list, question_vars, [("most_frequent_question", most_frequent_questions),
                                                        ("Bloom", bloom_percentages),
                                                        ("Difficulty", difficulty_percentages),
                                                        ("QuestionType", question_type_percentages)])

    # if LpStatus[problem.status] == "Optimal":
    #     return successMsg(questions_list, question_vars)

    # elif LpStatus[problem.status] == "Infeasible":
    #     print("No feasible solution found. Removing most_frequent_question constraint.")
    #     remove_frequency_constraint(problem, question_vars, most_frequent_questions)
                
    #     problem.solve()
        
    #     if LpStatus[problem.status] == "Optimal":
    #         return successMsg(questions_list, question_vars)
    #     else:
    #         print("No feasible solution found. Removing Bloom constraint.")
    #         remove_constraints(problem, "Bloom", bloom_percentages)
    #         problem.solve()
    #         if LpStatus[problem.status] == "Optimal":
    #             return successMsg(questions_list, question_vars)
    #         else:
    #             print("No feasible solution found. Removing Difficulty constraint.")
    #             remove_constraints(problem, "Difficulty", difficulty_percentages)
    #             problem.solve()
    #             if LpStatus[problem.status] == "Optimal":
    #                 return successMsg(questions_list, question_vars)
    #             else: 
    #                 print("No feasible solution found. Removing Question Type constraint.")
    #                 remove_constraints(problem, "QuestionType", question_type_percentages)
    #                 problem.solve()
    #                 if LpStatus[problem.status] == "Optimal":
    #                     return successMsg(questions_list, question_vars)
    #                 else:  
    #                     return errorMsg()

    # else:
    #     print("No optimal solution found.")

    
        