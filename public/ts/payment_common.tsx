/// <reference path="../node_modules/@types/stripe-v3/index.d.ts" />
import { useEffect, useRef } from "preact/hooks";
import * as common from "./common"
import { ServerResponse } from "./common";
import { StartSubscriptionsRequest, SubscriptionStart, SubscriptionType } from "./subscriptions";
import { useTranslation } from "./translations";
import { member_t } from "./member_common";
import Cart, { Item } from "./cart";

declare var UIkit: any;

export var stripe: stripe.Stripe;
var card: stripe.elements.Element;
var spinner: any;
var payButton: HTMLInputElement;
var errorElement: any;

export function initializeStripe() {
    // Create a Stripe client.
    stripe = Stripe(window.stripeKey);
}

export function mountStripe() {
    // Create an instance of Elements.
    const elements = stripe.elements({ locale: "sv" });
    // Custom styling can be passed to options when creating an Element.
    const stripeStyle = {
        base: {
            color: '#32325d',
            lineHeight: '18px',
            fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
            fontSmoothing: 'antialiased',
            fontSize: '16px',
            '::placeholder': {
                color: '#aab7c4'
            }
        },
        invalid: {
            color: '#fa755a',
            iconColor: '#fa755a'
        }
    };

    // Create an instance of the card Element.
    card = elements.create('card', { style: stripeStyle });
    card.mount("#card-element");

    payButton = document.getElementById("pay-button") as HTMLInputElement;
    spinner = document.querySelector(".progress-spinner");
    errorElement = document.getElementById('card-errors');
    return card;
}

interface InitializePaymentFunction {
    (result: any): Promise<any>;
}
interface ResponseFunction {
    (json: any): void;
}
export interface PaymentFlowDefinition {
    initiate_payment: InitializePaymentFunction;
    before_initiate_payment?: Function;
    on_stripe_error?: (error: stripe.Error) => void;
    handle_backend_response?: (json: ServerResponse<BackendPaymentResponse>) => void;
    on_payment_success?: (json: ServerResponse<BackendPaymentResponse>) => void;
    on_failure?: (error: any) => void;
}

let waitingForPaymentResponse = false;

export function enable_pay_button() {
    spinner.classList.remove("progress-spinner-visible");
    waitingForPaymentResponse = false;
    payButton.disabled = false;
};
export function disable_pay_button() {
    payButton.disabled = true;
    waitingForPaymentResponse = true;
    spinner.classList.add("progress-spinner-visible");
};

function default_before_initiate_payment() {
    disable_pay_button();
    errorElement.textContent = "";
};
export function display_stripe_error(error: any) {
    errorElement.textContent = error.message;
    UIkit.modal.alert("<h2>Your payment failed</h2>" + errorElement.innerHTML);
}

export enum PaymentIntentNextActionType {
    USE_STRIPE_SDK = 'use_stripe_sdk',
}

export type PaymentAction = {
    type: PaymentIntentNextActionType
    client_secret: string
}

export type PaymentRequest = {
    cart: Item[],
    expected_sum: number,
    stripe_payment_method_id: string,
    transaction_id: number | null
}

export type BackendPaymentResponse = {
    type: PaymentIntentResult
    transaction_id: number,
    action_info: PaymentAction,
}

export type CartItem = {
    id: number
    count: number
}

export type Purchase = {
    cart: CartItem[]
    expected_sum: string
    stripe_payment_method_id: string
}

export type PriceLevel = "normal" | "low_income_discount";

export type Product = {
    category_id: number,
    created_at: string,
    deleted_at: string | null,
    updated_at: string,
    description: string,
    display_order: number,
    filter: string,
    id: number,
    image_id: number | null,
    product_metadata: {
        subscription_type?: SubscriptionType,
        special_product_id?: string,
        allowed_price_levels?: PriceLevel[],
    },
    name: string,
    price: string,
    show: boolean,
    smallest_multiple: number,
    unit: string,
}

export type RegisterPageData = {
    membershipProducts: {
        id: number,
        name: string,
        price: number,
    }[],
    productData: ProductCategory[],
    discounts: Record<PriceLevel, number>,
}

