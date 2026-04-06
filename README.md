# Mercadona CLI

Unofficial command-line client for the [Mercadona online store](https://tienda.mercadona.es) API.

Browse the catalog, search products, manage your cart, review past orders, and access your shopping lists — all from the terminal.

> **Disclaimer:** This tool is not affiliated with, endorsed by, or connected to Mercadona S.A. It interacts with publicly observable API endpoints on `tienda.mercadona.es`. Use responsibly and respect their Terms of Service.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Authentication](#authentication)
  - [Login](#login)
  - [Logout](#logout)
  - [Status](#status)
- [Setting Your Postal Code](#setting-your-postal-code)
- [Products](#products)
  - [Search Products](#search-products)
  - [Get Product Details](#get-product-details)
  - [Find Similar Products](#find-similar-products)
- [Categories](#categories)
  - [List Categories](#list-categories)
  - [Browse a Category](#browse-a-category)
- [Orders](#orders)
  - [List Past Orders](#list-past-orders)
  - [View Order Details](#view-order-details)
  - [View Order Line Items](#view-order-line-items)
- [Shopping Lists](#shopping-lists)
  - [List Shopping Lists](#list-shopping-lists)
  - [View Shopping List Contents](#view-shopping-list-contents)
- [Cart](#cart)
  - [Show Cart](#show-cart)
  - [Add Product to Cart](#add-product-to-cart)
  - [Remove Product from Cart](#remove-product-from-cart)
- [Home & Featured](#home--featured)
  - [Home Sections](#home-sections)
  - [New Arrivals](#new-arrivals)
  - [Price Drops](#price-drops)
- [JSON Output](#json-output)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## Installation

**Requirements:** Python 3.10+

```bash
# Clone or download the project
cd mercadona-cli

# Install as a CLI tool (editable mode — changes to the source take effect immediately)
pip install -e .
```

This registers the `mercadona` command globally. Verify with:

```bash
mercadona --version
# mercadona, version 1.0.0
```

### Manual alternative (without installing)

```bash
pip install click requests
python mercadona.py --help
```

---

## Quick Start

```bash
# 1. Set your postal code (determines your warehouse/store)
mercadona postal-code 28001

# 2. Browse categories
mercadona categories list

# 3. Search for a product
mercadona products search "leche"

# 4. Get product details
mercadona products get 10381

# 5. Log in for account features (orders, lists, cart)
mercadona auth login

# 6. View your past orders
mercadona orders list

# 7. Add something to your cart
mercadona cart add 10381 -q 2
```

---

## Authentication

Some features (orders, shopping lists, cart) require a Mercadona account. The CLI authenticates via email and password, storing the session token locally.

### Login

```bash
mercadona auth login
```

You will be prompted for your email and password (password input is hidden). You can also pass them as options:

```bash
mercadona auth login --email user@example.com --password secret
```

Optionally set your postal code at login time:

```bash
mercadona auth login --postal-code 46001
```

**Options:**

| Option           | Description                                |
|------------------|--------------------------------------------|
| `--email`        | Mercadona account email (prompted if omitted) |
| `--password`     | Account password (prompted if omitted, hidden input) |
| `--postal-code`  | Postal code to resolve warehouse at login time |

### Logout

```bash
mercadona auth logout
```

Removes the stored token and customer ID from the local config.

### Status

```bash
mercadona auth status
```

Displays your current authentication state:

```
Logged in as: user@example.com
Customer ID:  12345
Warehouse:    vlc1
Postal code:  46001
```

---

## Setting Your Postal Code

The postal code determines which warehouse (store) serves your area. This affects product availability and pricing.

```bash
mercadona postal-code <CODE>
```

**Example:**

```bash
mercadona postal-code 28001
# Postal code: 28001  →  Warehouse: mad1
```

The resolved warehouse is saved and sent with subsequent requests automatically.

---

## Products

### Search Products

```bash
mercadona products search <QUERY>
```

Searches product names across the catalog. The search is smart: it first identifies categories whose names match your query and scans those, making most searches fast (2-5 HTTP requests).

**Example:**

```bash
mercadona products search "yogur"
```

```
Searching for 'yogur'…

37 result(s) across 9 categories:
  [28496] Yogur azucarado YogoMix Hacendado variado ...  —  3.15 €  (3.500 €/kg)
  [20499] Yogur azucarado YogoMix Bolitas Hacendado ...  —  1.30 €  (4.334 €/kg)
  [20221] Yogur natural edulcorado Hacendado 0% MG ...    —  1.05 €  (1.400 €/kg)
  ...
```

If your search term doesn't match any category name and returns no results, use `--all` to do an exhaustive scan of all ~150 categories:

```bash
mercadona products search "trufa" --all
```

**Options:**

| Option    | Description                                                     |
|-----------|-----------------------------------------------------------------|
| `--all`   | Scan every category (~150 requests, slower but comprehensive)   |
| `--json`  | Output raw JSON instead of formatted text                       |

### Get Product Details

```bash
mercadona products get <PRODUCT_ID>
```

**Example:**

```bash
mercadona products get 10381
```

```
ID:       10381
Name:     Leche semidesnatada Hacendado
Brand:    Hacendado
Price:    5.04 €  (0.840 €/L)
Category: Lácteos y huevos > Leche y bebidas vegetales > Leche
```

### Find Similar Products

```bash
mercadona products similar <PRODUCT_ID>
```

Returns products the API considers similar to the given one.

**Example:**

```bash
mercadona products similar 10381
```

---

## Categories

### List Categories

```bash
mercadona categories list
```

Displays the full category tree (top-level sections and their subcategories):

```
[12] Aceite, especias y salsas
      [112] Aceite, vinagre y sal
      [115] Especias
      [116] Mayonesa, ketchup y mostaza
      [117] Otras salsas
[18] Agua y refrescos
      [156] Agua
      [163] Isotónico y energético
      ...
```

### Browse a Category

```bash
mercadona categories get <CATEGORY_ID>
```

Lists all products within a category, grouped by subcategory:

```bash
mercadona categories get 156
```

```
Category: Agua [156]

  Agua sin gas
    [28035] Agua mineral grande Bronchales  —  1.30 €  (0.217 €/L)
    [23448] Agua mineral grande Bronchales  —  2.34 €  (0.260 €/L)
    ...

  Agua con gas
    [10101] Agua con gas Hacendado  —  0.55 €  (0.367 €/L)
    ...
```

---

## Orders

> Requires authentication. Run `mercadona auth login` first.

### List Past Orders

```bash
mercadona orders list
```

**Options:**

| Option     | Default | Description                     |
|------------|---------|---------------------------------|
| `--limit`  | `20`    | Maximum number of orders to show |
| `--json`   | —       | Output raw JSON                 |

**Example:**

```bash
mercadona orders list --limit 5
```

```
[98765]  2026-03-15  delivered  87.43 €
[98501]  2026-02-28  delivered  62.10 €
...
```

### View Order Details

```bash
mercadona orders get <ORDER_ID>
```

**Example:**

```bash
mercadona orders get 98765
```

```
Order: 98765
Date:  2026-03-15
Status:delivered
Total: 87.43 €
```

### View Order Line Items

```bash
mercadona orders detail <ORDER_ID>
```

Fetches the fully prepared line items for a past order, including product names, quantities, and prices. Requires authentication.

**Example:**

```bash
mercadona orders detail 29593104
```

```
Items for order 29593104:
  x2  [64492]  Helado Mochi mango Hacendado  —  2.90 €  (13.426 €/L)
  x1  [79006]  Solución fisiológica Deliplus  —  3.23 €  (0.108 €/ud)
  x3  [10783]  Leche entera Hacendado  —  1.71 €  (1.425 €/L)
  ...
```

**Options:**

| Option    | Description             |
|-----------|-------------------------|
| `--json`  | Output raw JSON         |

---

## Shopping Lists

> Requires authentication. Run `mercadona auth login` first.

### List Shopping Lists

```bash
mercadona lists list
```

```
[abc123]  Lista semanal  (12 items)
[def456]  Cena viernes   (5 items)
```

### View Shopping List Contents

```bash
mercadona lists get <LIST_ID>
```

**Example:**

```bash
mercadona lists get abc123
```

```
List: Lista semanal
  x2  [10381]  Leche semidesnatada Hacendado
  x1  [20210]  Yogur natural Hacendado 0% MG
  x3  [28035]  Agua mineral grande Bronchales
  ...
```

---

## Cart

> Requires authentication. Run `mercadona auth login` first.

### Show Cart

```bash
mercadona cart show
```

```
Cart (3 items)  —  Total: 12.50 €
  x2  [10381]  Leche semidesnatada Hacendado  —  5.04 €  (0.840 €/L)
  x1  [20210]  Yogur natural Hacendado 0% MG  —  1.05 €  (1.400 €/kg)
  x1  [28035]  Agua mineral grande Bronchales  —  1.30 €  (0.217 €/L)
```

### Add Product to Cart

```bash
mercadona cart add <PRODUCT_ID> [--quantity N]
```

**Options:**

| Option              | Default | Description          |
|---------------------|---------|----------------------|
| `-q`, `--quantity`  | `1`     | Number of units to add |
| `--json`            | —       | Output raw JSON      |

**Examples:**

```bash
# Add 1 unit
mercadona cart add 10381

# Add 3 units
mercadona cart add 10381 -q 3
```

### Remove Product from Cart

```bash
mercadona cart remove <PRODUCT_ID>
```

**Example:**

```bash
mercadona cart remove 10381
# Removed product 10381 from cart.
```

---

## Home & Featured

These commands access the storefront's featured sections without authentication.

### Home Sections

```bash
mercadona home show
```

### New Arrivals

```bash
mercadona home new-arrivals
```

### Price Drops

```bash
mercadona home price-drops
```

All three accept `--json` for raw output.

---

## JSON Output

Every command that displays data supports a `--json` flag. When set, it outputs the raw API response as pretty-printed JSON instead of the human-readable format.

```bash
mercadona products get 10381 --json
```

```json
{
  "id": 10381,
  "display_name": "Leche semidesnatada Hacendado",
  "brand": "Hacendado",
  "price_instructions": {
    "unit_price": "5.04",
    "reference_price": "0.840",
    "reference_format": "L",
    ...
  },
  ...
}
```

This is useful for piping into `jq`, scripting, or debugging:

```bash
# Get just the price of a product
mercadona products get 10381 --json | jq '.price_instructions.unit_price'

# Export a category to CSV
mercadona categories get 156 --json | jq -r '.categories[].products[] | [.id, .display_name, .price_instructions.unit_price] | @csv'
```

---

## Configuration

All configuration is stored in `~/.mercadona/config.json` (file permissions: `600`).

| Field            | Description                         | Set by                  |
|------------------|-------------------------------------|-------------------------|
| `token`          | Auth bearer token                   | `auth login`            |
| `refresh_token`  | Token refresh value (if provided)   | `auth login`            |
| `email`          | Account email                       | `auth login`            |
| `customer_id`    | Customer identifier                 | `auth login`            |
| `postal_code`    | Current postal code                 | `postal-code` / `auth login --postal-code` |
| `warehouse`      | Resolved warehouse code (e.g. `vlc1`) | `postal-code` / `auth login --postal-code` |

To reset all configuration:

```bash
rm -rf ~/.mercadona
```

---

## Troubleshooting

### "Not authenticated" error

Run `mercadona auth login` to authenticate. Account-related commands (orders, lists, cart) require a valid session.

### Search returns no results

The default search only scans categories whose names match your query. If your product lives in an unrelated category, use the `--all` flag:

```bash
mercadona products search "mozzarella" --all
```

### Token expired

If API calls start returning 401 errors, re-authenticate:

```bash
mercadona auth login
```

### Products show different prices or availability

Set your postal code to match your delivery area — product availability and pricing depend on the warehouse:

```bash
mercadona postal-code 46001
```

### Unexpected API responses

Use `--json` on any command to inspect the raw API response. The Mercadona API is undocumented and may change its response structure at any time.

```bash
mercadona orders list --json
```
