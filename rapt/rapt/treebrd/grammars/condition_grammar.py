from pyparsing import oneOf, CaselessKeyword, operatorPrecedence, opAssoc

from .proto_grammar import ProtoGrammar
from .syntax import Syntax

# TODO: Add schema as a parameter to the get_attribute_references function and modify its uses
def get_attribute_references(instring):
    """
    Return a list of attribute references in the condition expression.

    attribute_reference ::= relation_name "." attribute_name | attribute_name

    :param instring: a condition expression.
    :return: a list of attribute references.
    """
    parsed = ConditionGrammar().conditions.parseString(instring)
    result = parsed if isinstance(parsed[0], str) else parsed[0]
    return result.attribute_reference.asList() if result.attribute_reference else []


class ConditionGrammar(ProtoGrammar):
    """
    A grammar for condition expressions.
    """

    def __init__(self, schema=None, syntax=None):
        """
        Initializes a ConditionGrammar. Uses the default syntax if none
        is provided.

        :param syntax: a syntax for this grammar.
        """
        if not schema:
            schema = {}
        super().__init__(schema, syntax or Syntax())
        #self.syntax = syntax or Syntax()
    

    @property
    def comparator_op(self):
        return oneOf([self.syntax.equal_op,
                      self.syntax.not_equal_op,
                      self.syntax.not_equal_alt_op,
                      self.syntax.less_than_op,
                      self.syntax.less_than_equal_op,
                      self.syntax.greater_than_op,
                      self.syntax.greater_than_equal_op])

    @property
    def not_op(self):
        return CaselessKeyword(self.syntax.not_op)

    @property
    def logical_binary_op(self):
        """
        logical_binary_op ::=  and_op | or_op
        """
        return (CaselessKeyword(self.syntax.and_op) |
                CaselessKeyword(self.syntax.or_op))

    @property
    def operand(self):
        """
        operand ::= identifier | string_literal | number
        """
        return (self.attribute_reference('attribute_reference*') |
                self.string_literal |
                self.number)

    @property
    def condition(self):
        """
        condition ::= operand comparator_op operand | not_op condition |
                  paren_left condition paren_right
        not_op and grouping rules are defined using operatorPrecedence in
        conditions.
        """
        return self.operand + self.comparator_op + self.operand

    @property
    def conditions(self):
        """
        conditions ::= condition | condition logical_binary_op conditions
        Note: By default lpar and rpar arguments are suppressed.
        """
        return operatorPrecedence(
            baseExpr=self.condition,
            opList=[(self.not_op, 1, opAssoc.RIGHT),
                    (self.logical_binary_op, 2, opAssoc.LEFT)],
            lpar=self.syntax.paren_left,
            rpar=self.syntax.paren_right)