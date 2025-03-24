import sys
# sys.path.insert(0, '/Users/jeegndani/Library/CloudStorage/OneDrive-purdue.edu/CS348_RA_Autograder/RAGrading2024/RA_Autograder/rapt/rapt/')
# print(sys.path)

from .treebrd.grammars import CoreGrammar, GRAMMARS
from .treebrd.grammars.syntax import Syntax
from .treebrd.treebrd import TreeBRD
from .transformers.sql import sql_translator
from .transformers.qtree import qtree_translator


class Rapt:
    @staticmethod
    def configure_grammar(schema, **config):
        syntax = Syntax(**config.get('syntax', {}))
        grammar_class_name = config.get('grammar', 'Core Grammar')
        grammar_class = GRAMMARS.get(grammar_class_name, CoreGrammar)
        return grammar_class(schema, syntax)

    def __init__(self, schema, **config):
        grammar = self.configure_grammar(schema, **config)
        self.builder = TreeBRD(grammar)

    def to_syntax_tree(self, instring, schema):
        """
        Return a list of syntax trees that represent the instring.

        :param instring: a relational algebra string
        :param schema: a schema for the string
        :return: a list of syntax trees
        """
        return self.builder.build(instring, schema)

    def to_sql(self, instring, schema, use_bag_semantics=False):
        """
        Translate a relational algebra string into a SQL string.

        :param instring: a relational algebra string to translate
        :param schema: a mapping of relation names to their attributes
        :param use_bag_semantics: flag for using relational algebra bag semantics
        :return: a SQL translation string
        """
        root_list = self.to_syntax_tree(instring, schema)
        return sql_translator.translate(root_list, use_bag_semantics)

    def batch_to_sql(self, instrings, schema, use_bag_semantics=False):
        """
        Translate multiple relational algebra strings into a list of SQL strings.

        :param instring: a list of relational algebra string to translate
        :param schema: a mapping of relation names to their attributes
        :param use_bag_semantics: flag for using relational algebra bag semantics
        :return: a list of SQL translation strings
        """
        sql_statements = []
        for instring in instrings:
            root_list = self.to_syntax_tree(instring, schema)
            sql_statement = sql_translator.translate(root_list, use_bag_semantics)
            sql_statements.append(sql_statement[0])
        return sql_statements
    
    def to_sql_sequence(self, instring, schema, use_bag_semantics=False):
        """
        Translate a relational algebra string into a list of SQL strings generated
        by a post-order traversal of the parse tree for the input string.

        :param instring: a relational algebra string to translate
        :param schema: a mapping of relation names to their attributes
        :param use_bag_semantics: flag for using relational algebra bag semantics
        :return: a list of SQL translation strings
        """
        root_list = self.to_syntax_tree(instring, schema)
        return [
            sql_translator.translate(root.post_order(), use_bag_semantics)
            for root in root_list
        ]

    def to_qtree(self, instring, schema):
        """
        Translate a relational algebra string into a string representing a
        latex tree, using the grammar.
        """
        root_list = self.to_syntax_tree(instring, schema)
        return qtree_translator.translate(root_list)