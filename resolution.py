import math                                           
import re                                             
from sympy import symbols, sympify                     
from sympy.logic.boolalg import to_cnf, conjuncts, disjuncts, Not as SympyNot   
from sympy.core.symbol import Symbol                   
from sympy import false as SympyFalse, true as SympyTrue 

#  Supported symbols (spaces don't matter with connectives but NO SPACE in variables please):
#    ~                negation
#    &                conjunction
#    |                disjunction
#    >>               implication
#    ( )              parentheses
 

def extract_var_names(text):
    """Return the set of all variable names found in a formula string."""
    # No spaces allowed in variable names and they must start with a letter but can have numerals and underscores later
    return set(re.findall(r'\b[A-Za-z][A-Za-z0-9_]*\b', text))


def parse_sympy(text, local_dict):
    """Parse a formula string into a sympy expression."""
    return sympify(text, locals=local_dict)

def clauses_from_formula(sympy_expr, var_index):
    """
    Convert a sympy expression to CNF and return it as a list of vector tuples.
    Each tuple has length n: 1 = positive literal, -1 = negative literal, 0 = absent.
    """
    num_vars = len(var_index)
    cnf = to_cnf(sympy_expr)

    if cnf == SympyFalse:                           # expression is a contradiction
        return [tuple([0] * num_vars)]              # return the empty clause directly

    clauses = []
    for clause in conjuncts(cnf):
        if clause == SympyTrue:                     # sympy already simplified to True
            continue                                # tautological clause, carries no information

        vec = [0] * num_vars
        is_tautology = False

        for lit in disjuncts(clause):
            if isinstance(lit, SympyNot):          # checking whether negated literal is present
                name = str(lit.args[0])
                if name in var_index:
                    idx = var_index[name]
                    if vec[idx] == 1:               # already has +ve literal as well i.e. tautology
                        is_tautology = True
                        break
                    vec[idx] = -1
            elif isinstance(lit, Symbol):           # checking whether +ve literal is present
                name = str(lit)
                if name in var_index:
                    idx = var_index[name]
                    if vec[idx] == -1:              # already has -ve literal so tautology
                        is_tautology = True
                        break
                    vec[idx] = 1

        if not is_tautology:
            clauses.append(tuple(vec))

    return clauses



def resolve(c1, c2):
    """
    Tries to resolve two clauses. Returns the resolvent tuple if there
    is a unique complimentary literal, or None if:
      - no complementary literal exists (not resolvable), or
      - more than one complementary literal exists (tautology).
    """
    pivot = None                                            # index of the one unique complimentrary literal
    for i in range(len(c1)):
        if c1[i] * c2[i] == -1:                                   # product -1 means complimentary literal
            if pivot is not None:                                  # second complement found
                return None                                        # which means a tautology, so  discard
            pivot = i                                              # record the index of complimentary literal

    if pivot is None:
        return None

    return tuple(
        int(math.copysign(1, c1[i] + c2[i]))                      # sign(sum): keeps +1 or -1 as some values would have become -2 or 2
        if (c1[i] + c2[i]) != 0 else 0                            # 0 if absent in both or cancelled at the pivot
        for i in range(len(c1))
    )


def print_proof(empty_clause, parent_map, var_names):
    """Trace back from the empty clause and print each step of the proof."""

    def clause_str(c):
        """Convert a vector clause to a readable string e.g. (p v ~q)."""
        lits = []
        for i, v in enumerate(c):
            if v ==  1: lits.append(var_names[i])                 # positive literal
            if v == -1: lits.append(f"~{var_names[i]}")           # negative literal
        return "(" + " v ".join(lits) + ")" if lits else "[]"     # return [] i.e. empty clause if nothing is -1 or 1

    stack   = [empty_clause]                                       # trace back starting from empty clause
    visited = set()                                                # skip already-printed clauses
    steps   = []                                                   # collect steps, print in order after

    while stack:
        clause = stack.pop()
        if clause in visited:
            continue
        visited.add(clause)

        entry = parent_map[clause]
        if entry == "PREMISE":                                     # base case: came directly from the assumptions
            steps.append(f"  Premise : {clause_str(clause)}")
        else:
            c1, c2, pivot = entry                                  # derived by resolving c1 and c2
            steps.append(
                f"  Resolving  {clause_str(c1)}  and  {clause_str(c2)}"
                f"  on  {var_names[pivot]}  to get  {clause_str(clause)}"
            )
            stack.append(c1)                                       # trace c1's parents next
            stack.append(c2)                                       # trace c2's parents next

    print("\n-- Proof --")
    for step in reversed(steps):                                   # reversed: premise first, empty clause last
        print(step)
    print()


def process_pair(c1, c2, all_clauses, parent_map, curr_new):
    """
    Resolve a pair and handle the result:
      - None       -> skip (not resolvable or tautology)
      - empty      -> record and return True  (contradiction found)
      - new clause -> add to curr_new and all_clauses
    Returns True if the empty clause was found, else False.
    """
    if c1 == c2:                                                   # skip identical pairs
        return False

    r = resolve(c1, c2)                                            # attempt resolution
    if r is None:                                                   # not resolvable or tautology
        return False

    pivot = next(i for i in range(len(c1)) if c1[i] * c2[i] == -1)  # recover pivot for proof generation later

    if all(v == 0 for v in r):                                     # all zeros = empty clause = contradiction
        parent_map[r] = (c1, c2, pivot)                            # record its derivation
        return True

    if r not in all_clauses:                                       # only add the clause to the current set if not already generated/present
        all_clauses.add(r)                                         
        curr_new.add(r)                                            
        parent_map[r] = (c1, c2, pivot)                            # record the derivation for proof generation later

    return False


