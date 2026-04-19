class StronglyConnectedComponents:
    def __new__(cls, graph):
        instance = super().__new__(cls)
        instance.__init__(graph)
        return instance.run()

    def __init__(self, graph):
        self.graph = graph
        self.index = 0
        self.stack = []
        self.indices = {}
        self.lowlink = {}
        self.onStack = {}
        self.sccs = []

    def run(self):
        # for every unvisited node, traverse the graph from the node
        for node in self.graph:
            if node not in self.indices:
                # while traversing with strongConnect, newly found SCC's are registered in self.sccs
                self.strongConnect(node)

        return self.sccs

    def strongConnect(self, node):
        self.indices[node] = self.index
        self.lowlink[node] = self.index
        self.index += 1
        self.stack.append(node)
        self.onStack[node] = True

        for successor in self.graph[node]:
            # if successor has not been visited yet, continue search recursively
            if successor not in self.indices:
                self.strongConnect(successor)
                self.lowlink[node] = min(self.lowlink[node], self.lowlink[successor])
            elif self.onStack[successor]:
                # Successor is in the stack and hence in the current SCC
                self.lowlink[node] = min(self.lowlink[node], self.indices[successor])

        # If node is a root node, pop the stack and generate an SCC
        if self.lowlink[node] == self.indices[node]:
            scc = []
            while True:
                w = self.stack.pop()
                self.onStack[w] = False
                scc.append(w)
                if w == node:
                    break
            self.sccs.append(scc)
