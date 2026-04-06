#!/usr/bin/env python3
"""
Mercadona CLI — unofficial client for tienda.mercadona.es
"""
import json
import os
import sys
from pathlib import Path

import click
import requests

BASE_URL = "https://tienda.mercadona.es/api"
CONFIG_DIR = Path.home() / ".mercadona"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "x-version": "v8451",
}


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2))
    CONFIG_FILE.chmod(0o600)


def get_session_headers(config: dict) -> dict:
    headers = DEFAULT_HEADERS.copy()
    token = config.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    wh = config.get("warehouse")
    if wh:
        headers["x-customer-wh"] = wh
    return headers


def require_auth(config: dict) -> None:
    if not config.get("token"):
        click.echo("Not authenticated. Run: mercadona auth login", err=True)
        sys.exit(1)


def get_customer_uuid(config: dict) -> str | None:
    """Extract customer UUID from config or by decoding the JWT payload."""
    uuid = config.get("customer_uuid")
    if uuid:
        return uuid
    token = config.get("token")
    if token:
        try:
            import base64
            payload = token.split(".")[1]
            payload += "=" * (-len(payload) % 4)
            return json.loads(base64.b64decode(payload)).get("customer_uuid")
        except Exception:
            pass
    return None


def require_customer(config: dict) -> str:
    require_auth(config)
    customer_id = config.get("customer_id")
    if not customer_id:
        click.echo("Customer ID missing. Re-authenticate: mercadona auth login", err=True)
        sys.exit(1)
    return str(customer_id)


