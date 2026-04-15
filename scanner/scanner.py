from functools import reduce
from scanner.abstract_regex_tree import Regex, Union
from specification.token import Token

class Scanner:
    def __init__(self, token_register):
        self.tokens = token_register.get_tokens()
        # TODO: investigate: non-disjoint token overlaps

        # build master regex
        self.regex = reduce(Union, [ast for _, ast in self.tokens])
        self.nfa = self.regex.to_nfa()

        # determine which final states correspond to the recognition of which token type
        self.exclusive_final_states = []
        remaining_final_states = set(self.nfa.final_states)

        for token, ast in self.tokens:
            final_states = (ast.last | ({ast} if ast.empty else set())) & remaining_final_states
            self.exclusive_final_states.append((token, final_states))
            remaining_final_states -= final_states

    def recognized_token(self, reached_final_states):
        for name, exclusive_final_states in self.exclusive_final_states:
            if reached_final_states & exclusive_final_states:
                return name
        return None

    def scan(self, input_string):
        line = 0
        start_position = 0
        while start_position < len(input_string):
            current_states = self.nfa.start_states
            reached_final_states = None
            end_start_position_of_match = None

            # scan as far as possible, while keeping track possible matches
            scan_position = start_position
            while scan_position < len(input_string):
                symbol = input_string[scan_position]
                current_states = self.nfa.transition(current_states, symbol)

                # as soon as a transition leads to an error state, stop
                if not current_states:
                    break

                if current_states & self.nfa.final_states:
                    reached_final_states = current_states
                    end_start_position_of_match = scan_position + 1

                scan_position += 1

            if end_start_position_of_match is not None:
                name = self.recognized_token(reached_final_states)
                value = input_string[start_position:end_start_position_of_match]
                yield Token(name, value)
                start_position = end_start_position_of_match
            else:
                # TODO: implement practical error messages
                raise ValueError(f"Lexical error at {start_position}: '{input_string[start_position]}'")
                start_position += 1

        # TODO: abstraction for EOF token
        yield Token("$")

    def scan_file(self, file_name, encoding="utf-8"):
        with open(file_name, "r", encoding=encoding) as file:
            text = file.read()
            for token in self.scan(text):
                yield token
            