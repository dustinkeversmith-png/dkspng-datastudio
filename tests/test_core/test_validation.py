import pytest
from app.core.validation import ValidationResult

def test_validation_success():
    result = ValidationResult.success()
    assert result.ok is True
    assert len(result.errors) == 0
    assert len(result.warnings) == 0

def test_validation_failure():
    result = ValidationResult.failure(["missing_key", "invalid_type"])
    assert result.ok is False
    assert len(result.errors) == 2
    assert "missing_key" in result.errors
    assert "invalid_type" in result.errors
    assert len(result.warnings) == 0

def test_validation_with_warnings():
    result = ValidationResult(ok=True, warnings=["deprecated_field"])
    assert result.ok is True
    assert "deprecated_field" in result.warnings
