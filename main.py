"""PyScript behavior for the Printora website."""

import asyncio

from pyscript import document, window, when

RATES = {
    "bw": {"label": "B&W Printing", "rate": 2},
    "color": {"label": "Color Printing", "rate": 10},
    "copy": {"label": "Photocopying", "rate": 2},
    "bind": {"label": "Document Binding", "rate": 30},
    "check": {"label": "PrintCheck file check", "rate": None},
}


def by_id(element_id):
    return document.getElementById(element_id)


def peso(amount):
    return f"₱{amount:,}"


def read_positive_int(element_id):
    try:
        value = int(by_id(element_id).value)
    except (TypeError, ValueError):
        return 0
    return value if value > 0 else 0


def update_order(event=None):
    service = by_id("f-service")
    if not service:
        return

    key = service.value
    info = RATES[key]
    pages = read_positive_int("f-pages")
    copies = read_positive_int("f-copies")
    pages_field = by_id("f-pages").closest(".field")

    if key == "bind":
        pages_field.hidden = True
        by_id("l-copies").textContent = "Documents to bind"
        total = copies * info["rate"]
    elif key == "check":
        pages_field.hidden = False
        by_id("l-copies").textContent = "Copies"
        total = None
    else:
        pages_field.hidden = False
        by_id("l-copies").textContent = "Copies"
        total = pages * copies * info["rate"]

    if total is None:
        by_id("est-total").textContent = "We will quote"
        by_id("est-note").textContent = "PrintCheck estimate"
    else:
        by_id("est-total").textContent = peso(total)
        by_id("est-note").textContent = "Estimated total"

    lines = ["Hi Printora, I would like to place an order."]
    name = by_id("f-name").value.strip()
    contact = by_id("f-contact").value.strip()
    if name:
        lines.append(f"Name: {name}")
    if contact:
        lines.append(f"Contact: {contact}")
    lines.append(f"Service: {info['label']}")

    if key == "bind":
        lines.append(f"Documents to bind: {copies}")
    else:
        lines.extend((f"Pages per copy: {pages}", f"Copies: {copies}"))

    lines.append(f"Paper size: {by_id('f-size').value}")
    if total is not None:
        lines.append(f"Estimate: {peso(total)}")
    notes = by_id("f-notes").value.strip()
    if notes:
        lines.append(f"Notes: {notes}")
    if key == "check":
        lines.append("I will send my file for PrintCheck.")

    by_id("preview").textContent = "\n".join(lines)


def select_node(node):
    selection = window.getSelection()
    selection.removeAllRanges()
    rng = document.createRange()
    rng.selectNodeContents(node)
    selection.addRange(rng)


async def copy_text(text, fallback_node=None):
    try:
        await window.navigator.clipboard.writeText(text)
        return True
    except Exception:
        if fallback_node is not None:
            select_node(fallback_node)
        return False


@when("submit", "#order-form")
async def on_order_submit(event):
    event.preventDefault()
    update_order()
    preview = by_id("preview")
    copied = await copy_text(preview.textContent, preview)
    if copied:
        by_id("status").textContent = (
            "Copied. Paste it in a message to printora@gmail.com "
            "or text +63 912 345 6789."
        )
    else:
        by_id("status").textContent = (
            "Your browser blocked copying. The message is selected, "
            "so press Copy on your device."
        )


@when("click", ".copy-btn")
async def on_copy_click(event):
    button = event.currentTarget
    shown = button.parentNode.querySelector(".info-body span")
    copied = await copy_text(button.getAttribute("data-copy"), shown)
    button.textContent = "Copied" if copied else "Selected"
    await asyncio.sleep(1.8)
    button.textContent = "Copy"


@when("input", "#order-form")
def on_order_input(event):
    update_order()


@when("change", "#order-form")
def on_order_change(event):
    update_order()

if by_id("order-form"):
    query = str(window.location.search).lstrip("?")
    service = next(
        (
            value
            for item in query.split("&")
            for key, separator, value in [item.partition("=")]
            if separator and key == "service"
        ),
        None,
    )
    if service in RATES:
        by_id("f-service").value = service
    update_order()
