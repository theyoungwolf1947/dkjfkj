# coding=utf-8
"""
Door module
Puts doors in a plan

"""

import logging
from typing import List, Tuple

from libs.plan.plan import Space, Plan, Edge, Linear, LINEAR_CATEGORIES

from libs.utils.geometry import (
    parallel,
    move_point,
    dot_product
)

DOOR_WIDTH = 90
epsilon = 2

"""
process:
pour chaque pièce de circulation, placer les portes avec un espace de circulation adjacent
nb : 
couloir en priorité
si pas de couloir connecté
*connecter avec une pièce de circulation avec un ordre de priorité
    -entrée
    -salon
    -dining?

*fonctions :
    -place_doors(plan)
    -place_door(space1,space2)
"""


def place_doors(plan: 'Plan'):
    """
    Places the doors in the plan
    Process:
    -for circulation spaces,
        *place doors between the space and adjacent corridors if any
        *place a door between the space and the entrance if it is adjacent
        *else place a door with any adjacent circulation space
    -for non circulation spaces:
        *place a door between the space and a corridor if any
        *else place a door between the space and the entrance if it is adjacent
        *else place a door with any adjacent circulation space
    :param plan:
    :return:
    """

    def _open_space(_space: 'Space'):
        """
        place necessary doors on _space border
        :param _space:
        :return:
        """
        if _space.category.name == "entrance":
            return
        if _space.category.name == "circulation":
            return

        adjacent_circulation_spaces = [adj for adj in _space.adjacent_spaces() if
                                       adj.category.circulation]

        circulation_spaces = [sp for sp in adjacent_circulation_spaces if
                              sp.category.name in ["circulation"]]
        entrance_spaces = [sp for sp in adjacent_circulation_spaces if
                           sp.category.name in ["entrance"]]

        if _space.category.circulation:
            for circulation_space in circulation_spaces:
                place_door_between_two_spaces(_space, circulation_space)
            for entrance_space in entrance_spaces:
                place_door_between_two_spaces(_space, entrance_space)
            if not entrance_spaces and not circulation_spaces and adjacent_circulation_spaces:
                place_door_between_two_spaces(_space, adjacent_circulation_spaces[0])
        else:
            for circulation_space in circulation_spaces:
                place_door_between_two_spaces(_space, circulation_space)
                return
            for entrance_space in entrance_spaces:
                place_door_between_two_spaces(_space, entrance_space)
                return
            if adjacent_circulation_spaces:
                place_door_between_two_spaces(_space, adjacent_circulation_spaces[0])

    mutable_spaces = [sp for sp in plan.spaces if sp.mutable]
    for mutable_space in mutable_spaces:
        _open_space(mutable_space)


def get_door_edges(contact_line: List['Edge'], start: bool = True) -> List['Edge']:
    """
    determines edges of contact_line that will be door linears
    The output list, door_edges, is a list of contiguous edges
    A door has width DOOR_WIDTH unless the length of contact_line is smaller
    :param contact_line:
    :param start:
    :return:
    """

    def _is_edge_of_point(_edge: 'Edge', _point: Tuple):
        """
        checks if point is on the segment defined by edge
        assumes _point belongs to the line defined by _edge
        :param _edge:
        :param _point:
        :return:
        """
        vect1 = (_point[0] - _edge.start.coords[0], _point[1] - _edge.start.coords[1])
        vect2 = (_point[0] - _edge.end.coords[0], _point[1] - _edge.end.coords[1])
        return dot_product(vect1, vect2) < 0

    if not start:
        contact_line = [e.pair for e in contact_line]
        contact_line.reverse()

    # determines door edges
    if contact_line[0].length > DOOR_WIDTH - epsilon:  # deal with snapping
        end_edge = contact_line[0]
    else:
        end_door_point = move_point(contact_line[0].start.coords,
                                    contact_line[0].unit_vector,
                                    DOOR_WIDTH)
        end_edge = list(e for e in contact_line if _is_edge_of_point(e, end_door_point))[0]
    end_index = [i for i in range(len(contact_line)) if contact_line[i] is end_edge][0]
    door_edges = contact_line[:end_index + 1]

    # splits door_edges[-1] if needed, so as to get a proper door width
    end_split_coeff = (DOOR_WIDTH - end_edge.start.distance_to(
        contact_line[0].start)) / (end_edge.length)
    if not 1 >= end_split_coeff >= 0:
        end_split_coeff = 0 * (end_split_coeff < 0) + (end_split_coeff > 1)
    door_edges[-1] = end_edge.split_barycenter(end_split_coeff).previous

    if not start:
        door_edges = [e.pair for e in door_edges]
        door_edges.reverse()

    return door_edges


