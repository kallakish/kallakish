
import os
import re
import math
import hashlib
from datetime import datetime, timedelta
pip install pandas openpyxl faker python-dateutil
import pandas as pd
from dateutil.parser import parse as dtparse
from faker import Faker

# --------------------- CONFIG: update these paths ---------------------
dataset_path    = r"/content/9. Sales-Data-Analysis.csv"       # e.g. r"C:\work\data\main_dataset.xlsx" or .csv
attributes_path = r"/content/sales-Data-Analysis.xlsx"    # must be Excel; must include TABLE_COLUMN_NAME & IS_Masked
output_path     = r"/path/to/output/masked_dataset.xlsx"
# ----------------------------------------------------------------------

# Optional: force a specific sheet in the attributes file (None = first sheet)
ATTR_SHEET_NAME = None

# Optional: column name aliases (case-insensitive)
COL_NAME_FIELD_ALIASES = ["TABLE_COLUMN_NAME", "COLUMN_NAME", "FIELD_NAME", "ATTRIBUTE", "NAME"]
IS_MASKED_FIELD_ALIASES = ["IS_MASKED", "IS_MASKED?", "MASK", "MASKED", "IS MASKED", "IS-MASKED"]

# Optional: columns that deserve a specific masking strategy (case-insensitive)
# Choose from: "email", "name", "phone", "address", "city", "state", "postcode", "date", "numeric", "id", "text"
COLUMN_STRATEGY_OVERRIDES = {
    # "customer_email": "email",
    # "first_name": "name",
    # "mobile": "phone",
}

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

fake = Faker()
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_DIGIT_RE = re.compile(r"\d")
POSTCODE_RE = re.compile(r"^[A-Za-z0-9\s-]{3,10}$")
ONLY_LETTERS_RE = re.compile(r"^[A-Za-z\s\.'-]+$")
TOKEN_RE = re.compile(r"^[A-Za-z0-9_\-\.]+$")

def norm(s):
    if s is None:
        return None
    return str(s).strip()

def upper_no_space(s):
    return norm(s).replace(" ", "").upper() if s is not None else None

def pick_field(df, candidates):
    cols_norm = {upper_no_space(c): c for c in df.columns}
    for cand in candidates:
        k = upper_no_space(cand)
        if k in cols_norm:
            return cols_norm[k]
    # try fuzzy contains
    for c in df.columns:
        cu = upper_no_space(c)
        if cu is None:
            continue
        for cand in candidates:
            if upper_no_space(cand) in cu:
                return c
    raise ValueError(f"Could not locate any of these columns in attributes file: {candidates}")