export type ToPay = {
    product: Product,
    amount: number,
    count: number,
    originalAmount: number,
}

export type Discount = {
    priceLevel: PriceLevel,
    fractionOff: number,
}

const WellKnownProducts = ["access_starter_pack", "single_membership_year", "single_labaccess_month", "membership_subscription", "labaccess_subscription"] as const;
type WellKnownProductId = typeof WellKnownProducts[number];

export function AssertIsWellKnownProductId(id: string | undefined): asserts id is WellKnownProductId {
    if (!WellKnownProducts.includes(id as any)) {
        throw new Error(`Unknown product id ${id}`);
    }
}

export function FindWellKnownProduct(products: Product[], id: WellKnownProductId): Product | null {
    return products.find(p => p.product_metadata.special_product_id === id) || null;
}

export const calculateAmountToPay = ({ productData, cart, currentMemberships, discount }: { productData: ProductData, cart: Cart, discount: Discount, currentMemberships: SubscriptionType[] }) => {
    const payNow: ToPay[] = [];
    const payRecurring: ToPay[] = [];

    // Calculate which memberships the user will have after the non-subscription products have been purchased.
    // This is important to handle e.g. purchasing the starter pack and a membership at the same time.
    // This is because the starter pack includes makerspace acccess membership for 2 months, so the subscription will then only start
    // after the starter pack is over, and thus the subscription will not be included in the paidRightNow output.
    currentMemberships = [...currentMemberships];
    const cartProducts = cart.items.map(i => productData.id2item.get(i.id)!);
    if (FindWellKnownProduct(cartProducts, "single_labaccess_month") !== null || FindWellKnownProduct(cartProducts, "access_starter_pack") !== null) {
        currentMemberships.push("labaccess");
    }
    if (FindWellKnownProduct(cartProducts, "single_membership_year") !== null) {
        currentMemberships.push("membership");
    }

    for (const item of cart.items) {
        const product = productData.id2item.get(item.id)!;
        const subscriptionType = product.product_metadata.subscription_type;

        if (subscriptionType !== undefined) {
            if (item.count != product.smallest_multiple) {
                throw new Error(`Cannot purchase ${item.count} of product ${product.name}. Expected ${product.smallest_multiple}`);
            }
        } else if (item.count % product.smallest_multiple !== 0) {
            throw new Error(`Cannot purchase ${item.count} of product ${product.name}. Expected a multiple of ${product.smallest_multiple}`);
        }

        let price = parseFloat(product.price);
        const originalPrice = price;
        if (product.product_metadata.allowed_price_levels?.includes(discount.priceLevel) ?? false) {
            price *= 1 - discount.fractionOff;
        }
        if (subscriptionType === undefined || !currentMemberships.includes(subscriptionType)) {
            // TODO: There's no support right now for displaying a different price during the binding period, if one exists
            payNow.push({
                product,
                count: item.count,
                amount: price * item.count,
                originalAmount: originalPrice * item.count,
            });
        }
        if (subscriptionType !== undefined) {
            // The recurring price is always just a single unit of the product
            payRecurring.push({
                product,
                count: 1,
                amount: price,
                originalAmount: originalPrice,
            });
        }
    }
    return { payNow, payRecurring };
}

export type ProductCategory = {
    id: number
    name: string
    items: Product[]
}

export type TransactionItem = {
    product: Product
    count: number
    unit: string
    amount: string
}

export type Transaction = {
    id: number
    created_at: string
    status: "pending" | "completed" | "failed"
    amount: string
    contents: TransactionItem[]
}

export type ProductData = {
    categories: ProductCategory[]
    products: Product[]
    id2item: Map<number, Product>
}

export async function LoadProductData(): Promise<ProductData> {
    const categories = (await common.ajax("GET", window.apiBasePath + "/webshop/product_data", null)).data as ProductCategory[];
    return ProductDataFromProducts(categories);
}

