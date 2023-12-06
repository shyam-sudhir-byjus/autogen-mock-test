from pulp import lpSum
from bson import ObjectId
from constants import bloom_mapper_dict

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

def remove_average_difficulty_constraint(problem, constraint_name):
    if constraint_name in problem.constraints:
        del problem.constraints[constraint_name]
        print(f"Constraint '{constraint_name}' removed.")
    else:
        print(f"Constraint '{constraint_name}' not found in the model.")

def remove_at_least_one_question_constraint(problem, chapter_list):
    for chapter in chapter_list:
        constraint_name = f"AtLeastOneQuestionInChapter_{chapter}"
        constraint_name = constraint_name.replace(" ","_")

        if constraint_name in problem.constraints:
            problem.constraints.pop(constraint_name)

def remove_topic_distribution_constraint(problem, percentages, constraint_type):
    for constraint_param in percentages:
        constraint_name = f"{constraint_type}_Constraint_{constraint_param}"
        if constraint_name in problem.constraints:
            del problem.constraints[constraint_name]
            print(f"Constraint '{constraint_name}' removed.")
        else:
            print(f"Constraint '{constraint_name}' not found in the model.")

def get_chapter_topic_weights(questions_list):
    '''
        Returns Weightage of Chapter/Topic from the given questions list
        for the input parameters
    '''
    chapter_counts, topics_count = {}, {}
    for q in questions_list:
        chapter, topic = q['chapter'], q['topic']
        chapter_counts[chapter] = chapter_counts.get(chapter, 0) + 1
        topics_count[topic] = topics_count.get(topic, 0) + 1
        
    total_sum_chapters = sum(chapter_counts.values())
    total_sum_topics = sum(topics_count.values())
    
    chapter_weights, topic_weights = {}, {}
    for chapter, count in chapter_counts.items():
        chapter_weights[chapter] = count / total_sum_chapters

    for topic, count in topics_count.items():
        topic_weights[topic] = count / total_sum_topics
    
    return chapter_weights, topic_weights

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