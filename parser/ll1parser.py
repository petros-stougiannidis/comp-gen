from collections import defaultdict
from specification import unicode
from specification.grammar import concat1
from specification.item import Item

class LL1Parser:

    def __init__(self, grammar):
        self.grammar = grammar

        if not self.grammar.is_LL1():
            raise ValueError("Grammar is not LL(1)")

        self.compute_lookahead_table()

    def compute_lookahead_table(self):
        self.lookahead_table = defaultdict(list)

        # fill in lookahead table, such that every production alternative can be
        # deterministicly chosen, given the next lookahead symbol.
        # If the given grammar is LL(1), deteminism is guaranteed
        for (A, rhs) in self.grammar.productions():
            for lookahead_symbol in concat1(self.grammar.first1(rhs), self.grammar.follow1_set[A]):
                self.lookahead_table[(A, lookahead_symbol)].append(rhs)

    def lookahead(self, tokens):
        try:
            token = next(tokens)
            if token.type not in self.grammar.terminals:
                raise RuntimeError(f"Unknown token: {token.type}")
            return token.type, token.value
        except StopIteration:
            return None

    def parse(self, tokens, print_stack=False):
        
        start_item = Item(self.grammar.artificial_start_symbol, [self.grammar.original_start_symbol, "$"]) 
        stack, value_stack = [start_item], []
        tokens = iter(tokens)
        lookahead, value = self.lookahead(tokens)
        
        while True:
            
            if print_stack:
                print("...", stack[-3:], "→ lookahead:", lookahead)
                print("stack:", value_stack)
            match stack:
                case [final_item] if lookahead == "$" and final_item == start_item.advance():
                    return True, value_stack

                #expand: apply expansion rule given the next lookahead symbol
                case [*rest, top] if not top.is_complete() and top.next_symbol() in self.grammar.non_terminals:
                    non_terminal = top.next_symbol()
                    expansions = self.lookahead_table[(non_terminal, lookahead)]
                    match expansions:
                        # single deterministic choice
                        case [expansion]:
                            stack.append(Item(non_terminal, expansion))
                        # parse error: no rule to apply, the word is rejected
                        case []:
                            raise SyntaxError(f"Parsing error: Cannot expand {top} for lookahead: {lookahead}")
                        # sanity check: non deterministic choices as a result of the grammar not beeing LL(1)
                        case [*rules]:
                            raise ValueError(f"Lookahead table is ambiguous: {rules}")
                    
                #shift: terminal symbol is encountered, shift to the next lookahead symbol
                case [*rest, top] if not top.is_complete() and top.next_symbol() in self.grammar.terminals and top.next_symbol() == lookahead:
                    stack[-1] = top.advance()
                    value_stack.append(value)
                    # print("shoift-push:", value)
                    
                    lookahead, value = self.lookahead(tokens)

                #reduce: an item was completed, pop the complete item and proceed with the next symbol of the item before
                case [*rest, second, top] if top.is_complete() and second.next_symbol() == top.lhs:

                    #TODO execute callbacks on successful reductions
                    # print("REDUCE", top)
                    # if callback := self.grammar.actions[(top.lhs, top.rhs)]:
                    #     children = []
                    #     for _ in range(len(top.rhs)):
                    #         b = value_stack.pop()
                    #         print("pop:", b)
                    #         children.append(b)
                    #     children.reverse()
                    #     node = callback(children)
                    #     value_stack.append(node)
                    #     print("push:", str(node))
                    print("REDUCE", top)
                    children = []
                    for _ in range(len(top.rhs)):
                        b = value_stack.pop()
                        print("pop:", b)
                        children.append(b)
                    children.reverse()
                    if callback := self.grammar.actions[(top.lhs, top.rhs)]:
                        node = callback(children)
                    else:
                        node = children
                    value_stack.append(node)
                    print("push:", str(node))

                    stack.pop()
                    stack[-1] = stack[-1].advance()
                
                case _:
                    raise SyntaxError(f"Parsing error: {top} could neither be expanded, shifted nor reduced for lookahead: {lookahead}")
