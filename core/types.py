"""Type aliases and NewTypes for domain modeling."""
from __future__ import annotations

from typing import NewType, TypeAlias
from pathlib import Path

# Strong type aliases for domain concepts
SiteName: TypeAlias = str
StepName: TypeAlias = str
FieldName: TypeAlias = str
XPathSelector: TypeAlias = str
CSSSelector: TypeAlias = str
URL: TypeAlias = str

# NewTypes for additional type safety
ArtifactPath = NewType("ArtifactPath", Path)
SecretKey = NewType("SecretKey", str)
MetricName = NewType("MetricName", str)
TraceID = NewType("TraceID", str)