export function ProductDataFromProducts(categories: ProductCategory[]): ProductData {
    const id2item = new Map<number, Product>();
    const products = [];

    for (const c of categories) {
        for (const item of c.items) {
            id2item.set(item.id, item);
            products.push(item);
        }
    }
    return { categories, products, id2item };
}

export const StripeCardInput = ({ element }: { element: stripe.elements.Element }) => {
    const mountPoint = useRef<HTMLDivElement>(null);

    useEffect(() => {
        element.mount(mountPoint.current!);
    }, []);

    return (
        <div ref={mountPoint}></div>
    )
}

export const createStripeCardInput = () => {
    // Create an instance of Elements.
    const elements = stripe.elements({ locale: "sv" });
    // Custom styling can be passed to options when creating an Element.
    const stripeStyle = {
        base: {
            color: '#32325d',
            lineHeight: '18px',
            fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
            fontSmoothing: 'antialiased',
            fontSize: '16px',
            '::placeholder': {
                color: '#aab7c4'
            }
        },
        invalid: {
            color: '#fa755a',
            iconColor: '#fa755a'
        }
    };

    // Create an instance of the card Element.
    return elements.create('card', { style: stripeStyle, hidePostalCode: true });
}

const currencyToString = (value: number) => {
    if (value - Math.abs(value) < 0.01) {
        return value.toFixed(0);
    } else {
        return value.toFixed(2);
    }
}


export const ToPayPreview = ({ productData, cart, discount, currentMemberships }: { productData: ProductData, cart: Cart, discount: Discount, currentMemberships: SubscriptionType[] }) => {
    const t = useTranslation();
    const { payNow, payRecurring } = calculateAmountToPay({ productData, cart, discount, currentMemberships });

    let renewInfoText = payRecurring.map(({ product, amount }) => {
        const product_id = product.product_metadata.special_product_id;
        AssertIsWellKnownProductId(product_id);
        return t(`special_products.${product_id}.renewal`)(amount)
    }).join(" ");
    if (payRecurring.length == 1) {
        renewInfoText += " " + t("special_products.renewal.one");
    } else if (payRecurring.length > 1) {
        renewInfoText += " " + t("special_products.renewal.many");
    }

    let anyDiscountedColumn = false;
    const paidRightNowItems: [string, number, number | undefined][] = payNow.map(({ product, amount, originalAmount }, i) => {
        const product_id = product.product_metadata.special_product_id;
        AssertIsWellKnownProductId(product_id);
        if (product.unit !== "mån" && product.unit !== "år" && product.unit !== "st") throw new Error(`Unexpected unit '${product.unit}' for ${product.name}. Expected one of år/mån/st`);
        let period = product.smallest_multiple + " " + t(`unit.${product.unit}.${product.smallest_multiple > 1 ? "many" : "one"}`);
        if (product_id === "access_starter_pack") {
            // Special case for the starter pack period. Otherwise it would show "1 st"
            period = t("special_products.access_starter_pack.period");
        }
        if (amount !== originalAmount) {
            anyDiscountedColumn = true;
        }
        return [t(`special_products.${product_id}.summary`) + " - " + period, amount, amount !== originalAmount ? originalAmount : undefined];
    });

    if (paidRightNowItems.length === 0) {
        return <>
            <span className="small-print">{t("special_products.payment_right_now_nothing")}</span>
            {payRecurring.length > 0 ? (<span className="small-print">{renewInfoText}</span>) : null}
        </>
    } else {
        return (
            <>
                <span className="small-print">{t("special_products.payment_right_now")}</span>
                <div class="history-item to-pay-preview">
                    <div class={"receipt-items " + (anyDiscountedColumn ? "with-original-price-column" : "")}>
                        {paidRightNowItems.map(([summary, price, normalPrice]) => (
                            <>
                                <span className="product-title">{summary}</span>
                                {normalPrice !== undefined && <span className="receipt-item-original-amount strikethrough-price">{currencyToString(normalPrice)} {t("priceUnit")}</span>}
                                <span className="receipt-item-amount">{currencyToString(price)} {t("priceUnit")}</span>
                            </>
                        ))}
                    </div>
                    <div class="receipt-amount">
                        <span>{t("special_products.cart_total")}</span>
                        <span className="receipt-amount-value">{currencyToString(payNow.reduce((s, { amount }) => s + amount, 0))} {t("priceUnit")}</span>
                    </div>
                </div>
                {payRecurring.length > 0 ? (<span className="small-print">{renewInfoText}</span>) : null}
            </>
        )
    }
}

