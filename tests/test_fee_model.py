from galapagos.execution.fee_model import FeeModel


def test_fee_model_calculates_fee() -> None:
    assert FeeModel(0.001).calculate(10_000) == 10

