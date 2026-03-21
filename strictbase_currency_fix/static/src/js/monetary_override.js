/** @odoo-module **/

import { registry } from "@web/core/registry";
import { getCurrency } from "@web/core/currency";
import { MonetaryField } from "@web/views/fields/monetary/monetary_field";
import { patch } from "@web/core/utils/patch";
import { onWillRender } from "@odoo/owl";




function normalizeCurrencyId(currencyId, options = {}) {
    // Odoo can pass a currency as a many2one value (e.g. [id, "EUR"]).
    if (Array.isArray(currencyId)) {
        return currencyId[0];
    }

    // Or as an object in some contexts.
    if (currencyId && typeof currencyId === "object" && currencyId.id) {
        return currencyId.id;
    }

    if (currencyId) {
        return currencyId;
    }

    // Some list/tree contexts do not provide options.currencyId nor options.currencyField,
    // but still include the currency as a field on the row data. Try common field names.
    const tryContainers = [];
    if (options.data) {
        tryContainers.push(options.data);
    }
    if (options.record && options.record.data) {
        tryContainers.push(options.record.data);
    }
    if (options.record && typeof options.record === "object") {
        tryContainers.push(options.record);
    }
    for (const container of tryContainers) {
        if (!container) {
            continue;
        }
        for (const key of ["currency_id", "currencyId", "currency", "currencyID"]) {
            if (Object.prototype.hasOwnProperty.call(container, key) && container[key]) {
                const raw = container[key];
                if (Array.isArray(raw)) {
                    return raw[0];
                }
                if (raw && typeof raw === "object" && raw.id) {
                    return raw.id;
                }
                return raw;
            }
        }
    }

    // Fallback used in list/tree renderers: options.currencyField + record/data.
    // Depending on the renderer, the record payload may be passed as:
    // - options.data
    // - options.record.data
    // - options.record (already the data object in some contexts)
    if (options.currencyField) {
        let container = null;

        if (options.data) {
            container = options.data;
        } else if (options.record && options.record.data) {
            container = options.record.data;
        } else if (options.record && typeof options.record === "object") {
            container = options.record;
        }

        if (container && Object.prototype.hasOwnProperty.call(container, options.currencyField)) {
            const raw = container[options.currencyField];
            if (Array.isArray(raw)) {
                return raw[0];
            }
            return raw;
        }
    }

    return currencyId;
}

// -------------------------------------------------------------------------
// 1. SHARED HELPER: Strict Intl Formatting
// -------------------------------------------------------------------------
function getIntlData(value, currencyId, options = {}) {
    // 1. Handle Empty Values (false, null, undefined) -> Empty String
    if (value === false || value === null || value === undefined) {
        return { text: "", config: null };
    }

	const resolvedCurrencyId = normalizeCurrencyId(currencyId, options);
    const currency = getCurrency(resolvedCurrencyId);
    if (!currency) {
        return { text: String(value), config: null };
    }
try {
        let userLang = document.documentElement.lang || "en-US";
        userLang = userLang.replace("_", "-");

        const digits = (currency.digits && currency.digits[1] !== undefined) ? currency.digits[1] : 2;
        
        const formatter = new Intl.NumberFormat(userLang, {
            style: 'currency',
            currency: currency.name,
            minimumFractionDigits: digits,
            maximumFractionDigits: digits,
        });

		// 2. Generate Display String
		const text = formatter.format(value).replace(/ /g, "\u00A0");

        // 3. Analyze Layout (for Edit Mode)
        const parts = formatter.formatToParts(1);
        const symbolIndex = parts.findIndex(p => p.type === 'currency');
        const valueIndex = parts.findIndex(p => p.type === 'integer');
        const isBefore = symbolIndex < valueIndex;

        let hasSpace = false;
        if (isBefore) {
            const next = parts[symbolIndex + 1];
            hasSpace = next && next.type === 'literal' && next.value.trim() === '';
        } else {
            const prev = parts[symbolIndex - 1];
            hasSpace = prev && prev.type === 'literal' && prev.value.trim() === '';
        }

		return {
			text,
            config: { isBefore, hasSpace } 
        };

    } catch (e) {
		return { text: String(value), config: null };
    }
}

// -------------------------------------------------------------------------
// 2. REGISTRY PATCH (Read-Only Lists/Kanbans)
// -------------------------------------------------------------------------
registry.category("formatters").add("monetary", (value, options = {}) => {
	const result = getIntlData(value, options.currencyId, options);
    return result.text;
}, { force: true });


// -------------------------------------------------------------------------
// 2b. FLOAT FORMATTER PATCH
// Some list/tree contexts render currency amounts using the float formatter
// (not the monetary formatter), while still providing currency_id on row data.
// We detect that case and delegate to the currency-aware formatter.
// -------------------------------------------------------------------------
const _formatters = registry.category("formatters");
let _originalFloat = null;
try {
    _originalFloat = _formatters.get("float");
} catch (e) {
    _originalFloat = null;
}

_formatters.add("float", (value, options = {}) => {
    // Only apply currency-aware formatting to specific "unit price" fields.
    // Otherwise we risk turning quantities, delivered, etc. into currency values.
    const fieldName =
        options.fieldName ||
        options.name ||
        (options.field && options.field.name) ||
        (options.field && options.field.fieldName) ||
        "";

    const shouldFormatAsCurrency = fieldName === "price_unit";
    if (shouldFormatAsCurrency) {
        const inferredCurrencyId = normalizeCurrencyId(options.currencyId, options);
        if (inferredCurrencyId) {
            const result = getIntlData(value, inferredCurrencyId, options);
            return result.text;
        }
        // If we expected a currency but could not infer it, still mark it for diagnostics.
        return String(value);
    }

    if (_originalFloat) {
        return _originalFloat(value, options);
    }
    return String(value);
}, { force: true });
// -------------------------------------------------------------------------
// 3. COMPONENT PATCH (Forms, Pricelists, Editable Lists)
// -------------------------------------------------------------------------
patch(MonetaryField.prototype, {
    setup() {
        super.setup();
        // NUCLEAR OPTION: Delete Odoo's XML spacer
        this.nbsp = ""; 
        onWillRender(() => { this.nbsp = ""; });
    },

    get currency() {
        const c = super.currency;
        if (!c) return c;
        
		const data = getIntlData(0, this.currencyId);
        if (data.config) {
            return { ...c, position: data.config.isBefore ? 'before' : 'after' };
        }
        return c;
    },

    get currencySymbol() {
        const c = super.currency;
        if (!c) return "";
        const symbol = c.symbol;

		const data = getIntlData(0, this.currencyId);
        if (data.config && data.config.hasSpace) {
            return data.config.isBefore ? symbol + "\u00A0" : "\u00A0" + symbol;
        }
        return symbol;
    },

    get formattedValue() {
        if (this.props.readonly) {
			const result = getIntlData(this.value, this.currencyId);
            return result.text;
        }
        return super.formattedValue;
    }
});