def hash_int(*parts, bits=32):
    h = hashlib.sha256("||".join(map(lambda x: str(x), parts)).encode("utf-8")).digest()
    return int.from_bytes(h[:bits // 8], "big")

def seeded_faker(*parts):
    f = Faker()
    f.seed_instance(hash_int(*parts))
    return f

def looks_like_date(x):
    if pd.isna(x):
        return False
    if isinstance(x, (pd.Timestamp, datetime)):
        return True
    s = str(x)
    try:
        dtparse(s, fuzzy=True)
        return True
    except Exception:
        return False

def to_datetime(x):
    if isinstance(x, (pd.Timestamp, datetime)):
        return pd.to_datetime(x)
    return pd.to_datetime(dtparse(str(x), fuzzy=True))

def decimals_count(x):
    s = str(x)
    if "." in s:
        return len(s.split(".")[1])
    return 0

def preserve_length_text(s, faked):
    """Return faked text trimmed/padded to roughly match length of s."""
    if s is None:
        return s
    target_len = len(str(s))
    t = str(faked)
    if len(t) == target_len:
        return t
    if len(t) > target_len:
        return t[:target_len]
    return (t + " " * target_len)[:target_len]

def mask_email(col, val):
    s = str(val)
    # preserve domain if possible
    try:
        local, domain = s.split("@", 1)
    except ValueError:
        domain = None
    f = seeded_faker(col, s)
    user = f.user_name()
    if domain and re.match(r"^[A-Za-z0-9\.\-\_]+\.[A-Za-z]{2,}$", domain):
        return f"{user}@{domain.lower()}"
    return f.email()

def mask_phone(col, val):
    s = str(val)
    ndigits = len(PHONE_DIGIT_RE.findall(s))
    f = seeded_faker(col, s)
    # generate digits then reapply simple formatting: keep only digits if original was mostly digits
    digits = "".join([str(f.random_digit()) for _ in range(max(ndigits, 7))])
    # basic regrouping similar to mobile length
    if ndigits >= 10:
        # Try to format like international or local: return digits as is
        return digits
    return digits

def mask_address(col, val):
    f = seeded_faker(col, str(val))
    return f.street_address()

def mask_city(col, val):
    f = seeded_faker(col, str(val))
    return f.city()

def mask_state(col, val):
    f = seeded_faker(col, str(val))
    return f.state()

def mask_postcode(col, val):
    f = seeded_faker(col, str(val))
    return f.postcode()

def mask_name(col, val):
    f = seeded_faker(col, str(val))
    return f.name()

def mask_text(col, val):
    f = seeded_faker(col, str(val))
    t = f.sentence(nb_words=6)
    return preserve_length_text(val, t)

def mask_id(col, val):
    """Generate a consistent pseudo-ID with similar length class."""
    s = str(val)
    f = seeded_faker(col, s)
    # If numeric-ish, keep digits
    if s.isdigit():
        # Keep length, avoid leading zeros if original didn't have them
        n = len(s)
        out = "".join(str((hash_int(col, s, i) % 10)) for i in range(n))
        if not s.startswith("0") and out.startswith("0") and n > 1:
            out = "1" + out[1:]
        return out
    # If looks like token (mix), make something similar
    if TOKEN_RE.match(s):
        base = f.bothify("??##??##").replace(" ", "")
        return preserve_length_text(s, base)
    # fallback text
    return mask_text(col, s)

def mask_numeric(col, val):
    try:
        if pd.isna(val):
            return val
    except Exception:
        pass
    try:
        v = float(val)
    except Exception:
        return val
    decs = decimals_count(val)
    # multiplicative noise within ±10% deterministically
    rnd = (hash_int(col, val) % 2001) / 10000.0  # 0.000..0.2001
    factor = 0.9 + rnd  # 0.9 .. 1.1001
    out = v * factor
    if v >= 0 and out < 0:
        out = abs(out)
    if decs > 0:
        return round(out, decs)
    # keep ints as ints if possible
    if float(out).is_integer():
        return int(out)
    return out

def mask_date(col, val):
    dt = to_datetime(val)
    # shift by -365..+365 days deterministically
    delta_days = (hash_int(col, str(val)) % 731) - 365
    return dt + timedelta(days=int(delta_days))

def infer_strategy(colname, sample_value):
    # Column-name hints (override if provided)
    c = colname.lower()
    for k, strat in COLUMN_STRATEGY_OVERRIDES.items():
        if c == k.lower():
            return strat

    if sample_value is not None:
        s = str(sample_value)
        # Strong detectors first
        if EMAIL_RE.match(s):
            return "email"
        if looks_like_date(sample_value):
            return "date"

    # Name-based hints
    if any(tok in c for tok in ["email", "e-mail", "mail"]):
        return "email"
    if any(tok in c for tok in ["phone", "mobile", "tel", "contact", "msisdn"]):
        return "phone"
    if any(tok in c for tok in ["address", "street", "addr", "line1", "line2"]):
        return "address"
    if any(tok in c for tok in ["city", "town"]):
        return "city"
    if any(tok in c for tok in ["state", "province", "county", "region"]):
        return "state"
    if any(tok in c for tok in ["postcode", "postal", "zip", "pincode"]):
        return "postcode"
    if any(tok in c for tok in ["name", "firstname", "lastname", "surname", "contact_name"]):
        return "name"
    if any(tok in c for tok in ["date", "dob", "birth", "created", "updated", "timestamp"]):
        return "date"
    if any(tok in c for tok in ["id", "uuid", "guid", "number", "no."]):
        return "id"

    # Type-based hints
    if pd.api.types.is_numeric_dtype(type(sample_value)) or isinstance(sample_value, (int, float)) or pd.api.types.is_number(sample_value):
        return "numeric"

    if isinstance(sample_value, str):
        if ONLY_LETTERS_RE.match(sample_value) and len(sample_value.split()) <= 3:
            return "name"
        if POSTCODE_RE.match(sample_value) and any(tok in c for tok in ["code", "postcode", "zip"]):
            return "postcode"
        if PHONE_DIGIT_RE.findall(sample_value) and len(PHONE_DIGIT_RE.findall(sample_value)) >= 7:
            return "phone"

    return "text"

def get_masker(strategy):
    return {
        "email":    mask_email,
        "name":     mask_name,
        "phone":    mask_phone,
        "address":  mask_address,
        "city":     mask_city,
        "state":    mask_state,
        "postcode": mask_postcode,
        "date":     mask_date,
        "numeric":  mask_numeric,
        "id":       mask_id,
        "text":     mask_text,
    }.get(strategy, mask_text)

# Cache to ensure same original -> same masked within a column
class ColumnMasker:
    def __init__(self, colname, strategy, sample_value=None):
        self.colname = colname
        self.strategy = strategy
        self.mask_fn = get_masker(strategy)
        self.map = {}

    def mask(self, v):
        if pd.isna(v):
            return v
        key = str(v)
        if key in self.map:
            return self.map[key]
        masked = self.mask_fn(self.colname, v)
        self.map[key] = masked
        return masked

# ----------------------------------------------------------------------
# Load inputs
# ----------------------------------------------------------------------
if not os.path.exists(dataset_path):
    raise FileNotFoundError(f"Dataset not found: {dataset_path}")
if not os.path.exists(attributes_path):
    raise FileNotFoundError(f"Attributes file not found: {attributes_path}")

# Dataset can be Excel or CSV
ext = os.path.splitext(dataset_path)[1].lower()
if ext in [".xls", ".xlsx", ".xlsm", ".xlsb"]:
    df = pd.read_excel(dataset_path)
elif ext in [".csv", ".txt"]:
    df = pd.read_csv(dataset_path)
else:
    raise ValueError(f"Unsupported dataset extension: {ext}")

# Attributes must be Excel
attr = pd.read_excel(attributes_path, sheet_name=ATTR_SHEET_NAME)

# If sheet_name was None, pd.read_excel returns a dict; use the first sheet
if isinstance(attr, dict):
    attr = list(attr.values())[0]


# Find fields in attributes
col_field = pick_field(attr, COL_NAME_FIELD_ALIASES)
mask_field = pick_field(attr, IS_MASKED_FIELD_ALIASES)

# Normalize attribute flags
attr["_COLNAME_NORM"] = attr[col_field].astype(str).str.strip()
attr["_MASK_NORM"] = attr[mask_field].astype(str).str.strip().str.upper()

mask_truthy = {"YES", "Y", "TRUE", "1"}
to_mask_cols = [c for c in attr["_COLNAME_NORM"] if attr.loc[attr["_COLNAME_NORM"] == c, "_MASK_NORM"].iloc[0] in mask_truthy]

# Only mask columns that actually exist in dataset
present_mask_cols = [c for c in to_mask_cols if c in df.columns]

# Build strategy per column
report_rows = []
col_maskers = {}

for col in present_mask_cols:
    # pick a sample value (first non-null)
    sample_val = None
    if not df[col].isna().all():
        sample_val = df.loc[df[col].first_valid_index(), col]
    strategy = infer_strategy(col, sample_val)
    col_maskers[col] = ColumnMasker(col, strategy, sample_val)
    report_rows.append({"column": col, "strategy": strategy})

# Apply masking
df_masked = df.copy()
for col, cm in col_maskers.items():
    df_masked[col] = df[col].map(cm.mask)

# Create output directory if it doesn't exist
output_dir = os.path.dirname(output_path)
if output_dir and not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Save output + report
report_df = pd.DataFrame(report_rows).sort_values("column")
with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
    df_masked.to_excel(writer, index=False, sheet_name="masked_data")
    report_df.to_excel(writer, index=False, sheet_name="_masking_report")

print(f"✅ Masked dataset saved to: {output_path}")
print("Columns masked and strategies used:")
print(report_df.to_string(index=False))
