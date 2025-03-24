from pyparsing import *

from .core_grammar import CoreGrammar


class ExtendedGrammar(CoreGrammar):
    """
    A parser that recognizes an extended relational algebra grammar.

    The rules are annotated with their BNF equivalents. For a complete
    specification refer to the associated grammar file.
    """

    """
    Support for Right/Left/Full Outer Joins added later
    """
    @property
    def left_outer_join(self):
        """
        left_outer_join_expr ::= expression left_outer_join expression
        """
        return CaselessKeyword(self.syntax.leftouter_join_op)
    
    @property
    def right_outer_join(self):
        """
        right_outer_join_expr ::= expression right_outer_join expression
        """
        return CaselessKeyword(self.syntax.rightouter_join_op)
    
    @property
    def full_outer_join(self):
        """
        full_outer_join_expr ::= expression full_outer_join expression
        """
        return CaselessKeyword(self.syntax.fullouter_join_op)
    
    @property
    def natural_join(self):
        """
        natural_join_expr ::= expression natural_join expression
        """
        return CaselessKeyword(self.syntax.natural_join_op)


    @property
    def theta_join(self):
        """
        select_expr ::= select param_start conditions param_stop expression
        """
        long = self.parametrize(self.syntax.theta_join_op, self.conditions)
        short = self.parametrize(self.syntax.join_op, self.conditions).\
            setParseAction(self.theta_parse_action)
        return long ^ short

    def theta_parse_action(self, s, l, t):
        t[0] = self.syntax.theta_join_op
        return t

    @property
    def theta_right_outer_join(self):
        """
        select_expr ::= select param_start conditions param_stop expression
        """
        return self.parametrize(self.syntax.theta_rightouter_join_op, self.conditions)

    @property
    def theta_left_outer_join(self):
        """
        select_expr ::= select param_start conditions param_stop expression
        """
        return self.parametrize(self.syntax.theta_leftouter_join_op, self.conditions)
    
    @property
    def theta_full_outer_join(self):
        """
        select_expr ::= select param_start conditions param_stop expression
        """
        return self.parametrize(self.syntax.theta_fullouter_join_op, self.conditions)

    @property
    def binary_op_p1(self):
        return super().binary_op_p1 ^ self.natural_join ^ self.theta_join \
            ^ self.left_outer_join ^ self.right_outer_join ^ self.full_outer_join ^\
            self.theta_right_outer_join ^ self.theta_left_outer_join ^ self.theta_full_outer_join

    @property
    def intersect(self):
        """
        intersect_op ::= intersect_name
        """
        return CaselessKeyword(self.syntax.intersect_op)

    @property
    def expression(self):
        return operatorPrecedence(self.relation, [
            (self.unary_op, 1, opAssoc.RIGHT),
            (self.binary_op_p1, 2, opAssoc.LEFT),
            (self.intersect, 2, opAssoc.LEFT),
            (self.binary_op_p2, 2, opAssoc.LEFT)])

    def is_unary(self, operator):
        return operator in {self.syntax.select_op,
                            self.syntax.project_op,
                            self.syntax.rename_op}

    def is_binary(self, operator):
        return (operator in {self.syntax.intersect_op,
                             self.syntax.natural_join_op,
                             self.syntax.theta_join_op,
                             self.syntax.leftouter_join_op,
                             self.syntax.rightouter_join_op,
                             self.syntax.fullouter_join_op,
                             self.syntax.theta_rightouter_join_op,
                             self.syntax.theta_leftouter_join_op,
                             self.syntax.theta_fullouter_join_op} or
                super().is_binary(operator))