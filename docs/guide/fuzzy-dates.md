# Fuzzy Dates

Stash v0.30.0+ introduced support for partial dates (fuzzy dates), allowing you to store dates with varying levels of precision. This guide explains how to work with fuzzy dates in the client library.

## What Are Fuzzy Dates?

Fuzzy dates allow you to express dates when you don't know the complete information:

- **Year only**: `"2024"` - You know the year but not the month/day
- **Year-Month**: `"2024-03"` - You know the year and month but not the day
- **Full date**: `"2024-03-15"` - Complete date information

This is particularly useful for:

- Performer birthdates when exact date is unknown
- Scene release dates with only year/month known
- Historical events with approximate dates

## Date Precision Levels

The library defines three precision levels:

```python
from stash_graphql_client.types import DatePrecision

DatePrecision.YEAR   # "YYYY" format (e.g., "2024")
DatePrecision.MONTH  # "YYYY-MM" format (e.g., "2024-03")
DatePrecision.DAY    # "YYYY-MM-DD" format (e.g., "2024-03-15")
```

## Working with Fuzzy Dates

### Creating Fuzzy Dates

```python
from stash_graphql_client.types import FuzzyDate

# Year precision
year_date = FuzzyDate("2024")
print(year_date.precision)  # DatePrecision.YEAR
print(year_date.value)      # "2024"

# Month precision
month_date = FuzzyDate("2024-03")
print(month_date.precision)  # DatePrecision.MONTH
print(month_date.value)      # "2024-03"

# Day precision (full date)
day_date = FuzzyDate("2024-03-15")
print(day_date.precision)  # DatePrecision.DAY
print(day_date.value)      # "2024-03-15"
```

### Validating Date Strings

Use the validation utility to check if a date string is valid:

```python
from stash_graphql_client.types import validate_fuzzy_date

# Valid formats
validate_fuzzy_date("2024")         # True
validate_fuzzy_date("2024-03")      # True
validate_fuzzy_date("2024-03-15")   # True

# Invalid formats
validate_fuzzy_date("2024-3")       # False - month must be zero-padded
validate_fuzzy_date("2024-03-5")    # False - day must be zero-padded
validate_fuzzy_date("24")           # False - year must be 4 digits
validate_fuzzy_date("2024/03/15")   # False - wrong separator
```

### Converting to Python datetime

Convert fuzzy dates to Python datetime objects:

```python
from stash_graphql_client.types import FuzzyDate

# Year precision - defaults to January 1st
year_date = FuzzyDate("2024")
dt = year_date.to_datetime()  # datetime(2024, 1, 1)

# Month precision - defaults to 1st of month
month_date = FuzzyDate("2024-03")
dt = month_date.to_datetime()  # datetime(2024, 3, 1)

# Day precision - exact date
day_date = FuzzyDate("2024-03-15")
dt = day_date.to_datetime()  # datetime(2024, 3, 15)
```

## Normalizing Dates

Convert between different precision levels:

```python
from stash_graphql_client.types import normalize_date

full_date = "2024-03-15"

# Reduce precision
normalize_date(full_date, "year")   # "2024"
normalize_date(full_date, "month")  # "2024-03"
normalize_date(full_date, "day")    # "2024-03-15" (unchanged)

# Increase precision (adds defaults)
year_only = "2024"
normalize_date(year_only, "month")  # "2024-01"
normalize_date(year_only, "day")    # "2024-01-01"

month_only = "2024-03"
normalize_date(month_only, "day")   # "2024-03-01"
```

## Using Fuzzy Dates with Stash

### Performer Birthdates

```python
async with StashContext(conn=conn) as client:
    # Exact birthdate known
    performer1 = await client.create_performer(
        name="Jane Doe",
        birthdate="1990-05-15"
    )

    # Only birth year known
    performer2 = await client.create_performer(
        name="John Smith",
        birthdate="1985"
    )

    # Birth year and month known
    performer3 = await client.create_performer(
        name="Alice Johnson",
        birthdate="1992-07"
    )
```

### Scene Dates

```python
async with StashContext(conn=conn) as client:
    # Exact date
    scene1 = await client.update_scene(
        id="scene-id-1",
        date="2024-03-15"
    )

    # Month precision
    scene2 = await client.update_scene(
        id="scene-id-2",
        date="2024-03"
    )

    # Year only
    scene3 = await client.update_scene(
        id="scene-id-3",
        date="2024"
    )
```

## Comparing Fuzzy Dates

