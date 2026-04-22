from specification.token import TokenRegistry
from lexer.lexer import Lexer
from specification.grammar import Grammar
from parser.lr1 import LR1Parser
from visualization.graph import render_nfa

# TODO: implement parsing of parser actions
# TODO: investigate right workings of escaping mechanisms
class LR1GrammarParser:
    
    def __init__(self):

        grammar_tokens = TokenRegistry()

        grammar_tokens.register("WHITESPACE", r"\s+")
        grammar_tokens.register("ARROW", r"\->")
        grammar_tokens.register("PIPE", r"\|")
        grammar_tokens.register("SEMI", r";")
        grammar_tokens.register("ACTION", r"{[^{}]*}")
        grammar_tokens.register("ESCAPED", r"\\.")
        grammar_tokens.register("SYMBOL", r"[^\s\|;{}]+")
    
        self.lexer = Lexer(grammar_tokens)

        productions = {}

        productions["production_list"] = {
            ("production", "production_list"): lambda c: c[0] | c[1], # unify dictionaries representing lefthandside->(righthandside->action)
            tuple(): lambda c: {} # base case: empty dictionary
        }

        productions["production"] = {
            ("lhs", "ARROW", "rhs_list", "SEMI"): lambda c: {c[0]: c[2]} # single entry dictionary lefthandside->(righthandside->action)
        }

        productions["lhs"] = {
            ("SYMBOL",): lambda c: c[0] # string representing scanend token value
        }

        productions["rhs_list"] = {
            ("rhs", "PIPE", "rhs_list"): lambda c: {c[0][0]:c[0][1]} | c[2], # unify dictionaries representing righthandsides->action
            ("rhs",): lambda c: {c[0][0]:c[0][1]}, # single entry dictionary righthandside->actions
        }

        productions["rhs"] = {
            ("symbol_seq", "ACTION"): lambda c: (tuple(c[0]), c[1]), # wrap into tuple in order to access symbol sequence and corresponding action
            ("symbol_seq",): lambda c: (tuple(c[0]), None),
        }

        productions["symbol_seq"] = {
            ("SYMBOL", "symbol_seq"): lambda c: [c[0]] + c[1], #wrap into list for concatenation into ssequence of symbols
            ("ESCAPED", "symbol_seq"): lambda c: [c[0][1]] + c[1], #wrap into list for concatenation into ssequence of symbols
            tuple(): lambda c: [], # base case: empty list
        }

        grammar = Grammar(start_symbol="production_list", productions=productions, terminals=grammar_tokens.get_names())
        self.parser = LR1Parser(grammar)

    def parse_file(self, file_path):

        token_stream = (token for token in self.lexer.scan_file(file_path) if token.type != "WHITESPACE")
        accepted, stack = self.parser.parse(token_stream)
        return stack[0] if accepted else None