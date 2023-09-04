import { render } from "preact";
import { member_t, membership_t } from "./member_common"
import { Discount, LoadProductData, PaymentFailedError, Product, ProductData, ProductDataFromProducts, RegisterPageData, SetupIntentResponse, StripeCardInput, ToPayPreview, calculateAmountToPay, createPaymentMethod, createStripeCardInput, extractRelevantProducts, handleStripeSetupIntent, pay } from "./payment_common";
import { ajax, show_error } from "./common";
import { useState } from "preact/hooks";
import { TranslationWrapper, useTranslation, translateUnit } from "./translations";
import Cart from "./cart";
declare var UIkit: any;

export type SubscriptionType = "membership" | "labaccess"

export type SubscriptionStart = {
    subscription: SubscriptionType
    expected_to_pay_now: string // Encoded decimal
    expected_to_pay_recurring: string // Encoded decimal
}

export type UpcomingInvoice = {
    payment_date: string
    amount_due: string
}

export type SubscriptionInfo = {
    type: SubscriptionType
    active: boolean
    upcoming_invoice: UpcomingInvoice | null
}

export type SubscriptionInfos = {
    base_membership: SubscriptionInfo,
    makerspace_access: SubscriptionInfo,
}

export type StartSubscriptionsRequest = {
    subscriptions: SubscriptionStart[]
}

const PayDialog = ({ stripe, products, productData, discount, currentMemberships, memberInfo, onCancel, onPay }: { stripe: stripe.elements.Element, productData: ProductData, products: Product[], currentMemberships: SubscriptionType[], discount: Discount, memberInfo: member_t, onCancel: () => void, onPay: () => void }) => {
    const t = useTranslation();
    const [inProgress, setInProgress] = useState(false);
    const cart = new Cart(products.map(p => ({ id: p.id, count: p.smallest_multiple })));
    return (
        <>
            <div class="uk-modal-header">
                <h2>{t('member_page.subscriptions.pay_dialog.title')}</h2>
            </div>
            <div class="uk-modal-body">
                {products.filter(p => p.smallest_multiple > 1).map(p => {
                    const sub_type = p.product_metadata.subscription_type;
                    if (sub_type === undefined) return null;

                    // If the member already has membership, information about the binding period is redundant, or even misleading
                    if (currentMemberships.includes(sub_type)) return null;

                    return <p class="small-print">{t(`special_products.${sub_type}_subscription.summary`)} {t('member_page.subscriptions.binding_period')(p.smallest_multiple, translateUnit(p.unit, p.smallest_multiple, t))}</p>;
                })}
                <ToPayPreview productData={productData} cart={cart} discount={discount} currentMemberships={currentMemberships} />
                <div class="uk-margin"></div>
                <StripeCardInput element={stripe} />
            </div>
            <div class="uk-modal-footer uk-text-right">
                <button class="uk-button" onClick={onCancel}>{t("cancel")}</button>{" "}
                <button class="uk-button uk-button-primary spinner-button" disabled={inProgress} onClick={async () => {
                    setInProgress(true);
                    const paymentMethod = await createPaymentMethod(stripe, memberInfo);
                    if (paymentMethod === null) {
                        onCancel();
                        setInProgress(false);
                        return;
                    }
                    try {
                        await pay(paymentMethod, cart, productData, discount, currentMemberships);
                    } catch (e) {
                        setInProgress(false);
                        if (e instanceof PaymentFailedError) {
                            onCancel();
                            UIkit.modal.alert("<h2>Payment failed</h2>" + e.message);
                        } else {
                            throw e;
                        }
                    }
                    setInProgress(false);
                    onPay();
                }}>
                    <span className={"uk-spinner uk-icon progress-spinner " + (inProgress ? "progress-spinner-visible" : "")} uk-spinner={''} />
                    <span>{t("payment.pay_with_stripe")}</span>
                </button>
            </div>
        </>
    );
};

