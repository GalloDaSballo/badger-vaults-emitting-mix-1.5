"""
This conftest setups the emitting strategy which is the base of any other strategy you want to test
"""
import time
from brownie import (
    EmittingStrategy,
    BadgerTree,
    TheVault,
    interface,
    accounts,
)
from _setup.config import (
    WANT, 
    WHALE_ADDRESS,

    REWARD,
    REWARD_WHALE,

    PERFORMANCE_FEE_GOVERNANCE,
    PERFORMANCE_FEE_STRATEGIST,
    WITHDRAWAL_FEE,
    MANAGEMENT_FEE,
)
from helpers.constants import MaxUint256
from rich.console import Console

console = Console()

from dotmap import DotMap
import pytest


## Accounts ##
@pytest.fixture
def deployer():
    return accounts[0]

@pytest.fixture
def user():
    return accounts[9]


## Fund the account
@pytest.fixture
def want(deployer):
    """
        TODO: Customize this so you have the token you need for the strat
    """
    TOKEN_ADDRESS = WANT
    token = interface.IERC20Detailed(TOKEN_ADDRESS)
    WHALE = accounts.at(WHALE_ADDRESS, force=True) ## Address with tons of token
    token.transfer(deployer, token.balanceOf(WHALE) // 10, {"from": WHALE})
    return token




@pytest.fixture
def strategist():
    return accounts[1]


@pytest.fixture
def keeper():
    return accounts[2]


@pytest.fixture
def guardian():
    return accounts[3]


@pytest.fixture
def governance():
    return accounts[4]

@pytest.fixture
def treasury():
    return accounts[5]


@pytest.fixture
def proxyAdmin():
    return accounts[6]


@pytest.fixture
def randomUser():
    return accounts[7]


@pytest.fixture
def reward():
    return interface.IERC20Detailed(REWARD)

@pytest.fixture
def reward_whale():
    return accounts.at(REWARD_WHALE, force=True)

@pytest.fixture
def badgerTree(deployer):
  c = BadgerTree.deploy({"from": deployer})

  return c


@pytest.fixture
def deployed(want, deployer, strategist, keeper, guardian, governance, proxyAdmin, randomUser, badgerTree, reward, reward_whale):
    """
    Deploys, vault and test strategy, mock token and wires them up.
    """
    want = want


    vault = TheVault.deploy({"from": deployer})
    vault.initialize(
        want,
        governance,
        keeper,
        guardian,
        governance,
        strategist,
        badgerTree,
        "",
        "",
        [
            PERFORMANCE_FEE_GOVERNANCE,
            PERFORMANCE_FEE_STRATEGIST,
            WITHDRAWAL_FEE,
            MANAGEMENT_FEE,
        ],
    )
    vault.setStrategist(deployer, {"from": governance})
    # NOTE: TheVault starts unpaused

    strategy = EmittingStrategy.deploy({"from": deployer})
    strategy.initialize(vault, [want, REWARD])
    # NOTE: Strategy starts unpaused

    ## Simulate earning by sending a deposit of rewards[0]
    reward.transfer(strategy, 10e18, {"from": reward_whale})

    vault.setStrategy(strategy, {"from": governance})

    return DotMap(
        deployer=deployer,
        vault=vault,
        strategy=strategy,
        want=want,
        governance=governance,
        proxyAdmin=proxyAdmin,
        randomUser=randomUser,
        performanceFeeGovernance=PERFORMANCE_FEE_GOVERNANCE,
        performanceFeeStrategist=PERFORMANCE_FEE_STRATEGIST,
        withdrawalFee=WITHDRAWAL_FEE,
        managementFee=MANAGEMENT_FEE,
        badgerTree=badgerTree
    )


## Contracts ##
@pytest.fixture
def vault(deployed):
    return deployed.vault


@pytest.fixture
def strategy(deployed, reward, reward_whale):
    ## Simulate earning by sending a deposit of rewards[0]
    reward.transfer(deployed.strategy, 10e18, {"from": reward_whale}) ## TODO: Remove
    return deployed.strategy


@pytest.fixture
def tokens(deployed):
    return [deployed.want]

### Fees ###
@pytest.fixture
def performanceFeeGovernance(deployed):
    return deployed.performanceFeeGovernance


@pytest.fixture
def performanceFeeStrategist(deployed):
    return deployed.performanceFeeStrategist


@pytest.fixture
def withdrawalFee(deployed):
    return deployed.withdrawalFee


@pytest.fixture
def setup_share_math(deployer, vault, want, governance):

    depositAmount = int(want.balanceOf(deployer) * 0.5)
    assert depositAmount > 0
    want.approve(vault.address, MaxUint256, {"from": deployer})
    vault.deposit(depositAmount, {"from": deployer})

    vault.earn({"from": governance})

    return DotMap(depositAmount=depositAmount)



## Forces reset before each test
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass
