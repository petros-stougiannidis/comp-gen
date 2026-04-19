import graphviz
import tempfile
import os
from formatting.print import pretty_set

def render_lr1(lr1_automaton):
        def content_of(state):
            lines = [f"State: {state.id}"]
            for item in state:
                lines.append(str(item))
            return "\n".join(lines)

        automaton = graphviz.Digraph("LR1")
        automaton.graph_attr['rankdir'] = 'LR'

        for state in lr1_automaton.states:
            automaton.node(
                name=f"{state.id}",
                label=content_of(state),
                shape='box',
                style='filled' if state.is_final() else '',
                fillcolor='lightgreen' if state.is_final() else None,
                peripheries="2" if state.is_final() else "1"
            )
        
        for (source_state, symbol), target_state in lr1_automaton.transitions.items():
            
            automaton.edge(
                f"{source_state.id}",
                f"{target_state.id}",
                label=str(symbol)
            )

        automaton.node("start", shape="point", width="0")
        automaton.edge("start", f"{lr1_automaton.start_state.id}")

        pdf_bytes = automaton.pipe(format='pdf')

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_bytes)
            tmp.flush()
            os.system(f"wslview {tmp.name}")

def render_nfa(nfa):

        def shape_of(state):
            return 'doublecircle' if state in nfa.final_states else 'circle'

        automaton = graphviz.Digraph("NFA") 
        automaton.graph_attr['rankdir'] = 'LR'

        states = set()
        for source_state, transitions in nfa.transitions.items():
            for symbol, destination_states in transitions.items():
                states.add(source_state)
                for state in destination_states:
                    states.add(state)
        
        for state in states:
            automaton.node(
                repr(state), 
                repr(state), 
                shape='doublecircle' if state in nfa.final_states else 'circle'
            )

        for source_state, transitions in nfa.transitions.items():
            for symbol, destination_states in transitions.items():
                states.add(source_state)
                for state in destination_states:
                    automaton.edge(
                        repr(source_state), 
                        repr(state), 
                        label=repr(pretty_set(symbol))
                    )

        for i, state in enumerate(nfa.start_states):
            automaton.node(f"start_{i}", shape="point", width="0")
            automaton.edge(f"start_{i}", repr(state))

        pdf_bytes = automaton.pipe(format='pdf')
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_bytes)
            tmp.flush()
            os.system(f"wslview {tmp.name}")