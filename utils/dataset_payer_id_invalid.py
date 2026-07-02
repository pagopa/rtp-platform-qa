"""Invalid payer identifier test dataset.

``INVALID_PAYER_IDS`` is a list of ``(description, value)`` pairs covering every
invalid fiscal-code and VAT-number format that the RTP platform must reject with
a 400 response.  Import it wherever parametrized negative-path assertions on
``payerId`` are needed.

Validation rules enforced by the backend:

- **Fiscal code**: 16 uppercase alphanumeric characters, valid month code
  (A B C D E H L M P R S T), birth day in range 01-31 (male) or 41-71 (female),
  and a correct Luhn-style control character.
- **VAT number**: exactly 11 decimal digits.

Edge-case rationale
-------------------
- **Month codes**: the valid set is non-contiguous.  F and G (between valid E and H)
  and U are the most common off-by-one mistakes in validators.
- **Birth day dead zone**: 32-40 is always invalid (male max = 31, female min = 41).
- **EU VAT prefix**: ``IT`` + 11 digits produces a 13-char string - a common client
  mistake that must be rejected on length grounds before any digit check.
- **Checksum probe** (``cf_wrong_checksum``): syntactically valid CF with a wrong
  control character.  Acts as a TDD sentinel - stays red until the backend enforces
  checksum validation.
"""

INVALID_PAYER_IDS = [
    ("too_short_fiscal_code", "XCGCHS98M13F16"),
    ("too_long_fiscal_code", "XCGCHS98M13F166EXX"),
    ("vat_number_10_digits", "1234567890"),
    ("vat_number_12_digits", "123456789012"),
    ("lowercase_fiscal_code", "xcgchs98m13f166e"),
    ("mixed_case_fiscal_code", "XcGCHS98M13F166E"),
    ("invalid_month_code_F", "XCGCHS98F13F166E"),
    ("invalid_month_code_G", "XCGCHS98G13F166E"),
    ("invalid_month_code_U", "XCGCHS98U13F166E"),
    ("invalid_birth_day_00", "XCGCHS98M00F166E"),
    ("invalid_birth_day_32_male", "XCGCHS98M32F166E"),
    ("invalid_birth_day_40_dead_zone", "XCGCHS98M40F166E"),
    ("invalid_birth_day_72_female", "XCGCHS98M72F166E"),
    ("non_alphanumeric_character", "XCGCHS98M13F166!"),
    ("space_in_fiscal_code", "XCGCHS98M13 F66E"),
    ("cf_with_leading_whitespace", " XCGCHS98M13F166E"),
    ("cf_with_trailing_whitespace", "XCGCHS98M13F166E "),
    ("non_numeric_vat_like", "ABCDEFGHIJK"),
    ("all_zeros_10_digits", "0000000000"),
    ("vat_with_eu_it_prefix", "IT12345678903"),
    ("cf_wrong_checksum", "RSSMRA85T10A562T"),
]
