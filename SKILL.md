---
name: mercadona-cli
description: Interact with the Mercadona online supermarket via the mercadona-cli tool. Use when the user asks about their Mercadona orders, wants to look up products or prices, browse categories, manage their cart, or check shopping lists. Triggers - "mercadona", "mis pedidos", "buscar producto mercadona", "pedido mercadona", "carrito mercadona", "lista mercadona", "cuanto cuesta", "ver pedido".
homepage: https://github.com/tatopane/mercadona-cli
metadata:
  {"clawdbot":{"emoji":"🛒","requires":{"bins":["python3"],"env":["MERCADONA_USERNAME","MERCADONA_PASSWORD","MERCADONA_POSTAL_CODE"]}}}
---

# Mercadona CLI Skill


<objective>
Help the user interact with the Mercadona online store (tienda.mercadona.es) using the `mercadona` CLI tool installed in the virtual environment at `/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona`. Run commands via Bash and present the results cleanly. Never fabricate product data, prices, or order information — always run the actual CLI command.

The user will always speak in Spanish. All examples, explanations, and responses must be provided in Spanish.
</objective>

<language>
El usuario siempre se comunicará en español. Todas las respuestas, ejemplos y explicaciones deben estar en español.

## Vocabulario español → comandos CLI

| Expresión en español | Comando CLI |
|---|---|
| "iniciar sesión / entrar / login" | `/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona auth login` |
| "cerrar sesión / salir" | `/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona auth logout` |
| "mis pedidos / pedido anterior / última compra" | `/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona orders list` |
| "detalles del pedido / qué compré" | `/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona orders detail <ID>` |
| "buscar producto / cuánto cuesta / precio de" | `/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona products search "<QUERY>"` |
| "ver producto / información de" | `/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona products get <ID>` |
| "mi carrito / qué tengo en el carrito" | `/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona cart show` |
| "añadir al carrito / agregar / meter en el carrito" | `/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona cart add <ID> -q <N>` |
| "quitar del carrito / eliminar del carrito" | `/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona cart remove <ID>` |
| "mis listas / lista de la compra" | `/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona lists list` |
| "ver lista" | `/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona lists get <ID>` |
| "categorías / secciones" | `/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona categories list` |
| "productos similares / alternativas" | `/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona products similar <ID>` |
| "novedades / nuevos productos" | `/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona home new-arrivals` |
| "ofertas / bajadas de precio" | `/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona home price-drops` |
</language>

<install>

## Requirements

Python 3.10+

## Install

```bash
# Clone or download the project
cd mercadona-cli

# Create a virtual environment
python3 -m venv venv

# Install dependencies and the package in editable mode
./venv/bin/pip install -e .
```

Verify the installation:

```bash
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona --version
# mercadona, version 1.0.0
```


## Manual alternative (without installing)

```bash
./venv/bin/pip install click requests
./venv/bin/python mercadona.py --help
```

## Credentials
After installation, set your Mercadona credentials as environment variables (or store them securely in `~/.openclaw/openclaw.json`).

Set `MERCADONA_USERNAME`, `MERCADONA_PASSWORD`, `MERCADONA_POSTAL_CODE` , or configure it in `~/.openclaw/openclaw.json`:

```json5
{
  "skills": {
    "mercadona-cli": {
      "env": {
        "MERCADONA_USERNAME": "MERCADONA_USERNAME",
        "MERCADONA_PASSWOD": "MERCADONA_PASSWORD",
        "MERCADONA_POSTAL_CODE": "MERCADONA_POSTAL_CODE" 
      }
    }
  }
}
```

</install>

<setup>
The CLI is installed and available as `/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona` in the shell. Config and auth token are stored in `~/.mercadona/config.json`. Authentication is required for orders, shopping lists, and cart commands.

**IMPORTANT — login automático antes de acciones protegidas:** Antes de ejecutar cualquier comando que requiera autenticación (pedidos, carrito, listas), siempre ejecuta primero `/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona auth login` usando las credenciales almacenadas en `~/.openclaw/openclaw.json`. No esperes a que falle con un error de autenticación — haz el login proactivamente como primer paso.

