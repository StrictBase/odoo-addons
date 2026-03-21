from __future__ import annotations

import re
from babel.numbers import format_currency
from babel.core import Locale

import odoo.tools as tools
import odoo.tools.misc as misc
from odoo.tools.float_utils import float_round


# Keep originals
_original_formatLang = misc.formatLang
_original_format_amount = misc.format_amount



def _get_lang(env, lang_code=None) -> str:
    return (lang_code or env.context.get("lang") or "en_US").replace("-", "_")


def _nbspify(s: str) -> str:
    # Do NOT introduce spaces, only make existing ones non-breaking
    return s.replace(" ", "\u00A0")


def _adjust_currency_pattern(lang: str, digits: int, grouping: bool) -> str:
    """
    Take the locale's standard currency pattern and rewrite the fraction
    part so it uses exactly `digits` decimals, matching Odoo behavior.
    """
    loc = Locale.parse(lang)
    pattern = loc.currency_formats["standard"].pattern  # may contain pos;neg

    def adjust_one(p: str) -> str:
        if not grouping:
            p = p.replace(",", "")

        if digits <= 0:
            p = re.sub(r"\.[0#]+", "", p)
        else:
            if re.search(r"\.[0#]+", p):
                p = re.sub(r"\.[0#]+", "." + ("0" * digits), p)
            else:
                p = p + "." + ("0" * digits)
        return p

    parts = pattern.split(";")
    return ";".join(adjust_one(p) for p in parts)


# ----------------------------------------------------------------------
# formatLang
# ----------------------------------------------------------------------

def formatLang_babel(
    env,
    value,
    digits=2,
    grouping=True,
    dp=None,
    currency_obj=None,
    rounding_method="HALF-EVEN",
    rounding_unit="decimals",
    **kwargs,
):
    if value == "":
        return ""

    if not currency_obj:
        return (_original_formatLang(
            env,
            value,
            digits=digits,
            grouping=grouping,
            dp=dp,
            currency_obj=currency_obj,
            rounding_method=rounding_method,
            rounding_unit=rounding_unit,
            **kwargs,
        ))

    # Let Odoo decide digits exactly
    if rounding_unit == "decimals":
        if dp:
            digits = env["decimal.precision"].precision_get(dp)
        else:
            digits = currency_obj.decimal_places
    else:
        digits = 0

    rounded = float_round(
        value,
        precision_digits=digits,
        rounding_method=rounding_method,
    )

    lang = _get_lang(env)
    pattern = _adjust_currency_pattern(lang, digits, grouping)

    try:
        s = format_currency(
            rounded,
            currency_obj.name,
            locale=lang,
            currency_digits=False,
            format=pattern,
        )
        return (_nbspify(s))
    except Exception:
        return (_original_formatLang(
            env,
            value,
            digits=digits,
            grouping=grouping,
            dp=dp,
            currency_obj=currency_obj,
            rounding_method=rounding_method,
            rounding_unit=rounding_unit,
            **kwargs,
        ))


# ----------------------------------------------------------------------
# format_amount
# ----------------------------------------------------------------------

def format_amount_babel(
    env,
    amount: float,
    currency,
    lang_code: str | None = None,
    trailing_zeroes: bool = True,
):
    lang = _get_lang(env, lang_code)

    rounded = currency.round(amount)
    digits = currency.decimal_places
    pattern = _adjust_currency_pattern(lang, digits, grouping=True)

    try:
        s = format_currency(
            rounded,
            currency.name,
            locale=lang,
            currency_digits=False,
            format=pattern,
        )

        if not trailing_zeroes and digits > 0:
            dec = Locale.parse(lang).number_symbols.get("decimal", ".")
            s = re.sub(fr"{re.escape(dec)}?0+$", "", s)

        return (_nbspify(s))
    except Exception:
        return (_original_format_amount(
            env,
            amount,
            currency,
            lang_code=lang_code,
            trailing_zeroes=trailing_zeroes,
        ))


# ----------------------------------------------------------------------
# format_decimalized_amount
# ----------------------------------------------------------------------

def format_decimalized_amount_babel(amount: float, currency=None) -> str:
    s = misc.format_decimalized_number(amount)

    if not currency:
        return (s)

    if currency.position == "before":
        return (f"{currency.symbol or ''}{s}")

    return (_nbspify(f"{s} {currency.symbol or ''}"))


# ----------------------------------------------------------------------
# Apply patches
# ----------------------------------------------------------------------

def apply():
    # Canonical locations
    misc.formatLang = formatLang_babel
    misc.format_amount = format_amount_babel
    misc.format_decimalized_amount = format_decimalized_amount_babel

    # Re-exports used by "from odoo.tools import ..."
    tools.formatLang = formatLang_babel
    tools.format_amount = format_amount_babel
    tools.format_decimalized_amount = format_decimalized_amount_babel
