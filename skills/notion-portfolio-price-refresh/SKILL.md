---
name: notion-portfolio-price-refresh
description: Refresh stock portfolio market fields in Notion. Use when user asks to update a Notion stock portfolio DB by fetching USD/KRW first, then iterating rows to update current price and exchange-rate fields.
---

# notion-portfolio-price-refresh

Update Notion portfolio rows with latest market values in a fixed sequence.

## Fixed sequence

1. Fetch USD/KRW rate
2. Iterate portfolio rows and update price/rate fields

## Preconditions

- Notion API key exists (`~/.config/notion/api_key` or `NOTION_API_KEY`).
- Target DB is the data-bearing `주식 포트폴리오` DB (user-approved ID preferred).
- Required columns exist:
  - `티커` (rich_text)
  - `현재가` (number)
  - `통화` (select)
  - `환율 기록` (number)

## Step 1) Fetch exchange rate

- Use yfinance ticker `KRW=X`.
- Resolve in this order:
  1. `fast_info.last_price`
  2. `history(period="1d", interval="1m")` last close (fallback)
- Round to 2 decimals.
- If both fail, stop and report failure.

## Step 2) Update portfolio rows

- Query rows from the target DB.
- For each row:
  - Read `티커`, `통화`.
  - Resolve market ticker:
    - If ticker has `.` suffix, keep as-is.
    - If ticker looks like Korean code (leading digit), use `.KS` suffix.
    - Keep US symbols as-is (e.g., `TSM`, `AAPL`, `BRK-B`).
    - Normalize known exception: `BRK.b` → `BRK-B`.
  - Fetch latest price via yfinance (same fallback order as above for price).
  - Update `현재가` with 2-decimal rounding.
  - If `통화 == USD`, update `환율 기록` with Step 1 rate.
  - If `통화` is cash (`KRW`, `USD`) and user asked to exclude cash, skip price updates.

## Output to user

Return a short execution summary:

- Applied USD/KRW rate
- Updated row count
- Skipped row count
- Skipped reasons (ticker unresolved, price fetch failed, excluded cash)

## Safety / behavior

- Never modify DBs outside user-approved scope.
- Do not create/delete rows unless explicitly requested.
- Prefer minimal, deterministic updates to existing fields only.