```bash
# Secuencia obligatoria para cualquier acción protegida:
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona auth login   # 1. Login con credenciales almacenadas
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona <comando>    # 2. Ejecutar la acción solicitada
```
</setup>

<commands>

## Authentication
```bash
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona auth status          # check current login state
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona auth login --email {MERCADONA_USERNAME} --password {MERCADONA_PASSWORD} --postal-code {MERCADONA_POSTAL_CODE}          # interactive login (email + password)
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona auth logout
```

## Postal code / warehouse
```bash
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona postal-code <CODE>   # e.g. 28001 — sets delivery area
```

## Products
```bash
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona products get <ID>              # product details: name, brand, price, category
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona products search "<QUERY>"      # search by name (scans matching categories)
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona products search "<QUERY>" --all  # exhaustive scan of all ~150 categories
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona products similar <ID>          # similar products
```

## Categories
```bash
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona categories list                # full category tree
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona categories get <CATEGORY_ID>   # products within a category
```

## Orders (requires login)
```bash
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona orders list                    # recent orders: date, status, total
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona orders list --limit 50         # fetch more
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona orders get <ORDER_ID>          # order summary: date, status, total
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona orders detail <ORDER_ID>       # full item list with quantities and prices
```

## Shopping lists (requires login)
```bash
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona lists list                     # all shopping lists
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona lists get <LIST_ID>            # contents of a list
```

## Cart (requires login)
```bash
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona cart show                      # current cart and total
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona cart add <PRODUCT_ID> -q <N>   # add N units (default 1)
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona cart remove <PRODUCT_ID>       # remove a product
```

Cart rules:
- Every time I ask you to add something to my cart, first check in `products_preferred.md` if the product is in my list or not. If it is in my list, add it to my cart directly. If you don't find it in my list, then search the mercadona catalog using a search by name and present me with the top 3 results. I'll tell you which one to add.

## Home / featured
```bash
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona home show                      # featured sections
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona home new-arrivals              # new products
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona home price-drops               # products with price reductions
```

## Raw JSON output
Every command accepts `--json` to return the full API response. Useful for extracting specific fields or debugging.

</commands>

<process>

<step name="1_understand_request">
Identify what the user needs:
- **Order lookup** → `orders list` then `orders get` or `orders detail` for line items
- **Product search** → `products search` (add `--all` if results are sparse)
- **Product price** → `products get <ID>` or `products search`
- **Cart action** → `cart show`, `cart add`, `cart remove`
- **Shopping list** → `lists list`, `lists get`
- **Browsing** → `categories list`, `categories get`

If the user doesn't know a product or order ID, run a list/search command first.
</step>

<step name="2_run_command">
If the command requires login (orders, cart, lists), **always run `/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona auth login` first** using the stored credentials before the actual command. Then run the appropriate CLI command via Bash. Use `--json` when you need to extract specific fields that the default output doesn't show. Chain commands when needed (e.g., search for a product ID, then get its details).
</step>
<step name="3_present_results">
Present results cleanly in plain text or a markdown table. For long lists (orders, search results), summarise the most relevant entries. For order details, show items grouped logically if there are many. Always include prices with the € symbol. Never invent or infer data not returned by the CLI.
</step>
<step name="4_handle_errors">
- **Error de autenticación tras login automático** → el token almacenado puede haber expirado; pide al usuario que ejecute `! /home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona auth login` manualmente en el prompt
- **HTTP 4xx/5xx** → muestra el mensaje de error del CLI y sugiere usar `--json` para inspeccionar la respuesta completa
- **Sin resultados** → en búsquedas de productos, sugiere añadir `--all`; en pedidos, sugiere aumentar `--limit`
</step>

</process>

<workflows>

## Generar lista de productos únicos de los últimos 10 pedidos
Este flujo permite consolidar todos los productos comprados en los últimos 10 pedidos en una única lista deduplicada en formato Markdown.

