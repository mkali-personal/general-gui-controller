# python
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set

# A declaration looks like: "Name" = <rhs>
DECL_RE = re.compile(r'^\s*"([^"]+)"\s*=\s*(.+?)\s*$')
# Any quoted token on RHS is considered a reference to another name
REF_RE = re.compile(r'"([^"]+)"')


# ---------------------------
# Parsing and analysis helpers
# ---------------------------

def parse_declarations(lines: List[str]) -> List[Tuple[str, str, int, str]]:
    """Extract declaration lines.

    Returns a list of tuples: (name, rhs, line_number, original_line).
    Non-declaration lines are ignored.
    """
    decls: List[Tuple[str, str, int, str]] = []
    for lineno, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        m = DECL_RE.match(line)
        if not m:
            continue
        lhs = m.group(1).strip()
        rhs = m.group(2).strip()
        decls.append((lhs, rhs, lineno, raw.rstrip('\n')))
    return decls


def extract_dependencies(rhs: str) -> Set[str]:
    """Return a set of names referenced on the RHS (quoted strings)."""
    return {ref.strip() for ref in REF_RE.findall(rhs)}


def dedupe_keep_last(decls: List[Tuple[str, str, int, str]]) -> Tuple[Dict[str, Tuple[str, int]], Dict[str, Set[str]], Dict[str, List[int]]]:
    """Keep only the last declaration per name.

    Returns:
      - kept: name -> (rhs, last_decl_line)
      - deps: name -> set of dependency names (only names appearing on RHS)
      - all_decl_lines: name -> list of all declaration line numbers (to report duplicates)
    """
    all_decl_lines: Dict[str, List[int]] = {}

    # Walk once to collect all declaration lines per name
    for name, _rhs, lineno, _raw in decls:
        all_decl_lines.setdefault(name, []).append(lineno)

    # Keep only the last declaration for each name
    kept: Dict[str, Tuple[str, int]] = {}
    deps: Dict[str, Set[str]] = {}

    # Iterate in input order; overwrite to keep only the last one
    for name, rhs, lineno, _raw in decls:
        kept[name] = (rhs, lineno)
        deps[name] = extract_dependencies(rhs)

    return kept, deps, all_decl_lines


def build_graph(kept: Dict[str, Tuple[str, int]], deps: Dict[str, Set[str]]) -> Tuple[Dict[str, Set[str]], Dict[str, int]]:
    """Build dependency graph for topological sort.

    Edge direction: dep -> name (dep must appear before name).

    Returns:
      - adj: name -> set of neighbors (names that depend on this name)
      - indegree: name -> number of incoming edges
    """
    nodes = set(kept.keys())
    adj: Dict[str, Set[str]] = {n: set() for n in nodes}
    indegree: Dict[str, int] = {n: 0 for n in nodes}

    for name, rhs_deps in deps.items():
        for d in rhs_deps:
            if d == name:
                # ignore self-references for ordering
                continue
            if d in nodes:
                # d -> name
                if name not in adj[d]:
                    adj[d].add(name)
                    indegree[name] += 1
    return adj, indegree


def topo_sort_with_fallback(kept: Dict[str, Tuple[str, int]], deps: Dict[str, Set[str]]) -> List[str]:
    """Perform Kahn topological sort. If cycles remain, append remaining nodes
    in order of their last declaration line (stable fallback).
    """
    adj, indegree = build_graph(kept, deps)

    # Kahn's algorithm
    from collections import deque

    q = deque([n for n, deg in indegree.items() if deg == 0])
    order: List[str] = []

    while q:
        n = q.popleft()
        order.append(n)
        for m in adj[n]:
            indegree[m] -= 1
            if indegree[m] == 0:
                q.append(m)

    if len(order) == len(kept):
        return order

    # Cycle detected; collect remaining nodes and append by their last decl line order
    remaining = [n for n in kept.keys() if n not in order]
    remaining.sort(key=lambda x: kept[x][1])
    return order + remaining


# ---------------------------
# Public API
# ---------------------------

def reorder_and_dedupe(lines: List[str]) -> Tuple[List[str], Dict[str, List[int]]]:
    """Return new lines with duplicates removed (keep only last) and reordered
    so that each name appears after its dependencies.

    Returns:
      - new_lines: List[str] containing only declaration lines in sorted order
      - duplicates: name -> list of all declaration line numbers (len > 1 means duplicate)
    """
    decls = parse_declarations(lines)
    kept, deps, all_decl_lines = dedupe_keep_last(decls)

    # Compute topo order
    order = topo_sort_with_fallback(kept, deps)

    # Compose sorted output
    new_lines = [f'"{name}" = {kept[name][0]}' for name in order]
    return new_lines, all_decl_lines


