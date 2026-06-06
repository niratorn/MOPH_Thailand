"""moph_report — validation & reporting tools for MOPH Thailand 43-file datasets.

This package helps healthcare workers and hospital IT staff check the standard
"43 แฟ้ม" (43-file) export against MOPH/HDC structure rules *before* submitting,
catching common errors (missing fields, bad dates, invalid codes, broken
national-ID check digits, duplicate keys) that would otherwise cause rejected
submissions and manual rework.
"""

__version__ = "0.1.0"
