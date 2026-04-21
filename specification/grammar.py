from collections import defaultdict
from itertools import combinations

from visualization import unicode
from specification.strongly_connected_components import StronglyConnectedComponents
from visualization.print import Sequence, pretty_set

class Grammar:

    def __init__(self, start_symbol, productions, terminals):
        self.start_symbol = start_symbol

        non_terminals = set(productions.keys())

        if not start_symbol in set(non_terminals):
            raise ValueError(f"Start symbol {start_symbol} {unicode.not_element_of} N")

        for symbol in {unicode.epsilon, "$"}:
            if symbol in set(terminals):
                raise ValueError(f"{symbol} is not allowed as a terminal symbol")

        for symbol in {"S'"}:
            if symbol in set(non_terminals):
                raise ValueError(f"{symbol} is not allowed as a nonterminal symbol")

        if set(terminals) & set(non_terminals):
            raise ValueError(f"The set of terminals and nonterminals are not disjoint: {unicode.Sigma} {unicode.set_union} N = {set(terminals) & set(non_terminals)}")

        for A in productions.keys():
            for alternative, action in productions[A].items():
                for symbol in alternative:
                    if symbol not in non_terminals and symbol not in terminals:
                        raise ValueError(f"{symbol} {unicode.not_element_of} (N {unicode.set_union} T)")
        
        self.actions = dict()
        self.delta = defaultdict(set)
        # TODO: prune actions after reduce()
        for A in productions.keys():
            for alternative, action in productions[A].items(): 
                self.delta[A].add(alternative)
                self.actions[(A, alternative)] = action
        
        self.terminals = set(terminals) | {"$"}
        self.non_terminals = set(non_terminals) | {"S'"}

        self.artificial_start_symbol = "S'"
        self.original_start_symbol = self.start_symbol
        self.delta[self.artificial_start_symbol] = {(self.start_symbol,)}
        self.start_symbol = self.artificial_start_symbol

        self.reduce()
        # TODO: check if start symbol is still productive
        self.compute_empty_attributes()
        self.compute_first1_sets()
        self.compute_follow1_sets()
        self.compute_LL1_conflicts()

        
    def productions(self):
        return [(A, rhs) for A in self.delta for rhs in self.delta[A]]
    
    # reduces a context free grammar such that unproductive and non-reachable nonterminals are 
    # removed
    def reduce(self):
        productive_non_terminals = set()
        number_of_unproductive_non_terminals = dict()
        rhs_occurences = defaultdict(set)

        # find non-terminals and register in which productions they appear, initially all 
        # lefthand sides are registered as unproductive
        for production in self.productions():
            (_, rhs) = production
            number_of_unproductive_non_terminals[production] = 0
            for A in self.non_terminals:
                if A in rhs:
                    number_of_unproductive_non_terminals[production] += 1
                    rhs_occurences[A].add(production)
        
        # fix-point algorithm implementing the AND-OR-GRAPH analysis for
        # the productiviy of a production
        productive_productions = {production for production, count in number_of_unproductive_non_terminals.items() if count == 0}
        while productive_productions:
            A, rhs = productive_productions.pop()
            if A not in productive_non_terminals:
                productive_non_terminals.add(A)
                for B in rhs_occurences[A]:
                    number_of_unproductive_non_terminals[B] -= 1
                    if number_of_unproductive_non_terminals[B] == 0:
                        productive_productions.add(B)
        
        productive_productions = defaultdict(set)
        for A, rhs in {production for production, count in number_of_unproductive_non_terminals.items() if count == 0}:
            productive_productions[A].add(rhs)
        
        # Graph reachability algorithm determining which nonterminals are reachable
        reachable_non_terminals = set()
        currenlty_reachable_non_terminals = {self.start_symbol}
        while currenlty_reachable_non_terminals:
            A = currenlty_reachable_non_terminals.pop()
            if A not in reachable_non_terminals:
                reachable_non_terminals.add(A)
                for rhs in productive_productions[A]:
                    for B in rhs:
                        if B in self.non_terminals:
                            currenlty_reachable_non_terminals.add(B)

        reachable_and_productive_productions = {A: set(productive_productions[A]) for A in reachable_non_terminals}
        self.delta = reachable_and_productive_productions

        reachable_and_productive_non_terminals = reachable_non_terminals
        self.non_terminals = reachable_and_productive_non_terminals

    # computes which nonterminals are capable of producing the empty word
    def compute_empty_attributes(self):
        self.is_nullable = {symbol:False for symbol in self.non_terminals | self.terminals}
        
        number_of_non_nullable_symbols = dict()
        rhs_occurences = defaultdict(set)

        for production in self.productions():
            (A, rhs) = production
            number_of_non_nullable_symbols[production] = len(rhs)
            for B in self.non_terminals:
                if B in rhs:
                    rhs_occurences[B].add(production)

        productions_with_nullable_rhss = {production for production, count in number_of_non_nullable_symbols.items() if count == 0}
        
        while productions_with_nullable_rhss:
            A, _ = productions_with_nullable_rhss.pop()
            self.is_nullable[A] = True
            for occurence in rhs_occurences[A]:
                number_of_non_nullable_symbols[occurence] -= 1
                if(number_of_non_nullable_symbols[occurence] == 0):
                    productions_with_nullable_rhss.add(occurence)

    # for each nonterminal, determine the set of terminals which are possibly
    # the first that can be produced by the nonterminal
    def compute_first1_sets(self):
        self.epsilon_free_first1_set = defaultdict(set)
        variable_dependency_graph = {A:set() for A in self.non_terminals}

        for (A, rhs) in self.productions():
            for B in rhs:
                if B in self.non_terminals:
                    variable_dependency_graph[B].add(A)
                elif B in self.terminals:
                    self.epsilon_free_first1_set[A].add(B)
                if not self.is_nullable[B]:
                    break

        strongly_connected_components = StronglyConnectedComponents(variable_dependency_graph)

        # Tarjans algorithm for finding strongly connected components automatically induces
        # a topological order, such that reversing the found list of SCC is sufficient for 
        # forwarding the attributes correctly
        strongly_connected_components = list(reversed(strongly_connected_components))

        for component in strongly_connected_components:
            for A in component:
                for B in component:
                    self.epsilon_free_first1_set[A] |= self.epsilon_free_first1_set[B]

                for B in variable_dependency_graph[A]:
                    self.epsilon_free_first1_set[B] |= self.epsilon_free_first1_set[A]
        
        self.first1_set = defaultdict(set)
        for A in self.non_terminals:
            self.first1_set[A] = self.epsilon_free_first1_set[A] | ({unicode.epsilon} if self.is_nullable[A] else set())

    # for each non terminal, find its occurences and determine which symbols 
    # can be produced directly after the occurence
    def compute_follow1_sets(self):
        self.follow1_set = defaultdict(set)
        variable_dependency_graph = {A:set() for A in self.non_terminals}

        #None (or $) represents the lookahead pointing to the end of input
        # TODO: decide
        self.follow1_set[self.start_symbol].add("$")

        for (A, rhs) in self.productions():
            for index, B in enumerate(rhs):
                if B in self.non_terminals:
                    for C in rhs[index+1:]:
                        if C in self.non_terminals:
                            self.follow1_set[B] |= self.epsilon_free_first1_set[C]
                        elif C in self.terminals:
                            self.follow1_set[B].add(C)
                        if not self.is_nullable[C]:
                            break

                    if all(map(lambda x: self.is_nullable[x], rhs[index+1:])):
                        variable_dependency_graph[A].add(B)

        strongly_connected_components = StronglyConnectedComponents(variable_dependency_graph)
        strongly_connected_components = list(reversed(strongly_connected_components))

        for component in strongly_connected_components:
            for A in component:
                for B in component:
                    self.follow1_set[A] |= self.follow1_set[B]

                for B in variable_dependency_graph[A]:
                    self.follow1_set[B] |= self.follow1_set[A]

    # analyze first1 and follow1 sets in order to determine possible LL(1) conflicts 
    def compute_LL1_conflicts(self):
        self.LL1_conflicts = []
        for A in self.delta:
            for alternative1, alternative2 in combinations(self.delta[A], 2):
                if concat1(self.first1(alternative1), self.follow1_set[A]) & concat1(self.first1(alternative2), self.follow1_set[A]):
                    self.LL1_conflicts.append((A, alternative1, alternative2))

    def first1(self, sequence):
        if not sequence:
            return {unicode.epsilon}
        else:
            first1_set = set()
            for symbol in sequence:
                if symbol in self.non_terminals:
                    first1_set |= self.first1_set[symbol]
                elif symbol in self.terminals:
                    first1_set |= {symbol}
                if not self.is_nullable[symbol]:
                    break
            return first1_set

    def is_LL1(self):
        return not self.LL1_conflicts

    def print_LL1_conflicts(self):
        for A, alternative1, alternative2 in self.LL1_conflicts:
            lookahead_symbols1 = concat1(self.first1(alternative1), self.follow1_set[A])
            lookahead_symbols2 = concat1(self.first1(alternative2), self.follow1_set[A])
            production1, production2 = Sequence(alternative1), Sequence(alternative2)
            print(f"LL1 conflict: [{A} → {Sequence(production1)}] vs [{A} → {Sequence(production2)}]")
            print(f"First{unicode.subscript1}({production1}) {unicode.concat1} Follow{unicode.subscript1}({A}) {unicode.set_union} First{unicode.subscript1}({production2}) {unicode.concat1} Follow{unicode.subscript1}({A}) = {pretty_set(lookahead_symbols1&lookahead_symbols2)}\n")

    def __repr__(self):
        string = "Reduced grammar:\n"
        string += f"Start symbol:\t{self.start_symbol}\n"
        string += f"{unicode.Sigma}:\t{pretty_set(self.terminals)}\n"
        string += f"N:\t{pretty_set(self.non_terminals)}\n"
        string += f"{unicode.delta}:\n"
        
        for A in self.delta:
            for i, rhs in enumerate(self.delta[A]):
                if len(rhs) == 0:
                    string += f"{A} {unicode.right_arrow} {unicode.epsilon}"
                else:
                    string += f"{A} {unicode.right_arrow} {Sequence(rhs)}"
                if i < len(self.delta[A])-1:
                    string += " | "
                else:
                    string += "\n"
        string += "\n"
        

        for A in self.non_terminals:
            string += f"F{unicode.epsilon}({A}) = {pretty_set(self.epsilon_free_first1_set[A])}\n"
        string += "\n"

        for A in self.non_terminals:
            string += f"First{unicode.subscript1}({A}) = {pretty_set(self.first1_set[A])}\n"
        string += "\n"
        
        for A in self.non_terminals:
            string += f"Follow{unicode.subscript1}({A}) = {pretty_set(self.follow1_set[A])}\n"

        string += f"\nLL(1): {self.is_LL1()}\n"
        return string

def concat1(L1, L2):
    return L1 if unicode.epsilon not in L1 else (L1 - {unicode.epsilon}) | L2