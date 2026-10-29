# tests/test_field_options.py
from django.test import TestCase

from analytics.models import CardExpansion, DigimonCard
from analytics.utils.field_options import get_field_options


def make_card(number, **fields):
    return DigimonCard.objects.create(
        card_number=number,
        name=fields.pop("name", f"Card {number}"),
        **fields,
    )


def by_value(options):
    return {o["value"]: o for o in options}


class ExpansionFieldOptionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Promos: one code, many names.
        for name in ("Winter Promo 2023", "Tamer Party", "Digimon Card Game Tournament Pack"):
            CardExpansion.objects.create(expansion_code="P", expansion_name=name)
        for i in range(2):
            make_card(f"P-{i:03}", expansion="P")
        
        CardExpansion.objects.create(expansion_code="BT07", expansion_name="New Awakening")
        CardExpansion.objects.create(expansion_code="BT08", expansion_name="Ultimate Power")
        CardExpansion.objects.create(expansion_code="BT09", expansion_name="Renewed Hope")
        # Merged regional release: one code, two names.
        CardExpansion.objects.create(expansion_code="EX01", expansion_name="Classic Collection")
        CardExpansion.objects.create(expansion_code="EX01", expansion_name="Alternative Being")
        # Stored lower case in CardExpansion, upper case on the cards.
        CardExpansion.objects.create(expansion_code="bt10", expansion_name="Xros Encounter")

        for i in range(2):
            make_card(f"BT07-{i:03}", expansion="BT07")
        for i in range(3):
            make_card(f"BT08-{i:03}", expansion="BT08")
        for i in range(5):
            make_card(f"BT09-{i:03}", expansion="BT09")
        make_card("EX01-001", expansion="EX01")
        make_card("BT10-001", expansion="BT10")
        # No CardExpansion row at all.
        make_card("ST01-001", expansion="ST01")
        # Empty / placeholder values must never show up.
        make_card("X-001", expansion="")
        make_card("X-002", expansion="-")

    def test_promo_label_is_fixed_not_a_list_of_names(self):
        options = by_value(get_field_options("expansion", ""))
        self.assertEqual(options["P"]["label"], "Promos")

    def test_promo_found_by_any_of_its_names(self):
        for query in ("winter", "tamer", "tournament"):
            with self.subTest(query=query):
                options = get_field_options("expansion", query)
                self.assertEqual([o["value"] for o in options], ["P"])
                self.assertEqual(options[0]["label"], "Promos")

    def test_promo_found_by_its_label(self):
        options = get_field_options("expansion", "promos")
        self.assertEqual([o["value"] for o in options], ["P"])
        
    def test_code_substring_still_matches(self):
        options = by_value(get_field_options("expansion", "bt0"))
        self.assertEqual(set(options), {"BT07", "BT08", "BT09"})

    def test_matches_by_expansion_name(self):
        options = get_field_options("expansion", "awakening")
        self.assertEqual([o["value"] for o in options], ["BT07"])
        self.assertEqual(options[0]["label"], "New Awakening")
        self.assertEqual(options[0]["count"], 2)

    def test_name_match_is_case_insensitive(self):
        options = get_field_options("expansion", "NEW AWA")
        self.assertEqual([o["value"] for o in options], ["BT07"])

    def test_name_match_does_not_return_unrelated_codes(self):
        options = by_value(get_field_options("expansion", "power"))
        self.assertEqual(set(options), {"BT08"})

    def test_label_falls_back_to_code_without_expansion_row(self):
        options = by_value(get_field_options("expansion", "st01"))
        self.assertEqual(options["ST01"]["label"], "ST01")

    def test_merged_expansion_joins_names(self):
        options = by_value(get_field_options("expansion", "ex01"))
        label = options["EX01"]["label"]
        self.assertIn("Classic Collection", label)
        self.assertIn("Alternative Being", label)
        self.assertEqual(label, "Alternative Being / Classic Collection")

    def test_merged_expansion_matches_either_name(self):
        for query in ("classic", "alternative"):
            with self.subTest(query=query):
                options = get_field_options("expansion", query)
                self.assertEqual([o["value"] for o in options], ["EX01"])

    def test_name_prefix_ranks_before_higher_count_substring(self):
        # "Renewed Hope" (BT09, 5 cards) only contains "new"; "New Awakening"
        # (BT07, 2 cards) starts with it, so it must come first.
        options = get_field_options("expansion", "new")
        self.assertEqual([o["value"] for o in options][:2], ["BT07", "BT09"])

    def test_code_prefix_still_ranks_first(self):
        options = get_field_options("expansion", "bt0")
        # No prefix advantage between them, so ordering falls back to count.
        self.assertEqual([o["value"] for o in options], ["BT09", "BT08", "BT07"])

    def test_name_search_works_when_code_case_differs(self):
        options = get_field_options("expansion", "xros")
        self.assertEqual([o["value"] for o in options], ["BT10"])
        self.assertEqual(options[0]["label"], "Xros Encounter")

    def test_empty_and_placeholder_values_excluded(self):
        values = {o["value"] for o in get_field_options("expansion", "")}
        self.assertNotIn("", values)
        self.assertNotIn("-", values)

    def test_empty_query_returns_all_expansions_with_labels(self):
        options = by_value(get_field_options("expansion", ""))
        self.assertEqual(options["BT09"]["label"], "Renewed Hope")
        self.assertEqual(options["BT09"]["count"], 5)

    def test_limit_is_applied(self):
        self.assertEqual(len(get_field_options("expansion", "", limit=2)), 2)

    def test_no_match_returns_empty_list(self):
        self.assertEqual(get_field_options("expansion", "zzzz"), [])


class OtherFieldOptionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        CardExpansion.objects.create(expansion_code="BT07", expansion_name="New Awakening")
        make_card("BT07-001", expansion="BT07", rarity="Rare", color="Red/Blue",
                  subtype="Vaccine/Data")
        make_card("BT07-002", expansion="BT07", rarity="Rare", color="Red",
                  subtype="Vaccine")
        make_card("BT07-003", expansion="BT07", rarity="Common", color="-")

    def test_label_equals_value_for_non_expansion_fields(self):
        for option in get_field_options("rarity", ""):
            self.assertEqual(option["label"], option["value"])

    def test_expansion_names_do_not_affect_other_fields(self):
        # "awakening" is an expansion name, not a rarity.
        self.assertEqual(get_field_options("rarity", "awakening"), [])

    def test_split_field_counts_each_part(self):
        options = by_value(get_field_options("color", ""))
        self.assertEqual(options["Red"]["count"], 2)
        self.assertEqual(options["Blue"]["count"], 1)
        self.assertNotIn("Red/Blue", options)
        self.assertNotIn("-", options)

    def test_split_field_substring_match(self):
        options = by_value(get_field_options("subtype", "vac"))
        self.assertEqual(set(options), {"Vaccine"})
        
    def test_override_does_not_leak_into_other_fields(self):
        make_card("BT07-004", expansion="BT07", rarity="P")
        options = by_value(get_field_options("rarity", "p"))
        self.assertEqual(options["P"]["label"], "P")        