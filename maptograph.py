from collections import deque

from tilesmap import find_neighbours


def is_map_walkable(grid):
    def BFS(G, root):
        visited = [False] * len(G)
        Q = deque()
        visited[root] = True
        Q.append(root)
        while len(Q):
            u = Q.popleft()
            for v in G[u]:
                if not visited[v]:
                    visited[v] = True
                    Q.append(v)
        return visited

    def make_graph():
        G = [[] for _ in range(rows * columns)]
        for j in range(rows):
            for i in range(columns):
                n = j * rows + i
                G[n].extend(find_neighbours(grid[j][i].result, n, columns, rows))
        return G

    rows = len(grid)
    columns = len(grid[0])
    G = make_graph()
    root = next((i for i in range(rows * columns) if grid[i // columns][i % columns].result != "r"))
    visited = BFS(G, root)
    for i in range(len(visited)):
        if not visited[i] and grid[i // columns][i % columns].result != "r":
            return False
    return True
