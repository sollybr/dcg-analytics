import { useEffect, useState } from "react";

import {
    ComboBox,
    Input,
    Label,
    ListBox,
    ListBoxItem,
    Popover,
} from "react-aria-components";
import type { Key } from "react-aria-components";

import { fetchFieldOptions } from "../api";
import type { FieldName } from "../fieldOptions";

import "./autocomplete.css";

type FieldConfig = {
    label: string;
    placeholder: string;
    // Fields with thousands of distinct values (card names) shouldn't be
    // fetched until the user has typed something. Small sets (color,
    // rarity) can show their options straight away.
    minChars: number;
};

const FIELD_CONFIG: Record<FieldName, FieldConfig> = {
    name: {
        label: "Card name",
        placeholder: "Type at least 2 characters...",
        minChars: 2,
    },
    color: { label: "Color", placeholder: "Search colors...", minChars: 0 },
    rarity: { label: "Rarity", placeholder: "Search rarities...", minChars: 0 },
    expansion: {
        label: "Expansion",
        placeholder: "Search expansions...",
        minChars: 0,
    },
    subtype: { label: "Subtype", placeholder: "Search subtypes...", minChars: 0 },
    card_type: {
        label: "Card type",
        placeholder: "Search card types...",
        minChars: 0,
    },
};

const DEBOUNCE_MS = 250;

type Suggestion = {
    id: string;
    label: string;
    count?: number;
};

type SearchResult = {
    query: string;
    items: Suggestion[];
    error: boolean;
};

type Props = {
    context?: FieldName;
    // Override the per-field defaults in FIELD_CONFIG.
    label?: string;
    placeholder?: string;
    // Starting text; use it to restore the input if the parent remounts this.
    initialValue?: string;
    // Fires when a suggestion is picked.
    onSelect?: (value: string) => void;
    // Fires on every keystroke, so a parent can also accept free text.
    onInputChange?: (value: string) => void;
};

export function CardAutocomplete({ context = "name", ...rest }: Props) {
    // Keyed by context so the input and results reset when it changes.
    return <FieldAutocomplete key={context} context={context} {...rest} />;
}

function FieldAutocomplete({
    context,
    label: labelOverride,
    placeholder: placeholderOverride,
    initialValue = "",
    onSelect,
    onInputChange,
}: Props & { context: FieldName }) {
    const config = FIELD_CONFIG[context];
    const label = labelOverride ?? config.label;
    const placeholder = placeholderOverride ?? config.placeholder;
    const { minChars } = config;

    const [inputValue, setInputValue] = useState(initialValue);
    const [result, setResult] = useState<SearchResult | null>(null);

    const query = inputValue.trim();
    const tooShort = query.length < minChars;

    // Only trust a result that belongs to what's currently typed.
    const current = result && result.query === query ? result : null;
    const hasCurrent = current !== null;

    useEffect(() => {
        if (query.length < minChars || hasCurrent) {
            return;
        }

        // Debounced; cleanup cancels both the timer and any in-flight
        // request, so a slow response for an old query can't land late.
        const controller = new AbortController();

        const timer = window.setTimeout(async () => {
            try {
                const response = await fetchFieldOptions(
                    context,
                    query,
                    controller.signal
                );

                setResult({
                    query,
                    error: false,
                    items: response.options.map((option) => ({
                        id: option.value,
                        label: option.value,
                        count: option.count,
                    })),
                });
            } catch {
                if (controller.signal.aborted) {
                    return;
                }

                setResult({ query, items: [], error: true });
            }
        }, DEBOUNCE_MS);

        return () => {
            window.clearTimeout(timer);
            controller.abort();
        };
    }, [query, context, minChars, hasCurrent]);

    const visibleItems: Suggestion[] =
        !tooShort && current ? current.items : [];

    return (
        <ComboBox
            className="field-autocomplete"
            allowsCustomValue
            allowsEmptyCollection
            menuTrigger={minChars === 0 ? "focus" : "input"}
            items={visibleItems}
            inputValue={inputValue}
            onInputChange={(value) => {
                setInputValue(value);
                onInputChange?.(value);
            }}
            onSelectionChange={(key: Key | null) => {
                if (key === null) {
                    return;
                }

                const selected = visibleItems.find(
                    (item) => item.id === String(key)
                );

                if (!selected) {
                    return;
                }

                // Seed a result for the picked value so choosing it
                // doesn't trigger another fetch.
                setResult({
                    query: selected.label.trim(),
                    items: [selected],
                    error: false,
                });
                setInputValue(selected.label);
                onSelect?.(selected.id);
            }}
        >
            <Label>{label}</Label>
            <Input placeholder={placeholder} autoComplete="off" />

            <Popover className="field-autocomplete-popover">
                <ListBox
                    className="field-autocomplete-list"
                    renderEmptyState={() => (
                        <div className="field-autocomplete-empty">
                            {tooShort
                                ? `Type at least ${minChars} characters.`
                                : !current
                                    ? "Searching..."
                                    : current.error
                                        ? "Unable to load options."
                                        : "No matches found."}
                        </div>
                    )}
                >
                    {(item) => (
                        <ListBoxItem
                            id={item.id}
                            textValue={item.label}
                            className="field-autocomplete-item"
                        >
                            <span>{item.label}</span>
                            {item.count !== undefined && (
                                <span className="field-autocomplete-count">
                                    {item.count}
                                </span>
                            )}
                        </ListBoxItem>
                    )}
                </ListBox>
            </Popover>
        </ComboBox>
    );
}
