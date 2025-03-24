import json
import re
import sqlite3
import os
from rapt.rapt import Rapt
from datetime import datetime
from pyparsing import ParseException
print("sqlite3.sqlite_version is", sqlite3.sqlite_version)

class RA_AutoGrader:
    
    @staticmethod
    def custom_sort_key(item):
        # Define a priority order for sorting
        # Empty strings are placed last, numbers first, and strings in between
        if isinstance(item, int):
            return (0, item)
        elif item == '':
            return (2, None)  # Place empty strings at the end
        else:
            return (1, str(item))
        
    def __init__(self, database, schema_file, submission_file, answers_file, grammar_file, scores, disallowed_ops, required_ops):

        # Load the schema from the JSON file
        with open(schema_file) as f:
            self.schema = json.load(f)

        # Load the grammar from the JSON file
        with open(grammar_file) as f:
            self.grammar = json.load(f)

        # Load the content of the LaTeX file
        with open(submission_file, 'r') as f:
            self.submission = f.read()

        # Load the given solution SQL queries
        with open(answers_file, 'r') as f:
            self.solution = json.load(f)

        # Extract the answers and relational algebra expressions from the LaTeX file
        self.num_tests = len(self.solution)
        self.remove_comments()
        self.extract_answers()
        self.extract_RAs()

        self.rapt_instance = Rapt(self.schema, **self.grammar)
        self.conn = sqlite3.connect(database)

        self.scores = scores
        self.gradebook = [0] * self.num_tests # keep track of score for each question 
        self.disallowed_ops = disallowed_ops
        self.required_ops = required_ops

        self.time_stamp = datetime.now()
        self.num_passed = 0
        self.student_score = 0
        self.feedback = ""
        self.temp_tables = []
        self.temp_RAs = []
        self.temp_queries = []
    
    def outputFeedback(self, outfile):
        print(f"Passed {self.num_passed}/{self.num_tests} tests. Student Score: {self.student_score}")
        result = {
            "score": self.student_score,
            "max_score": self.scores,
            "output": f"Passed {self.num_passed}/{self.num_tests} tests. Student Score: {self.student_score}.  \n  \n  Feedback:  \n  {self.feedback}"
        }
        
        with open(outfile, 'w') as f:
            json.dump(result, f)
    

    # Remove comments
    def remove_comments(self):
        self.submission_lines = self.submission.split('\n')
        self.comments = [line for line in self.submission_lines if line.strip().startswith('%')]
        self.submission = "\n".join([line for line in self.submission_lines if not line.strip().startswith('%')])

    # Extracting the answers from the LaTeX file
    # This relies on the latex file having the \textbf{Answer:} tag when starting each answer and \vspace{15 mm} tag at the end of all questions
    # The answers are extracted by finding the text between the \question tags
    def extract_answers(self):
        # self.answers = re.findall(r'(\\question\s+.*?)(?=\\question|\\end\{questions\})', self.submission, re.DOTALL)
        self.answers = re.findall(r'\\textbf{Answer:}(.+?)\\vspace{15 mm}', self.submission, re.DOTALL)
    
    # Extracting the relational algebra expressions from the answers
    # This relies on each Relational Algebra expressino being enclosed in $ signs
    # The expressions are extracted by finding the text between the $ signs
    def extract_RAs(self):
        self.expressions = []
        for answer in self.answers:
            self.expressions.append(re.findall(r'\$(.*?)\$', answer, re.DOTALL))
    
    # Cleaning the relational algebra expression to match the parsing syntax of RAPT
    def cleanLatex(self, RA):
    
        # Eliminating spaces before and after the underscores
        RA = re.sub(r'\s+_', '_', RA)
        RA = re.sub(r'_\s+', '_', RA)

        # Spacing out all the operators for parsing
        op_pattern = r'(\\(?!_)\w+)' # Matches all words beginning with a backslash that are not followed by an underscore
        RA = re.sub(op_pattern, r' \1', RA)

        # Removing the text tag from the attributes
        text_pattern = r'\\text\{(.*?)\}'
        RA = re.sub(text_pattern, r'\1', RA)

        # Replacing the operator representations with the actual operators recognised by RAPT
        operator_reps = {
        'Join_' : ' theta_',
        'Join': ' bowtie ',
        'bowtie_' : ' theta_',
        'leftouterjoin_' : ' lojc_',
        'rightouterjoin_' : ' rojc_',
        'fullouterjoin_' : ' fojc_',
        'leq' : ' <= ',
        'geq' : ' >= ',
        'neq': ' != ',
        ':' : ' = ',
        "*" : " times ",
        "wedge" : " and ",
        'land' : ' and ',
        'lor' : ' or ',
        'SetDiff': ' - ',
        'left(': '(',
        'right)': ')',
        'left[': '[',
        'right]': ']',
        'left{': '{',
        'right}': '}',
        }

        for op, rep in operator_reps.items():
            RA = RA.replace(op, rep)

        # Surrounding rename attributes with parantheses
        # Define the callback function for substitution
        def add_parentheses_if_needed(match):
            content = match.group(1)
            if '(' in content and ')' in content:
                return f'\\rho_{{{content}}}'
            else:
                return f'\\rho_{{({content})}}'
            
        rho_pattern = r'\\rho_\{(.*?)\}'
        RA = re.sub(rho_pattern, add_parentheses_if_needed, RA)
        
        # Remove all the commas, semicolons and newlines
        RA = RA.replace(r'\,' , '')
        RA = RA.replace(r'\; ', '')
        RA = RA.replace('\\', '')
        RA = RA.replace('\n', '')
        RA += ";"

        # Check if the RA is an assignment expression and add it to the temp_tables list
        if "leftarrow" in RA:
            self.temp_tables.append(RA.split("leftarrow")[0].strip().lower())

        return RA

    def toSQL(self, expressions):
        try:
            sql = self.rapt_instance.batch_to_sql(expressions, self.schema)
            return sql
        except Exception as e:
            raise

    def executeSQL(self, queries):
        con_out = None
        try:
            for query in queries:
                query = query.strip()
                con_out = self.conn.execute(query)
        except sqlite3.Error as e:
            raise
        
        if con_out:
            return con_out.fetchall()
        else:
            return []
        
    def checkDisallowedOps(self, RAs, test_num):
        for RA in RAs:
            for op in self.disallowed_ops[test_num-1]:
                if op in RA:
                    return False
        return True

    def checkRequiredOps(self, RAs, test_num):
        if not self.required_ops[test_num-1]:
            return True
        for op in self.required_ops[test_num-1]:
            for RA in RAs:
                if op in RA:
                    return True
        return False

    def executeTest(self, ra, expected_sql, test_num, expr_num):
        try:
            cleaned_ra = ""
            actual_sql = ""
            cleaned_ra = self.cleanLatex(ra)
            self.temp_RAs.append(cleaned_ra)
            actual_sql = self.toSQL([cleaned_ra])
            self.rawsql.append(actual_sql)
            # Surrounding order and order-table with double quotes
            pattern = r'\b(order-product)\b'
            actual_sql[0] = re.sub(pattern, r'"\1"', actual_sql[0])
            pattern = r'(?<!")\b(order)(?!-)\b'
            actual_sql[0] = re.sub(pattern, r'"\1"', actual_sql[0])
            pattern = r'(?<!")order-product(?!")'
            actual_sql[0] = re.sub(pattern, 'op', actual_sql[0])
            self.temp_queries.append(actual_sql)
            actual_result = sorted(self.executeSQL(actual_sql), key = self.custom_sort_key)

            if expected_sql:

                expected_sql = [expected_sql]
                if test_num == 8:
                    greater_query = ["SELECT DISTINCT a1.agent_id AS agent1_id, a1.first AS agent1_first, a1.last AS agent1_last, a2.agent_id AS agent2_id, a2.first AS agent2_first, a2.last AS agent2_last, aff.title AS affiliation, a1.clearance_id FROM affiliationrel ar1 JOIN affiliationrel ar2 ON ar1.aff_id = ar2.aff_id AND ar1.agent_id > ar2.agent_id JOIN agent a1 ON ar1.agent_id = a1.agent_id JOIN agent a2 ON ar2.agent_id = a2.agent_id AND a1.clearance_id = a2.clearance_id JOIN affiliation aff ON ar1.aff_id = aff.aff_id;"]
                    lesser_query = ["SELECT DISTINCT a1.agent_id AS agent1_id, a1.first AS agent1_first, a1.last AS agent1_last, a2.agent_id AS agent2_id, a2.first AS agent2_first, a2.last AS agent2_last, aff.title AS affiliation, a1.clearance_id FROM affiliationrel ar1 JOIN affiliationrel ar2 ON ar1.aff_id = ar2.aff_id AND ar1.agent_id < ar2.agent_id JOIN agent a1 ON ar1.agent_id = a1.agent_id JOIN agent a2 ON ar2.agent_id = a2.agent_id AND a1.clearance_id = a2.clearance_id JOIN affiliation aff ON ar1.aff_id = aff.aff_id;"]
                    expected_sql.append(greater_query)
                    expected_sql.append(lesser_query)
                
                correct = False
                for exp_sql in expected_sql:
                    expected_result = sorted(self.executeSQL(exp_sql), key=self.custom_sort_key)
                    if expected_result == []:
                            print("Empty Expected Results")
                    if actual_result == []:
                        self.feedback += f"Your final results are empty.\nPlease don't forget to state the intermediate relation that holds your final output as your last RA expression.\n"
                        print(f"\033[91mYour final results are empty.\nPlease don't forget to state the intermediate relation that holds your final output as your last RA expression.\033[0m")
                    # Compare the actual and expected results
                    if expected_result == actual_result:
                        correct = True
                        if self.checkDisallowedOps(self.temp_RAs, test_num) and self.checkRequiredOps(self.temp_RAs, test_num):
                            self.num_passed += 1
                            self.student_score += self.scores[test_num-1]
                            self.feedback += f"Correct\n"
                            print(f"\033[92mCorrect\033[0m")
                        else:
                            self.feedback += f"Used disallowed operator/s OR did not use required operator/s\n"
                            print(f"\033[91mUsed disallowed operator/s OR did not use required operator/s\033[0m")
                        break
                if not correct:
                    self.feedback += f"Incorrect\n"
                    print(f"\033[91mIncorrect\033[0m")  
                     
             
        except Exception as e:
            
            if isinstance(e, ParseException):
                self.feedback += f"LaTex Syntax Error in RA Expression #{expr_num} at char {e.loc}\n"
                print(f"\033[91mLaTex Syntax Error in RA Expression #{expr_num} at char {e.loc}\033[0m")
                if e.col:
                    self.feedback += f"{cleaned_ra[:e.col]}\u2C7D{cleaned_ra[e.col:]}\n"
                    print(f"{cleaned_ra[:e.col]}\033[91m\u2C7D\033[0m{cleaned_ra[e.col:]}")
            else:
                self.feedback += f"Error in RA Expression #{expr_num}: {ra}\n{e}\n"
                print(f"\033[91mError in RA Expression #{expr_num}: {ra}\n{e}\033[0m")
                
            # self.feedback += f"Question {test_num}: Could not run query\n{e}\n"
            # for temp_ra, temp_query in zip(self.temp_RAs, self.temp_queries):
            #     print(f"Cleaned RA Expression: {temp_ra}")
            #     print(f"Converted SQL query: {temp_query}")
            #     print('-'*100)
            # if cleaned_ra and cleaned_ra != temp_ra[-1]:
            #     print(f"Cleaned RA Expression: {cleaned_ra}")
            # if actual_sql and actual_sql != temp_query[-1]:
            #     print(f"Converted SQL query: {actual_sql}")
            raise

    def cleanUp(self):
        # Delete entries in schema whose keys are in self.temp_tables
        for table in self.temp_tables:
            try:
                self.conn.execute(f"DROP TABLE {table};")
            except sqlite3.Error as e: 
                pass
            if table in self.schema:
                del self.schema[table]
        self.temp_tables = []
        self.temp_RAs = []
        self.temp_queries = []

    # Driver function to test all the relational algebra expressions
    def test_all(self):
        for RAs, expected_sql, i in zip(self.expressions[:], self.solution[:], range(1, self.num_tests+1)):
            # if i == 2:
            #     print("Debugging")
            #     # continue
            print(f"Question {i}")
            self.feedback += f"Question {i}\n"
            self.rawsql = []
            if not RAs:
                print(f"\033[93mNo RA expressions found \033[0m")
                self.feedback += f"No RA expressions found\n"
            try:
                # Translate and execute the intermediate RA expressions
                for expr_num, RA in enumerate(RAs[:]):
                   
                    if expr_num == len(RAs) - 1:
                        # Translate and execute the last RA expression, and compare the result with the expected SQL query output
                        self.executeTest(RA, expected_sql, i, expr_num+1)
                    else:
                        # Translate and execute the intermediate RA expressions
                        self.executeTest(RA, "", i, expr_num+1)
                
            except Exception as e:
                self.feedback += '-'*100 + '\n' + "Converted Raw SQL queries for the parsed RA expressions:\n" + "\n".join(map(str, self.rawsql)) + '\n' + '-'*100 + '\n'
                self.cleanUp()
                continue
            self.feedback += '-'*100 + '\n' + "Converted Raw SQL queries for the parsed RA expressions:\n" + "\n".join(map(str, self.rawsql)) + '\n' + '-'*100 + '\n'
            self.cleanUp()



