import Cart from "./cart"
import * as common from "./common"
import { login } from "./common";
import { initializeStripe, pay } from "./payment_common"
declare var UIkit: any;


common.onGetAndDocumentLoaded("/webshop/register_page_data", (value: any) => {
    common.addSidebarListeners();

    const { productData, membershipProducts } = value;

    const apiBasePath = window.apiBasePath;

    // Add membership products
    membershipProducts.forEach((product: any) => {
        document.querySelector("#products")!.innerHTML += `<div><input class="uk-radio" type="radio" value="${product.id}" name="product" checked/> ${product.name}: ${product.price} kr</div>`;
    });

    // Add an instance of the card Element into the `card-element` <div>.
    initializeStripe();

    const id2item = new Map();

    for (const cat of productData) {
        for (const item of cat.items) {
            id2item.set(item.id, item);
        }
    }

    let cart: Cart = new Cart([]);

    function refresh() {
        let checked = document.querySelectorAll(".uk-radio:checked");

        // Should only have 1 checked radio button
        if (checked.length !== 1) throw new Error("expected one checked radio button was " + checked.length);

        cart = new Cart([{
            id: Number((<HTMLInputElement>checked[0]).value),
            count: 1,
        }]);

        const totalSum = cart.sum(id2item);
        document.querySelector("#pay-button")!.querySelector("span")!.innerHTML = "Betala " + Cart.formatCurrency(totalSum);
    }

    [].forEach.call(document.querySelectorAll(".uk-radio"), (el: HTMLElement) => {
        el.addEventListener("change", () => {
            refresh();
        });
        el.addEventListener("input", () => {
            refresh();
        });
    });

    const payment_button = document.querySelector<HTMLButtonElement>("#pay-button")!;
    const validate_fields: Array<string> = ['firstname', 'lastname', 'email', 'address_zipcode'];

    function checkInputField(field: string): boolean {
        const el = document.querySelector<HTMLInputElement>("#" + field)!;
        return el.checkValidity();
    }

    function isInputInvalid(): boolean {
        return validate_fields.reduce<boolean>((acc, field) => acc || !checkInputField(field), false);
    }

    function updatePaymentButton() {
        payment_button.disabled = isInputInvalid();
    }

    validate_fields.forEach(field => {
        const el = document.querySelector<HTMLElement>("#" + field)!;
        el.addEventListener("change", () => {
            updatePaymentButton();
        });
        el.addEventListener("input", () => {
            updatePaymentButton();
        });
    });


    function pay_config() {
        function initiate_payment(result: any) {
            return common.ajax("POST", apiBasePath + "/webshop/register", {
                member: {
                    firstname: common.getValue("#firstname"),
                    lastname: common.getValue("#lastname"),
                    email: common.getValue("#email"),
                    // phone: common.getValue("#phone"), disabled until we can validate phone on register
                    address_street: "", // common.getValue("#address_street"),
                    address_extra: "", // common.getValue("#address_extra"),
                    address_zipcode: parseInt(common.getValue("#address_zipcode").replace(/ /g, '')) || null,
                    address_city: "", // common.getValue("#address_city"),
                },
                purchase: {
                    cart: cart.items,
                    expected_sum: cart.sum(id2item),
                    stripe_payment_method_id: result.paymentMethod.id,
                }
            });
        };
        function handle_backend_response(json: any) {
            const token: string = json.data.token;
            if (token) {
                login(token);
            }
        };
        function on_failure(json: any) {
            if (json.what === "not_unique") {
                UIkit.modal.alert("<h2>Email has already been registered</h2>Log in <a href=\"/member\">on the member pages</a> and then continue to the shop, where you can buy either the membership or the starter pack.</p>");
            } else {
                UIkit.modal.alert("<h2>The payment failed</h2>" + common.get_error(json));
            }
        };
        return {
            initiate_payment: initiate_payment,
            handle_backend_response: handle_backend_response,
            on_failure: on_failure,
        };
    };
    const payment_config = pay_config();

    document.querySelector("#pay-button")!.addEventListener("click", ev => {
        ev.preventDefault();
        pay(payment_config);
    });

    refresh();
});
