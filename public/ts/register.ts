import Cart from "./cart"
import * as common from "./common"
import { login } from "./common";
import { Product, ProductData, ProductDataFromProducts, Purchase, RegisterPageData, SetupIntentResponse, calculateAmountToPay, createPaymentMethod, disable_pay_button, enable_pay_button, handleStripeSetupIntent, initializeStripe, mountStripe } from "./payment_common"
declare var UIkit: any;

type MemberInfo = {
    firstName: string,
    lastName: string,
    email: string,
    phone: string,
    zipCode: string,
}

type RegisterRequest = {
    purchase: Purchase
    setup_intent_id: string | null
    member: MemberInfo
    subscriptions: []
    discount: null
}

type RegistrationSuccess = {
    loginToken: string
}

type Plan = {
    products: Product[],
}

async function registerMember(paymentMethod: stripe.paymentMethod.PaymentMethod, productData: ProductData, memberInfo: MemberInfo, selectedPlan: Plan): Promise<RegistrationSuccess> {
    const { payNow, payRecurring } = calculateAmountToPay({ cart: Cart.oneOfEachProduct(selectedPlan.products), productData, discount: { priceLevel: "normal", fractionOff: 0 }, currentMemberships: [] })
    const nonSubscriptionProducts = selectedPlan.products.filter(p => p.product_metadata.subscription_type === undefined);
    const data: RegisterRequest = {
        member: memberInfo,
        purchase: {
            cart: nonSubscriptionProducts.map(p => ({
                id: p.id,
                count: 1,
            })),
            expected_sum: "" + payNow.filter(p => p.product.product_metadata.subscription_type === undefined).reduce((sum, { amount }) => sum + amount, 0),
            stripe_payment_method_id: paymentMethod.id,
        },
        subscriptions: [],
        setup_intent_id: null,
        discount: null,
    };

    return {
        loginToken: (await handleStripeSetupIntent<RegisterRequest, SetupIntentResponse & { token: string }>(window.apiBasePath + "/webshop/register", data)).token!
    };
}

common.onGetAndDocumentLoaded("/webshop/register_page_data", (value: RegisterPageData) => {
    common.addSidebarListeners();
    initializeStripe();

    const { membershipProducts } = value;
    const productData = ProductDataFromProducts(value.productData);

    const apiBasePath = window.apiBasePath;

    // Add membership products
    membershipProducts.forEach((product: any) => {
        document.querySelector("#products")!.innerHTML += `<div><input class="uk-radio" type="radio" value="${product.id}" name="product" checked/> ${product.name}: ${product.price} kr</div>`;
    });

    // Add an instance of the card Element into the `card-element` <div>.
    const element = mountStripe();

    let cart: Cart = new Cart([]);

    function refresh() {
        let checked = document.querySelectorAll(".uk-radio:checked");

        // Should only have 1 checked radio button
        if (checked.length !== 1) throw new Error("expected one checked radio button was " + checked.length);

        cart = new Cart([{
            id: Number((<HTMLInputElement>checked[0]).value),
            count: 1,
        }]);

        const totalSum = cart.sum(productData.id2item);
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
    const validate_fields: Array<string> = ['firstname', 'lastname', 'email', 'phone', 'address_zipcode'];

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

    document.querySelector("#pay-button")!.addEventListener("click", async ev => {
        ev.preventDefault();
        try {
            disable_pay_button();
            const memberInfo: MemberInfo = {
                firstName: common.getValue("#firstname"),
                lastName: common.getValue("#lastname"),
                email: common.getValue("#email"),
                phone: common.getValue("#phone"),
                zipCode: common.getValue("#address_zipcode").replace(/ /g, ''),
            };
            const paymentMethod = await createPaymentMethod(element, {
                address_street: "",
                address_extra: "",
                address_zipcode: memberInfo.zipCode,
                address_city: "",
                email: memberInfo.email,
                member_number: 0,
                firstname: memberInfo.firstName,
                lastname: memberInfo.lastName,
                phone: "",
                pin_code: "",
                labaccess_agreement_at: "",
            });
            if (paymentMethod !== null) {
                const registration = await registerMember(paymentMethod, productData, memberInfo, {
                    products: productData.products.filter((p: any) => cart.items.find(x => x.id === p.id)),
                });
                login(registration.loginToken);
                window.location.href = "/member";
            }
        } catch (e: any) {
            enable_pay_button();
            if (e.what === "not_unique") {
                UIkit.modal.alert("<h2>Registration failed</h2><p>This email has already been registered</p>");
            } else {
                common.show_error("Registrering misslyckades", e);
            }
        }
    });

    refresh();
});