if __name__ == '__main__':
    # Spring 2025
    # Replace the test_dir with the path to the directory containing the submission.tex, solution.json, and grammar.json files
    test_dir = os.path.abspath("./")
    submission_dir = os.path.abspath("../submission/")
    output_dir = "/autograder/results/"

    database = os.path.join(test_dir, "spy.db")
    schema_file = os.path.join(test_dir, "spySchema.json")
    scores = [6, 6, 6, 6, 8, 6, 8, 9, 10]
    disallowed_ops = [["theta_", "times"],["bowtie", "theta_"],["bowtie", "times"],[],[],[],[],[],[]]
    requried_ops = [["bowtie"],["times"],["theta_"],["cup","cap","-"],["-","cap","cup"],[],[],[],[]]
    
    subs = os.listdir(submission_dir)
    tex = [f for f in subs if f.endswith(".tex")]
    if not tex:
        print("Warning: Please submit a .tex file. (Latex source file)")
        tex = subs
    
    submission_file = os.path.join(submission_dir, tex[0])
    answers_file = os.path.join(test_dir, "solution.json")
    grammar_file = os.path.join(test_dir, "grammar.json")
    output_file = os.path.join(output_dir, "results.json")
    grader = RA_AutoGrader(database, schema_file, submission_file, answers_file, grammar_file, scores, disallowed_ops, requried_ops)
    
    grader.test_all()
    grader.outputFeedback(output_file)