export type RelevantProducts = {
    starterPackProduct: Product,
    baseMembershipProduct: Product,
    labaccessProduct: Product,
    membershipSubscriptionProduct: Product,
    labaccessSubscriptionProduct: Product,
}

export const extractRelevantProducts = (products: Product[]): RelevantProducts => {
    const starterPackProduct = FindWellKnownProduct(products, "access_starter_pack");
    const baseMembershipProduct = FindWellKnownProduct(products, "single_membership_year");
    const labaccessProduct = FindWellKnownProduct(products, "single_labaccess_month");
    const membershipSubscriptionProduct = FindWellKnownProduct(products, "membership_subscription");
    const labaccessSubscriptionProduct = FindWellKnownProduct(products, "labaccess_subscription");
    if (starterPackProduct === null) throw new Error("No starter pack product found");
    if (baseMembershipProduct === null) throw new Error("No base membership product found");
    if (labaccessProduct === null) throw new Error("No labaccess product found");
    if (membershipSubscriptionProduct === null) throw new Error("No membership subscription product found");
    if (labaccessSubscriptionProduct === null) throw new Error("No labaccess subscription product found");
    return {
        starterPackProduct,
        baseMembershipProduct,
        labaccessProduct,
        membershipSubscriptionProduct,
        labaccessSubscriptionProduct,
    };

}

export async function createPaymentMethod(element: stripe.elements.Element, memberInfo: member_t): Promise<stripe.paymentMethod.PaymentMethod | null> {
    const result = await stripe.createPaymentMethod('card', element, {
        billing_details: {
            name: `${memberInfo.firstname} ${memberInfo.lastname}`,
            email: memberInfo.email,
            phone: memberInfo.phone,
            address: {
                postal_code: `${memberInfo.address_zipcode}`,
            },
        },
    });
    if (result.error) {
        UIkit.modal.alert("<h2>Your payment failed</h2>" + result.error.message);
        return null;
    }
    console.assert(result.paymentMethod !== undefined);
    return result.paymentMethod!;
}

export class PaymentFailedError {
    message: string;

    constructor(message: string) {
        this.message = message;
    }
}

export enum SetupIntentResult {
    Success = "success",
    RequiresAction = "requires_action",
    Wait = "wait",
    Failed = "failed",
}

export type SetupIntentResponse = {
    setup_intent_id: string
    type: SetupIntentResult
    error: string | null
    action_info: PaymentAction | null
}

export type SetupPaymentMethodRequest = {
    stripe_payment_method_id: string
    setup_intent_id: string | null
}

export type SetupPaymentMethodResponse = SetupIntentResponse;

export enum PaymentIntentResult {
    Success = "success",
    RequiresAction = "requires_action",
    Wait = "wait",
}

export async function handleStripeSetupIntent<T extends { setup_intent_id: string | null }, R extends SetupIntentResponse>(endpoint: string, data: T): Promise<R> {
    while (true) {
        let res: ServerResponse<R>;
        try {
            res = await common.ajax("POST", endpoint, data);
        } catch (e: any) {
            if (e["message"] !== undefined) {
                throw new PaymentFailedError(e["message"]);
            } else {
                throw e;
            }
        }
        data.setup_intent_id = res.data.setup_intent_id;

        switch (res.data.type) {
            case SetupIntentResult.Success:
                return res.data;
            case SetupIntentResult.RequiresAction:
                if (res.data.action_info!.type === PaymentIntentNextActionType.USE_STRIPE_SDK) {
                    const stripeResult = await stripe.confirmCardSetup(res.data.action_info!.client_secret);
                    if (stripeResult.error) {
                        throw new PaymentFailedError(stripeResult.error.message!);
                    } else {
                        // The card action has been handled
                        // Now we try the server endpoint again in the next iteration of the loop
                    }
                } else {
                    throw new Error("Unexpected action type");
                }
                break;
            case SetupIntentResult.Wait:
                // Stripe needs some time to confirm the payment. Wait a bit and try again.
                await new Promise(resolve => setTimeout(resolve, 500));
                break;
            case SetupIntentResult.Failed:
                throw new PaymentFailedError(res.data.error!)
        }
    }
}

