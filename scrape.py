from playwright.sync_api import sync_playwright
import json

URL = "https://www.lgcstandards.com/GB/en/ChromaDex/cat/279850"
MAX_PRODUCTS = 200


def get_text(parent, selector):
    locator = parent.locator(selector).first

    if locator.count():
        return locator.inner_text().strip()

    return None


def get_attribute(parent, label):
    items = parent.locator(
        "ul.plp-item__attributes-list li"
    )

    for i in range(items.count()):
        text = items.nth(i).inner_text().strip()

        if text.startswith(label):
            return text[len(label):].strip()

    return None


def accept_cookies(page):
    try:
        button = page.get_by_text(
            "Accept cookies",
            exact=True
        )

        if button.count():
            button.first.click(timeout=3000)
            page.wait_for_timeout(1000)

    except:
        pass


with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=False
    )

    page = browser.new_page()

    page.goto(
        URL,
        wait_until="domcontentloaded"
    )

    page.wait_for_timeout(5000)

    accept_cookies(page)

    products_data = []

    while len(products_data) < MAX_PRODUCTS:

        page.wait_for_selector(
            "div.plp-item__inner"
        )

        products = page.locator(
            "div.plp-item__inner"
        )

        product_count = products.count()

        for i in range(product_count):

            if len(products_data) >= MAX_PRODUCTS:
                break

            product = products.nth(i)

            name = get_text(
                product,
                ".plp-item__name a"
            )

            link = product.locator(
                ".plp-item__name a"
            ).first

            product_url = None

            if link.count():
                product_url = link.get_attribute("href")

                if product_url:
                    if product_url.startswith("//"):
                        product_url = "https:" + product_url

                    elif product_url.startswith("/"):
                        product_url = (
                            "https://www.lgcstandards.com"
                            + product_url
                        )

            product_data = {
                "name": name,
                "product_code": get_attribute(
                    product,
                    "Product Code:"
                ),
                "cas_number": get_attribute(
                    product,
                    "CAS Number:"
                ),
                "brand": get_attribute(
                    product,
                    "Brand:"
                ),
                "product_format": get_attribute(
                    product,
                    "Product Format:"
                ),
                "analytes": get_attribute(
                    product,
                    "Analytes:"
                ),
                "pack_size": get_text(
                    product,
                    ".packsize__value"
                ),
                "stock": get_text(
                    product,
                    ".product-stock"
                ),
                "price": get_text(
                    product,
                    ".packsize__price-text"
                ),
                "url": product_url
            }

            products_data.append(product_data)

        print(f"Collected {len(products_data)} / {MAX_PRODUCTS}")

        if len(products_data) >= MAX_PRODUCTS:
            break

        accept_cookies(page)

        next_button = page.locator(
            "button.btn-next"
        )

        if not next_button.count():
            break

        if (
            next_button.get_attribute("disabled")
            is not None
            or
            next_button.get_attribute("aria-disabled") == "true"
        ):
            break

        current_first_code = get_attribute(
            products.first,
            "Product Code:"
        )

        next_button.click(
            force=True
        )

        try:
            page.wait_for_function(
                """
                (oldCode) => {
                    const element =
                        document.querySelector(
                            "ul.plp-item__attributes-list"
                        );

                    return element &&
                           !element.innerText.includes(oldCode);
                }
                """,
                current_first_code,
                timeout=15000
            )

        except:
            page.wait_for_timeout(3000)

    products_data = products_data[:MAX_PRODUCTS]

    with open(
        "products.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            products_data,
            file,
            indent=4,
            ensure_ascii=False
        )

    print()

    print("SCRAPING COMPLETE")
    print("Total products:", len(products_data))
    print("Saved to products.json")

    input("\nPress Enter to close...")

    browser.close()