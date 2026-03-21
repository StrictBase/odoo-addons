/** @odoo-module **/
import { reactive } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { user } from "@web/core/user";
import { formatFloat, humanNumber } from "@web/core/utils/numbers";
import { nbsp } from "@web/core/utils/strings";
import { session } from "@web/session";


export const currencies = session.currencies || {};
// to make sure code is reading currencies from here
delete session.currencies;

export function getCurrency(id) {
    return currencies[id];
}

export async function getCurrencyRates() {
    const rates = reactive({});

    function recordsToRates(records) {
        return Object.fromEntries(records.map((r) => [r.id, r.inverse_rate]));
    }

    const model = "res.currency";
    const method = "read";
    const url = `/web/dataset/call_kw/${model}/${method}`;
    const context = {
        ...user.context,
        to_currency: user.activeCompany.currency_id,
    };
    const params = {
        model,
        method,
        args: [Object.keys(currencies).map(Number), ["inverse_rate"]],
        kwargs: { context },
    };
    const records = await rpc(url, params, {
        cache: {
            type: "disk",
            update: "once",
            callback: (records, hasChanged) => {
                if (hasChanged) {
                    Object.assign(rates, recordsToRates(records));
                }
            },
        },
    });
    Object.assign(rates, recordsToRates(records));
    return rates;
}

/**
 * Returns a string representing a monetary value. The result takes into account
 * the user settings (to display the correct decimal separator, currency, ...).
 *
 * @param {number} value the value that should be formatted
 * @param {number} [currencyId] the id of the 'res.currency' to use
 * @param {Object} [options]
 *   additional options to override the values in the python description of the
 *   field.
 * @param {Object} [options.data] a mapping of field names to field values,
 *   required with options.currencyField
 * @param {boolean} [options.noSymbol] this currency has not a sympbol
 * @param {boolean} [options.humanReadable] if true, large numbers are formatted
 *   to a human readable format.
 * @param {number} [options.minDigits] see @humanNumber
 * @param {boolean} [options.trailingZeros] if false, numbers will have zeros
 *  to the right of the last non-zero digit hidden
 * @param {[number, number]} [options.digits] the number of digits that should
 *   be used, instead of the default digits precision in the field.  The first
 *   number is always ignored (legacy constraint)
 * @returns {string}
 */

function _getSymbolSeparator(currency) {
    try {
        let lang = document.documentElement.lang || "en-US";
        lang = lang.replace("_", "-");

        const formatter = new Intl.NumberFormat(lang, {
            style: "currency",
            currency: currency.name,
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        });

        const parts = formatter.formatToParts(1);
        const currencyIndex = parts.findIndex((p) => p.type === "currency");
        const integerIndex = parts.findIndex((p) => p.type === "integer");

        if (currencyIndex === -1 || integerIndex === -1) {
            return "";
        }

        const start = Math.min(currencyIndex, integerIndex);
        const end = Math.max(currencyIndex, integerIndex);

        const between = parts
            .slice(start + 1, end)
            .map((p) => p.value)
            .join("");

        return between.replace(/ /g, nbsp);
    } catch {
        // Keep legacy behavior on failure.
        return nbsp;
    }
}

export function formatCurrency(amount, currencyId, options = {}) {
    // In many Odoo contexts (notably x2many list/tree views), currencyId can be:
    // - a numeric id
    // - a many2one value: [id, display_name]
    // - undefined, in which case we must resolve from options.currencyField + options.data
    function _extractId(value) {
        if (Array.isArray(value)) {
            return value[0];
        }
        if (value && typeof value === "object") {
            if ("id" in value) {
                return value.id;
            }
            if ("resId" in value) {
                return value.resId;
            }
        }
        return value;
    }

    let resolvedCurrencyId = _extractId(currencyId);
    if (!resolvedCurrencyId && options.currencyField && options.data) {
        resolvedCurrencyId = _extractId(options.data[options.currencyField]);
    }

    const currency = getCurrency(resolvedCurrencyId);
    const digits = options.digits || (currency && currency.digits);

    let formattedAmount;
    if (options.humanReadable) {
        formattedAmount = humanNumber(amount, {
            decimals: digits ? digits[1] : 2,
            minDigits: options.minDigits,
        });
    } else {
        formattedAmount = formatFloat(amount, { digits, trailingZeros: options.trailingZeros });
    }

    if (!currency || options.noSymbol) {
        return formattedAmount;
    }
    const formatted = [currency.symbol, formattedAmount];
    if (currency.position === "after") {
        formatted.reverse();
    }
    const sep = _getSymbolSeparator(currency);
    return formatted.join(sep);
}

