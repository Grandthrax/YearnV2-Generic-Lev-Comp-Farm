from itertools import count
from brownie import Wei, reverts
from useful_methods import (
    genericStateOfStrat,
    withdraw,
    stateOfStrat,
    genericStateOfVault,
    deposit,
    tend,
    sleep,
    harvest,
)
import random
import brownie


def test_full_generic(largerunningstrategy, strategist, RentryTest):
    reentry = strategist.deploy(RentryTest)
    with brownie.reverts():
        reentry.execute(largerunningstrategy)

