# coding=utf-8
"""
Solution collector

"""
from typing import List
from libs.specification import Specification
from libs.plan import Plan, Space
import logging
from libs.utils.geometry import polygon_distance

CORRIDOR_SIZE = 120


class SolutionsCollector:
    """
    Solutions Collector
    """

    def __init__(self, spec: 'Specification'):
        self.solutions: List['Solution'] = []
        self.spec = spec

    def add_plan(self, plan: 'Plan') -> None:
        """
        add solutions to the list
        :return: None
        """
        sol = Solution(self, plan, len(self.solutions))
        self.solutions.append(sol)

    @property
    def solutions_distance_matrix(self):
        # Distance matrix
        distance_matrix = []
        for i in range(len(self.solutions)):
            distance_matrix.append([])
            for j in range(len(self.solutions)):
                distance_matrix[i].append(0)

        for i, sol1 in enumerate(self.solutions):
            for j, sol2 in enumerate(self.solutions):
                if i < j:
                    distance = sol1.distance(sol2)
                    distance_matrix[i][j] = distance
                    distance_matrix[j][i] = distance

        logging.debug('Distance_matrix : {0}'.format(distance_matrix))
        return distance_matrix

    def find_best_distribution(self) -> list('Solution'):
        best_sol_list = []

        list_scores = []
        for sol in self.solutions:
            list_scores.append(sol.score)

        # Choose the tree best distributions :
        best_score = max(list_scores)
        index_best_sol = list_scores.index(best_score)
        logging.debug('Best solution : index : {0}, score : {1}'.format(index_best_sol, best_score))

        best_sol_list.append(self.solutions[index_best_sol])

        if self.spec.number_of_items <= 4:
            return best_sol_list

        distance_matrix = self.solutions_distance_matrix

        dist_from_best_sol = distance_matrix[index_best_sol]

        second_score = -10e5
        index_second_sol = None
        for i in range(len(self.solutions)):
            if dist_from_best_sol[i] > 30 and list_scores[i] > second_score:
                index_second_sol = i
                second_score = list_scores[i]
        best_sol_list.append(self.solutions[index_second_sol])
        logging.debug('Second solution : index : {0}, score : {1}'.format(index_second_sol,
                                                                          second_score))

        index_third_sol = None
        if index_second_sol:
            dist_from_second_sol = distance_matrix[index_second_sol]

            third_score = -10e5
            for i in range(len(self.solutions)):
                if dist_from_best_sol[i] > 20 and dist_from_second_sol[i] > 20 and \
                        list_scores[i] > third_score:
                    index_third_sol = i
                    third_score = list_scores[i]
            best_sol_list.append(self.solutions[index_third_sol])
            logging.debug('Third solution : index : {0}, score : {1}'.format(index_third_sol,
                                                                             third_score))

        best_distribution_list = [index_best_sol, index_second_sol, index_third_sol]
        for i in best_distribution_list:
            for j in best_distribution_list:
                if i and j:
                    if i < j:
                        logging.debug('Distance {0} {1} : {2}'.format(i, j, distance_matrix[i][j]))

        return best_sol_list