```python
from stash_graphql_client.types import FuzzyDate

date1 = FuzzyDate("2024")
date2 = FuzzyDate("2024-03")
date3 = FuzzyDate("2024-03-15")

# Compare precision
print(date1.precision == DatePrecision.YEAR)   # True
print(date2.precision == DatePrecision.MONTH)  # True
print(date3.precision == DatePrecision.DAY)    # True

# Compare values
print(date1.value)  # "2024"
print(date2.value)  # "2024-03"
print(date3.value)  # "2024-03-15"

# Compare as datetime (all convert to first day)
dt1 = date1.to_datetime()  # 2024-01-01
dt2 = date2.to_datetime()  # 2024-03-01
dt3 = date3.to_datetime()  # 2024-03-15

print(dt1 < dt2 < dt3)  # True
```

## Handling Unknown Dates

When dates are completely unknown, use `None`:

```python
async with StashContext(conn=conn) as client:
    # Birthdate unknown
    performer = await client.create_performer(
        name="Unknown Birthdate",
        birthdate=None
    )

    # Check if birthdate is set
    if performer.birthdate is None:
        print("Birthdate unknown")
    elif performer.birthdate is not UNSET:
        print(f"Birthdate: {performer.birthdate}")
```

## Best Practices

### 1. Use the Most Specific Precision Available

```python
# ✅ Good - Use what you know
birthdate = "1990-07"  # Year and month known

# ❌ Bad - Guessing the day
birthdate = "1990-07-01"  # Day unknown, shouldn't guess
```

### 2. Validate Before Saving

```python
from stash_graphql_client.types import validate_fuzzy_date

user_input = "2024-3"  # From user

# ✅ Good - Validate first
if validate_fuzzy_date(user_input):
    await client.create_performer(name="Name", birthdate=user_input)
else:
    # Normalize or fix the input
    normalized = user_input if len(user_input.split('-')[1]) == 2 else f"2024-03"
```

### 3. Handle All Precision Levels

```python
# ✅ Good - Handle all cases
date = FuzzyDate(performer.birthdate)

if date.precision == DatePrecision.DAY:
    print(f"Born on {date.value}")
elif date.precision == DatePrecision.MONTH:
    print(f"Born in {date.value}")
else:
    print(f"Born in {date.value}")

# ❌ Bad - Assuming full date
print(f"Born on {performer.birthdate}")  # Might be "1990"!
```

### 4. Use Normalization for Consistency

```python
from stash_graphql_client.types import normalize_date

# ✅ Good - Normalize for comparison
dates = ["2024", "2024-03", "2024-03-15"]
normalized = [normalize_date(d, "day") for d in dates]
# All normalized to full dates for comparison

# Sort by normalized dates
sorted_dates = sorted(dates, key=lambda d: normalize_date(d, "day"))
```

## Common Patterns

### Age Calculation with Fuzzy Dates

```python
from datetime import datetime
from stash_graphql_client.types import FuzzyDate

def calculate_age(birthdate_str: str) -> int:
    """Calculate age from fuzzy birthdate."""
    fuzzy_date = FuzzyDate(birthdate_str)
    birth_dt = fuzzy_date.to_datetime()
    today = datetime.now()

    age = today.year - birth_dt.year

    # Adjust if birthday hasn't occurred this year yet
    # (Only accurate for full dates)
    if fuzzy_date.precision == DatePrecision.DAY:
        if (today.month, today.day) < (birth_dt.month, birth_dt.day):
            age -= 1

    return age

# Usage
age = calculate_age("1990-05-15")  # Exact
approx_age = calculate_age("1990")  # Approximate
```

### Display Formatting

```python
from stash_graphql_client.types import FuzzyDate, DatePrecision

def format_date(date_str: str) -> str:
    """Format fuzzy date for display."""
    date = FuzzyDate(date_str)

    if date.precision == DatePrecision.YEAR:
        return date.value
    elif date.precision == DatePrecision.MONTH:
        # Convert to "March 2024"
        dt = date.to_datetime()
        return dt.strftime("%B %Y")
    else:
        # Convert to "March 15, 2024"
        dt = date.to_datetime()
        return dt.strftime("%B %d, %Y")

# Usage
print(format_date("2024"))         # "2024"
print(format_date("2024-03"))      # "March 2024"
print(format_date("2024-03-15"))   # "March 15, 2024"
```

## Next Steps

- [UNSET Pattern](unset-pattern.md) - Distinguish unset from null values
- [API Reference](../api/types.md) - Explore type definitions
- [Client API](../api/client.md) - Explore client methods