def exhaustive_resolution(initial_clauses, n, var_names):
    """
    Main resolution loop.
    Batches clauses into old and prev_new to avoid re-trying already-processed pairs.
    Stops on contradiction  or when no new clauses can be generated. Keeps all_clauses to make sure not 
    to add the same clauses again. 
    """
    all_clauses = set()                                            # every clause ever seen (O(1) uniqueness check)
    parent_map  = {}                                               # Maps every derrived clause to tuple of two clauses and variable that was used i.e. c1,c2,pivot. Used later for writing the Proof as c: Resolving c1, c2 on pivot
    old         = set()                                            # pair of each clause in this set has already been processed. No need to go over them again
    prev_new    = set()                                            # clauses derrived in the last iteration. The pairs in this set are yet to be processed  

    for c in initial_clauses:
        t = tuple(c)                                               # tuple is hashablebut lists are not so clauses need to be changed to tuples
        all_clauses.add(t)
        prev_new.add(t)                                            # initial clauses form the first batch
        parent_map[t] = "PREMISE"                                  # no parents means they are from the premise. will used while generating proof as well

    empty_clause = tuple([0] * n)                                  # all-zero vector = contradiction target
    iteration    = 0

    while True:
        iteration += 1
        curr_new = set()                                           # clauses found in this resolutin iteration
        print(f"  Iteration {iteration}:  |old|={len(old)}  |prev_new|={len(prev_new)}")

        # new x old: each new clause paired with every already-processed clause
        for c1 in prev_new:
            for c2 in old:
                if process_pair(c1, c2, all_clauses, parent_map, curr_new):
                    print("  Empty clause derived!")
                    print_proof(empty_clause, parent_map, var_names)
                    return "UNSATISFIABLE"

        # new x new: new clauses paired with each other (i < j avoids duplicate pairs)
        prev_list = list(prev_new)
        for i in range(len(prev_list)):
            for j in range(i + 1, len(prev_list)):
                if process_pair(prev_list[i], prev_list[j],
                                all_clauses, parent_map, curr_new):
                    print("  Empty clause derived!")
                    print_proof(empty_clause, parent_map, var_names)
                    return "UNSATISFIABLE"

        if not curr_new:                                           # nothing new added = fixed point
            print("  Fixed point reached, no new clauses.")
            return "SATISFIABLE"

        print(f"  {len(curr_new)} new clause(s) added.")
        old      = old | prev_new                                  # prev_new is fully processed, so moving the clauses there to old
        prev_new = curr_new                                        # cuurent iteration's clauses become the previous for the next iteration

#  Proof by refutation:
#    negate the conclusion, add to premise, run resolution.
#    UNSATISFIABLE -> contradiction found -> conclusion is PROVED
#    SATISFIABLE   -> fixed point reached -> conclusion is NOT provable

def prove(premise, conclusion):
    """
    premise   : list of formula strings  e.g. ["p", "p -> q"]
    conclusion : formula string           e.g. "q"
    """
    all_text   = " ".join(premise) + " " + conclusion            
    var_names  = sorted(extract_var_names(all_text))               # alphabetically sorted variable names
    n          = len(var_names)                                   
    var_index  = {v: i for i, v in enumerate(var_names)}          # indices used for variable names in vector representing the clauses
    local_dict = {v: symbols(v) for v in var_names}               # variable name used as sympy symbol

    print(f"Variables : {var_names}")

    all_clauses = []

    print("\n-- Premise (CNF vectors) --")
    for raw in premise:
        expr    = parse_sympy(raw, local_dict)                     
        clauses = clauses_from_formula(expr, var_index)            
        print(f"  {raw:30s} :  {[list(c) for c in clauses]}")
        all_clauses.extend(clauses)

    conc_expr   = parse_sympy(conclusion, local_dict)              
    neg_clauses = clauses_from_formula(SympyNot(conc_expr), var_index)  
    print(f"\n-- Negated conclusion --")
    print(f"  not({conclusion:27s}) :  {[list(c) for c in neg_clauses]}")
    all_clauses.extend(neg_clauses)                                

    print("\n-- Resolution --")
    result = exhaustive_resolution(all_clauses, n, var_names)

    print("=" * 50)
    if result == "UNSATISFIABLE":
        print(f"  PROVED:  '{conclusion}'")
    else:
        print(f"  NOT PROVABLE:  '{conclusion}'")
    print("=" * 50)
    return result




def main():
    """Prompt for premise and conclusion"""
    print("###############  Welcome to Resolution Proof Generator. ##########################\n")
    print("Use | for disjunctions, & for conjunctions, ~ for negations, and >> for implications\n")
    
    raw        = input("Premise (comma separated): ").strip()     
    premise   = [p.strip() for p in raw.split(",") if p.strip()]               
    conclusion = input("Conclusion to derive: ").strip()
    print()
    prove(premise, conclusion)

if __name__ == "__main__":
    main()