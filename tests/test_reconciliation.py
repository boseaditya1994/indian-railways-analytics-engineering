import pytest

from railway_pipeline.audit.reconciliation import reconcile


def test_reconciliation_accounts_for_source_records() -> None:
    result = reconcile(
        source_count=10, raw_count=7, staging_count=7, mart_count=7, rejected_count=2, duplicate_count=1
    )
    assert result.accounted_for
    assert result.transformations_complete


def test_reconciliation_rejects_negative_counts() -> None:
    with pytest.raises(ValueError):
        reconcile(source_count=-1, raw_count=0, staging_count=0, mart_count=0, rejected_count=0, duplicate_count=0)
