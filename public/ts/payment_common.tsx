/// <reference path="../node_modules/@types/stripe-v3/index.d.ts" />
import { useEffect, useRef } from "preact/hooks";
import * as common from "./common"
import { ServerResponse } from "./common";
import Cart from "./cart";

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

function enable_pay_button() {
    spinner.classList.remove("progress-spinner-visible");
    waitingForPaymentResponse = false;
    payButton.disabled = false;
};
function disable_pay_button() {
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

// This function might be called recursively doing multiple authentication steps.
async function handleBackendResponse(json: ServerResponse<BackendPaymentResponse>, object: PaymentFlowDefinition) {
    if (object.handle_backend_response) { object.handle_backend_response(json); }

    const action_info = json.data.action_info;
    if (action_info && action_info.type === PaymentIntentNextActionType.USE_STRIPE_SDK) {
        // This might be a recursive call doing multiple authentication steps.
        await handleStripeAction(action_info.client_secret, object);
    } else {
        if (object.on_payment_success) { object.on_payment_success(json); }
    }
}

// This function might be called recursively doing multiple authentication steps.
async function handleStripeAction(client_secret: string, object: PaymentFlowDefinition) {
    const result = await stripe.handleCardAction(
        client_secret
    );
    if (result.error) {
        display_stripe_error(result.error);
        if (object.on_stripe_error) { object.on_stripe_error(result.error); }
        enable_pay_button();
    } else {
        // The card action has been handled
        // The PaymentIntent can be confirmed again on the server
        try {
            const json = await common.ajax("POST", window.apiBasePath + "/webshop/confirm_payment", {
                payment_intent_id: result.paymentIntent!.id,
            });
            // This might be a recursive call doing multiple authentication steps.
            await handleBackendResponse(json as ServerResponse<BackendPaymentResponse>, object);
        } catch (json) {
            if (object.on_failure) { object.on_failure(json as ServerResponse<any>); }
            enable_pay_button();
        }
    }
}


export async function pay(object: PaymentFlowDefinition) {
    // Don't allow any clicks while waiting for a response from the server
    if (waitingForPaymentResponse) {
        return;
    }

    if (object.before_initiate_payment) { object.before_initiate_payment(); }
    default_before_initiate_payment();

    const result = await stripe.createPaymentMethod('card', card);
    if (result.error) {
        display_stripe_error(result.error);
        if (object.on_stripe_error) { object.on_stripe_error(result.error); }
        enable_pay_button();
    } else {
        try {
            const json = await object.initiate_payment(result);
            await handleBackendResponse(json, object);
        } catch (json) {
            if (object.on_failure) { object.on_failure(json); }
            enable_pay_button();
        }
    }
}

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
    name: string,
    price: string,
    show: boolean,
    smallest_multiple: number,
    unit: string,
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
    products: ProductCategory[]
    id2item: Map<number, Product>
}

export async function LoadProductData(): Promise<ProductData> {
    const products = (await common.ajax("GET", window.apiBasePath + "/webshop/product_data", null)).data as ProductCategory[];

    const id2item = new Map<number, Product>();

    for (const category of products) {
        for (const item of category.items) {
            id2item.set(item.id, item);
        }
    }
    return { products, id2item };
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



export class PaymentFailedError {
    message: string;

    constructor(message: string) {
        this.message = message;
    }
}

export enum PaymentIntentResult {
    Success = "success",
    RequiresAction = "requires_action",
    Wait = "wait",
}

export async function negotiatePayment<T extends { transaction_id: number | null }, R extends BackendPaymentResponse>(endpoint: string, data: T): Promise<R> {
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