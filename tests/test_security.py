import brownie


def test_security_flash(strategy, user, reentry_test):
    # should revert because caller is not lender
    with brownie.reverts():
        reentry_test.callOnFlashLoan(strategy)