def analyze_lines(lines: List[str]) -> Tuple[Dict[str, List[int]], Dict[str, List[int]], Dict[str, int]]:
    """Legacy analyzer retained for optional reporting.

    Returns:
      - duplicates: name -> list of declaration line numbers (len > 1 means duplicate)
      - misordered: name -> list of usage line numbers where it appeared before its first declaration
      - first_decl_line: name -> first declaration line number
    """
    declared: set = set()
    decl_lines: Dict[str, List[int]] = {}
    first_decl_line: Dict[str, int] = {}
    misordered: Dict[str, List[int]] = {}

    for lineno, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        m = DECL_RE.match(line)
        if not m:
            # Not a declaration line; ignore
            continue

        lhs = m.group(1).strip()
        rhs = m.group(2)

        # Record declaration
        decl_lines.setdefault(lhs, []).append(lineno)
        if lhs not in first_decl_line:
            first_decl_line[lhs] = lineno

        # Consider LHS declared for this line's RHS scan
        declared_for_rhs = set(declared)
        declared_for_rhs.add(lhs)

        # Scan references on RHS
        for ref in REF_RE.findall(rhs):
            ref_name = ref.strip()
            if ref_name not in declared_for_rhs:
                misordered.setdefault(ref_name, []).append(lineno)

        # After processing RHS, make this declaration globally visible
        declared.add(lhs)

    # Keep only names that actually have duplicates
    duplicates = {name: lns for name, lns in decl_lines.items() if len(lns) > 1}

    return duplicates, misordered, first_decl_line


def process_file(path: Path, output: Optional[Path] = None, in_place: bool = False) -> None:
    """Read file, remove duplicates (keep last), reorder by dependencies, and write/print.

    - If in_place is True, overwrite the input file with the new content.
    - Else if output is provided, write to that path.
    - Else, print to stdout.
    """
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    new_lines, all_decl_lines = reorder_and_dedupe(lines)

    # Report duplicates to stderr (optional)
    duplicates = {k: v for k, v in all_decl_lines.items() if len(v) > 1}
    if duplicates:
        sys.stderr.write("Removed duplicate declarations (kept last occurrence):\n")
        for name, lns in sorted(duplicates.items()):
            sys.stderr.write(f"  {name}: lines {lns}\n")

    output_text = "\n".join(new_lines) + "\n"

    if in_place:
        path.write_text(output_text, encoding="utf-8")
    elif output is not None:
        output.write_text(output_text, encoding="utf-8")
    else:
        # Print to stdout
        sys.stdout.write(output_text)


def analyze_file(path: Path) -> None:
    """Legacy: print duplicate and misordered info for a file."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    duplicates, misordered, first_decl_line = analyze_lines(lines)

    print("Duplicate declarations:")
    if not duplicates:
        print("  none")
    else:
        for name, lns in sorted(duplicates.items()):
            print(f"  {name}: declared on lines {lns}")

    print("\nImproperly ordered references (used before first declaration):")
    if not misordered:
        print("  none")
    else:
        for name, usage_lines in sorted(misordered.items()):
            decl_line: Optional[int] = first_decl_line.get(name)
            decl_info = f"declared on line {decl_line}" if decl_line is not None else "never declared"
            print(f"  {name}: used on lines {usage_lines} ({decl_info})")


if __name__ == "__main__":
    # CLI:
    #   python debug_solidworks_equations_file.py <input.txt> [--in-place | --out <output.txt>]
    if len(sys.argv) < 2:
        print("Usage: python debug_solidworks_equations_file.py <path-to-spec.txt> [--in-place | --out <output.txt>]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    in_place = False
    out_path: Optional[Path] = None

    if "--in-place" in sys.argv[2:]:
        in_place = True
    else:
        if "--out" in sys.argv[2:]:
            try:
                idx = sys.argv[2:].index("--out")
                out_arg = sys.argv[2:][idx + 1]
                out_path = Path(out_arg)
            except (ValueError, IndexError):
                print("--out requires a file path argument")
                sys.exit(2)

    process_file(input_path, output=out_path, in_place=in_place)
