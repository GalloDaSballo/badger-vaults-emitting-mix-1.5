from brownie import *
from helpers.constants import MaxUint256

## TODO: Make test fail by default so dev has to fix

def test_are_you_trying(deployer, user, reward, reward_whale, badgerTree, vault, strategy, want, governance):
    """
    Verifies that you set up the Strategy properly
    """
    # Setup
    startingBalance = want.balanceOf(deployer)

    depositAmount = startingBalance // 2
    assert startingBalance >= depositAmount
    assert startingBalance >= 0
    # End Setup

    # Deposit
    assert want.balanceOf(vault) == 0

    want.approve(vault, MaxUint256, {"from": deployer})
    vault.depositFor(user, depositAmount, {"from": deployer})

    available = vault.available()
    assert available > 0

    vault.earn({"from": governance})

    chain.sleep(10000 * 13)  # Mine so we get some interest

    ## TEST 1: Does the want get used in any way?
    assert want.balanceOf(vault) == depositAmount - available

    # Did the strategy do something with the asset?
    # assert want.balanceOf(strategy) < available

    # Use this if it should invest all
    # assert want.balanceOf(strategy) == 0 ## Most staking invest all, change to above if needed

    # Change to this if the strat is supposed to hodl and do nothing
    assert strategy.balanceOfWant() == depositAmount * vault.toEarnBps() // vault.MAX_BPS()

    ## Simulate earning by sending yield to the underlying emitting vaults strategy
    reward.transfer(underlying_vault_strategy, 10e18, {"from": reward_whale})

    harvest = strategy.harvest({"from": governance})

    ## Optional: Does the strategy emit anything?
    # event = harvest.events["TreeDistribution"]
    # assert event["token"] == reward.address ## Add token you emit
    # assert event["amount"] > 0 ## We want it to emit something