**Pasos del flujo:**
1. **Autenticación y obtención de pedidos:** Buscar los últimos 10 pedidos realizados.
   ```bash
   /home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona auth login
   /home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona orders list --limit 10 --json
   ```
2. **Recopilación de productos:** Iterar sobre cada ID de pedido para obtener el detalle de los productos comprados.
   ```bash
   /home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona orders detail <ORDER_ID> --json
   ```
3. **Creación del archivo Markdown:** Generar un archivo (ej. `mis_productos.md`) que contenga una tabla o lista con el ID y la descripción de todos los productos recopilados.
4. **Deduplicación:** Ejecutar un script de Python para procesar el archivo y asegurar que cada producto aparezca una sola vez.

**Script de deduplicación sugerido:**
```python
import sys

def deduplicar_productos(ruta_archivo):
    # Diccionario para almacenar la primera aparición de cada ID
    productos_unicos = {}
    with open(ruta_archivo, 'r') as f:
        lineas = f.readlines()
    
    for linea in lineas:
        if '|' in linea and not linea.startswith('|---'):
            partes = linea.split('|')
            # Asumimos formato: | ID | Nombre | ...
            if len(partes) > 1:
                prod_id = partes[1].strip()
                if prod_id not in productos_unicos:
                    productos_unicos[prod_id] = linea
        else:
            # Mantener encabezados o líneas de formato
            productos_unicos[linea] = linea
    
    with open(ruta_archivo, 'w') as f:
        f.writelines(productos_unicos.values())

if __name__ == "__main__":
    if len(sys.argv) > 1:
        deduplicar_productos(sys.argv[1])
```
</workflows>

<examples>

**"Iniciar sesión en Mercadona"**
```bash
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona auth login --email usuario@ejemplo.com --password contraseña
```

**"¿Qué pedí la última vez?"**
```bash
# Paso 1: login con credenciales almacenadas
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona auth login
# Paso 2: obtener el pedido más reciente
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona orders list --limit 1
# → obtener el ID del pedido, luego:
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona orders detail <ORDER_ID>
```

**"Ver todos los productos de mi último pedido"**
```bash
# Paso 1: login con credenciales almacenadas
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona auth login
# Paso 2: obtener el ID del pedido más reciente
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona orders list --limit 1
# → anota el ORDER_ID del resultado

# Paso 3: ver el detalle completo con todos los productos
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona orders detail <ORDER_ID>
# Presenta los artículos con nombre, cantidad y precio unitario
```

**"¿Cuánto cuesta la leche entera?"**
```bash
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona products search "leche entera"
# → elegir el ID de producto relevante, luego:
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona products get <ID>
```

**"Muéstrame mis últimos 5 pedidos con totales"**
```bash
# Paso 1: login con credenciales almacenadas
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona auth login
# Paso 2: listar pedidos
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona orders list --limit 5
```

**"¿Qué tengo en el carrito?"**
```bash
# Paso 1: login con credenciales almacenadas
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona auth login
# Paso 2: mostrar carrito
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona cart show
```

**"Añadir 2 unidades de Regañas Artesanas al carrito"**
```bash
# Paso 1: buscar el producto para obtener su ID (no requiere login)
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona products search "Regañas Artesanas"
# → anota el ID del producto (ej. 12345)

# Paso 2: login con credenciales almacenadas
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona auth login

# Paso 3: añadir 2 unidades al carrito
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona cart add 12345 -q 2
```

**"Añadir tomates a Mercadona" / "Agregar tomates al carrito"**
```bash
# Paso 1: buscar tomates para encontrar el producto adecuado (no requiere login)
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona products search "tomates"
# → si los resultados son escasos, usar --all:
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona products search "tomates" --all
# → elegir el ID del producto deseado (ej. 67890)

# Paso 2: login con credenciales almacenadas
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona auth login

# Paso 3: añadir al carrito (1 unidad por defecto)
/home/tato/.openclaw/workspace/skills/mercadona-cli/venv/bin/mercadona cart add 67890
```

</examples>