const CancelDialog = ({ types, membership, onCancelDialog, onCancelSubscriptions }: { types: SubscriptionType[], membership: membership_t, onCancelDialog: () => void, onCancelSubscriptions: () => void }) => {
    const t = useTranslation();
    const typeStr = types.map(ty => t(`special_products.${ty}_subscription.summary`)).join(" " + t("and") + " ");
    return <>
        <div class="uk-modal-header">
            <h2>Cancel auto-renewal</h2>
        </div>
        <div class="uk-modal-body">
            <p>Your {typeStr} will no longer be automatically renewed.</p>
            {types.includes("membership") && membership.membership_active && <p>{t("member_page.subscriptions.cancel.membership.valid_until")(membership.membership_end)}</p>}
            {types.includes("labaccess") && membership.labaccess_active && <p>{t("member_page.subscriptions.cancel.labaccess.valid_until")(membership.labaccess_end)}</p>}
        </div>
        <div class="uk-modal-footer uk-text-right">
            <button class="uk-button" onClick={onCancelDialog}>Nevermind</button>{" "}
            <button class="uk-button uk-button-primary" onClick={async () => {
                try {
                    await ajax('DELETE', `${window.apiBasePath}/webshop/member/current/subscriptions`, { subscriptions: types });
                } catch (e) {
                    show_error("Failed to cancel subscription", e);
                    onCancelDialog();
                    return;
                }
                onCancelSubscriptions();
            }}>Cancel subscription</button>
        </div>
    </>;
}

export async function getCurrentSubscriptions(): Promise<SubscriptionInfo[]> {
    return (await ajax('GET', `${window.apiBasePath}/webshop/member/current/subscriptions`)).data as SubscriptionInfo[];
}

export async function cancelSubscription(type: SubscriptionType, membership: membership_t, subscriptions: SubscriptionInfo[]) {
    const types = [type];
    if (type === "membership" && subscriptions.some(s => s.type === "labaccess")) {
        // If we cancel membership, we must also cancel labaccess
        types.push("labaccess");
    }

    const p = UIkit.modal.dialog("", { bgClose: false });
    const promise = new Promise((resolve, reject) => {
        render(
            <TranslationWrapper>
                <CancelDialog
                    types={types}
                    membership={membership}
                    onCancelDialog={() => {
                        p.hide();
                        reject();
                    }}
                    onCancelSubscriptions={async () => {
                        await p.hide();
                        resolve(null);
                        location.reload();
                    }}
                />
            </TranslationWrapper>,
            p.panel
        );
        p.panel.parentElement!.addEventListener("hide", reject);
    });

    await promise;
}

export async function activateSubscription(type: SubscriptionType, member: member_t, membership: membership_t, subscriptions: SubscriptionInfo[]) {
    if (subscriptions.some(s => s.type === type)) {
        throw new Error("Member already has this subscription");
    }

    let to_activate: SubscriptionType[] = [type];
    if (type === "labaccess" && !subscriptions.some(s => s.type === "membership")) {
        try {
            await UIkit.modal.alert("<p>Activating Makerspace Access Auto-renewal will also activate Base Membership auto-renewal</p>");
        } catch {
            return;
        }
        to_activate.push("membership");
    }

    // Note: This is not the same as the subscriptions array. A member may have access even if they do not have an active subscription.
    const currentMemberships: SubscriptionType[] = [];
    if (membership.membership_active) currentMemberships.push("membership");
    if (membership.labaccess_active) currentMemberships.push("labaccess");

    const productData = await LoadProductData();
    const products = productData.products.filter(p => to_activate.includes(p.product_metadata.subscription_type!));
    if (products.length !== to_activate.length) {
        throw new Error("Could not find all subscription products");
    }

    const stripe = createStripeCardInput();

    const p = UIkit.modal.dialog("", { bgClose: false });
    const panel: HTMLDivElement = p.panel;
    const promise = new Promise((resolve, reject) => {
        render(
            <TranslationWrapper>
                <PayDialog
                    stripe={stripe}
                    products={products}
                    productData={productData}
                    discount={{ priceLevel: "normal", fractionOff: 0.0 }}
                    memberInfo={member}
                    currentMemberships={currentMemberships}
                    onCancel={() => {
                        reject();
                    }}
                    onPay={() => {
                        resolve(null);
                    }}
                />
            </TranslationWrapper>,
            p.panel
        );
        panel.parentElement!.addEventListener("hide", reject);
    });
    try {
        await promise;
        await p.hide();
        location.reload();
    } catch {
        p.hide();
        return;
    };
}
