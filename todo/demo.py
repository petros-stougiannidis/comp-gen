from contextfreegrammar import Grammar
from ll1parser import LL1Parser

startSymbol = "S"
nonTerminals = "SABCDE"
terminals = "abcde"
# productions LHS -> RHS1 | RHS2 | ... are specified by a dictionary with a LHS nonterminal as key
# and a list for each alternative RHS and values.
# A single RHS is specified by a list of terminals. An empty list represents the empty word epsilon
productions = {
 'S' : [['S', 'A'], ['B'], ['C']],
 'A' : [['a'], []],
 'B' : [['b'], []],
 'C' : [['D']],
 'D' : [['C']],
}
nonLL1Grammar = Grammar(startSymbol=startSymbol, terminals=terminals, nonTerminals=nonTerminals, productions=productions)

# the resulting grammar is reduced, i.e., unproductive productions and non-reachable 
# nonterminals are filtered out
print(nonLL1Grammar)

# the grammar is analyzed if has the property of beeing LL(1), which allows
# to automatically generate an LL(1)-Parser from the grammar
if not nonLL1Grammar.isLL1():
    nonLL1Grammar.printConflicts()

# example specification for a LL1 parser which parses regular expressions
class CharacterRange:
    def __new__(cls, start, end):
        return [chr(integer) for integer in range(ord(start), ord(end)+1)]

# define an LL(1) grammar for regex expressions over the alphabet a-z, A-Z and 0-9
startSymbol = "regex"
nonTerminals = {"regex", "concat", "rep", "atom", "A1", "A2", "A3", "symbol"}
characters = set(CharacterRange('a', 'z')) | set(CharacterRange('A', 'Z')) | set(CharacterRange('0', '9'))
# the empty string is represented by "_"
symbols = {"_"} | characters
metaCharacters = {"|", "(", ")", "*", "?", "+"}
terminals = symbols | metaCharacters
productions = {
    "regex": [["concat", "A1"]],
    "A1": [["|" ,"regex"], []],
    "concat": [["rep", "A2"]],
    "A2": [["concat"], []],
    "rep": [["atom" ,"A3"]],
    "A3": [["*"], ["?"], ["+"], []],
    "atom": [["(", "regex", ")"], ["symbol"]],
    "symbol" : [[symbol] for symbol in symbols]
} 

regexGrammar = Grammar(startSymbol=startSymbol, terminals=terminals, nonTerminals=nonTerminals, productions=productions) 

if not regexGrammar.isLL1():
    regexGrammar.printConflicts()

regexParser = LL1Parser(regexGrammar)

while (i := input("Type in a regex to parser or \"quit\" in order to terminate the program: ")) != "quit":
    try:
        if regexParser.parse(iter(i), printErrorMessages=True, printStack=True):
            print(f"Success: \"{i}\" is a valid regex expression")

    except Exception as e:
        print(e)

