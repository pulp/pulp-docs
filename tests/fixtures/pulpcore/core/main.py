"""
This is a docstring.

Example:
    ```
    my_class = MyClass("foo", 30)
    result = my_class.create("somethinng")
    result_2 = my_function(result, "12", 13)
    print(result_2)
    ```
"""

import typing as t

SOME_CONSTANT = 123
OTHER_CONSTANT = True
global_variable = "foobar"
global_dict = {"a": 123, "b": 456, "c": False}


class MyClass:
    """
    My class is awsome.
    """

    def __init__(self, name: str, age: int):
        """
        This generates a MyClass instance.

        Args:
            name: The name of the class
            age: The age of the class.
        Raises:
            ValueError: If name or age is invalid
        """
        self.name = name
        self.age = age

    def get(self, object: t.Any) -> t.Any:
        """This is my method"""

    def create(self, overwrite: bool) -> None:
        """This is my method"""

    def update(self, object: t.Any) -> int:
        """This is my method"""

    def delete(self, object: t.Any) -> str:
        """This is my method"""


def my_function(a: int, b: str, c: float):
    """
    This is a utility function

    Args:
        a: Integer number presenting something.
        b: Another number but as a string.
        c: Yet another number, but as a float.
    """
