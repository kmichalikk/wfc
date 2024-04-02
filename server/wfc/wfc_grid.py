from server.wfc.wfc_cell import WFCCell
from common.typings import Direction


class WFCGrid:
    def __init__(self, size, cells):
        self.size = size
        self.cells = cells
        self.players_cells: [WFCCell] = []

    def cell_neighbours(self, cell: WFCCell) -> dict[Direction, WFCCell]:
        neighbours: dict[Direction, WFCCell] = {}
        if cell.position[1] < self.size-1:
            neighbours["n"] = self.cells[cell.position[0]][cell.position[1]+1]
        if cell.position[0] < self.size-1:
            neighbours["e"] = self.cells[cell.position[0]+1][cell.position[1]]
        if cell.position[1] > 0:
            neighbours["s"] = self.cells[cell.position[0]][cell.position[1]-1]
        if cell.position[0] > 0:
            neighbours["w"] = self.cells[cell.position[0]-1][cell.position[1]]

        return neighbours