def api_get(path: str, config: dict, params: dict = None) -> dict | list:
    url = f"{BASE_URL}{path}"
    resp = requests.get(url, headers=get_session_headers(config), params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def api_post(path: str, payload: dict, config: dict) -> dict:
    url = f"{BASE_URL}{path}"
    resp = requests.post(url, json=payload, headers=get_session_headers(config), timeout=15)
    resp.raise_for_status()
    return resp.json()


def api_patch(path: str, payload: dict, config: dict) -> dict:
    url = f"{BASE_URL}{path}"
    resp = requests.patch(url, json=payload, headers=get_session_headers(config), timeout=15)
    resp.raise_for_status()
    return resp.json()


def api_put(path: str, payload: dict, config: dict) -> dict:
    url = f"{BASE_URL}{path}"
    resp = requests.put(url, json=payload, headers=get_session_headers(config), timeout=15)
    resp.raise_for_status()
    return resp.json()


def http_error_message(exc: requests.HTTPError) -> str:
    try:
        body = exc.response.json()
        if isinstance(body, dict):
            errors = body.get("errors") or body.get("detail") or body.get("message")
            if isinstance(errors, list):
                return "; ".join(e.get("detail", str(e)) for e in errors)
            if errors:
                return str(errors)
    except Exception:
        pass
    text = exc.response.text.strip()
    # Strip HTML error pages down to something readable
    if text.startswith("<"):
        return f"HTTP {exc.response.status_code}"
    return f"HTTP {exc.response.status_code}: {text[:200]}"


def print_json(data) -> None:
    click.echo(json.dumps(data, indent=2, ensure_ascii=False))


def fmt_price(price_info: dict | None) -> str:
    if not price_info:
        return "N/A"
    # Flat structure (actual API response)
    unit_price = price_info.get("unit_price")
    if unit_price:
        ref = price_info.get("reference_price", "")
        ref_fmt = price_info.get("reference_format", "")
        suffix = f"  ({ref} €/{ref_fmt})" if ref and ref_fmt else ""
        return f"{unit_price} €{suffix}"
    # Nested structure (fallback)
    current = price_info.get("current", {})
    amount = current.get("unit_price") or current.get("total_price", "?")
    return f"{amount} €"


# ---------------------------------------------------------------------------
# CLI groups
# ---------------------------------------------------------------------------

@click.group()
@click.version_option("1.0.0")
def cli():
    """Unofficial Mercadona tienda CLI."""


# ── auth ────────────────────────────────────────────────────────────────────

@cli.group()
def auth():
    """Authentication commands."""


@auth.command("login")
@click.option("--email", prompt=True, help="Mercadona account email")
@click.option("--password", prompt=True, hide_input=True, help="Mercadona account password")
@click.option("--postal-code", default=None, help="Postal code to set warehouse (e.g. 28001)")
def auth_login(email: str, password: str, postal_code: str | None):
    """Log in and store credentials locally."""
    config = load_config()

    # Optionally resolve warehouse first
    if postal_code:
        try:
            resp = requests.put(
                f"{BASE_URL}/postal-codes/actions/change-pc/",
                json={"new_postal_code": postal_code},
                headers=DEFAULT_HEADERS,
                timeout=10,
            )
            wh = resp.headers.get("x-customer-wh")
            if wh:
                config["warehouse"] = wh
                config["postal_code"] = postal_code
                click.echo(f"Warehouse set: {wh}")
        except requests.RequestException as exc:
            click.echo(f"Warning: could not resolve postal code ({exc})", err=True)

    try:
        # Auth endpoint rejects the x-version header, so use minimal headers
        auth_headers = {k: v for k, v in DEFAULT_HEADERS.items() if k != "x-version"}
        resp = requests.post(
            f"{BASE_URL}/auth/tokens/",
            json={"username": email, "password": password},
            headers=auth_headers,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.HTTPError as exc:
        click.echo(f"Login failed: {http_error_message(exc)}", err=True)
        sys.exit(1)
    except requests.RequestException as exc:
        click.echo(f"Network error: {exc}", err=True)
        sys.exit(1)

    # The API returns a token and customer object — field names may vary
    token = data.get("access_token") or data.get("access") or data.get("token") or data.get("key")
    if not token and isinstance(data, dict):
        # Try nested structures
        for key in ("data", "user", "customer"):
            nested = data.get(key, {})
            if isinstance(nested, dict):
                token = nested.get("access") or nested.get("token")
                if token:
                    break

    if not token:
        click.echo("Unexpected response — storing raw data for inspection:")
        print_json(data)
        click.echo("\nCould not extract token. Check the output above.", err=True)
        sys.exit(1)

    customer = data.get("customer") or data.get("user") or {}
    customer_id = None
    if isinstance(customer, dict):
        customer_id = customer.get("id") or customer.get("pk")
    if not customer_id:
        customer_id = data.get("customer_id") or data.get("id")

    config["token"] = token
    config["email"] = email
    if customer_id:
        config["customer_id"] = customer_id
    if data.get("refresh"):
        config["refresh_token"] = data["refresh"]

    save_config(config)
    click.echo(f"Logged in as {email}" + (f" (customer {customer_id})" if customer_id else ""))


@auth.command("logout")
def auth_logout():
    """Remove stored credentials."""
    config = load_config()
    for key in ("token", "refresh_token", "customer_id", "email"):
        config.pop(key, None)
    save_config(config)
    click.echo("Logged out.")


@auth.command("status")
def auth_status():
    """Show current auth state."""
    config = load_config()
    if config.get("token"):
        click.echo(f"Logged in as: {config.get('email', 'unknown')}")
        click.echo(f"Customer ID:  {config.get('customer_id', 'unknown')}")
        click.echo(f"Warehouse:    {config.get('warehouse', 'not set')}")
        click.echo(f"Postal code:  {config.get('postal_code', 'not set')}")
    else:
        click.echo("Not authenticated.")


# ── postal ───────────────────────────────────────────────────────────────────

@cli.command("postal-code")
@click.argument("code")
def set_postal_code(code: str):
    """Set postal code and derive warehouse."""
    config = load_config()
    try:
        resp = requests.put(
            f"{BASE_URL}/postal-codes/actions/change-pc/",
            json={"new_postal_code": code},
            headers=get_session_headers(config),
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    wh = resp.headers.get("x-customer-wh") or "unknown"
    config["postal_code"] = code
    config["warehouse"] = wh
    save_config(config)
    click.echo(f"Postal code: {code}  →  Warehouse: {wh}")


# ── products ─────────────────────────────────────────────────────────────────

@cli.group()
def products():
    """Product commands."""


@products.command("get")
@click.argument("product_id")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON")
def products_get(product_id: str, as_json: bool):
    """Get a product by ID."""
    config = load_config()
    try:
        data = api_get(f"/products/{product_id}/", config)
    except requests.HTTPError as exc:
        click.echo(f"Error {http_error_message(exc)}", err=True)
        sys.exit(1)

    if as_json:
        print_json(data)
        return

    name = data.get("display_name") or data.get("name", "?")
    click.echo(f"ID:       {data.get('id')}")
    click.echo(f"Name:     {name}")
    brand = data.get("brand")
    if brand:
        click.echo(f"Brand:    {brand}")
    click.echo(f"Price:    {fmt_price(data.get('price_instructions'))}")
    # Build category path by traversing nested categories
    cats = data.get("categories") or []
    if cats:
        node = cats[0]
        path_parts = [node.get("name", "")]
        while node.get("categories"):
            node = node["categories"][0]
            path_parts.append(node.get("name", ""))
        click.echo(f"Category: {' > '.join(path_parts)}")
    desc = data.get("description") or data.get("details", {}).get("description", "")
    if desc and desc != name:
        click.echo(f"Desc:     {desc[:200]}")


@products.command("similar")
@click.argument("product_id")
@click.option("--json", "as_json", is_flag=True)
def products_similar(product_id: str, as_json: bool):
    """Get similar products."""
    config = load_config()
    data = api_get(f"/products/{product_id}/similars/", config)
    if as_json:
        print_json(data)
        return
    results = data if isinstance(data, list) else data.get("results", [data])
    for p in results:
        click.echo(f"  [{p.get('id')}] {p.get('display_name') or p.get('name')}  —  {fmt_price(p.get('price_instructions'))}")


@products.command("search")
@click.argument("query")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON")
@click.option("--all", "scan_all", is_flag=True, help="Scan every category (slow, ~150 requests)")
def products_search(query: str, as_json: bool, scan_all: bool):
    """Search products by name.

    First tries to find matching categories by name, then scans those.
    Use --all to search every category if results are missing.
    """
    config = load_config()
    click.echo(f"Searching for '{query}'…", err=True)
    try:
        cats_data = api_get("/categories/", config)
    except requests.RequestException as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    top_cats = cats_data if isinstance(cats_data, list) else cats_data.get("results", [])
    query_lower = query.lower()

    # Build (leaf_id, leaf_name, top_name) list
    all_leaves: list[tuple[str, str, str]] = []
    for cat in top_cats:
        for sub in cat.get("categories", []):
            all_leaves.append((str(sub["id"]), sub.get("name", "").lower(), cat.get("name", "").lower()))

    # Prefer leaves whose name or parent name contains the query
    priority = [t for t in all_leaves if query_lower in t[1] or query_lower in t[2]]
    rest = [t for t in all_leaves if t not in priority]
    candidates = priority + (rest if scan_all else [])

    if not candidates:
        click.echo("No categories available.")
        return

    found: list[dict] = []
    scanned = 0

    for leaf_id, leaf_name, _ in candidates:
        try:
            detail = api_get(f"/categories/{leaf_id}/", config)
        except requests.RequestException:
            continue
        scanned += 1
        for sub in detail.get("categories", [detail]):
            for p in sub.get("products", []):
                name = (p.get("display_name") or p.get("name") or "").lower()
                if query_lower in name:
                    found.append(p)

    if not found:
        hint = "" if scan_all else "  Try --all to scan every category."
        click.echo(f"No products found (scanned {scanned} categories).{hint}")
        return

    if as_json:
        print_json(found)
        return

    click.echo(f"\n{len(found)} result(s) across {scanned} categories:")
    for p in found:
        click.echo(f"  [{p.get('id')}] {p.get('display_name') or p.get('name')}  —  {fmt_price(p.get('price_instructions'))}")


# ── categories ───────────────────────────────────────────────────────────────

@cli.group()
def categories():
    """Category commands."""


@categories.command("list")
@click.option("--json", "as_json", is_flag=True)
def categories_list(as_json: bool):
    """List top-level categories."""
    config = load_config()
    data = api_get("/categories/", config)
    if as_json:
        print_json(data)
        return
    results = data if isinstance(data, list) else data.get("results", [])
    for cat in results:
        click.echo(f"[{cat.get('id')}] {cat.get('name')}")
        for sub in cat.get("categories", []):
            click.echo(f"      [{sub.get('id')}] {sub.get('name')}")


@categories.command("get")
@click.argument("category_id")
@click.option("--json", "as_json", is_flag=True)
def categories_get(category_id: str, as_json: bool):
    """Get products in a category."""
    config = load_config()
    data = api_get(f"/categories/{category_id}/", config)
    if as_json:
        print_json(data)
        return
    click.echo(f"Category: {data.get('name')} [{data.get('id')}]")
    for sub in data.get("categories", []):
        click.echo(f"\n  {sub.get('name')}")
        for p in sub.get("products", []):
            click.echo(f"    [{p.get('id')}] {p.get('display_name') or p.get('name')}  —  {fmt_price(p.get('price_instructions'))}")


# ── orders ───────────────────────────────────────────────────────────────────

@cli.group()
def orders():
    """Past order commands (requires login)."""


@orders.command("list")
@click.option("--json", "as_json", is_flag=True)
@click.option("--limit", default=20, show_default=True)
def orders_list(as_json: bool, limit: int):
    """List past orders."""
    config = load_config()
    customer_id = require_customer(config)
    try:
        data = api_get(f"/customers/{customer_id}/orders/", config, params={"limit": limit})
    except requests.HTTPError as exc:
        click.echo(f"Error {http_error_message(exc)}", err=True)
        sys.exit(1)

    if as_json:
        print_json(data)
        return

    results = data if isinstance(data, list) else data.get("results", [])
    if not results:
        click.echo("No orders found.")
        return
    for o in results:
        oid = o.get("id") or o.get("order_id")
        date = (o.get("start_date") or "?")[:10]
        status = o.get("status_ui") or o.get("status", "?")
        total = (o.get("summary") or {}).get("total") or o.get("price", "?")
        click.echo(f"[{oid}]  {date}  {status}  {total} €")


@orders.command("get")
@click.argument("order_id")
@click.option("--json", "as_json", is_flag=True)
def orders_get(order_id: str, as_json: bool):
    """Get details of a specific order."""
    config = load_config()
    customer_id = require_customer(config)
    try:
        data = api_get(f"/customers/{customer_id}/orders/{order_id}/", config)
    except requests.HTTPError as exc:
        click.echo(f"Error {http_error_message(exc)}", err=True)
        sys.exit(1)

    if as_json:
        print_json(data)
        return

    click.echo(f"Order: {data.get('id') or order_id}")
    date = data.get("start_date") or (data.get("slot") or {}).get("start") or "?"
    click.echo(f"Date:  {date[:10]}")
    click.echo(f"Status:{data.get('status_ui') or data.get('status', '?')}")
    click.echo(f"Total: {(data.get('summary') or {}).get('total') or data.get('price', '?')} €")
    lines = data.get("lines") or data.get("items") or data.get("products", [])
    if lines:
        click.echo("\nItems:")
        for line in lines:
            p = line.get("product") or line
            name = p.get("display_name") or p.get("name", "?")
            qty = line.get("quantity") or line.get("amount", "?")
            click.echo(f"  x{qty}  {name}")


@orders.command("detail")
@click.argument("order_id")
@click.option("--json", "as_json", is_flag=True)
def orders_detail(order_id: str, as_json: bool):
    """Get the prepared line items for a past order."""
    config = load_config()
    require_auth(config)
    customer_uuid = get_customer_uuid(config)
    if not customer_uuid:
        click.echo("Customer UUID not available. Re-authenticate: mercadona auth login", err=True)
        sys.exit(1)
    wh = config.get("warehouse", "")
    try:
        data = api_get(
            f"/customers/{customer_uuid}/orders/{order_id}/lines/prepared/",
            config,
            params={"lang": "es", "wh": wh},
        )
    except requests.HTTPError as exc:
        click.echo(f"Error {http_error_message(exc)}", err=True)
        sys.exit(1)

    if as_json:
        print_json(data)
        return

    lines = data if isinstance(data, list) else data.get("results", [])
    if not lines:
        click.echo("No items found.")
        return
    click.echo(f"Items for order {order_id}:")
    for line in lines:
        p = line.get("product") or line
        name = p.get("display_name") or p.get("name", "?")
        pid = p.get("id") or line.get("product_id", "?")
        qty_raw = line.get("ordered_quantity") or line.get("quantity") or line.get("amount")
        qty = int(qty_raw) if isinstance(qty_raw, float) and qty_raw.is_integer() else (qty_raw or "?")
        price = fmt_price(p.get("price_instructions"))
        click.echo(f"  x{qty}  [{pid}]  {name}  —  {price}")


# ── shopping lists ────────────────────────────────────────────────────────────

@cli.group("lists")
def shopping_lists():
    """Shopping list commands (requires login)."""


@shopping_lists.command("list")
@click.option("--json", "as_json", is_flag=True)
def lists_list(as_json: bool):
    """List all shopping lists."""
    config = load_config()
    customer_id = require_customer(config)
    try:
        data = api_get(f"/customers/{customer_id}/shopping-lists/", config)
    except requests.HTTPError as exc:
        click.echo(f"Error {http_error_message(exc)}", err=True)
        sys.exit(1)

    if as_json:
        print_json(data)
        return

    results = data if isinstance(data, list) else data.get("results", [])
    if not results:
        click.echo("No shopping lists found.")
        return
    for sl in results:
        sid = sl.get("id") or sl.get("uuid")
        name = sl.get("name") or sl.get("title", "?")
        count = sl.get("products_count") or len(sl.get("products", []))
        click.echo(f"[{sid}]  {name}  ({count} items)")


@shopping_lists.command("get")
@click.argument("list_id")
@click.option("--json", "as_json", is_flag=True)
def lists_get(list_id: str, as_json: bool):
    """Get contents of a shopping list."""
    config = load_config()
    customer_id = require_customer(config)
    try:
        data = api_get(f"/customers/{customer_id}/shopping-lists/{list_id}/", config)
    except requests.HTTPError as exc:
        click.echo(f"Error {http_error_message(exc)}", err=True)
        sys.exit(1)

    if as_json:
        print_json(data)
        return

    click.echo(f"List: {data.get('name') or data.get('title', list_id)}")
    products_list = data.get("products") or data.get("items") or []
    if not products_list:
        click.echo("(empty)")
    for p in products_list:
        pid = p.get("id") or p.get("product_id")
        name = p.get("display_name") or p.get("name", "?")
        qty = p.get("quantity", 1)
        click.echo(f"  x{qty}  [{pid}]  {name}")


# ── cart ──────────────────────────────────────────────────────────────────────

@cli.group()
def cart():
    """Shopping cart commands (requires login)."""


@cart.command("show")
@click.option("--json", "as_json", is_flag=True)
def cart_show(as_json: bool):
    """Show current cart contents."""
    config = load_config()
    customer_id = require_customer(config)
    try:
        data = api_get(f"/customers/{customer_id}/cart/", config)
    except requests.HTTPError as exc:
        click.echo(f"Error {http_error_message(exc)}", err=True)
        sys.exit(1)

    if as_json:
        print_json(data)
        return

    lines = data.get("lines") or data.get("items") or data.get("products") or []
    total = data.get("summary", {}).get("total") or data.get("total_price") or data.get("amount")
    click.echo(f"Cart ({len(lines)} items)" + (f"  —  Total: {total} €" if total else ""))
    for line in lines:
        p = line.get("product") or line
        name = p.get("display_name") or p.get("name", "?")
        pid = p.get("id") or line.get("product_id")
        qty = line.get("quantity") or line.get("amount", "?")
        price = fmt_price(p.get("price_instructions"))
        click.echo(f"  x{qty}  [{pid}]  {name}  —  {price}")


def _cart_put(customer_id: str, cart_data: dict, lines: list[dict], config: dict) -> dict:
    """PUT the cart. Requires cart version for optimistic locking."""
    payload = {"lines": lines}
    if cart_data.get("version") is not None:
        payload["version"] = cart_data["version"]
    return api_put(f"/customers/{customer_id}/cart/", payload, config)


def _current_lines(cart_data: dict) -> list[dict]:
    """Extract current cart lines as PUT-compatible dicts (preserving version fields)."""
    result = []
    for line in cart_data.get("lines", []):
        product = line.get("product", {})
        pid = str(product.get("id") or line.get("product_id", ""))
        qty = line.get("quantity", 1)
        if pid:
            entry: dict = {"product_id": pid, "quantity": qty}
            if line.get("version") is not None:
                entry["version"] = line["version"]
            result.append(entry)
    return result


@cart.command("add")
@click.argument("product_id")
@click.option("--quantity", "-q", default=1, show_default=True, help="Quantity to add")
@click.option("--json", "as_json", is_flag=True)
def cart_add(product_id: str, quantity: int, as_json: bool):
    """Add a product to the cart (or increase its quantity)."""
    config = load_config()
    customer_id = require_customer(config)

    try:
        cart_data = api_get(f"/customers/{customer_id}/cart/", config)
    except requests.HTTPError as exc:
        click.echo(f"Error fetching cart: {http_error_message(exc)}", err=True)
        sys.exit(1)

    # Merge: increment if already in cart, otherwise append
    lines = _current_lines(cart_data)
    for line in lines:
        if line["product_id"] == str(product_id):
            line["quantity"] = line["quantity"] + quantity
            break
    else:
        lines.append({"product_id": str(product_id), "quantity": quantity})

    try:
        data = _cart_put(customer_id, cart_data, lines, config)
    except requests.HTTPError as exc:
        click.echo(f"Error updating cart: {http_error_message(exc)}", err=True)
        sys.exit(1)

    if as_json:
        print_json(data)
        return

    total = data.get("summary", {}).get("total", "?")
    click.echo(f"Added product {product_id} x{quantity} to cart.  Total: {total} €")


@cart.command("remove")
@click.argument("product_id")
@click.option("--json", "as_json", is_flag=True)
def cart_remove(product_id: str, as_json: bool):
    """Remove a product from the cart."""
    config = load_config()
    customer_id = require_customer(config)

    try:
        cart_data = api_get(f"/customers/{customer_id}/cart/", config)
    except requests.HTTPError as exc:
        click.echo(f"Error fetching cart: {http_error_message(exc)}", err=True)
        sys.exit(1)

    # Set quantity=0 to remove — omitting the line is ignored by the API
    lines = _current_lines(cart_data)
    found = False
    for line in lines:
        if line["product_id"] == str(product_id):
            line["quantity"] = 0
            found = True
            break
    if not found:
        click.echo(f"Product {product_id} is not in the cart.", err=True)
        sys.exit(1)

    try:
        data = _cart_put(customer_id, cart_data, lines, config)
    except requests.HTTPError as exc:
        click.echo(f"Error updating cart: {http_error_message(exc)}", err=True)
        sys.exit(1)

    if as_json:
        print_json(data)
        return

    total = data.get("summary", {}).get("total", "?")
    click.echo(f"Removed product {product_id} from cart.  Total: {total} €")


# ── home ──────────────────────────────────────────────────────────────────────

@cli.group()
def home():
    """Home/featured sections."""


@home.command("show")
@click.option("--json", "as_json", is_flag=True)
def home_show(as_json: bool):
    """Show home sections."""
    config = load_config()
    data = api_get("/home/", config)
    if as_json:
        print_json(data)
        return
    sections = data if isinstance(data, list) else data.get("results", [])
    for s in sections:
        click.echo(f"[{s.get('id') or s.get('uuid')}] {s.get('title') or s.get('name', '?')}")


@home.command("new-arrivals")
@click.option("--json", "as_json", is_flag=True)
def home_new_arrivals(as_json: bool):
    """Show new arrivals."""
    config = load_config()
    data = api_get("/home/new-arrivals/", config)
    if as_json:
        print_json(data)
        return
    results = data if isinstance(data, list) else data.get("results", [])
    for p in results:
        click.echo(f"  [{p.get('id')}] {p.get('display_name') or p.get('name')}  —  {fmt_price(p.get('price_instructions'))}")


@home.command("price-drops")
@click.option("--json", "as_json", is_flag=True)
def home_price_drops(as_json: bool):
    """Show products with price drops."""
    config = load_config()
    data = api_get("/home/price-drops/", config)
    if as_json:
        print_json(data)
        return
    results = data if isinstance(data, list) else data.get("results", [])
    for p in results:
        click.echo(f"  [{p.get('id')}] {p.get('display_name') or p.get('name')}  —  {fmt_price(p.get('price_instructions'))}")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cli()
