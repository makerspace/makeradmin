/// <reference path="../node_modules/@types/stripe-v3/index.d.ts" />
import * as common from "./common"

// TODO QA New file, composed from old code?

var stripe: stripe.Stripe;
var card: stripe.elements.Element;
var spinner: any;
var payButton: HTMLButtonElement;
var errorElement: any;

export function initializeStripe() {
    // Create a Stripe client.
    stripe = Stripe(window.stripeKey);
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

    payButton = <HTMLInputElement> document.getElementById("pay-button");
    spinner = document.querySelector(".progress-spinner");
    errorElement = document.getElementById('card-errors');
}

interface InitializePaymentFunction{
    (result: any): Promise<any>;
}
interface ResponseFunction{
    (json: any): void;
}
export interface PaymentFlowDefinition{
    initiate_payment: InitializePaymentFunction;
    before_initiate_payment?: Function;
    on_stripe_error?: ResponseFunction;
    handle_backend_response?: ResponseFunction;
    on_payment_success?: ResponseFunction;
    on_failure?: ResponseFunction;
}

let waitingForPaymentResponse = false;

function enable_pay_button(){
    spinner.classList.remove("progress-spinner-visible");
    waitingForPaymentResponse = false;
    payButton.disabled = false;
};
function disable_pay_button(){
    payButton.disabled = true;
    waitingForPaymentResponse = true;
    spinner.classList.add("progress-spinner-visible");
};

function default_before_initiate_payment(){
    disable_pay_button();
    errorElement.textContent = "";
};
function display_stripe_error(error: any){
    errorElement.textContent = error.message;
}

function handleBackendResponse(json: any, object: PaymentFlowDefinition) {
    if (object.handle_backend_response) {object.handle_backend_response(json);}

    const action_info = json.data.action_info;
    if (action_info && action_info.type === 'use_stripe_sdk') {
        handleStripeAction(action_info.client_secret, object);
    } else if (action_info && action_info.type === 'redirect_to_url') {
        if (object.on_payment_success) {object.on_payment_success(json);}
        window.location.href = action_info.redirect;
    } else {
        if (object.on_payment_success) {object.on_payment_success(json);}
        window.location.href = "receipt/" + json.data.transaction_id;
    }
}

function handleStripeAction(client_secret: any, object: PaymentFlowDefinition) {
    stripe.handleCardAction(
          client_secret
    ).then(function(result: any) {
        if (result.error) {
            display_stripe_error(result.error);
            if (object.on_stripe_error) {object.on_stripe_error(result.error);}
            enable_pay_button();
        } else {
            // The card action has been handled
            // The PaymentIntent can be confirmed again on the server
            common.ajax("POST", window.apiBasePath + "/webshop/confirm_payment", {
                payment_intent_id: result.paymentIntent.id,
            }).then(json => {
                handleBackendResponse(json, object);
            }).catch(json => {
                if (object.on_failure) {object.on_failure(json);}
                enable_pay_button();
            })
        }
    });
}


// TODO QA No spinner? Just test in browser.
export function pay(object: PaymentFlowDefinition) {
    // Don't allow any clicks while waiting for a response from the server
    if (waitingForPaymentResponse) {
        return;
    }

    if (object.before_initiate_payment) {object.before_initiate_payment();}
    default_before_initiate_payment();

    stripe.createPaymentMethod('card', card).then(function(result: any) {
        if (result.error) {
            display_stripe_error(result.error);
            if (object.on_stripe_error) {object.on_stripe_error(result.error);}
            enable_pay_button();
        } else {
            object.initiate_payment(result).then(json => {
                handleBackendResponse(json, object);
            }).catch(json => {
                if (object.on_failure) {object.on_failure(json);}
                enable_pay_button();
            });
        }
    });
}
