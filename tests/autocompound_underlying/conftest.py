import time

from brownie import (
    AutoCompoundingStrategyUnderlying,
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

## Fund the account
@pytest.fixture
def want(deployer):
    """
        TODO: Customize this so you have the token you need for the strat
    """
    TOKEN_ADDRESS = WANT
    token = interface.IERC20Detailed(TOKEN_ADDRESS)
    WHALE = accounts.at(WHALE_ADDRESS, force=True) ## Address with tons of token

    token.transfer(deployer, token.balanceOf(WHALE), {"from": WHALE})
    return token


@pytest.fixture
def deployed_autocompound(deployed, want, deployer, strategist, keeper, guardian, governance, proxyAdmin, randomUser, badgerTree, reward, reward_whale):
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

    strategy = AutoCompoundingStrategyUnderlying.deploy({"from": deployer})
    
    ## deployed.vault is the emitting vault
    strategy.initialize(vault, [want, REWARD, deployed.vault], {"from": deployer})
    # NOTE: Strategy starts unpaused

    vault.setStrategy(strategy, {"from": governance})

    return DotMap(
        deployer=deployer,
        vault=vault,
        emittingVault=deployed.vault,
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
def vault(deployed_autocompound):
    return deployed_autocompound.vault

@pytest.fixture
def emitting_vault(deployed_autocompound):
    return deployed_autocompound.emittingVault

@pytest.fixture
def emitting_strategy(emitting_vault):
    return EmittingStrategy.at(emitting_vault.strategy())

@pytest.fixture
def strategy(deployed_autocompound):
    return deployed_autocompound.strategy


@pytest.fixture
def tokens(deployed_autocompound):
    return [deployed_autocompound.want]

### Fees ###
@pytest.fixture
def performanceFeeGovernance(deployed):
    return deployed.performanceFeeGovernance


@pytest.fixture
def performanceFeeStrategist(deployed_autocompound):
    return deployed_autocompound.performanceFeeStrategist


@pytest.fixture
def withdrawalFee(deployed_autocompound):
    return deployed_autocompound.withdrawalFee


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
