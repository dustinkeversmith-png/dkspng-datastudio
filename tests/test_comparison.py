from app.comparison import comparison_presets


def test_comparison_presets_has_presets():
    result = comparison_presets()
    assert result["status"] == "success"
    assert len(result["presets"]) > 0
