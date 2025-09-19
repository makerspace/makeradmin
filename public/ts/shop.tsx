import { render } from "preact";
import { useState } from "preact/hooks";
import Cart, { useCart } from "./cart";
import * as common from "./common";
import { url } from "./common";
import { useTranslation } from "./i18n";
import * as login from "./login";
import { LoadCurrentMemberInfo } from "./member_common";
import {
    LoadProductData,
    Product,
    ProductCategory,
    ProductData,
} from "./payment_common";
import * as shopsearch from "./shopsearch";
import { Sidebar } from "./sidebar";
declare var UIkit: any;

const ProductCategoryHeader = ({ category }: { category: ProductCategory }) => {
    return (
        <li>
            <h3 id={`category${category.id}`}>{category.name}</h3>
        </li>
    );
};

/// Input field which only allows integers, and rounds up to the nearest step
const RoundedInputField = ({
    value,
    onChange,
    min,
    max,
    step,
    placeholder,
    className,
}: {
    value: number;
    onChange: (value: number) => void;
    min: number;
    max: number;
    step: number;
    placeholder: string;
    className?: string;
}) => {
    // Show the placeholder if the value is zero
    const valueStr = value != 0 ? `${value}` : "";

    // Keep track of the current value in the textfield, but only show the rounded and clamped value when the user removes focus from the text field
    const [tempValue, setTempValue] = useState(valueStr);
    const [focused, setFocused] = useState(false);
    if (!focused && tempValue !== valueStr) {
        setTempValue(valueStr);
    }

    return (
        <input
            type="text"
            pattern="[0-9]*"
            inputMode="numeric"
            step={step}
            placeholder={placeholder}
            value={tempValue}
            className={className}
            onClick={(e) => {
                // Select everything in the textfield when clicking on it
                e.currentTarget.select();
            }}
            onInput={(e) => {
                const normalized = e.currentTarget.value.replace(",", ".");
                setTempValue(normalized);
                const num = Number(normalized);
                if (normalized != "" && isFinite(num)) {
                    // Note: the |0 will ensure the number is a 32-bit integer
                    const rounded = (Math.ceil(num / step) * step) | 0;
                    const clamped = Math.min(Math.max(rounded, min), max);
                    onChange(clamped);
                }
            }}
            onFocus={(_e) => {
                setFocused(true);
            }}
            onBlur={(_e) => {
                setFocused(false);
            }}
        />
    );
};

const ProductItem = ({
    item,
    cart,
    onChangeCart,
}: {
    item: Product;
    cart: Cart;
    onChangeCart: (cart: Cart) => void;
}) => {
    const price = Number(item.price) * item.smallest_multiple;

    let baseStr =
        item.smallest_multiple > 1
            ? item.smallest_multiple + item.unit
            : item.unit;

    const image_url = `${window.apiBasePath}/webshop/image/${
        item.image_id || 0
    }`;
    const count = cart.getItemCount(item.id);

    return (
        <div className="product-container">
            <div class="product-image-container">
                <a href={url(`product/${item.id}`)}>
                    <img src={image_url} alt={item.name} />
                </a>
            </div>
            <div id={`product-${item.id}`} class="product">
                <div class="product-line">
                    <a class="product-title" href={url(`product/${item.id}`)}>
                        {item.name}
                    </a>
                    <span class="product-price">
                        {price} {Cart.currency}/{baseStr}
                    </span>
                </div>
                <div class="product-input product-line">
                    <RoundedInputField
                        min={0}
                        max={9999}
                        step={item.smallest_multiple}
                        placeholder="0"
                        value={count}
                        className="product-amount"
                        onChange={(newAmount) => {
                            cart.setItem(
                                item.id,
                                Cart.adjustItemCount(newAmount, item),
                            );
                            onChangeCart(cart);
                        }}
                    />
                    <span class="product-unit">{item.unit}</span>
                    <button
                        type="button"
                        class="number-add uk-button uk-button-small uk-button-primary"
                        data-amount="1"
                        onClick={(e) => {
                            cart.setItem(
                                item.id,
                                Cart.adjustItemCount(
                                    cart.getItemCount(item.id) + 1,
                                    item,
                                ),
                            );
                            onChangeCart(cart);
                            e.preventDefault();
                        }}
                    >
                        +
                    </button>
                </div>
            </div>
        </div>
    );
};

