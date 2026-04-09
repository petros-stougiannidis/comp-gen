import os
import graphviz
import tempfile

class NFA:
    def __init__(self, start_states, final_states, transitions):
        self.start_states = start_states
        self.final_states = final_states
        self.transitions = transitions

    def transition(self, current_states, symbol):
        result = set()
        for state in current_states:
            for symbol_set, destination_states in self.transitions[state].items():
                if symbol in symbol_set:  # check membership
                    result |= destination_states  # use the destination_states directly
                    break
        return result

    def accepts(self, word):
        current_states = self.start_states
        for s in word:
            current_states = self.transition(current_states, s)
        return any(state in self.final_states for state in current_states)

    def generatePDF(self):

        def shape_of(state):
            return 'doublecircle' if state in self.final_states else 'circle'

        automaton = graphviz.Digraph("nfa") 
        automaton.graph_attr['rankdir'] = 'LR'
        
        for source_state, transitions in self.transitions.items():
            automaton.node(repr(source_state), repr(source_state), shape=shape_of(source_state))
            for symbol, destination_states in transitions.items():
                for state in destination_states:
                    automaton.node(repr(state), shape=shape_of(state))
                    automaton.edge(repr(source_state), repr(state), label=repr(symbol))

        anchor_of_arrows_leading_to_start_states = {
            'shape': 'point',    # use 'point' for invisible anchor nodes
            'width': '0',        # corrected spelling
            'height': '0',
            'label': ''
        }

        automaton.attr('node', **anchor_of_arrows_leading_to_start_states)

        for state in self.start_states:
            automaton.node("start" + repr(state))
            automaton.edge("start" + repr(state), repr(state))


        pdf_bytes = automaton.pipe(format='pdf')
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_bytes)
            tmp.flush()
            os.system(f"wslview {tmp.name}")