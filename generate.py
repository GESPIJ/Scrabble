import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }
        
    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for var,domain in self.domains.items():
            self.domains[var]=set([dom for dom in list(domain) if len(dom)==var.length])
        return None

    def revise(self, x, y):
        """
        
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        xOriginal=self.domains[x].copy()
        yOverlap=self.crossword.overlaps[y,x][0]
        xOverlap=self.crossword.overlaps[y,x][1]
        auxiliar=set()
        for domY in self.domains[y]:
            res=[domX for domX in list(self.domains[x]) if domX[xOverlap]==domY[yOverlap]]
            if domY in res:
                res.remove(domY)
            auxiliar=auxiliar.union(set(res).difference(auxiliar))
        self.domains[x]=auxiliar
        return len(xOriginal)!=self.domains[x]

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        quee=[]
        for var in self.crossword.variables:
            for vecino in list(self.crossword.neighbors(var)):
                quee.append((vecino,var))
        while len(quee)!=0:
            q=quee.pop(0)
            if (self.revise(q[0],q[1])):
                if (self.domains[q[0]]==0):
                    return False
                vecinos=self.crossword.neighbors(q[0])
                vecinos.remove(q[1])
                for vecino in list(vecinos):
                    quee.append((vecino,q[0]))
        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        return len(self.crossword.variables)==len(assignment.keys()) and self.consistent(assignment)

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        consisten=True
        assignVec=set(assignment.keys())
        for var,word in assignment.items():
            if var.length==len(word):
                vecinos=set(self.crossword.neighbors(var)).intersection(assignVec)
                for vecino in list(vecinos):
                    overlap=self.crossword.overlaps[(var,vecino)]
                    if word[overlap[0]]!=assignment[vecino][overlap[1]]:
                        consisten=False
            else:
                consistent=False

        return consisten

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        domOriginal=self.domains[var].copy()
        vecinos=self.crossword.neighbors(var)
        knownVecinos=set(assignment.keys()).intersection_update(vecinos)
        arcDomains={dom:0 for dom in list(self.domains[var])}
        if knownVecinos:
            for vecino in list(knownVecinos):
                self.domains[var]=domOriginal
                self.revise(var,vecino)
                for dom in self.domains[var]:
                    if dom in domOriginal:
                        arcDomains[dom]=arcDomains[dom]+1
            return list(arcDomains.keys()).sort()
        else:
            return list(domOriginal)

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        usedVariables=[var for var in assignment.keys()]
        unusedVar= self.crossword.variables.symmetric_difference(set(usedVariables))
        maxdatosDict={x:len(self.domains[x]) for x in list(unusedVar)}
        degreeDatosDict={x:len(self.crossword.neighbors(x)) for x in list(unusedVar)}
        maxDict={key:item for key,item in maxdatosDict.items() if item==max(maxdatosDict.values())}
        degreeDict={key:item for key,item in degreeDatosDict.items() if item==max(degreeDatosDict.values())}
        if len(maxdatosDict)>1:
            if len(degreeDict)>1:
                return list(degreeDict.keys()).pop()
            else:
                return list(degreeDict.keys()).pop()
        else:
            return list(maxDict.keys()).pop()

    def backtrack(self, assignment):
        usedVariables=[var for var in assignment.keys()]
        
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment):
            return assignment
        variable = self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(variable,assignment):
            assignment[variable]=value
            if self.consistent(assignment):
                result=self.backtrack(assignment)
                if result!=None:
                    return result
                return result
            else:
                assignment.pop(variable)
        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    #structure='C://Users//Greg//Documents//Harvard AI Scrabble//crossword//data//structure0.txt'
    words = sys.argv[2]
    #words = 'C://Users//Greg//Documents//Harvard AI Scrabble//crossword//data//words0.txt'
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    creator.select_unassigned_variable({})
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
