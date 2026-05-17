from galapagos.execution.slippage_model import SlippageModel


def test_slippage_model_adjusts_long_entry_up() -> None:
    adjusted, slippage = SlippageModel(10).apply(100, "LONG", "entry")
    assert adjusted == 100.1
    assert round(slippage, 4) == 0.1

