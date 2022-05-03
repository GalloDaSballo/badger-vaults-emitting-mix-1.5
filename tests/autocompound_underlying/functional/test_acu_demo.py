from brownie import *
from helpers.constants import MaxUint256

## TODO: Make test fail by default so dev has to fix

def test_are_you_trying(deployer, user, reward, emitting_strategy, emitting_vault, reward_whale, badgerTree, vault, strategy, want, governance):
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
    assert want.balanceOf(strategy) == 0 ## Most staking invest all, change to above if needed

    ## Send funds to underlying vault to simulate yield
    reward.transfer(emitting_strategy, 1e6, {"from": reward_whale})
    emitting_strategy.harvest({"from": governance})

    ## Claim from tree to the strat
    current_epoch = badgerTree.currentEpoch()

    ## Wait for end of epoch
    chain.sleep(badgerTree.SECONDS_PER_EPOCH() + 1)
    chain.mine()
    badgerTree.startNextEpoch({"from": user})

    ## Claim to Strategy
    badgerTree.claimReward(current_epoch, emitting_vault, reward, strategy)

    ## TEST 2: Is the Harvest profitable?
    harvest = strategy.harvest({"from": governance}) ## NOTE: At time of dev this reverts as we don't have a swap
    event = harvest.events["Harvested"]
    # If it doesn't print, we don't want it
    assert event["amount"] > 0

    ## Optional: Does the strategy emit anything?
    # event = harvest.events["TreeDistribution"]
    # assert event["token"] == reward.address ## Add token you emit
    # assert event["amount"] > 0 ## We want it to emit something


