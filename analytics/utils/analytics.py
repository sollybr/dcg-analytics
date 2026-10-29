"""Chart-data generation for /api/analytics/."""
from collections import Counter

from .expansions import get_expansion_type
from .text import natural_sort_key, split_multi


def chart_payload(prefix, pairs):
    """[(label, count), ...] -> {'<prefix>_labels': [...], '<prefix>_data': [...]}"""
    pairs = list(pairs)
    return {
        f"{prefix}_labels": [label for label, _ in pairs],
        f"{prefix}_data": [count for _, count in pairs],
    }


class CardAnalyticsEngine:
    """
    Encapsulates metric generation so metrics can be toggled on or off
    dynamically based on the API request.
    """

    def __init__(self, cards):
        self.cards = cards

    def compute(self, excluded=(), exclude_expansions=(), exclude_subtypes=()):
        """Run every metric whose name isn't in `excluded`; merge the results."""
        metrics = {
            "types": self.get_types,
            "names": self.get_names,
            "colors": self.get_colors,
            "expansions": lambda: self.get_expansions(exclude_prefixes=exclude_expansions),
            "sec_colors": self.get_sec_colors,
            "subtypes": lambda: self.get_subtypes(exclude_subtypes=exclude_subtypes),
        }
        data = {}
        for name, metric in metrics.items():
            if name not in excluded:
                data.update(metric())
        return data

    def get_types(self):
        counter = Counter(
            c.card_type for c in self.cards
            if c.card_type and c.card_type != "-"
        )
        return chart_payload("type", counter.items())

    def get_names(self, limit=15):
	    counter = Counter(c.name or "Unknown" for c in self.cards)
	    top = counter.most_common(limit)
	    top_names = {name for name, _ in top}

	    colors = {name: Counter() for name in top_names}
	    for c in self.cards:
	        name = c.name or "Unknown"
	        if name not in top_names:
	            continue
	        color = (c.color or "Unknown").strip()
	        colors[name].update(split_multi(color) if "/" in color else [color])

	    return {
	        **chart_payload("name", top),
	        "name_colors": {n: dict(cnt.most_common()) for n, cnt in colors.items()},
	    }

    def get_colors(self, multi_limit=10):
        single, multi = Counter(), Counter()

        for c in self.cards:
            color = (c.color or "Unknown").strip()
            if "/" in color:
                multi["/".join(sorted(split_multi(color)))] += 1
            else:
                single[color] += 1

        return {
            **chart_payload("single_color", single.items()),
            **chart_payload("multicolor", multi.most_common(multi_limit)),
        }

    def get_expansions(self, exclude_prefixes=()):
        prefixes = tuple(exclude_prefixes or ())
        counts = Counter()
        types = {}

        for c in self.cards:
            exp = c.expansion or "Other"

            # Skip cards whose expansion starts with an excluded prefix
            if exp.upper().startswith(prefixes):
                continue

            counts[exp] += 1
            if exp not in types:
                types[exp] = get_expansion_type(c.card_number)

        labels = sorted(counts, key=natural_sort_key)
        return {
            "expansion_labels": labels,
            "expansion_data": [counts[e] for e in labels],
            "expansion_types": [types[e] for e in labels],
        }

    def get_sec_colors(self):
        counter = Counter()
        for c in self.cards:
            if "SEC" not in str(c.rarity).upper():
                continue
            color = c.color or "Unknown"
            counter.update(split_multi(color) if "/" in color else [color])
        return chart_payload("sec_color", counter.items())

    def get_subtypes(self, limit=20, exclude_subtypes=()):
        excluded = {s.lower() for s in (exclude_subtypes or ())}
        counter = Counter()
        for c in self.cards:
            for value in split_multi(c.subtype):
                if value != "-" and value.lower() not in excluded:
                    counter[value] += 1
        return chart_payload("subtype", counter.most_common(limit))
