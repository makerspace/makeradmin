import { render } from "preact";
import { useMemo, useState } from "preact/hooks";
import Cart, { Item, useCart } from "./cart";
import * as common from "./common";
import { ServerResponse, UNAUTHORIZED } from "./common";
import { useTranslation } from "./i18n";
import * as login from "./login";
import { LoadCurrentMemberInfo } from "./member_common";
import {
    BackendPaymentResponse,
    LoadProductData,
    PaymentFlowDefinition,
    ProductData,
    StripeCardInput,
    createStripeCardInput,
    initializeStripe,
    pay,
    stripe,
} from "./payment_common";
import { Sidebar } from "./sidebar";
declare var UIkit: any;

const CartItem = ({
    cartItem,
    productData,
    cart,
    onChangeCart,
}: {
    cartItem: Item;
    productData: ProductData;
    cart: Cart;
    onChangeCart: (cart: Cart) => void;
}) => {
    const item = productData.id2item.get(cartItem.id);
    if (item === undefined || !item.show) {
        // Item no longer exists or should not be visible in the shop anymore.
        cart.setItem(cartItem.id, 0);
        onChangeCart(cart);
        return null;
    }

    let price = Number(item.price) * item.smallest_multiple;

    let baseStr =
        item.smallest_multiple > 1
            ? item.smallest_multiple + item.unit
            : item.unit;

    return (
        <div class="product">
            <div class="product-line">
                <a class="product-title" href="product/${item.id}">
                    {item.name}
                </a>
                <span class="product-price">
                    {price} {Cart.currency}/{baseStr}
                </span>
            </div>
            <div class="product-input product-line">
                <input
                    type="number"
                    min={0}
                    max={9999}
                    value={cartItem.count}
                    step={item.smallest_multiple}
                    placeholder="0"
                    class="product-amount"
                    onChange={(e) => {
                        let newAmount = Cart.adjustItemCount(
                            Number(e.currentTarget.value),
                            item,
                        );
                        cart.setItem(item.id, newAmount);
                        onChangeCart(cart);
                    }}
                />
                <span class="product-unit">{item.unit}</span>
                <button
                    type="button"
                    class="product-delete uk-button uk-button-small uk-button-danger"
                    uk-icon="trash"
                    onClick={(_e) => {
                        cart.setItem(item.id, 0);
                        onChangeCart(cart);
                    }}
                />
            </div>
        </div>
    );
};

const PaymentButton = ({
    cart,
    productData,
}: {
    cart: Cart;
    productData: ProductData;
}) => {
    function pay_config(): PaymentFlowDefinition {
        return {
            initiate_payment: (result) => {
                return common.ajax(
                    "POST",
                    window.apiBasePath + "/webshop/pay",
                    {
                        cart: cart.items,
                        expected_sum: cart.sum(productData.id2item),
                        stripe_payment_method_id: result.paymentMethod.id,
                    },
                );
            },
            on_payment_success: (
                json: ServerResponse<BackendPaymentResponse>,
            ) => {
                new Cart([]).saveToStorage();
                window.location.href = "receipt/" + json.data.transaction_id;
            },
            on_failure: (json: ServerResponse<any>) => {
                if (json.status === UNAUTHORIZED) {
                    UIkit.modal.alert(
                        "<h2>Betalningen misslyckades</h2>Du är inte inloggad",
                    );
                } else {
                    UIkit.modal.alert(
                        "<h2>Betalningen misslyckades</h2>" +
                            common.get_error(json),
                    );
                }
            },
        };
    }

    const [inProgress, setInProgress] = useState(false);
    const paymentConfig = pay_config();
    const element = useMemo(() => createStripeCardInput(), []);
    const { t } = useTranslation("payment");

    return (
        <>
            <form id="pay">
                <h3>{t("pay_with_stripe")}</h3>
                <div class="form-row">
                    <div id="payment_element"></div>
                    <div id="card-element">
                        <StripeCardInput element={element} />
                    </div>
                    <div id="card-errors" role="alert"></div>
                </div>

                <button
                    type="button"
                    id="pay-button"
                    class="spinner-button uk-button uk-button-default uk-button-primary"
                    disabled={inProgress}
                    onClick={async (e) => {
                        e.preventDefault();
                        setInProgress(true);
                        try {
                            const result = await stripe.createPaymentMethod(
                                "card",
                                element,
                            );
                            if (result.error) {
                                throw result.error;
                            } else {
                                const payment = await pay(
                                    result.paymentMethod!,
                                    cart,
                                    productData,
                                    {
                                        // TODO: Add support for discounts here
                                        priceLevel: "normal",
                                        fractionOff: 0,
                                    },
                                    [],
                                );

                                // Payment succeeded! Clear the cart and go to the receipt page.
                                new Cart([]).saveToStorage();
                                if (payment.transaction_id !== null) {
                                    window.location.href =
                                        "receipt/" + payment.transaction_id;
                                } else {
                                    // Shouldn't happen unless only subscriptions were started. Which shouldn't be possible from the cart page.
                                    window.location.href = "/member";
                                }
                            }
                        } catch (e) {
                            common.show_error(t("payment_failed"), e);
                        } finally {
                            setInProgress(false);
                        }
                    }}
                >
                    <span
                        class={`uk-spinner uk-icon progress-spinner ${
                            inProgress ? "progress-spinner-visible" : ""
                        }`}
                        uk-spinner={""}
                    ></span>
                    <span>
                        {t("pay")}
                        <span>
                            {" "}
                            {Cart.formatCurrency(cart.sum(productData.id2item))}
                        </span>
                    </span>
                </button>
            </form>
        </>
    );
};

const CartPage = ({ productData }: { productData: ProductData }) => {
    const { cart, setCart } = useCart();
    const { t } = useTranslation("payment");

    return (
        <>
            <Sidebar cart={{ cart, productData }} />
            <div id="content" class="cartpage">
                <div class="content-centering">
                    <h3 class="cart-header">{t("cart")}</h3>
                    <ul id="cart" class="layout-table">
                        {cart.items.length > 0 ? (
                            cart.items.map((cartItem) => (
                                <CartItem
                                    cartItem={cartItem}
                                    productData={productData}
                                    cart={cart}
                                    onChangeCart={setCart}
                                />
                            ))
                        ) : (
                            <p class="empty-cart-text">{t("cart_empty")}</p>
                        )}
                    </ul>
                    <div id="pay-module">
                        {cart.items.length > 0 && (
                            <PaymentButton
                                cart={cart}
                                productData={productData}
                            />
                        )}
                    </div>
                </div>
            </div>
        </>
    );
};

common.documentLoaded().then(() => {
    const productData = LoadProductData();
    const member = LoadCurrentMemberInfo();
    const root = document.querySelector("#root") as HTMLElement;
    initializeStripe();

    Promise.all([member, productData])
        .then(([_member, productData]) => {
            if (root != null) {
                root.innerHTML = "";
                render(<CartPage productData={productData} />, root);
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