export async function negotiatePayment<T extends { transaction_id: number | null }, R extends BackendPaymentResponse>(endpoint: string, data: T, options: { loginToken?: string } = {}): Promise<R> {
    while (true) {
        let res: ServerResponse<R>;
        try {
            res = await common.ajax("POST", endpoint, data, { loginToken: options.loginToken });
        } catch (e: any) {
            if (e["message"] !== undefined) {
                throw new PaymentFailedError(e["message"]);
            } else {
                throw e;
            }
        }
        data.transaction_id = res.data.transaction_id;

        switch (res.data.type) {
            case PaymentIntentResult.Success:
                return res.data;
            case PaymentIntentResult.RequiresAction:
                if (res.data.action_info!.type === PaymentIntentNextActionType.USE_STRIPE_SDK) {
                    const stripeResult = await stripe.handleCardAction(res.data.action_info!.client_secret);
                    if (stripeResult.error) {
                        throw new PaymentFailedError(stripeResult.error.message!);
                    } else {
                        // The card action has been handled
                        // Now we try the server endpoint again in the next iteration of the loop
                    }
                } else {
                    throw new Error("Unexpected action type");
                }
                break;
            case PaymentIntentResult.Wait:
                // Stripe needs some time to confirm the payment. Wait a bit and try again.
                await new Promise(resolve => setTimeout(resolve, 500));
                break;
        }
    }
}

export async function pay(paymentMethod: stripe.paymentMethod.PaymentMethod, cart: Cart, productData: ProductData, discount: Discount, currentMemberships: SubscriptionType[], options: { loginToken?: string } = {}): Promise<{ transaction_id: number | null }> {
    const { payNow, payRecurring } = calculateAmountToPay({ cart, productData, discount, currentMemberships })

    let transaction_id: number | null = null;

    if (payNow.length > 0) {
        transaction_id = (await negotiatePayment<PaymentRequest, BackendPaymentResponse>(window.apiBasePath + "/webshop/pay", {
            cart: payNow.map(p => ({
                id: p.product.id,
                count: p.count,
            })),
            expected_sum: payNow.reduce((sum, { amount }) => sum + amount, 0),
            stripe_payment_method_id: paymentMethod.id,
            transaction_id: null,
        }, { loginToken: options.loginToken })).transaction_id;
    } else {
        // This will configure the default payment method
        // This is necessary if the member already has membership (and thus the subscription will not start immediately),
        // but they have not had a subscription before, so no default payment method has been configured yet.
        await handleStripeSetupIntent<SetupPaymentMethodRequest, SetupIntentResponse>(window.apiBasePath + "/webshop/setup_payment_method", {
            stripe_payment_method_id: paymentMethod.id,
            setup_intent_id: null
        })
    }

    const subscriptionStarts: SubscriptionStart[] = payRecurring.map(({ product, amount }) => ({
        subscription: product.product_metadata.subscription_type!,
        expected_to_pay_recurring: "" + amount,
        expected_to_pay_now: "0", // We should already have paid for the member to be a member, so the subscription should start in the future and not charge anything right now
    }));

    if (subscriptionStarts.length > 0) {
        try {
            await common.ajax('POST', `${window.apiBasePath}/webshop/member/current/subscriptions`, {
                subscriptions: subscriptionStarts,
            } as StartSubscriptionsRequest, { loginToken: options.loginToken });
        } catch (e) {
            throw new PaymentFailedError(common.get_error(e));
        }
    }

    return { transaction_id }
}