def place_door_between_two_spaces(space1: 'Space', space2: 'Space'):
    """
    places a door between space1 and space2
    *sets the position of the door
    *sets the aperture direction
    :param space1:
    :param space2:
    :return:
    """

    def _start_side(_contact_line: List['Edge']) -> bool:

        linear_edges = [linear.edge for linear in space1.plan.linears if
                        space1.has_edge(linear.edge) or space2.has_edge(linear.edge)]
        duct_edges = [e for e in space1.edges if
                      e.pair.face and space1.plan.get_space_of_edge(e.pair).category.name == "duct"]
        duct_edges += [e for e in space2.edges if
                       e.pair.face and space2.plan.get_space_of_edge(
                           e.pair).category.name == "duct"]

        all_edges = linear_edges + duct_edges

        dist_to_start = min([_contact_line[0].start.distance_to(e.start) for e in all_edges])
        dist_to_end = min([_contact_line[-1].end.distance_to(e.start) for e in all_edges])

        # dist_to_windows_start = sum(
        #     [_contact_line[0].start.distance_to(linear.edge.start) for linear in space1.plan.linears
        #      if
        #      linear.category.window_type and _contact_line[0].start.distance_to(
        #          linear.edge.start) < 150])
        # dist_to_windows_end = sum(
        #     [_contact_line[-1].start.distance_to(linear.edge.start) for linear in
        #      space1.plan.linears if
        #      linear.category.window_type and _contact_line[-1].start.distance_to(
        #          linear.edge.start) < 150])

        return True if dist_to_start > dist_to_end else False

    # gets contact edges between both spaces
    contact_edges = [edge for edge in space1.edges if edge.pair in space2.edges]
    # reorders contact_edges
    start_index = 0
    for e, edge in enumerate(contact_edges):
        if not space1.previous_edge(edge) in contact_edges:
            start_index = e
            break
    contact_edges = contact_edges[start_index:] + contact_edges[:start_index]

    # gets the longest contact straight portion between both spaces
    lines = [[contact_edges[0]]]
    for edge in contact_edges[1:]:
        if parallel(lines[-1][-1].vector, edge.vector) and edge.start is lines[-1][-1].end:
            lines[-1].append(edge)
        else:
            lines.append([edge])
    contact_line = sorted(lines, key=lambda x: sum(e.length for e in x))[-1]
    contact_length = contact_line[0].start.distance_to(contact_line[-1].end)

    door_edges = []
    if contact_length < DOOR_WIDTH:
        door_edges.append(contact_line[0])
    else:
        door_edges = get_door_edges(contact_line, start=_start_side(contact_line))

    # determines opening sense

    # set linear
    door = Linear(space1.plan, space1.floor, door_edges[0], LINEAR_CATEGORIES["door"])
    if len(door_edges) == 1:
        return
    for door_edge in door_edges[1:]:
        door.add_edge(door_edge)


if __name__ == '__main__':
    import argparse
    from libs.modelers.grid import GRIDS
    from libs.modelers.seed import SEEDERS
    from libs.modelers.corridor import Corridor, CORRIDOR_BUILDING_RULES
    from libs.specification.specification import Specification

    # logging.getLogger().setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--plan_index", help="choose plan index",
                        default=1)

    args = parser.parse_args()
    plan_index = int(args.plan_index)

    plan_name = None
    if plan_index < 10:
        plan_name = '00' + str(plan_index) + ".json"
    elif 10 <= plan_index < 100:
        plan_name = '0' + str(plan_index) + ".json"


    def get_plan(input_file: str = "001.json") -> Tuple['Plan', 'Specification']:

        import libs.io.reader as reader
        import libs.io.writer as writer
        from libs.space_planner.space_planner import SPACE_PLANNERS
        from libs.io.reader import DEFAULT_PLANS_OUTPUT_FOLDER

        folder = DEFAULT_PLANS_OUTPUT_FOLDER

        spec_file_name = input_file[:-5] + "_setup0"
        plan_file_name = input_file

        try:
            new_serialized_data = reader.get_plan_from_json(input_file)
            plan = Plan(input_file[:-5]).deserialize(new_serialized_data)
            spec_dict = reader.get_json_from_file(spec_file_name + ".json",
                                                  folder)
            spec = reader.create_specification_from_data(spec_dict, "new")
            spec.plan = plan
            return plan, spec

        except FileNotFoundError:
            plan = reader.create_plan_from_file(input_file)
            spec = reader.create_specification_from_file(input_file[:-5] + "_setup0" + ".json")

            GRIDS["002"].apply_to(plan)
            # GRIDS['optimal_finer_grid'].apply_to(plan)
            SEEDERS["directional_seeder"].apply_to(plan)
            spec.plan = plan

            space_planner = SPACE_PLANNERS["standard_space_planner"]
            best_solutions = space_planner.apply_to(spec, 3)

            new_spec = space_planner.spec

            if best_solutions:
                solution = best_solutions[0]
                plan = solution.plan
                new_spec.plan = plan
                writer.save_plan_as_json(plan.serialize(), plan_file_name)
                writer.save_as_json(new_spec.serialize(), folder, spec_file_name + ".json")
                return plan, new_spec
            else:
                logging.info("No solution for this plan")


    def main(input_file: str):

        # TODO : à reprendre
        # * 61 : wrong corridor shape

        out = get_plan(input_file)
        plan = out[0]
        spec = out[1]
        plan.name = input_file[:-5]

        # corridor = Corridor(layer_width=25, nb_layer=5)

        corridor = Corridor(corridor_rules=CORRIDOR_BUILDING_RULES["no_cut"]["corridor_rules"],
                            growth_method=CORRIDOR_BUILDING_RULES["no_cut"]["growth_method"])
        corridor.apply_to(plan, spec=spec, show=False)

        print("ENTER DOOR PROCESS")
        bool_place_single_door = False
        if bool_place_single_door:
            cat1 = "bedroom"
            cat2 = "circulation"
            space1 = list(sp for sp in plan.spaces if
                          sp.category.name == cat1)[2]
            space2 = list(sp for sp in plan.spaces if
                          sp.category.name == cat2 and sp in space1.adjacent_spaces())[0]

            place_door_between_two_spaces(space1, space2)
        else:
            place_doors(plan)
        plan.plot()


    plan_name = "001.json"
    main(input_file=plan_name)
