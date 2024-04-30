from haversine import haversine


class Problem:
    def __init__(
        self,
        file,
    ) -> None:
        self._instance = self._read_file(file)
        (
            self._num_vessels,
            self._charge_capacity,
            self._velocity,
            self._consumption_rate,
            self._vessel_cost,
            self._station_cost,
            self._sailing_cost,
            self._num_time_windows,
        ) = self._get_parameters().values()
        self._nodes = self._get_nodes()
        self._map = self._get_map()
        self._demands = self._get_demands()
        self._distances = self._calculate_haversine()
        self._travel_times = self._calculate_travel_times()
        self._sailing_costs = self._calculate_sailing_costs()
        self._time_windows = self._create_time_windows()
        self._time_window_assignments = {
            w: [] for w in range(int(self._num_time_windows))
        }
        self._num_turbines = len(self._map["Turbines"])
        self._num_stations = len(self._map["Substations"])
        self._turbines = self._map["Turbines"]
        self._stations = self._map["Substations"]
        self._to_and_from_costs = self.compute_to_and_from_costs()
        self._fixed_costs = [self._station_cost for _ in range(self._num_stations)]

    @property
    def map(self) -> dict[int, list[int]]:
        return self._map

    @property
    def num_vessels(self) -> int:
        return self._num_vessels

    @property
    def num_turbines(self) -> int:
        return self._num_turbines

    @property
    def turbines(self) -> list[int]:
        return self._turbines

    @property
    def stations(self) -> list[int]:
        return self._stations

    @property
    def num_stations(self) -> int:
        return self._num_stations

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
    def sailing_costs(self) -> dict[tuple[int, int], float]:
        return self._sailing_costs

    @property
    def to_and_from_costs(self) -> dict[int, dict[int, dict[int, float]]]:
        return self._to_and_from_costs

    @property
    def fixed_costs(self) -> list[float]:
        return self._fixed_costs

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
    def nodes(self) -> dict[int, tuple[float, float]]:
        return self._nodes

    @property
    def time_windows(self) -> dict[int, list[int]]:
        return self._time_windows

    @property
    def demands(self) -> dict[int, float]:
        return self._demands

    @property
    def time_window_assignments(self) -> dict[int, int]:
        return self._time_window_assignments

    @time_window_assignments.setter
    def time_window_assignments(self, assignment: dict[int, list[int]]) -> None:
        self._time_window_assignments = assignment

    def assign_time_window(self, idx: int, tour: int) -> None:
        if idx in self._time_window_assignments:
            self._time_window_assignments[idx].append(tour)
        else:
            self._time_window_assignments[idx] = [tour]

    @DeprecationWarning
    def _calculate_distances(self) -> dict[tuple[int, int], float]:
        turbines = self._get_locations("Turbine")
        stations = self._get_locations("Substation")
        nodes = {node: coord for node, coord in enumerate(turbines + stations)}
        distances = {}
        for i, coord1 in nodes.items():
            for j, coord2 in nodes.items():
                dx = coord1[0] - coord2[0]
                dy = coord1[1] - coord2[1]
                distances[(i, j)] = (dx * dx + dy * dy) ** 0.5
        return distances

    def _calculate_haversine(self) -> dict[tuple[int, int], float]:
        nodes = {node: coord for node, coord in self._nodes.items()}
        distances = {}
        for i, coord1 in nodes.items():
            for j, coord2 in nodes.items():
                distances[(i, j)] = round(haversine(coord1, coord2, unit="m"), 3)
        return distances

    def _calculate_travel_times(self) -> dict[tuple[int, int], float]:
        return {
            (i, j): round(
                (self._distances[(i, j)] / self._velocity) / 3600, 3
            )  # NB: this rounding may be to small
            for i, j in self._distances
        }

    def _calculate_sailing_costs(self) -> dict[tuple[int, int], float]:
        return {
            (i, j): round(
                self._sailing_cost * self._distances[(i, j)], 1
            )  # NB: this rounding may be to small
            for i, j in self._distances
        }

    def _get_locations(self, kind: str) -> list[tuple[float, float]]:
        locations = []
        for row in self._instance:
            if row:
                if row[-1] == kind:
                    longitude, latitude = float(row[3]), float(row[2])
                    locations.append((longitude, latitude))
        return locations

    def _get_demands(self) -> dict[int, float]:
        demands = {}
        for row in self._instance:
            if row:
                demands[int(row[0]) + 1] = float(row[-2])
        return demands

    def _get_nodes(self) -> dict[int, tuple[float, float]]:
        node_map = {}
        for row in self._instance:
            if row:
                node_map[int(row[0]) + 1] = (
                    float(row[3]),
                    float(row[2]),
                )  # (longitude, latitude)
        return node_map

    def _create_time_windows(self):
        windows = []
        for i in range(int(self._num_time_windows)):
            if i == 0:
                start = 0.0
            else:
                start = windows[-1][1] + 1
            end = start + 8
            windows.append([start, end])
        return {i: w for i, w in enumerate(windows)}

    def _get_parameters(self):
        new_instance = []
        parameters = {}
        for row in self._instance:
            if not row[0].isdigit():
                parameters[row[0]] = float(row[1])
            else:
                new_instance.append(row)

        self._instance = new_instance
        return parameters

    def _read_file(self, file: str) -> list[list[str]]:
        with open(file, "r") as file:
            lines = file.readlines()
            lines = [line.strip().split(",") for line in lines]
        return lines[1:]  # skip header

    def _get_map(self) -> dict[int, list[int]]:
        turbines = self._get_locations("Turbine")
        stations = self._get_locations("Substation")
        mapping = {"Turbines": [], "Substations": []}
        for k, v in self._nodes.items():
            if v in turbines:
                mapping["Turbines"].append(k)
            else:
                mapping["Substations"].append(k)
        assert len(mapping["Turbines"]) == len(turbines)
        assert len(mapping["Substations"]) == len(stations)
        return mapping

    def compute_to_and_from_costs(self) -> dict[int, dict[int, dict[int, float]]]:
        to_and_from_costs = {}
        for t1 in self._turbines:
            to_and_from_costs[t1] = {}
            for t2 in self._turbines:
                to_and_from_costs[t1][t2] = {}
                for s in self._stations:
                    to_and_from_cost = (
                        self._sailing_costs[(t1, s)] + self._sailing_costs[(t2, s)]
                    )
                    to_and_from_costs[t1][t2][s] = round(to_and_from_cost, 2)
        return to_and_from_costs
