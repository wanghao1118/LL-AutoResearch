from __future__ import annotations

from collections import defaultdict
from statistics import fmean, stdev

from .model import Aggregate, Observation, ReportedSummary


def aggregate(observations: list[Observation | ReportedSummary]) -> list[Aggregate]:
    buckets: dict[tuple, list[Observation | ReportedSummary]] = defaultdict(list)
    for item in observations:
        key = (
            item.method, item.dataset, item.metric, item.setting, item.group,
            tuple(sorted(item.dimensions.items())),
        )
        buckets[key].append(item)

    output: list[Aggregate] = []
    for (method, dataset, metric, setting, group, dimensions), items in buckets.items():
        summaries = [item for item in items if isinstance(item, ReportedSummary)]
        if summaries:
            if len(items) != 1:
                raise ValueError(
                    "reported summary cannot be mixed with observations or another summary for "
                    f"method={method}, dataset={dataset}, metric={metric}, setting={setting}"
                )
            summary = summaries[0]
            output.append(Aggregate(
                method=method,
                method_source_fields=(summary.method_source_field,),
                dataset=dataset,
                metric=metric,
                setting=setting,
                group=group,
                dimensions=dict(dimensions),
                mean=summary.mean,
                sd=summary.sd,
                n=summary.n,
                values=(),
                run_ids=(),
                sources=(summary.source,) if summary.source else (),
                aggregation_source="reported_summary",
            ))
            continue
        raw_items = [item for item in items if isinstance(item, Observation)]
        values = tuple(item.value for item in raw_items)
        run_ids = tuple(item.run for item in raw_items if item.run is not None)
        if run_ids and len(set(run_ids)) != len(run_ids):
            raise ValueError(
                f"duplicate run IDs for method={method}, dataset={dataset}, metric={metric}, setting={setting}"
            )
        output.append(Aggregate(
            method=method,
            method_source_fields=tuple(dict.fromkeys(item.method_source_field for item in raw_items)),
            dataset=dataset,
            metric=metric,
            setting=setting,
            group=group,
            dimensions=dict(dimensions),
            mean=fmean(values),
            sd=stdev(values) if len(values) > 1 else None,
            n=len(values),
            values=values,
            run_ids=run_ids,
            sources=tuple(sorted({item.source for item in raw_items if item.source})),
            aggregation_source="observations",
        ))
    return output
