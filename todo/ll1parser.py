import unicode
from collections import defaultdict
from contextfreegrammar import concat1, Sequence

class LL1Parser:

    def __init__(self, grammar):
        self.grammar = grammar

        if not self.grammar.isLL1():
            raise ValueError("Grammar is not LL(1)")

        self.computeLookaheadTable()

    def computeLookaheadTable(self):
        self.lookaheadTable = defaultdict(list)

        # fill in lookahead table, such that every production alternative can be
        # deterministicly chosen, given the next lookahead symbol.
        # If the given grammar is LL(1), deteminism is guaranteed
        for (A, rightHandSide) in self.grammar.productions():
            lookaheadSymbols = concat1(self.grammar.first1(rightHandSide), self.grammar.follow1Set[A])
            for lookaheadSymbol in lookaheadSymbols:
                self.lookaheadTable[(A, lookaheadSymbol)].append(rightHandSide)

    def lookahead(self, tokens):
        try:
            lookahead = next(tokens)
            if lookahead not in self.grammar.terminals:
                raise RuntimeError(f"Unknown token: {lookahead}")
            return lookahead
        except StopIteration:
            return None

    def parse(self, tokens, actions=None, printErrorMessages=False, printStack=False):

        errorMessage = ErrorMessage()
        if printErrorMessages:
            errorMessage.activate()
    
        stack = [Item("S'", [self.grammar.startSymbol, "$"])]
        lookahead = self.lookahead(tokens)
        
        while True:
            if printStack:
                print(stack, lookahead)
            match stack:
                case [finalItem] if lookahead == None and finalItem == Item("S'", [self.grammar.startSymbol, "$"], marker=1):
                    return True
                #expand: apply expansion rule given the next lookahead symbol
                case [*rest, top] if not top.isComplete() and top.markedSymbol() in self.grammar.nonTerminals:
                    nonTerminal = top.markedSymbol()
                    expansions = self.lookaheadTable[(nonTerminal, lookahead)]
                    match expansions:
                        # single deterministic choice
                        case [expansion]:
                            stack.append(Item(nonTerminal, expansion))
                        # parse error: no rule to apply, the word is rejected
                        case []:
                            errorMessage.show(f"Parsing error: Cannot expand {top} for lookahead: \'{'EOF' if lookahead == None else lookahead}\'")
                            return False
                        # sanity check: non deterministic choices as a result of the grammar not beeing LL(1)
                        case [*rules]:
                            exit(f"Lookahead table is ambiguous: {rules}")
                    
                #shift: terminal symbol is encountered, shift to the next lookahead symbol
                case [*rest, top] if not top.isComplete() and top.markedSymbol() in self.grammar.terminals and top.markedSymbol() == lookahead:
                    stack[-1] = top.next()
                    lookahead = self.lookahead(tokens)
                #reduce: an item was completed, pop the complete item and proceed with the next symbol of the item before
                case [*rest, second, top] if top.isComplete() and second.markedSymbol() == top.leftHandSide:
                    #TODO execute callbacks on successful reductions
                    stack.pop()
                    stack[-1] = stack[-1].next()
                
                case _:
                    errorMessage.show(f"Parsing error: {top} could neither be expanded, shifted nor reduced for lookahead: \'{'EOF' if lookahead == None else lookahead}\'")
                    return False


class Item:
    def __init__(self, leftHandSide, rightHandSide, marker=0):
        self.leftHandSide = leftHandSide
        self.rightHandSide = rightHandSide
        self.marker = marker

    def isComplete(self):
        return self.marker == len(self.rightHandSide)

    def next(self):
        if not self.isComplete():
            return Item(self.leftHandSide, self.rightHandSide, self.marker+1)
        else:
            raise RuntimeError(f"{self} is already complete")

    def markedSymbol(self):
        return self.rightHandSide[self.marker] if not self.isComplete() else None

    def __repr__(self):
        processedRightHandSide = Sequence(self.rightHandSide[:self.marker])
        unprocessedRightHandSide = Sequence(self.rightHandSide[self.marker:])

        return f"[{self.leftHandSide}{unicode.rightArrow}{processedRightHandSide}{unicode.dot}{unprocessedRightHandSide}]"

    def __eq__(self, other):
        return self.leftHandSide == other.leftHandSide and self.rightHandSide == other.rightHandSide and self.marker == other.marker

    def __hash__(self):
        return hash(self.leftHandSide + str(self.rightHandSide) + str(self.marker))

class ErrorMessage:
    def __init__(self):
        self.active = False

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def show(self, message):
        if self.active:
            print(message)