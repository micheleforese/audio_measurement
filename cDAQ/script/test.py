import click
from cDAQ.timer import timeit
from cDAQ.console import console


def say_hi():
    console.print("HI!!")


@click.command(help="Test for Timer class")
def testTimer():

    decorator = timeit()
    timed_say_hi = decorator(say_hi)

    timed_say_hi()

    timeit()(say_hi)()
