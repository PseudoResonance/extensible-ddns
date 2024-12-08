from dataclasses import dataclass, field
from frozendict import frozendict
import numpy as np

from sources import SourceResult


@dataclass(frozen=True)
class Record:
    content: str
    type: str
    domain: str
    ttl: int
    extra: frozendict = field(default_factory=frozendict)
    internal: frozendict = field(default_factory=frozendict, compare=False)

    def compare(self, other):
        if not isinstance(other, Record):
            raise NotImplemented
        score = 0
        if self.domain == other.domain:
            score += 100
        # Some providers may not support changing record type
        if self.type != other.type:
            return -1
        if self.content == other.content:
            score += 1
        if self.ttl == other.ttl:
            score += 2
        for key, value in self.extra.items():
            if key in other.extra and value == other.extra[key]:
                score += 2
        return score


@dataclass(frozen=True)
class RecordSet:
    current: Record
    updated: Record


def calculate_records(configRecords, ipRecord: dict[str, SourceResult]) -> tuple[list[Record], set[str]]:
    plan = []
    ignored_sources = set()
    for record in configRecords:
        for type in record["sources"]:
            if record["sources"][type] not in ipRecord:
                print(f"No IPs from source: {record["sources"][type]}")
            elif not ipRecord[record["sources"][type]].status:
                print(f"Source failed to run, ignoring this time: {
                      record["sources"][type]}")
                ignored_sources.add(record["sources"][type])
            else:
                extra = {}
                if "extra" in record:
                    extra = record["extra"]
                ips = ipRecord[record["sources"][type]].ips
                for ip in ips:
                    plan.append(
                        Record(ip, type, record["domain"], record["ttl"], frozendict(extra), frozendict({"source": record["sources"][type]})))
    return plan, ignored_sources


def calculate_update(to_add: list[Record], to_delete: list[Record]) -> tuple[list[RecordSet], list[Record], list[Record]]:
    to_update = []
    # From https://stackoverflow.com/a/26300858
    scores = np.zeros((len(to_delete), len(to_add)))
    # Scores will become a 2D matrix where scores[i, j]=value means that
    # value is how similar thing[i] and thing[j] are.
    for i in range(len(to_delete)):
        for j in range(len(to_add)):
            scores[i, j] = (to_delete[i].compare(to_add[j]))

    # From https://stackoverflow.com/a/30577520
    # Flatten score array
    # Sort scores by indices
    # Unravel array back into original shape
    # Stack arrays to pair i/j values
    # Flip array to find highest score
    sorted = np.flip(np.dstack(np.unravel_index(
        np.argsort(scores.ravel()), (len(to_delete), len(to_add))))[0], 0)

    used_to_delete = []
    used_to_add = []

    for pair in sorted:
        if (pair[0] not in used_to_delete) and (pair[1] not in used_to_add) and (scores[pair[0]][pair[1]] >= 0):
            to_update.append(RecordSet(to_delete[pair[0]], to_add[pair[1]]))
            used_to_delete.append(pair[0])
            used_to_add.append(pair[1])
    return to_update, np.delete(to_add, used_to_add), np.delete(to_delete, used_to_delete)


def calculate_diff(plan, state, can_update=False) -> tuple[list[RecordSet], list[Record], list[Record]]:
    to_update = []
    to_add = list(set(plan) - set(state))
    to_delete = list(set(state) - set(plan))
    if can_update:
        to_update, to_add, to_delete = calculate_update(to_add, to_delete)
    return to_update, to_add, to_delete
