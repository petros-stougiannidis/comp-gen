class Sequence(tuple):
        def __repr__(self):
            string = ""
            for symbol in self:
                string += str(symbol) + " "
            return string[:-1]