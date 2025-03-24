from pyparsing import (alphanums, Regex, Word, alphas, quotedString,
                       removeQuotes, Combine, Optional, downcaseTokens, ParserElement,
                         MatchFirst, CaselessKeyword, Suppress, oneOf, Group, Keyword, OneOrMore)

ParserElement.enablePackrat()


class ProtoGrammar:
    """
    A grammar with fundamental rules for characters, strings, and
    numbers.

    The rules are annotated with their BNF equivalents. For a complete
    specification refer to the associated grammar file.
    """
    def __init__(self, schema, syntax):
        """
        Initializes a ProtoGrammar. Uses the provided schema to infer reserved keywords.

        :param schema: a schema for the relational algebra.
        """
        self.schema = schema
        self.syntax = syntax
        
    
    def parse(self, instring):
        """
        Defined by descendants.
        :param instring: A string to parse.
        """
        raise NotImplementedError

    @property
    def character(self):
        """
        character ::= letter | digit | "_"
        """
        return alphanums + '_' + '-'

    @property
    def number(self):
        """
        number ::= float | integer | natural_number
        """
        return Regex(r'[-+]?[0-9]*\.?[0-9]+')

    @property
    def string_literal(self):
        """
        string_literal ::= "'" string "'" | "\"" string "\""

        Any successful match is converted to a single quoted string to simplify
        post-parsed operations.
        """
        return quotedString.setParseAction(
            lambda s, l, t: "'{string}'".format(string=removeQuotes(s, l, t)))
    
    @property
    def identifier(self):
        """
        identifier ::= letter | letter string
        """
        word = Word(alphas, self.character).setParseAction(downcaseTokens)
        return word
    
    @property
    def reserved_words(self):
        """
        reserved_words ::= schema keys | syntax keys
        """
        # Reserved words like relation names and grammar keywords cannot be used as alias
        reserved = self.schema.keys() | self.syntax.__dict__.values()
        reserved_list = [CaselessKeyword(words) for words in reserved]
        reserved_list.extend([CaselessKeyword(words+"_") for words in self.syntax.__dict__.values()])
        
        return MatchFirst(reserved_list).setParseAction(downcaseTokens)
    
    @property
    def alias_identifier(self):
        """
        alias_identifier ::= Any words not in schema [and syntax To be implemented]
        """
        # Aliad idenitfier cannot be a reserved word
        alias_identifier = ~self.reserved_words + self.identifier
        return alias_identifier.setParseAction(downcaseTokens)
    
    # @property
    # def alias_relation_name(self):
    #     """
    #     alias_relation_name ::= [relation] non reserved words
    #     """
    #     alias = Suppress(self.relation_name) + self.non_reserved_word
    #     return alias.setParseAction(downcaseTokens)
    
    @property
    def relation_name(self):
        """
        relation_name ::= identifier | identifier identifier
        """
        #return self.identifier
        relation = MatchFirst([CaselessKeyword(rel_name) for rel_name in self.schema.keys()]).setParseAction(downcaseTokens)
        # alias = relation + self.alias_identifier
        return Group(relation + Optional(self.alias_identifier))
        return self.relation
        return self.identifier | self.alias_relation_name
        return self.reserved_words | self.reserved_words + self.identifier
       

    @property
    def attribute_name(self):
        """
        attribute_name ::= identifier
        """
        return self.identifier

    @property
    def attribute_reference(self):
        """
        attribute_reference ::= relation_name "." attribute_name |
        attribute_name
        """
        return Combine((Optional(self.identifier + '.') +
                        self.attribute_name))
