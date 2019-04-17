# coding=utf-8
"""
Specification module
Describes the specifications of the different spaces
"""

from libs.plan.category import SpaceCategory
from libs.plan.plan import Plan
from libs.specification.size import Size

from typing import List, Optional, Dict


class Specification:
    """
    The wishes of the user describing its flan
    """

    def __init__(self, name: str = '', plan: Optional[Plan] = None,
                 items: Optional[List['Item']] = None):
        self.name = name
        self.plan = plan
        self.items = items or []
        self.init_id()

    def __repr__(self):
        output = 'Specification: ' + self.name + '\n'
        for item in self.items:
            output += str(item.id) + ' • ' + item.__repr__() + '\n'

        return output

    def init_id(self, category_name_list: Optional[List[str]] = None) -> None:
        """
        Returns the number of rooms from the specification
        :return:
        """
        if category_name_list:
            new_items_list = []
            i = 0
            for name in category_name_list:
                for item in self.items:
                    if item.category.name == name:
                        item.id = i
                        i += 1
                        new_items_list.append(item)
            self.items = new_items_list
        else:
            i = 0
            for item in self.items:
                item.id = i
                i += 1

    @property
    def number_of_items(self):
        """
        Returns the number of rooms from the specification
        :return:
        """
        return len(self.items)

    @property
    def typology(self):
        """
        Returns the typology of the specification
        :return:
        """
        apartment_type = 1
        for item in self.items:
            if item.category.name in ['bedroom', 'study']:
                apartment_type += 1
        return apartment_type

    def category_items(self, category_name: str) -> ['Item']:
        """
        Returns the items of the category given
        :return:
        """
        items_list = []
        for item in self.items:
            if item.category.name == category_name:
                items_list.append(item)
        return items_list

    def add_item(self, value: 'Item'):
        """
        Adds a specification item to the specification
        :param value:
        :return:
        """
        value.id = len(self.items)
        self.items.append(value)

    def serialize(self) -> Dict:
        """
        Serialize the specification
        :return:
        """
        return {"rooms": [i.serialize() for i in self.items]}


class Item:
    """
    The items of the specification
    """

    def __init__(self, category: SpaceCategory,
                 variant: str, min_size: 'Size', max_size: 'Size',
                 opens_on: Optional[List['str']] = None, linked_to: Optional[List['str']] = None,
                 tags: Optional[List['str']] = None):
        self.category = category
        self.variant = variant
        self.min_size = min_size
        self.max_size = max_size
        self.opens_on = opens_on or []
        self.linked_to = linked_to or []
        self.tags = tags or []
        self.id = 0

    def __repr__(self):
        return 'Item: ' + self.category.name + ' ' + self.variant + ', Area : ' + \
               str(self.required_area)

    @property
    def required_area(self) -> float:
        """
        Returns the required size of the item
        :return:
        """
        return (self.min_size.area + self.max_size.area)/2

    def serialize(self) -> Dict:
        """
        Returns the dictionary format to save as json
        format :    {
                      "linkedTo": [],
                      "opensOn": [],
                      "requiredArea": {
                        "max": 100000,
                        "min": 80000
                      },
                      "tags": [],
                      "type": "bedroom",
                      "variant": "xs"
                    },
        :return:
        """
        output = {
            "linkedTo": self.linked_to,
            "opensOn": self.opens_on,
            "requiredArea": {
                "max": self.max_size.area,
                "min": self.min_size.area
            },
            "tags": self.tags,
            "type": self.category.name,
            "variant": self.variant
        }

        return output
