from pulp import LpProblem, LpVariable, lpSum, LpMinimize, LpStatus, LpBinary, const
from weights import Weights
from constants import *
from utils.db_utils import *
from bson import ObjectId
from common import *
from add_remove_constraints import *
from collections import Counter

def calculate_percentage(questions_list, bloom_weights, difficulty_weights, question_type_weights, topic_weights, chapter_weights):
    questions_len = len(questions_list)

    bloom_mapper_values = {bloom_type: set(bloom_mapper_dict[bloom_type]) for bloom_type, _ in bloom_weights}
    difficulty_values = [difficulty_level for difficulty_level, _ in difficulty_weights]
    q_type_values = [q_type for q_type, _ in question_type_weights]
    topic_values = list(topic_weights.keys())
    chapter_values = list(chapter_weights.keys())

    counters = {
        "bloom": Counter(q["bloom"] for q in questions_list),
        "difficulty": Counter(q["difficulty"] for q in questions_list),
        "q_type": Counter(q["type"] for q in questions_list),
        "topic": Counter(q["topic"] for q in questions_list),
        "chapter": Counter(q["chapter"] for q in questions_list),
    }

    bloom_percentages = {bloom_type: counters["bloom"][bloom] / questions_len for bloom_type, bloom in bloom_mapper_values.items()}
    difficulty_percentages = {difficulty_level: counters["difficulty"][difficulty_level] / questions_len for difficulty_level in difficulty_values}
    question_type_percentages = {q_type: counters["q_type"][q_type] / questions_len for q_type in q_type_values}
    topic_percentages = {topic: counters["topic"][topic] / questions_len for topic in topic_values}
    chapter_percentages = {chapter: counters["chapter"][chapter] / questions_len for chapter in chapter_values}
    return (bloom_percentages, difficulty_percentages, question_type_percentages, topic_percentages, chapter_percentages)


def pulp_solver(questions_list, similar_questions_list, input_data, most_frequent_questions, user_difficulty, total_marks):

    problem = LpProblem("Question_Selection", LpMinimize)

    chapter_weights, topic_weights = get_chapter_topic_weights(questions_list)

    question_vars = {
        q["_id"]: LpVariable(f"Question_{q['_id']}", 0, 1, LpBinary) for q in questions_list
    }

    average_difficulty = LpVariable("Average_Difficulty", user_difficulty - 1, user_difficulty + 1)
    question_difficulties = lpSum([difficulty_mapper_dict[q["difficulty"]] * question_vars[q["_id"]] for q in questions_list])
    problem += (
        average_difficulty - 1 <= question_difficulties / len(questions_list),
        "Average_Difficulty_Lower_Constraint"
    )

    problem += (
        question_difficulties / len(questions_list) <= average_difficulty + 1,
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
    
    weights_instance = Weights(db['city_school_question_tags_v2'], db['city_school_location_v2'], input_data)
    bloom_weights, difficulty_weights, question_type_weights, chapter_weights_school, bloom_nearby, diff_nearby, q_type_nearby, chapter_nearby = weights_instance._get_weights()

    nearby_school_data = {
        "bloom": bloom_nearby,
        "difficulty": diff_nearby,
        "question_type": q_type_nearby,
        "chapter": chapter_nearby
    }

    if chapter_weights_school != []:
        chapter_weights = chapter_weights_school

    tolerance = 0.1

    bloom_percentages = {bloom_type: lpSum([q["bloom"] in bloom_mapper_dict[bloom_type] for q in questions_list]) / len(questions_list) for bloom_type, _ in bloom_weights}
    difficulty_percentages = {difficulty_level: lpSum([q["difficulty"] == difficulty_level for q in questions_list]) / len(questions_list) for difficulty_level, _ in difficulty_weights}
    question_type_percentages = {q_type: lpSum([q["type"] == q_type for q in questions_list]) / len(questions_list) for q_type, _ in question_type_weights}
    topic_percentages = {topic: lpSum([q["topic"] == topic for q in questions_list]) / len(questions_list) for topic, _ in topic_weights.items()}
    chapter_percentages = {chapter: lpSum([q["chapter"] == chapter for q in questions_list]) / len(questions_list) for chapter, _ in chapter_weights.items()}

    add_constraints_bloom(problem, question_vars, questions_list, bloom_percentages, tolerance, total_marks)
    add_constraints_difficult(problem, question_vars, questions_list, difficulty_percentages, tolerance, total_marks)
    add_constraints_question_type(problem, question_vars, questions_list, question_type_percentages, tolerance, total_marks)
    add_constraints_chapter(problem, question_vars, questions_list, chapter_percentages, tolerance, total_marks)
    add_constraints_topic(problem, question_vars, questions_list, topic_percentages, tolerance, total_marks)
    
    for q in most_frequent_questions:
        question_id = ObjectId(q['question_id'])
        if question_id in question_vars:
            constraint_name = f"frequencyConstraint_{question_id}"
            problem += question_vars[question_id] <= q['frequency'], constraint_name
    
    problem.solve()

    if LpStatus[problem.status] == "Optimal":
        return successMsg(questions_list, question_vars, chapter_weights, nearby_school_data, [])

    properties, selected_questions, flag = solve_recursive(problem, questions_list, question_vars, [
                                                        ("Average_Difficulty_Lower_Constraint", []),
                                                        ("Bloom", bloom_percentages),
                                                        ("most_frequent_question", most_frequent_questions),
                                                        ("QuestionType", question_type_percentages),
                                                        ("Topic_Distribution", topic_percentages),
                                                        ("AtLeastOneQuestionInChapter", chapter_questions),
                                                        # ("Chapter_Distribution", chapter_percentages),
                                                        ("Difficulty", difficulty_percentages),
                                                        ], 
                                                        chapter_weights, nearby_school_data,
                                                        [])
    return properties, selected_questions, flag
