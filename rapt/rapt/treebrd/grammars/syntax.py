class Syntax:

    def __init__(self, **kwargs):

        # First initialize a default syntax.

        # General tokens.
        self.terminator = ';'
        self.delim = ','
        self.params_start = '_{'
        self.params_stop = '}'
        self.paren_left = '('
        self.paren_right = ')'

        # Logical tokens.
        self.not_op = 'not'
        self.and_op = 'and'
        self.or_op = 'or'

        # Comparison operators.
        self.equal_op = '='
        self.not_equal_op = '!='
        self.not_equal_alt_op = '<>'
        self.less_than_op = '<'
        self.less_than_equal_op = '<='
        self.greater_than_op = '>'
        self.greater_than_equal_op = '>='

        # Relational algebra operators.
        self.project_op = 'pi'
        self.rename_op = 'rho'
        self.select_op = 'sigma'
        self.assign_op = 'leftarrow'
        self.join_op = 'times'
        self.theta_join_op = 'theta'
        self.natural_join_op = 'bowtie'
        self.difference_op = '-'
        self.union_op = 'cup'
        self.intersect_op = 'cap'

        # Left/Right/Full outer join operators.
        self.leftouter_join_op = 'leftouterjoin'
        self.rightouter_join_op = 'rightouterjoin'
        self.fullouter_join_op = 'fullouterjoin'
        self.theta_leftouter_join_op = 'lojc'
        self.theta_rightouter_join_op = 'rojc'
        self.theta_fullouter_join_op = 'fojc'

        # Now set any user defined syntax.
        for key in kwargs:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])