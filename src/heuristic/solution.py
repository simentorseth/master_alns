from typing import Self


class Solution:
    def __init__(self) -> None:
        self._routes: list[int] = []
        self._stations: list[int] = []

    @property
    def routes(self) -> list[int]:
        return self._routes

    @routes.setter
    def routes(self, routes: list[int]) -> None:
        self._routes = routes

    @property
    def stations(self) -> list[int]:
        return self._stations

    @stations.setter
    def stations(self, stations: list[int]) -> None:
        self._stations = stations

    def __str__(self) -> str:
        return f"Routes: {self._routes}\nStations: {self._stations}"

    def __copy__(self) -> Self:
        new_solution = Solution()
        new_solution.routes = self._routes.copy()
        new_solution.stations = self._stations.copy()
        return new_solution

    def __eq__(self, other: object) -> bool:
        if type(self) != type(other):
            return False
        return self._routes == other._routes and self._stations == other._stations

    def __hash__(self) -> int:
        return hash((tuple(self._routes), tuple(self._stations)))
