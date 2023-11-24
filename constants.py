difficulty_mapper_dict = {"easy": 2, "medium": 5, "hard": 8}

knowledge_list = ['Knowledge', 'Remembering', 'knowledge', 'remembering', 'remember', 'Remember']
comprehension_list = ['Comprehension', 'Understanding', 'comprehension', 'understanding', 'understand', 'Understanding']
application_list = ['Application', 'Applying', 'Apply', 'application', 'applying', 'apply']
analysing_list = ['Analysis', 'analysis', 'Analyzing', 'analyzing']
evaluate_list = ['Evaluating', 'evaluating', 'Evaluate', 'evaluate']
create_list = ['Creating', 'creating', 'Creat', 'creat']

bloom_mapper_dict = {
    'Knowledge': knowledge_list,
    'Comprehension': comprehension_list,
    'Application': application_list,
    'Analysing': analysing_list,
    'Evaluation': evaluate_list,
    'Creation': create_list
}

constraint_dict = {
    "Bloom": "bloom",
    "Difficulty": "difficulty",
    "Question_Type": "type",
    "Chapter_Distribution": "chapter",
    "Topic_Distribution": "topic"
}
