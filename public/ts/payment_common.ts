/// <reference path="../node_modules/@types/stripe-v3/index.d.ts" />
import * as common from "./common"
import { ServerResponse } from "./common";

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

initializeStripe();

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

    payButton = <HTMLInputElement>document.getElementById("pay-button");
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
    transaction_id: string,
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
