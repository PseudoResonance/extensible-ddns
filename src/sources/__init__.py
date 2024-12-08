from dataclasses import dataclass


@dataclass(frozen=True)
class SourceResult:
    status: bool
    ips: list[str]