const ProductCategory = ({
    category,
    cart,
    onChangeCart,
    visibleItems,
}: {
    category: ProductCategory;
    cart: Cart;
    onChangeCart: (cart: Cart) => void;
    visibleItems: Set<number>;
}) => {
    const items = category.items.filter(
        (item) => visibleItems.has(item.id) && item.show,
    );
    if (items.length === 0) {
        return null;
    }

    return (
        <>
            <ProductCategoryHeader category={category} />
            <li className="product-container-list">
                {items.map((item) => (
                    <ProductItem
                        item={item}
                        cart={cart}
                        onChangeCart={onChangeCart}
                    />
                ))}
            </li>
        </>
    );
};

const SearchField = ({
    id2item,
    onChangeVisibleItems,
}: {
    id2item: Map<number, Product>;
    onChangeVisibleItems: (visible: Set<number>) => void;
}) => {
    const { t } = useTranslation("shop");
    return (
        <form className="product-search uk-search uk-search-default">
            <span uk-search-icon></span>
            <input
                className="uk-search-input"
                id="product-search-field"
                type="search"
                placeholder={t("search_placeholder")}
                onInput={(e) => {
                    const allItems = [];
                    for (const item of id2item.values()) allItems.push(item);
                    const matchingItems = shopsearch.search(
                        allItems,
                        (e.currentTarget as HTMLInputElement).value,
                    );
                    return onChangeVisibleItems(
                        new Set(matchingItems.map((item) => item.id)),
                    );
                }}
            />
        </form>
    );
};
const ShopPage = ({ productData }: { productData: ProductData }) => {
    const { cart, setCart } = useCart();
    const [visibleItems, setVisibleItems] = useState(
        new Set(productData.id2item.keys()),
    );

    // Load saved layout mode
    const [layoutMode, setLayoutModeInternal] = useState(
        localStorage.getItem("webshop-layout-mode") || "layout-grid",
    );
    const layoutModes = ["layout-grid", "layout-list", "layout-table"];
    function setLayoutMode(mode: string) {
        setLayoutModeInternal(mode);
        localStorage.setItem("webshop-layout-mode", mode);
    }
    if (!layoutModes.includes(layoutMode)) setLayoutMode(layoutModes[0]!);

    return (
        <>
            <Sidebar cart={{ cart, productData }} />
            <div id="content">
                <ul className={`product-list ${layoutMode}`}>
                    <li className="product-search-bar">
                        <SearchField
                            id2item={productData.id2item}
                            onChangeVisibleItems={setVisibleItems}
                        />
                        <div className="toggle-product-images uk-button-group">
                            <button
                                className={`layout-button uk-icon-button ${
                                    layoutMode === "layout-grid"
                                        ? "selected"
                                        : ""
                                }`}
                                uk-icon="icon: grid"
                                onClick={() => setLayoutMode("layout-grid")}
                            ></button>
                            <button
                                className={`layout-button uk-icon-button ${
                                    layoutMode === "layout-list"
                                        ? "selected"
                                        : ""
                                }`}
                                uk-icon="icon: list"
                                onClick={() => setLayoutMode("layout-list")}
                            ></button>
                            <button
                                className={`layout-button uk-icon-button ${
                                    layoutMode === "layout-table"
                                        ? "selected"
                                        : ""
                                }`}
                                uk-icon="icon: table"
                                onClick={() => setLayoutMode("layout-table")}
                            ></button>
                        </div>
                    </li>
                    {productData.categories.map((cat) => (
                        <ProductCategory
                            category={cat}
                            cart={cart}
                            onChangeCart={setCart}
                            visibleItems={visibleItems}
                        />
                    ))}
                </ul>
            </div>
        </>
    );
};

const productData = LoadProductData();
const member = LoadCurrentMemberInfo();
common.documentLoaded().then(() => {
    const root = document.querySelector("#root") as HTMLElement;

    // renderSidebarCategories(productData, true);
    Promise.all([member, productData])
        .then(([_member, productData]) => {
            if (root != null) {
                root.innerHTML = "";
                render(<ShopPage productData={productData} />, root);
            }
        })
        .catch((json) => {
            // Probably Unauthorized, redirect to login page.
            if (json.status === common.UNAUTHORIZED) {
                // Render login
                login.render_login(root, null, null);
            } else {
                UIkit.modal.alert(
                    "<h2>Misslyckades med att hämta köphistorik</h2>" +
                        common.get_error(json),
                );
            }
        });
});
