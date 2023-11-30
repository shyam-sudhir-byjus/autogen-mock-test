import pandas as pd
from pymongo import MongoClient
from collections import defaultdict, Counter

class Weights:
    def __init__(self, city_school_question_tags_collection, city_school_location, input_data):
        self.city_school_question_tags_collection = city_school_question_tags_collection
        self.city_school_location_collection = city_school_location
        self.input_data = input_data
        self.schools_nearby = None
        self.top_schools_locations = None
        self.bloom_avg_weight = None
        self.diff_avg_weight = None
        self.question_type_avg_weight = None
        self.difficulty_from_school_nearby = None
        self.blooms_from_nearby_school = None
        self.question_types_from_school_nearby = None
        self.school_q_counter = 0
        self.total_marks = input_data['total_marks']
        self.buffer_qns_count = int(self.total_marks * 2)  
        self.is_solvable = True
        self.source_tag = None
        self.qna_data = None 
        self.chapter_weightage = [] 

    def _get_nearby_schools_data(self):
        """
        Get the nearest school data in dict form in self.schools_nearby 
        And lat, long of the nearest school in self.top_schools_locations 
        """

        school_id_lat_lng_dict = self._get_nearest_schools(self.input_data['location']['latitude'],
                                                           self.input_data['location']['longitude'],
                                                           self.input_data['curriculum'])
        school_id_list = list(school_id_lat_lng_dict)

        schools_nearby_df = pd.DataFrame()
        qns_counter_cummulative = 0

        if len(school_id_list) != 0:
            schools_nearby_df = pd.DataFrame(
                self.city_school_question_tags_collection.find({
                    "school_id": {"$in": school_id_list},
                    "subject": self.input_data['subject'],
                    "grade": self.input_data['grade'],
                    "chapter": {"$in": self.input_data['chapter']}
                }))

        if len(schools_nearby_df) != 0:

            df_count = 0
            while df_count < len(schools_nearby_df):
                qns_counter_cummulative += sum(schools_nearby_df["difficulty"].tolist()[df_count].values())
                df_count += 1

            self.school_q_counter = qns_counter_cummulative
            schools_nearby_df = schools_nearby_df.head(df_count)
            index_school_by_nearest = {}
            for idx, school_id in enumerate(school_id_list):
                index_school_by_nearest[school_id] = idx + 1

            df_all_schools_locations = pd.DataFrame.from_dict(school_id_lat_lng_dict, orient='index',
                                                               columns=['school', 'location'])
            df_all_schools_locations['school_id'] = df_all_schools_locations.index
            df_all_schools_locations = df_all_schools_locations.reset_index(drop=True)

            schools_nearby_df["school_index"] = schools_nearby_df["school_id"].map(index_school_by_nearest)
            schools_nearby_df = schools_nearby_df.sort_values(by="school_index", ascending=True)
            self._get_lat_lng_nearest_schools(df_all_schools_locations, schools_nearby_df)

            self.schools_nearby = schools_nearby_df.to_dict('list')
            schools_count = len(schools_nearby_df)

        if len(schools_nearby_df) == 0:
            school_id_lat_lng_dict = self._get_all_schools()
            school_id_list = list(school_id_lat_lng_dict)
            schools_nearby_df = pd.DataFrame(
                self.city_school_question_tags_collection.find({
                    "school_id": {"$in": school_id_list},
                    "subject": self.input_data['subject'],
                    "grade": self.input_data['grade'],
                    "chapter": {"$in": self.input_data['chapter']}
                }))
            index_school_by_nearest = {}
            for idx, school_id in enumerate(school_id_list):
                index_school_by_nearest[school_id] = idx + 1

            df_all_schools_locations = pd.DataFrame.from_dict(school_id_lat_lng_dict, orient='index',
                                                               columns=['latitude', 'longitude'])
            df_all_schools_locations['school_id'] = df_all_schools_locations.index
            df_all_schools_locations = df_all_schools_locations.reset_index(drop=True)

            schools_nearby_df["school_index"] = schools_nearby_df["school_id"].map(index_school_by_nearest)
            schools_nearby_df = schools_nearby_df.sort_values(by="school_index", ascending=True)
            top_schools_locations = []
            self.schools_nearby = schools_nearby_df.to_dict('list')
            schools_count = len(schools_nearby_df)

    def _get_nearest_schools(self, lat, lng, curriculum):
        upper_bound_in_km = 52
        distance_in_radians = 1 / 111.12 * upper_bound_in_km
        nearest_school_cursor = self.city_school_location_collection.find(
            {"location": {"$near": [lat, lng], "$maxDistance": distance_in_radians}},
            {"school_id": 1, "location": 1, 'curriculum': 1, "school": 1}
        )
        nearest_school = list(nearest_school_cursor)

        if len(nearest_school) == 0:
            return []

        nearest_school = [school for school in nearest_school if school['curriculum'] == curriculum]
        for school in nearest_school:
            school['school'] = school['school'].replace(',', ' ')
            school['school_id'] = float(school['school_id'])

        nearest_school_lat_lng_dict = {school['school_id']: {'school': school['school'],
                                                             'location': (school['location']['latitude'],
                                                                          school['location']['longitude'])}
                                       for school in nearest_school}

        return nearest_school_lat_lng_dict

    def _get_all_schools(self):
        nearest_school_cursor = self.city_school_location_collection.find({})
        '''
        Assuming nearest_school_cursor is an iterable containing documents from the database
        '''
        nearest_school_lat_lng_dict = {}

        for school_data in nearest_school_cursor:
            school_id = float(school_data['school_id'])
            lat_lng = (school_data['location']['latitude'], school_data['location']['longitude'])
            nearest_school_lat_lng_dict[school_id] = lat_lng

        return nearest_school_lat_lng_dict

    def _get_lat_lng_nearest_schools(self, df_all_schools_locations, schools_nearby_df):
        """
        Get List[Schools] of nearby to the location of the user
        """
        result_top_schools_locations = pd.merge(df_all_schools_locations,
                                                schools_nearby_df,
                                                on='school_id',
                                                how='right')
        top_schools = list(tuple(zip(result_top_schools_locations['school'],
                                     result_top_schools_locations['location'])))
        self.top_schools_locations = top_schools

    def _get_difficulty_weights_from_db(self):
        """
        Updates self.diff_avg_weight using distribution of questions from the nearest school
        """
        if not self.top_schools_locations or self.school_q_counter < self.buffer_qns_count:
            qna_data = self.qna_data
            if self.source_tag == "QNA":
                self.diff_avg_weight = list(qna_data["diff_data"].values())
                self.difficulty_from_school_nearby = qna_data["diff_number_dict"]

            else:
                schools_nearby = self.schools_nearby
                easy_percentages = []
                medium_percentages = []
                hard_percentages = []
                easy_range = (0, 0)
                medium_range = (0, 0)
                hard_range = (0, 0)
                total_count = 0
                for d in schools_nearby['difficulty']:
                    total_count += sum(d.values())
                    if 'easy' in d.keys():
                        easy_percentages.append(d['easy'] / (sum(d.values())) * 100)
                        easy_range = (min(easy_percentages), max(easy_percentages))
                    if 'medium' in d.keys():
                        medium_percentages.append(d['medium'] / (sum(d.values())) * 100)
                        medium_range = (min(medium_percentages), max(medium_percentages))
                    if 'hard' in d.keys():
                        hard_percentages.append(d['hard'] / (sum(d.values())) * 100)
                        hard_range = (min(hard_percentages), max(hard_percentages))

                diff_avg_weight = []
                diff_percentage = {"easy": easy_range, "medium": medium_range, "hard": hard_range}
                for key, value in diff_percentage.items():
                    if value:
                        diff_avg_weight.append((min(value)) / 100)
                normalized_weights = [value / sum(diff_avg_weight) for value in diff_avg_weight]
                self.diff_avg_weight = normalized_weights
                difficulty_from_school_nearby = {"easy": int(normalized_weights[0] * total_count),
                                                 "medium": int(normalized_weights[1] * total_count),
                                                 "hard": int(normalized_weights[2] * total_count)}
                if sum(difficulty_from_school_nearby.values()) < self.buffer_qns_count:
                    self.is_solvable = False
                self.difficulty_from_school_nearby = difficulty_from_school_nearby

        else:
            schools_nearby = self.schools_nearby
            easy_percentages = []
            medium_percentages = []
            hard_percentages = []
            easy_range = (0, 0)
            medium_range = (0, 0)
            hard_range = (0, 0)
            total_count = 0
            for d in schools_nearby['difficulty']:
                total_count += sum(d.values())
                if 'easy' in d.keys():
                    easy_percentages.append(d['easy'] / (sum(d.values())) * 100)
                    easy_range = (min(easy_percentages), max(easy_percentages))
                if 'medium' in d.keys():
                    medium_percentages.append(d['medium'] / (sum(d.values())) * 100)
                    medium_range = (min(medium_percentages), max(medium_percentages))
                if 'hard' in d.keys():
                    hard_percentages.append(d['hard'] / (sum(d.values())) * 100)
                    hard_range = (min(hard_percentages), max(hard_percentages))

            diff_avg_weight = []
            diff_percentage = {"easy": easy_range, "medium": medium_range, "hard": hard_range}
            for key, value in diff_percentage.items():
                if value:
                    diff_avg_weight.append((min(value)) / 100)
            normalized_weights = [value / sum(diff_avg_weight) for value in diff_avg_weight]
            self.diff_avg_weight = normalized_weights
            self.difficulty_from_school_nearby = {"easy": int(normalized_weights[0] * total_count),
                                                  "medium": int(normalized_weights[1] * total_count),
                                                  "hard": int(normalized_weights[2] * total_count)}
            
    def get_weight_from_qna(self, location, curriculum, subject, grade, chapters):
        '''
            Get weights for bloom/difficulty for given location and details from QnA
            Args:
                location: Dict,
                curriculum: String,
                subject: String,
                grade: String,
                chapters: List[String]
            Returns:
                QnA Data Dict for difficulty and bloom and averages of them: Dict
        '''
        qna_dict = self.get_nearest_data_with_param(location["latitude"], 
                                            location["longitude"], 
                                            grade, 
                                            subject, 
                                            curriculum, 
                                            chapters)
        if qna_dict != {}:
            qna_dict_diff, qna_dict_bloom, qna_dict_ques_type  = qna_dict["difficulty"], qna_dict["bloom"], qna_dict["type"]
            qna_diff_weights= {}
            update_diff_dict = {
                "easy" : qna_dict_diff.get('Easy',0),
                "medium" : qna_dict_diff.get('Medium',0),
                "hard" : qna_dict_diff.get('Hard',0)
            }
            sum_dict = sum(update_diff_dict.values())
            qna_diff_weights = defaultdict(int, {'easy': 0, 'medium': 0, 'hard': 0})
                        
            if sum_dict != 0:
                qna_diff_weights['easy'] = (update_diff_dict["easy"]/sum_dict)
                qna_diff_weights['medium'] = (update_diff_dict["medium"]/sum_dict)
                qna_diff_weights['hard'] = (update_diff_dict["hard"]/sum_dict)

            qna_bloom_weights= {}
            update_bloom_dict = {
                "Knowledge" : qna_dict_bloom.get('Memory',0),
                "Comprehension" : qna_dict_bloom.get('Understand',0),
                "Application" : qna_dict_bloom.get('Apply',0),
                "Analysing" : qna_dict_bloom.get('Analysis',0),
                "Evaluation" : qna_dict_bloom.get('Evaluate',0),
                "Creation" : qna_dict_bloom.get('Create',0)
            }
            sum_dict2 = sum(update_bloom_dict.values())
            if sum_dict2 == 0: sum_dict2 =1
            qna_bloom_weights['Knowledge'] = (update_bloom_dict["Knowledge"]/sum_dict2)
            qna_bloom_weights['Comprehension'] = (update_bloom_dict["Comprehension"]/sum_dict2)
            qna_bloom_weights['Application'] = (update_bloom_dict["Application"]/sum_dict2)
            qna_bloom_weights['Analysing'] = (update_bloom_dict["Analysing"]/sum_dict2)
            qna_bloom_weights['Evaluation'] = (update_bloom_dict["Evaluation"]/sum_dict2)
            qna_bloom_weights['Creation'] = (update_bloom_dict["Creation"]/sum_dict2)

            qna_ques_type_weights = {}
            update_ques_type_dict = {
                "MC" : qna_dict_ques_type.get('MC',0),
                "FITB" : qna_dict_ques_type.get('FITB',0),
                "VSA" : qna_dict_ques_type.get('VSA',0),
                "SA" : qna_dict_ques_type.get('SA',0),
                "LA" : qna_dict_ques_type.get('LA',0),
                "TF" : qna_dict_ques_type.get('TF',0),
                "MTC" : qna_dict_ques_type.get('MTC',0),
                "GM" : qna_dict_ques_type.get('GM',0)
            }
            sum_dict = sum(update_ques_type_dict.values())
            qna_ques_type_weights = defaultdict(int, {'MC': 0, 'FITB': 0, 'VSA': 0, 'SA': 0,
                                                'LA': 0, 'TF': 0, 'MTC': 0, 'GM': 0})
                        
            if sum_dict != 0:
                qna_ques_type_weights['MC'] = (qna_ques_type_weights["MC"]/sum_dict)
                qna_ques_type_weights['FITB'] = (qna_ques_type_weights["FITB"]/sum_dict)
                qna_ques_type_weights['VSA'] = (qna_ques_type_weights["VSA"]/sum_dict)
                qna_ques_type_weights['SA'] = (qna_ques_type_weights["SA"]/sum_dict)
                qna_ques_type_weights['LA'] = (qna_ques_type_weights["LA"]/sum_dict)
                qna_ques_type_weights['TF'] = (qna_ques_type_weights["TF"]/sum_dict)
                qna_ques_type_weights['MTC'] = (qna_ques_type_weights["MTC"]/sum_dict)
                qna_ques_type_weights['GM'] = (qna_ques_type_weights["GM"]/sum_dict)

            qna_data = {"diff_data" : qna_diff_weights,
                        "diff_number_dict":update_diff_dict, 
                        "bloom_data":qna_bloom_weights,
                        "bloom_number_dict": update_bloom_dict,
                        "ques_type_data": qna_ques_type_weights,
                        "ques_type_number_dict": update_ques_type_dict}
        else:
            qna_data = {}
        return qna_data

    def _get_subject_details(self, subject):
        """
            Static Method that returns list of subjects for a subject,
            ie. Some subjects can have different subtypes 

            Args:
                subject: String
            
            Returns:
                List[String] -> Subjects
        """
        maths_list = ['Maths', 'MATHS', 'MATHEMATICS', 'Math', 'math', 'maths', 'Mathematics']
        science_list = ['SCIENCE', 'PHYSICS', 'BIOLOGY', 'CHEMISTRY', "Physics", "Biology", "Science", "Chemistry"]

        if subject in maths_list:
            return maths_list
        else :
            return science_list


    def get_nearest_data_with_param(self, lat, lng, grade, subject, syllabus, chapters_list):
        '''
            Function to get nearest data using QnA query logs for given parameters
            Args:
                lat: Float,
                lng: Float,
                grade: String,
                subject: String,
                syllabus: String,
                chapters_list: List[String]
            Returns:
                Dict with bloom, difficulty and type for nearest data
        '''
        client = MongoClient(
            "mongodb://abhi:dke28332nvk3ker3i3@52.72.223.17:27017/byjus_ingestion_data",
        )
        db = client["byjus_ingestion_data"]
        collection = db["slp_qna_test"]
        upper_bound_in_km = 52  
        distance_in_radians = 1 / 111.12 * upper_bound_in_km
        subject_list = self._get_subject_details(subject)

        nearest_data = pd.json_normalize(
            list(
                collection.aggregate([
                    # {
                    #     "location": {
                    #         "$near": [lat, lng],
                    #         "$maxDistance": distance_in_radians,
                    #     },
                    {"$geoNear":
                    {"near": { "type": "Point", "coordinates": [  lng, 
                lat ] },
                            "distanceField": "dist.calculated",
                            "maxDistance": 52000,
                            "spherical":True}},
                    {"$project":{"search_doc_id":1,"_id":0}},
                    {"$lookup":
                    {
                        "from":"q2c_search_logs_prd",
                        "localField":"search_doc_id",
                        "foreignField":"_id",
                        "as":"data"
                        }
                    },
                    {"$project":{"search_doc_id":1,"question_id":{"$first":"$data.qid"}}},
                    {"$lookup":
                    {
                        "from":"questions_v2",
                        "localField":"question_id",
                        "foreignField":"ID",
                        "as":"data"
                        }
                    },
                    {"$project":{"search_doc_id":1,"question_id":1, 
                                "DIFFICULTY":"$data.DIFFICULTY",
                                "CATEGORY_ID":"$data.CATEGORY_ID",
                                "type":{"$first":"$data.TYPE"},
                                "POINTS":{"$first":"$data.POINTS"},
                                "bloom":{"$first":"$data.SKILL"}}},
                    {"$lookup":
                    {
                        "from":"categories",
                        "localField":"CATEGORY_ID",
                        "foreignField":"ID",
                        "as":"data"
                        }
                    },
                    {"$project":{"search_doc_id":1,"question_id":1,
                                "difficulty":{"$first":"$DIFFICULTY"},
                                "type":1,
                                "bloom":1,
                                "CATEGORY_NAME":{"$first":"$data.NAME"},
                                "CATEGORY_TYPE":{"$first":"$data.TYPE"},
                                "ANCESTRY" :{ "$convert": { "input": { "$arrayElemAt": [{ "$split": [{ "$convert": { "input":{"$first":"$data.ANCESTRY"}, "to": "string"}}, "/"] },-1]}, "to": "int" ,"onError":0,"onNull": 0 }},
                                "GRADE":{"$first":"$data.GRADE"},
                                "SYLLABUS":{"$first":"$data.SYLLABUS"},
                                "SUBJECT":{"$first":"$data.SUBJECT"}}},
                    {"$lookup":
                    {
                        "from":"categories",
                        "localField":"ANCESTRY",
                        "foreignField":"ID",
                        "as":"data"
                        }
                    },
                    {"$project":{"search_doc_id":1,"question_id":1,
                                "difficulty":1,
                                "type":1,
                                "bloom":1,
                                "CATEGORY_NAME":1,
                                "CATEGORY_TYPE":1,
                                "GRADE":1,
                                "SYLLABUS":1,
                                "SUBJECT":1,
                                "CHAPTER_NAME":{"$first":"$data.NAME"},
                                "CHAPTER_TYPE":{"$first":"$data.TYPE"}
                            }},

                        {"$match":{"GRADE": grade, 
                            "SUBJECT":{"$in":subject_list},
                            "SYLLABUS": syllabus}},
                ])
            )
        )


        final_dict = {}
        if len(nearest_data) == 0:
            return {}
        
        keys_to_check = ['CHAPTER_NAME', 'difficulty', 'bloom', 'type']

        all_keys_exist = all(key in nearest_data for key in keys_to_check)
        if not all_keys_exist:
            return {}

        nearest_data = nearest_data[nearest_data['CHAPTER_NAME'].isin(chapters_list)]
        if len(nearest_data) == 0:
            return {}
        
        nearest_data.loc[:, 'difficulty'] = nearest_data['difficulty'].apply(lambda x: self.get_difficulty_value_for_qna(int(x)))
        final_dict["difficulty"] = nearest_data["difficulty"].value_counts().to_dict()
        final_dict["bloom"] = nearest_data["bloom"].value_counts().to_dict()
        final_dict["type"] = nearest_data["type"].value_counts().to_dict()

        return final_dict


    def get_difficulty_value_for_qna(self, x):
        '''
            Mapper function of Integer value to Difficulty Level
            Args:
                x: Integer
            Returns:
                String for difficulty level
        '''
        if x <= 1:
            return "Easy"
        elif x <= 3:
            return "Medium"
        else :
            return "Hard"
    
    def _get_clean_bloom_data(self, bloom_dic):

        knowledge_count, comprehension_count, application_count, analysing_count, \
        evaluting_count, creation_count = 0, 0, 0, 0, 0, 0
        knowledge_list = ['Knowledge', 'Remembering', 'knowledge', 'remembering', 'remember', 'Remember']
        comprehension_list = ['Comprehension', 'Understanding', 'comprehension', 'understanding', 'understand', 'Understanding']
        application_list = ['Application', 'Applying', 'Apply', 'application', 'applying', 'apply']
        analysing_list = ['Analysis', 'analysis', 'Analyzing', 'analyzing']
        evaluate_list = ['Evaluating', 'evaluating', 'Evaluate', 'evaluate']
        create_list = ['Creating', 'creating', 'Creat', 'creat']

        for bloom in bloom_dic.keys():
            if bloom in knowledge_list:
                knowledge_count = knowledge_count+ bloom_dic[bloom]
            elif bloom in comprehension_list:
                comprehension_count = comprehension_count+ bloom_dic[bloom]
            elif bloom in application_list:
                application_count = application_count+ bloom_dic[bloom]
            elif bloom in analysing_list:
                analysing_count = analysing_count+ bloom_dic[bloom]
            elif bloom in evaluate_list:
                evaluting_count = evaluting_count+ bloom_dic[bloom]
            else:
                creation_count = creation_count+ bloom_dic[bloom]


        return {'Knowledge':knowledge_count, 
                'Comprehension': comprehension_count, 
                'Application': application_count,
                'Analysing': analysing_count, 
                'Evaluation': evaluting_count,
                'Creation': creation_count}

        
    
    def _get_bloom_weights_from_db(self):
        """
        Updates self.bloom_avg_weight using blooms distribution of questions from the nearest school
        """
        if not self.top_schools_locations or self.school_q_counter < self.buffer_qns_count:
            qna_data = self.get_weight_from_qna(location=self.input_data['location'],
                                                 curriculum=self.input_data['curriculum'],
                                                 subject=self.input_data['subject'],
                                                 grade=self.input_data['grade'],
                                                 chapters=self.input_data['chapter'])
            self.qna_data = qna_data
            if qna_data == {}:
                self.source_tag = 'Pan India'
                self.top_schools_locations = []
                schools_nearby = self.schools_nearby
                bloom_percentages = {}
                total_count = 0
                for d in schools_nearby['bloom']:
                    total_questions = sum(d.values())
                    total_count += total_questions
                    bloom_data = self._get_clean_bloom_data(d)
                    for bloom_level in ['Knowledge', 'Comprehension', 'Application', 'Analysing', 'Evaluation', 'Creation']:
                        if bloom_level not in bloom_percentages:
                            bloom_percentages[bloom_level] = []
                        if bloom_level in bloom_data:
                            percentage = bloom_data[bloom_level] / total_questions
                            bloom_percentages[bloom_level].append(percentage)
                bloom_avg_weight = []
                for key, value in bloom_percentages.items():
                    if value:
                        bloom_avg_weight.append(((sum(value) / len(value))))
                self.bloom_avg_weight = bloom_avg_weight
                blooms_from_nearby_school = dict(zip(['Knowledge', 'Comprehension', 'Application', 'Analysing', 'Evaluation', 'Creation'],
                                                    [int(bloom * total_count) for bloom in bloom_avg_weight]))
                self.blooms_from_nearby_school = blooms_from_nearby_school

            elif qna_data and any(list(qna_data["bloom_data"].values())) and \
                    sum(qna_data['diff_number_dict'].values()) > self.buffer_qns_count:
                self.source_tag = 'QNA'
                self.top_schools_locations = []
                self.bloom_avg_weight = list(qna_data["bloom_data"].values())
                self.blooms_from_nearby_school = qna_data["bloom_number_dict"]

            else:
                self.source_tag = 'Pan India'
                self.top_schools_locations = []
                schools_nearby = self.schools_nearby
                bloom_percentages = {}
                total_count = 0
                for d in schools_nearby['bloom']:
                    total_questions = sum(d.values())
                    total_count += total_questions
                    bloom_data = self._get_clean_bloom_data(d)
                    for bloom_level in ['Knowledge', 'Comprehension', 'Application', 'Analysing', 'Evaluation', 'Creation']:
                        if bloom_level not in bloom_percentages:
                            bloom_percentages[bloom_level] = []
                        if bloom_level in bloom_data:
                            percentage = bloom_data[bloom_level] / total_questions
                            bloom_percentages[bloom_level].append(percentage)
                bloom_avg_weight = []
                for key, value in bloom_percentages.items():
                    if value:
                        bloom_avg_weight.append(((sum(value) / len(value))))
                self.bloom_avg_weight = bloom_avg_weight
                blooms_from_nearby_school = dict(zip(['Knowledge', 'Comprehension', 'Application', 'Analysing', 'Evaluation', 'Creation'],
                                                    [int(bloom * total_count) for bloom in bloom_avg_weight]))
                self.blooms_from_nearby_school = blooms_from_nearby_school

        else:
            self.source_tag = 'Nearby School'
            schools_nearby = self.schools_nearby
            bloom_percentages = {}
            total_count = 0
            for d in schools_nearby['bloom']:
                total_questions = sum(d.values())
                total_count += total_questions
                bloom_data = self._get_clean_bloom_data(d)
                for bloom_level in ['Knowledge', 'Comprehension', 'Application', 'Analysing', 'Evaluation', 'Creation']:
                    if bloom_level not in bloom_percentages:
                        bloom_percentages[bloom_level] = []
                    if bloom_level in bloom_data:
                        percentage = bloom_data[bloom_level] / total_questions
                        bloom_percentages[bloom_level].append(percentage)
            bloom_avg_weight = []
            for key, value in bloom_percentages.items():
                if value:
                    bloom_avg_weight.append(((sum(value) / len(value))))
            self.bloom_avg_weight = bloom_avg_weight
            self.blooms_from_nearby_school = dict(zip(['Knowledge', 'Comprehension', 'Application', 'Analysing', 'Evaluation', 'Creation'],
                                                  [int(bloom * total_count) for bloom in bloom_avg_weight]))


    def _get_question_type_weights_from_db(self):
        """
            Updates self.question_type_weights using distribution of questions from nearest school
        """
        if not self.top_schools_locations or self.school_q_counter < self.buffer_qns_count:
            qna_data = self.qna_data
            if self.source_tag == "QNA": 
                self.question_type_avg_weight = list(qna_data["ques_type_data"].values())
                self.question_types_from_school_nearby = qna_data["ques_type_number_dict"]
                
            else:
                schools_nearby = self.schools_nearby
                q_types = ["MC", "FITB", "VSA", "SA", "LA", "TF", "MTC", "GM"]
                percentages = {q_type: [] for q_type in q_types}
                ranges = {q_type: (0, 0) for q_type in q_types}

                total_count = 0
                for d in schools_nearby['type']:
                    total_count += sum(d.values()) 
                    for q_type in q_types:
                        if q_type in d.keys():
                            percentages[q_type].append(d[q_type] / sum(d.values()) * 100)
                            ranges[q_type] = (min(percentages[q_type]), max(percentages[q_type]))

                question_type_avg_weight = [(min(val) / 100) for val in ranges.values() if val]

                normalized_weights = [val / sum(question_type_avg_weight) for val in question_type_avg_weight]
                self.question_type_avg_weight = normalized_weights
                self.question_types_from_school_nearby = {q_types[i]: int(normalized_weights[i] * total_count) for i in range(len(q_types))}
                if sum(self.question_types_from_school_nearby.values()) < self.buffer_qns_count:
                    self.is_solvable = False
                
        else:
            q_types = ["MC", "FITB", "VSA", "SA", "LA", "TF", "MTC", "GM"]
            percentages = {q_type: [] for q_type in q_types}
            ranges = {q_type: (0, 0) for q_type in q_types}

            total_count = 0
            for d in self.schools_nearby['type']:
                total_count += sum(d.values()) 
                for q_type in q_types:
                    if q_type in d.keys():
                        percentages[q_type].append(d[q_type] / sum(d.values()) * 100)
                        ranges[q_type] = (min(percentages[q_type]), max(percentages[q_type]))

            question_type_avg_weight = [(min(val) / 100) for val in ranges.values() if val]

            normalized_weights = [val / sum(question_type_avg_weight) for val in question_type_avg_weight]
            self.question_type_avg_weight = normalized_weights
            self.question_types_from_school_nearby = {q_types[i]: int(normalized_weights[i] * total_count) for i in range(len(q_types))}

    def _get_chapter_weights(self):
        if self.schools_nearby:
            chapter_frequency = Counter(self.schools_nearby['chapter'])
            self.chapter_nearby = chapter_frequency

            total_chapters = len(self.schools_nearby['chapter'])

            chapter_weightage = {chapter: frequency / total_chapters for chapter, frequency in chapter_frequency.items()}
            self.chapter_weightage = chapter_weightage

    def _get_weights(self):
        self._get_nearby_schools_data()
        self._get_chapter_weights()
        self._get_bloom_weights_from_db()
        self._get_difficulty_weights_from_db()
        self._get_question_type_weights_from_db()
        bloom_weights = list(zip(list(self.blooms_from_nearby_school), self.bloom_avg_weight))
        difficulty_weights = list(zip(list(self.difficulty_from_school_nearby), self.diff_avg_weight))
        question_type_weights = list(zip(list(self.question_types_from_school_nearby), self.question_type_avg_weight))
        return bloom_weights, difficulty_weights, question_type_weights, self.chapter_weightage, self.blooms_from_nearby_school, self.difficulty_from_school_nearby, self.question_types_from_school_nearby, self.chapter_nearby


if __name__ == "__main__":
    client = MongoClient('mongodb://questiondb:d5a8c07f243ec9e54c18729a3bf91029d9250f1k@3.110.82.242:27017/questiondb')
    db = client['questiondb']
    city_school_question_tags_collection = db['city_school_question_tags_v2']
    city_school_location = db['city_school_location_v2']

    chapters = [
        "Cell Structure and Function",
        "Chemical Effects of Electric Current",
        "Coal and Petroleum",
        "Combustion and Flame",
    ]
    grade = "Standard VIII"
    subject = "Science"
    curriculum = "CBSE"
    latitude, longitude = 12.96614, 77.58694
    total_marks = 20

    input_data = {
        "location": {"latitude": latitude, "longitude": longitude},
        "subject": subject,
        "grade": grade,
        "chapter": chapters,
        "curriculum": curriculum,
        "total_marks": total_marks
    }
    weights_instance = Weights(city_school_question_tags_collection, city_school_location, input_data)
    bloom_weights, diff_weights, q_type_weights = weights_instance._get_weights()