class Solution:
    """
    Space planner Class
    """

    def __init__(self, collector: 'SolutionsCollector', plan: 'Plan', id: float):
        self.id = id
        self.collector = collector
        self.plan = plan
        self.plan.name = self.plan.name[:-5] + '_Solution_Id' + str(self.id)
        self.items_spaces = {}
        self.init_items_spaces()

    def __repr__(self):
        output = 'Solution Id' + str(self.id)
        return output

    def init_items_spaces(self):
        """
        Dict initialization
        """
        for item in self.collector.spec.items:
            for space in self.plan.mutable_spaces:
                if item.category.name == space.category.name:
                    self.items_spaces[item] = space

    def get_rooms(self, category_name: str) -> list('Space'):
        """
        Retrieves all spaces corresponding to the category_name
        :param category_name: str
        :return: List('Spaces')
        """
        rooms_list = []
        for item in self.collector.spec.items:
            if item.category.name == category_name:
                rooms_list.append(self.items_spaces[item])

        return rooms_list

    def _area_score(self) -> float:
        """
        Area score
        :return: score : float
        """
        good_overflow_categories = ['living', 'dining']

        area_score = 0
        area_penalty = 0
        for item in self.collector.spec.items:
            space = self.items_spaces[item]
            # Min < SpaceArea < Max
            if item.min_size.area <= space.area <= item.max_size.area:
                item_area_score = 100
            # good overflow
            elif item.max_size.area < space.area and \
                    space.category.name in good_overflow_categories:
                item_area_score = 100
            # overflow
            else:
                item_area_score = (100 - abs(item.required_area - space.area) /
                                   item.required_area * 100)
                if space.category.name == 'entrance':
                    if space.area < 20000:
                        area_penalty += 1
                elif space.category.name == 'wc':
                    if space.area < 10000:
                        area_penalty += 1
                    elif space.area > item.max_size.area:
                        area_penalty += 3
                elif space.category.name == 'bathroom' or space.category.name == 'wcBathroom':
                    if space.area < 20000:
                        area_penalty += 1
                elif space.category.name == 'bedroom':
                    if space.area < 75000:
                        area_penalty += 1

            # Area score
            area_score += item_area_score
            logging.debug('Area score : {0}, room : {1}'.format(item_area_score, item.id))

        area_score = round(area_score / self.collector.spec.number_of_items, 2) - area_penalty * 20
        logging.debug('Area score : {0}'.format(area_score))
        return area_score

    def _shape_score(self) -> float:
        """
        Shape score
        :return: score : float
        """
        shape_score = 100
        for item in self.collector.spec.items:
            space = self.items_spaces[item]
            sp_space = space.as_sp
            convex_hull = sp_space.convex_hull
            if convex_hull.is_valid and sp_space.is_valid:
                outside = convex_hull.difference(sp_space)
                item_shape_score = min(100, 100 - (
                            (outside.area - sp_space.area / 7) / (sp_space.area / 4) * 100))
                logging.debug('Shape score : {0}, room : {1}'.format(item_shape_score, item.category.name))
            else:
                logging.warning('Invalid shapely space')
                item_shape_score = 100

            shape_score = min(item_shape_score, shape_score)

        return shape_score

    def _good_size_bonus(self) -> float:
        """
        Good ordering items size bonus
        :return: score : float
        """
        for item1 in self.collector.spec.items:
            for item2 in self.collector.spec.items:
                if item1 != item2 and item1.category.name != 'entrance' and \
                        item2.category.name != 'entrance':
                    if item1.required_area < item2.required_area and \
                            self.items_spaces[item1].area > self.items_spaces[item2].area:
                        logging.debug('pbm size : {0}, {1}'.format(item1.category.name, item2.category.name))
                        logging.debug('Size bonus : {0}'.format(0))
                        return 0
        logging.debug('Size bonus : {0}'.format(10))
        return 10

    def _night_and_day_score(self) -> float:
        """
        Night and day score
        TODO : warning duplex
        :return: score : float
        """

        day_list = ['living', 'kitchen', 'cellar', 'dining']

        night_list = ['bedroom', 'bathroom', 'laundry']

        day_polygon = None
        night_polygon = None
        for item in self.collector.spec.items:
            # Day
            if item.category.name in day_list or \
                    (item.category.name == 'wc' and
                     self.items_spaces[item] == self.get_rooms('wc')[0]):
                if not day_polygon:
                    day_polygon = self.items_spaces[item].as_sp
                else:
                    day_polygon = day_polygon.union(self.items_spaces[item].as_sp)

            # Night
            elif item.category.name in night_list or \
                    (item.category.name == 'wc' and
                     self.items_spaces[item] != self.get_rooms('wc')[0]):
                if not night_polygon:
                    night_polygon = self.items_spaces[item].as_sp
                else:
                    night_polygon = night_polygon.union(self.items_spaces[item].as_sp)

        # groups of rooms
        groups_score = 100
        if day_polygon.geom_type != 'Polygon':
            day_polygon = day_polygon.union(
                self.get_rooms('entrance')[0].as_sp.buffer(1))
            if day_polygon.geom_type != 'Polygon':
                groups_score -= 50

        if night_polygon.geom_type != 'Polygon':
            night_polygon_with_entrance = night_polygon.union(
                self.get_rooms('entrance')[0].as_sp.buffer(CORRIDOR_SIZE))
            if night_polygon_with_entrance.geom_type != 'Polygon':
                if (len(night_polygon) > 2 and len(night_polygon_with_entrance) > 2) \
                        or (self.collector.spec.typology <= 2
                            or self.collector.spec.number_of_items < 6):
                    groups_score -= 50
                else:
                    groups_score -= 25

        logging.debug('Night and day score : {0}'.format(groups_score))
        return groups_score

    def _position_score(self) -> float:
        """
        Night and day score
        TODO : warning duplex
        :return: score : float
        """

        position_score = 100
        nbr_room_position_score = 0
        entrance_poly = self.get_rooms('entrance')[0].as_sp
        polygon_bathroom = None
        corridor_poly = None  #TODO
        for item in self.collector.spec.items:
            item_position_score = 0
            if item.category.name == 'wc' and self.items_spaces[item] == self.get_rooms('wc')[0]:
                nbr_room_position_score += 1
                # distance from the entrance
                if True:  # front door in this level:  self.items_spaces[item].level:
                    # distance from the entrance
                    plan_area = self.collector.spec.plan.area
                    criteria = plan_area ** 0.5
                    distance_wc_fd = self.items_spaces[item].as_sp.distance(entrance_poly)
                    if distance_wc_fd < criteria:
                        item_position_score = (criteria-distance_wc_fd) * 100 / criteria
            elif item.category.name == 'bedroom':
                nbr_room_position_score += 1
                # distance from a bedroom / bathroom
                for item_test in self.collector.spec.items:
                    if item_test.category.name == 'bathroom':
                        polygon_bathroom = self.items_spaces[item_test].as_sp
                        if polygon_bathroom.distance(self.items_spaces[item].as_sp) < CORRIDOR_SIZE:
                            item_position_score = 100
                            continue
            if item.category.name == 'wc' or item.category.name == 'bathroom':
                # could be private
                entrance_inter = []
                if True:  # entrance level
                    entrance_inter = entrance_poly.intersection(self.items_spaces[item].as_sp)
                if not entrance_inter and corridor_poly:
                    corridor_inter = corridor_poly.intersection(self.items_spaces[item].as_sp)
                    if not corridor_inter:
                        item_position_score -= 50
                if item.category.name == 'bathroom':
                    nbr_room_position_score += 1
            elif item.category.name == 'living':
                nbr_room_position_score += 1
                if True:  # front door in this level:  self.items_spaces[item].level:
                    # distance from the entrance
                    if entrance_poly.distance(self.items_spaces[item].as_sp) < CORRIDOR_SIZE:
                        item_position_score = 100

            logging.debug('Position score : {0}, room : {1}'.format(item_position_score, item.category.name))
            position_score = position_score + item_position_score

        position_score = position_score / nbr_room_position_score
        logging.debug('Position score : {0}'.format(position_score))

        return position_score

    def _something_inside_score(self) -> float:
        """
        Something inside
        TODO : warning duplex
        :return: score : float
        """
        # INSIDE ROOM
        # duct or bearing wall or pillar or isolated room : inside a room
        something_inside_score = 100
        for item in self.collector.spec.items:
            item_something_inside_score = 100
            # duct or pillar or small bearing wall
            # if self.items_spaces[item].has_holes:
            #     item_something_inside_score = 0
            #     something_inside_score = min(something_inside_score,
            #                                  item_something_inside_score)
            #     logging.debug('Something Inside score : {0}, room : {1}, has_holes'.format(
            #         something_inside_score, item.category.name))
            #     continue
            # isolated room
            list_of_non_concerned_room = ['entrance', 'circulationSpace', 'dressing', 'cellar',
                                          'office', 'laundry']
            space = self.items_spaces[item]
            sp_space = space.as_sp
            convex_hull = sp_space.convex_hull
            for i_item in self.collector.spec.items:
                if i_item != item and not (i_item.category.name in list_of_non_concerned_room):  #TODO level
                    if (convex_hull.intersection(self.items_spaces[i_item].as_sp)).area > (space.area / 8):
                        # Check jroom adjacency
                        other_room_adj = False
                        for j_item in self.collector.spec.items:
                                if j_item != i_item and j_item != item:
                                    if self.items_spaces[item].adjacent_to(self.items_spaces[j_item]):
                                        other_room_adj = True
                        if not other_room_adj:
                            item_something_inside_score = 0
                            something_inside_score = min(something_inside_score,
                                                         item_something_inside_score)
                            logging.debug('Something Inside score : {0}, room : {1}, isolated room'.format(
                                something_inside_score, item.category.name))
                            break

        logging.debug('Something Inside score : {0}'.format(something_inside_score))
        return something_inside_score

    @property
    def score(self) -> float:
        """
        Scoring
        :return: score : float
        """
        solution_score = (self._area_score() + self._shape_score() + self._night_and_day_score()
                          + self._position_score() + self._something_inside_score()) / 5
        solution_score = solution_score - self._good_size_bonus()

        return solution_score

    def distance(self, other_solution: 'Solution') -> float:
        """
        Distance with an other solution
        TODO : warning duplex
        :return: distance : float
        """
        # Day group
        day_list = ['living', 'kitchen', 'dining', 'cellar']
        # Night group
        night_list = ['bedroom', 'bathroom', 'wc', 'laundry', 'dressing', 'office']

        sol_day_poly = None
        other_sol_day_poly = None
        sol_night_poly = None
        other_sol_night_poly = None
        for item in self.collector.spec.items:
            if item.category.name in day_list:
                if not sol_day_poly:
                    sol_day_poly = self.items_spaces[item].as_sp
                else:
                    sol_day_poly.union(self.items_spaces[item].as_sp)
                if not other_sol_day_poly:
                    other_sol_day_poly = other_solution.items_spaces[item].as_sp
                else:
                    other_sol_day_poly.union(other_solution.items_spaces[item].as_sp)

            elif item.category.name in night_list:
                if not sol_night_poly:
                    sol_night_poly = self.items_spaces[item].as_sp
                else:
                    sol_night_poly.union(self.items_spaces[item].as_sp)
                if not other_sol_night_poly:
                    other_sol_night_poly = other_solution.items_spaces[item].as_sp
                else:
                    other_sol_night_poly.union(other_solution.items_spaces[item].as_sp)

        distance = (polygon_distance(sol_day_poly,other_sol_day_poly) +
                    polygon_distance(sol_night_poly, other_sol_night_poly))/2
        return distance
