from collections import defaultdict
from itertools import combinations

from specification import unicode
from specification.strongly_connected_components import StronglyConnectedComponents
from specification.token import Token
from formatting.print import Sequence

class Grammar:

    def __init__(self, startSymbol, productions):
        self.startSymbol = startSymbol

        terminals = {name for name, _ in Token.get_tokens()}
        nonTerminals = set(productions.keys())
        

        if not startSymbol in set(nonTerminals):
            raise ValueError(f"Start symbol {startSymbol} {unicode.notElementOf} N")

        for symbol in {unicode.epsilon, "$"}:
            if symbol in set(terminals):
                raise ValueError(f"{symbol} is not allowed as a terminal symbol")

        for symbol in {"S'"}:
            if symbol in set(nonTerminals):
                raise ValueError(f"{symbol} is not allowed as a nonterminal symbol")

        if set(terminals) & set(nonTerminals):
            raise ValueError(f"The set of terminals and nonterminals are not disjoint: {unicode.Sigma} {unicode.setUnion} N = {set(terminals) & set(nonTerminals)}")

        self.terminals = set(terminals)
        self.nonTerminals = set(nonTerminals)
        
        self.actions = dict()
        self.delta = defaultdict(set)
        for A, d in productions.items():
            for alternative, action in productions[A].items(): 
                self.delta[A].add(alternative)
                self.actions[(A, alternative)] = action
        
        self.terminals = set(terminals) | {"$"}
        self.nonTerminals = set(nonTerminals) | {"S'"}

        self.artificial_start_symbol = "S'"
        self.original_start_symbol = self.startSymbol
        self.delta[self.artificial_start_symbol] = {(self.startSymbol,)}
        self.startSymbol = self.artificial_start_symbol

        self.reduce()
        self.computeEmptyAttributes()
        self.computeFirst1Sets()
        self.computeFollow1Sets()
        self.computeLL1Conflicts()

        
    def productions(self):
        return [(A, rightHandSide) for A in self.delta for rightHandSide in self.delta[A]]
    
    # reduces a context free grammar such that unproductive and non-reachable nonterminals are 
    # removed
    def reduce(self):
        productiveNonTerminals = set()
        numberOfUnproductiveNonTerminals = dict()
        rightHandSideOccurences = defaultdict(set)

        # find non-terminals and register in which productions they appear, initially all 
        # lefthand sides are registered as unproductive
        for production in self.productions():
            (_, rightHandSide) = production
            numberOfUnproductiveNonTerminals[production] = 0
            for A in self.nonTerminals:
                if A in rightHandSide:
                    numberOfUnproductiveNonTerminals[production] += 1
                    rightHandSideOccurences[A].add(production)
        
        # fix-point algorithm implementing the AND-OR-GRAPH analysis for
        # the productiviy of a production
        productiveProductions = {production for production, count in numberOfUnproductiveNonTerminals.items() if count == 0}
        while productiveProductions:
            A, rightHandSide = productiveProductions.pop()
            if A not in productiveNonTerminals:
                productiveNonTerminals.add(A)
                for B in rightHandSideOccurences[A]:
                    numberOfUnproductiveNonTerminals[B] -= 1
                    if numberOfUnproductiveNonTerminals[B] == 0:
                        productiveProductions.add(B)
        
        productiveProductions = defaultdict(set)
        for A, rightHandSide in {production for production, count in numberOfUnproductiveNonTerminals.items() if count == 0}:
            productiveProductions[A].add(rightHandSide)
        
        # Graph reachability algorithm determining which nonterminals are reachable
        reachableNonTerminals = set()
        currenltyReachableNonTerminals = {self.startSymbol}
        while currenltyReachableNonTerminals:
            A = currenltyReachableNonTerminals.pop()
            if A not in reachableNonTerminals:
                reachableNonTerminals.add(A)
                for rightHandSide in productiveProductions[A]:
                    for B in rightHandSide:
                        if B in self.nonTerminals:
                            currenltyReachableNonTerminals.add(B)

        reachableAndProductiveProductions = {A: set(productiveProductions[A]) for A in reachableNonTerminals}
        self.delta = reachableAndProductiveProductions

        reachableAndProductiveNonTerminals = reachableNonTerminals
        self.nonTerminals = reachableAndProductiveNonTerminals

    # computes which nonterminals are capable of producing the empty word
    def computeEmptyAttributes(self):
        self.isNullable = {symbol:False for symbol in self.nonTerminals | self.terminals}
        
        numberOfNonNullableSymbols = dict()
        rightHandSideOccurences = defaultdict(set)

        for production in self.productions():
            (A, rightHandSide) = production
            numberOfNonNullableSymbols[production] = len(rightHandSide)
            for B in self.nonTerminals:
                if B in rightHandSide:
                    rightHandSideOccurences[B].add(production)

        productionsWithNullableRightHandSides = {production for production, count in numberOfNonNullableSymbols.items() if count == 0}
        
        while productionsWithNullableRightHandSides:
            A, _ = productionsWithNullableRightHandSides.pop()
            self.isNullable[A] = True
            for occurence in rightHandSideOccurences[A]:
                numberOfNonNullableSymbols[occurence] -= 1
                if(numberOfNonNullableSymbols[occurence] == 0):
                    productionsWithNullableRightHandSides.add(occurence)

    # for each nonterminal, determine the set of terminals which are possibly
    # the first that can be produced by the nonterminal
    def computeFirst1Sets(self):
        self.epsilonFreeFirst1Set = defaultdict(set)
        variableDependencyGraph = {A:set() for A in self.nonTerminals}

        for (A, rightHandSide) in self.productions():
            for B in rightHandSide:
                if B in self.nonTerminals:
                    variableDependencyGraph[B].add(A)
                elif B in self.terminals:
                    self.epsilonFreeFirst1Set[A].add(B)
                if not self.isNullable[B]:
                    break

        stronglyConnectedComponents = StronglyConnectedComponents(variableDependencyGraph)

        # Tarjans algorithm for finding strongly connected components automatically induces
        # a topological order, such that reversing the found list of SCC is sufficient for 
        # forwarding the attributes correctly
        stronglyConnectedComponents = list(reversed(stronglyConnectedComponents))

        for component in stronglyConnectedComponents:
            for A in component:
                for B in component:
                    self.epsilonFreeFirst1Set[A] |= self.epsilonFreeFirst1Set[B]

                for B in variableDependencyGraph[A]:
                    self.epsilonFreeFirst1Set[B] |= self.epsilonFreeFirst1Set[A]
        
        self.first1Set = defaultdict(set)
        for A in self.nonTerminals:
            self.first1Set[A] = self.epsilonFreeFirst1Set[A] | ({unicode.epsilon} if self.isNullable[A] else set())

    # for each non terminal, find its occurences and determine which symbols 
    # can be produced directly after the occurence
    def computeFollow1Sets(self):
        self.follow1Set = defaultdict(set)
        variableDependencyGraph = {A:set() for A in self.nonTerminals}

        #None (or $) represents the lookahead pointing to the end of input
        # TODO: decide
        self.follow1Set[self.startSymbol].add("$")

        for (A, rightHandSide) in self.productions():
            for index, B in enumerate(rightHandSide):
                if B in self.nonTerminals:
                    for C in rightHandSide[index+1:]:
                        if C in self.nonTerminals:
                            self.follow1Set[B] |= self.epsilonFreeFirst1Set[C]
                        elif C in self.terminals:
                            self.follow1Set[B].add(C)
                        if not self.isNullable[C]:
                            break

                    if all(map(lambda x: self.isNullable[x], rightHandSide[index+1:])):
                        variableDependencyGraph[A].add(B)

        stronglyConnectedComponents = StronglyConnectedComponents(variableDependencyGraph)
        stronglyConnectedComponents = list(reversed(stronglyConnectedComponents))

        for component in stronglyConnectedComponents:
            for A in component:
                for B in component:
                    self.follow1Set[A] |= self.follow1Set[B]

                for B in variableDependencyGraph[A]:
                    self.follow1Set[B] |= self.follow1Set[A]

    # analyze first1 and follow1 sets in order to determine possible LL(1) conflicts 
    def computeLL1Conflicts(self):
        self.LL1Conflicts = []
        for A in self.delta:
            for alternative1, alternative2 in combinations(self.delta[A], 2):
                if concat1(self.first1(alternative1), self.follow1Set[A]) & concat1(self.first1(alternative2), self.follow1Set[A]):
                    self.LL1Conflicts.append((A, alternative1, alternative2))

    def first1(self, sequence):
        if not sequence:
            return {unicode.epsilon}
        else:
            first1Set = set()
            for symbol in sequence:
                if symbol in self.nonTerminals:
                    first1Set |= self.first1Set[symbol]
                elif symbol in self.terminals:
                    first1Set |= {symbol}
                if not self.isNullable[symbol]:
                    break
            return first1Set

    def isLL1(self):
        return not self.LL1Conflicts

    def printConflicts(self):
        for A, alternative1, alternative2 in self.LL1Conflicts:
            lookaheadSymbols1 = concat1(self.first1(alternative1), self.follow1Set[A])
            lookaheadSymbols2 = concat1(self.first1(alternative2), self.follow1Set[A])
            print(f"LL1 conflict: {A} -> {alternative1} or {alternative2}")
            print(f"First{unicode.subscript1}({alternative1}) {unicode.concat1Symbol} Follow{unicode.subscript1}({A}) {unicode.setUnion} First{unicode.subscript1}({alternative2}) {unicode.concat1Symbol} Follow{unicode.subscript1}({A}) = {lookaheadSymbols1&lookaheadSymbols2}\n")

    def __repr__(self):
        string = "Reduced grammar:\n"
        string += f"Start symbol:\t{self.startSymbol}\n"
        string += f"{unicode.Sigma}:\t{self.terminals}\n"
        string += f"N:\t{self.nonTerminals}\n"
        string += f"{unicode.delta}:\n"
        
        for A in self.delta:
            for i, rightHandSide in enumerate(self.delta[A]):
                if len(rightHandSide) == 0:
                    string += f"{A}[{i}] {unicode.rightArrow} {unicode.epsilon}"
                else:
                    string += f"{A}[{i}] {unicode.rightArrow} {Sequence(rightHandSide)}"
                if i < len(self.delta[A])-1:
                    string += " | "
                else:
                    string += "\n"
        string += "\n"

        for A in self.nonTerminals:
            string += f"F{unicode.epsilon}({A}) = {self.epsilonFreeFirst1Set[A]}\n"
        string += "\n"

        for A in self.nonTerminals:
            string += f"First{unicode.subscript1}({A}) = {self.first1Set[A]}\n"
        string += "\n"
        
        for A in self.nonTerminals:
            string += f"Follow{unicode.subscript1}({A}) = {self.follow1Set[A]}\n"

        string += f"\nLL(1): {self.isLL1()}\n"
        return string

def concat1(L1, L2):
    return L1 if unicode.epsilon not in L1 else (L1 - {unicode.epsilon}) | L2