from functools import reduce
from scanner.abstract_regex_tree import Regex, Union
from specification.token import Token

class Scanner:
    def __init__(self):
        self.tokens = Token.get_registry()

        self.regex = reduce(Union, [token["ast"] for token in self.tokens])
        self.nfa = self.regex.to_nfa()

        self.exclusive_final_states = []
        remaining_final_states = set(self.nfa.final_states)

        for token in self.tokens:
            ast = token["ast"]
            final_states = (ast.last | ({ast} if ast.empty else set())) & remaining_final_states
            self.exclusive_final_states.append((token["name"], final_states))
            remaining_final_states -= final_states

    def token_type_of(self, reachedFinalStates):
        for name, exclusive_final_states in self.exclusive_final_states:
            if reachedFinalStates & exclusive_final_states:
                return name
        return None

    def scan(self, text):
        position = 0
        while position < len(text):
            current_states = self.nfa.start_states
            reached_final_states = None
            end_position_of_match = None

            i = position
            while i < len(text):
                current_states = self.nfa.transition(current_states, text[i])

                if not current_states:
                    break

                if any(state in self.nfa.final_states for state in current_states):
                    reached_final_states = current_states
                    end_position_of_match = i + 1

                i += 1

            if end_position_of_match is not None:
                name = self.token_type_of(reached_final_states)
                value = text[position:end_position_of_match]
                yield Token(name, value)
                position = end_position_of_match
            else:
                yield Token(None, text[position])
                position += 1
        yield Token("$", "$")

    def scan_file(self, file_name, encoding="utf-8"):
        with open(file_name, "r", encoding=encoding) as file:
            text = file.read()
            for token in self.scan(text):
                yield token
            