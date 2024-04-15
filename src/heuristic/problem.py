from haversine import haversine


class Problem:
    def __init__(
        self,
        file,
        num_vessels,
        charge_capacity,
        velocity,
        consumption_rate,
        vessel_cost,
        station_cost,
        num_time_windows,
    ) -> None:
        self._instance = self._read_file(file)
        self._num_vessels = num_vessels
        self._charge_capacity = charge_capacity
        self._velocity = velocity
        self._consumption_rate = consumption_rate
        self._vessel_cost = vessel_cost
        self._station_cost = station_cost
        self._num_time_windows = num_time_windows  # in hours
        self._node_map = self._create_node_map()
        self._demands = self._get_demands()
        self._distances = self._calculate_haversine()
        self._travel_times = self._calculate_travel_times()
        self._time_windows = self._create_time_windows()

    @property
    def num_vessels(self) -> int:
        return self._num_vessels

    @property
    def num_time_windows(self) -> int:
        return self._num_time_windows

    @property
    def distances(self) -> dict[tuple[int, int], float]:
        return self._distances

    @property
    def travel_times(self) -> dict[tuple[int, int], float]:
        return self._travel_times

    @property
    def charge_capacity(self) -> float:
        return self._charge_capacity

    @charge_capacity.setter
    def charge_capacity(self, value: float) -> None:
        self._charge_capacity = value

    @property
    def velocity(self) -> float:
        return self._velocity

    @velocity.setter
    def velocity(self, value: float) -> None:
        self._velocity = value

    @property
    def consumption_rate(self) -> float:
        return self._consumption_rate

    @consumption_rate.setter
    def consumption_rate(self, value: float) -> None:
        self._consumption_rate = value

    @property
    def vessel_cost(self) -> float:
        return self._vessel_cost

    @vessel_cost.setter
    def vessel_cost(self, value: float) -> None:
        self._vessel_cost = value

    @property
    def station_cost(self) -> float:
        return self._station_cost

    @station_cost.setter
    def station_cost(self, value: float) -> None:
        self._station_cost = value

    @property
    def node_map(self) -> dict[int, tuple[float, float]]:
        return self._node_map

    @property
    def time_windows(self) -> dict[int, list[int]]:
        return self._time_windows

    @property
    def demands(self) -> dict[int, float]:
        return self._demands

    @DeprecationWarning
    def _calculate_distances(self) -> dict[tuple[int, int], float]:
        turbines = self._get_locations("turbine")
        stations = self._get_locations("station")
        nodes = {node: coord for node, coord in enumerate(turbines + stations)}
        distances = {}
        for i, coord1 in nodes.items():
            for j, coord2 in nodes.items():
                dx = coord1[0] - coord2[0]
                dy = coord1[1] - coord2[1]
                distances[(i, j)] = (dx * dx + dy * dy) ** 0.5
        return distances

    def _calculate_haversine(self) -> dict[tuple[int, int], float]:
        turbines = self._get_locations("Turbine")
        stations = self._get_locations("Station")
        nodes = {node: coord for node, coord in self._node_map.items()}
        distances = {}
        for i, coord1 in nodes.items():
            for j, coord2 in nodes.items():
                distances[(i, j)] = round(haversine(coord1, coord2, unit="m"), 3)
        return distances

    def _calculate_travel_times(self) -> dict[tuple[int, int], float]:
        return {
            (i, j): (self._distances[(i, j)] / self._velocity) / 3600
            for i, j in self._distances
        }

    def _get_locations(self, kind: str) -> list[tuple[float, float]]:
        locations = []
        for row in self._instance:
            if row:
                if row[-1] == kind:
                    x, y = float(row[2]), float(row[3])
                    locations.append((x, y))
        return locations

    def _get_demands(self) -> dict[int, float]:
        demands = {}
        for row in self._instance:
            if row:
                demands[int(row[0])] = float(row[-2])
        return demands

    def _create_node_map(self) -> dict[int, tuple[float, float]]:
        node_map = {}
        for row in self._instance:
            if row:
                node_map[int(row[0]) + 1] = (float(row[2]), float(row[3]))
        return node_map

    def _create_time_windows(self):
        windows = []
        for i in range(self._num_time_windows):
            if i == 0:
                start = 0.0
            else:
                start = windows[-1][1] + 1
            end = start + 8
            windows.append([start, end])
        return {i: w for i, w in enumerate(windows)}

    def _read_file(self, file: str) -> list[list[str]]:
        with open(file, "r") as file:
            lines = file.readlines()
            lines = [line.strip().split(",") for line in lines]
        return lines[1:]  # skip header
