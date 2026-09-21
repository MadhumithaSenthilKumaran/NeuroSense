"""Compatibility import for the canonical fusion implementation."""

from fusion import CLINICAL_FEATURE_MAP, WEIGHTS, fuse, risk_class_from_probability

__all__ = ["CLINICAL_FEATURE_MAP", "WEIGHTS", "fuse", "risk_class_from_probability"]
