from problem import Problem
import networkx as nx
import matplotlib.pyplot as plt


def visualise(problem: Problem, routes: list, stations: list):
    fig, ax = plt.subplots()
    graph = nx.MultiDiGraph()

    used_stations = list(set(stations))
    turbines = {
        k: v
        for k, v in problem.node_map.items()
        if v in problem._get_locations("Turbine")
    }
    substations = {
        k: v
        for k, v in problem.node_map.items()
        if v in problem._get_locations("Substation")
    }

    nodes = problem.node_map
    edges = create_edge_list(routes, stations)
    graph.add_nodes_from(nodes.keys(), pos=nodes)
    graph.add_edges_from(edges)

    nx.draw_networkx_nodes(
        graph,
        nodes,
        ax=ax,
        nodelist=turbines,
        node_color="cornflowerblue",
        edgecolors="black",
        linewidths=1,
        label="Turbines",
    )
    if used_stations:
        nx.draw_networkx_nodes(
            graph,
            nodes,
            ax=ax,
            nodelist=used_stations,
            node_color="green",
            edgecolors="black",
            linewidths=1,
            label="Used substations",
        )
    if substations:
        nx.draw_networkx_nodes(
            graph,
            nodes,
            ax=ax,
            nodelist=[k for k in substations.keys() if k not in used_stations],
            node_color="gray",
            edgecolors="black",
            linewidths=1,
            label="Unused substations",
        )
    nx.draw_networkx_edges(
        graph,
        nodes,
        ax=ax,
    )
    nx.draw_networkx_labels(
        graph,
        nodes,
        ax=ax,
        font_size=9,
        font_weight="semibold",
        font_family="serif",
    )
    ax.tick_params(
        left=True, bottom=True, labelleft=True, labelbottom=True, labelsize=8
    )
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"Route Visualisation\n{routes}")
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    ax.legend(
        fontsize="small",
        markerscale=0.5,
        loc="upper left",
        bbox_to_anchor=(1, 1),
        fancybox=True,
        shadow=True,
    )
    ax.grid()
    ax.set_axisbelow(True)
    plt.show()


def create_edge_list(route, map):
    separators = [i for i, x in enumerate(route + [0]) if x == 0]
    start_idx = 0  # start index for current route

    edges = []
    num_tours = len(separators)
    for i in range(num_tours):
        # get the current route
        tour = route[start_idx : separators[i]]
        # adjust start index for next iteration
        start_idx = separators[i] + 1

        if len(tour) > 0:
            for j in range(len(tour)):
                if j == 0:
                    edges.append((map[i], tour[j]))
                else:
                    edges.append((tour[j - 1], tour[j]))
            edges.append((tour[-1], map[i]))

    return edges
