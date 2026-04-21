import graphviz
import tempfile
import os
import string

from formatting.print import pretty_set

def render_lr1(lr1_automaton):
    state_id = {lr1_automaton.start_state : 0}
    for i, state in enumerate(lr1_automaton.states - {lr1_automaton.start_state}, start=1):
        state_id[state] = i

    def content_of(state):
        lines = [f"State: {state_id[state]}"]
        for item in state:
            lines.append(str(item))
        return "\n".join(lines)

    automaton = graphviz.Digraph("LR1")
    automaton.graph_attr['rankdir'] = 'LR'

    for state in lr1_automaton.states:
        automaton.node(
            name=f"{state_id[state]}",
            label=content_of(state),
            shape='box',
            style='filled' if state.is_final() else '',
            fillcolor='lightgreen' if state.is_final() else None,
            peripheries="2" if state.is_final() else "1"
        )
    
    for (source_state, symbol), target_state in lr1_automaton.transitions.items():
        
        automaton.edge(
            f"{state_id[source_state]}",
            f"{state_id[target_state]}",
            label=str(symbol)
        )

    automaton.node("start", shape="point", width="0")
    automaton.edge("start", f"{state_id[lr1_automaton.start_state]}")

    pdf_bytes = automaton.pipe(format='pdf')

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp.flush()
        os.system(f"wslview {tmp.name}")

def render_nfa(nfa):

    def dot_label(state):
        if hasattr(state, "accepted_token") and state.accepted_token:
            return f'{state.accepted_token}\\nid={state.id}'
        if hasattr(state, "id"):
            return f'id={state.id}'
        return str(state)

    def compress_set(complete_set):
        new_set = set()
        if set(string.ascii_lowercase) <= complete_set:
            complete_set -= set(string.ascii_lowercase)
            new_set |= {"[a-z]"}
        if set(string.ascii_uppercase) <= complete_set:
            complete_set -= set(string.ascii_uppercase)
            new_set |= {"[A-Z]"}
        if set(string.digits) <= complete_set:
            complete_set -= set(string.digits)
            new_set |= {"[0-9]"}
        return new_set | complete_set

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
            dot_label(state), 
            shape='doublecircle' if state in nfa.final_states else 'circle'
        )

    for source_state, transitions in nfa.transitions.items():
        for symbol, destination_states in transitions.items():
            states.add(source_state)
            for state in destination_states:
                automaton.edge(
                    repr(source_state), 
                    repr(state), 
                    label=repr(pretty_set(compress_set(symbol)))
                )

    for i, state in enumerate(nfa.start_states):
        automaton.node(f"start_{i}", shape="point", width="0")
        automaton.edge(f"start_{i}", repr(state))

    pdf_bytes = automaton.pipe(format='pdf')
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp.flush()
        os.system(f"wslview {tmp.name}")