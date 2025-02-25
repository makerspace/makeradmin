import { render } from "preact";
import { useState } from "preact/hooks";
import Cart from "./cart";
import { ajax, formatDate, show_error } from "./common";
import { Translator, useTranslation } from "./i18n";
import { member_t, membership_t } from "./member_common";
import {
    Discount,
    FindWellKnownProduct,
    LoadProductData,
    PaymentFailedError,
    Product,
    ProductData,
    StripeCardInput,
    ToPayPreview,
    createPaymentMethod,
    createStripeCardInput,
    pay,
} from "./payment_common";
import { translateUnit } from "./translations";
declare var UIkit: any;

export type SubscriptionType = "membership" | "labaccess";

export type SubscriptionStart = {
    subscription: SubscriptionType;
    expected_to_pay_now: string; // Encoded decimal
    expected_to_pay_recurring: string; // Encoded decimal
};

export type UpcomingInvoice = {
    payment_date: string;
    amount_due: string;
};

export type SubscriptionInfo = {
    type: SubscriptionType;
    active: boolean;
    upcoming_invoice: UpcomingInvoice | null;
};

export type SubscriptionInfos = {
    base_membership: SubscriptionInfo;
    makerspace_access: SubscriptionInfo;
};

export type StartSubscriptionsRequest = {
    subscriptions: SubscriptionStart[];
};

const PayDialog = ({
    stripe,
    products,
    productData,
    discount,
    currentMemberships,
    memberInfo,
    onCancel,
    onPay,
}: {
    stripe: stripe.elements.Element;
    productData: ProductData;
    products: Product[];
    currentMemberships: SubscriptionType[];
    discount: Discount;
    memberInfo: member_t;
    onCancel: () => void;
    onPay: () => void;
}) => {
    const { t } = useTranslation("member_page");
    const { t: tPayment } = useTranslation("payment");
    const { t: tSpecial } = useTranslation("special_products");
    const { t: tCommon } = useTranslation("common");

    const [inProgress, setInProgress] = useState(false);
    const cart = new Cart(
        products.map((p) => ({ id: p.id, count: p.smallest_multiple })),
    );
    return (
        <>
            <div class="uk-modal-header">
                <h2>{t("subscriptions.pay_dialog.title")}</h2>
            </div>
            <div class="uk-modal-body">
                {products
                    .filter((p) => p.smallest_multiple > 1)
                    .map((p) => {
                        const sub_type = p.product_metadata.subscription_type;
                        if (sub_type === undefined) return null;

                        // If the member already has membership, information about the binding period is redundant, or even misleading
                        if (currentMemberships.includes(sub_type)) return null;

                        return (
                            <p class="small-print">
                                {tSpecial(`${sub_type}_subscription.summary`)}{" "}
                                {t("subscriptions.binding_period", {
                                    count: p.smallest_multiple,
                                    unit: translateUnit(
                                        p.unit,
                                        p.smallest_multiple,
                                        tCommon,
                                    ),
                                })}
                            </p>
                        );
                    })}
                <ToPayPreview
                    productData={productData}
                    cart={cart}
                    discount={discount}
                    currentMemberships={currentMemberships}
                />
                <div class="uk-margin"></div>
                <StripeCardInput element={stripe} />
            </div>
            <div class="uk-modal-footer uk-text-right">
                <button class="uk-button" onClick={onCancel}>
                    {tCommon("cancel")}
                </button>{" "}
                <button
                    class="uk-button uk-button-primary spinner-button"
                    disabled={inProgress}
                    onClick={async () => {
                        setInProgress(true);
                        const paymentMethod = await createPaymentMethod(
                            stripe,
                            memberInfo,
                        );
                        if (paymentMethod === null) {
                            onCancel();
                            setInProgress(false);
                            return;
                        }
                        try {
                            await pay(
                                paymentMethod,
                                cart,
                                productData,
                                discount,
                                currentMemberships,
                            );
                        } catch (e) {
                            setInProgress(false);
                            if (e instanceof PaymentFailedError) {
                                onCancel();
                                UIkit.modal.alert(
                                    "<h2>Payment failed</h2>" + e.message,
                                );
                            } else {
                                throw e;
                            }
                        }
                        setInProgress(false);
                        onPay();
                    }}
                >
                    <span
                        className={
                            "uk-spinner uk-icon progress-spinner " +
                            (inProgress ? "progress-spinner-visible" : "")
                        }
                        uk-spinner={""}
                    />
                    <span>{tPayment("pay_with_stripe")}</span>
                </button>
            </div>
        </>
    );
};

const CancelDialog = ({
    types,
    membership,
    onCancelDialog,
    onCancelSubscriptions,
}: {
    types: SubscriptionType[];
    membership: membership_t;
    onCancelDialog: () => void;
    onCancelSubscriptions: () => void;
}) => {
    const { t } = useTranslation("special_products");
    const { t: tCommon } = useTranslation("common");
    const { t: tMember } = useTranslation("member_page");

    const typeStr = types
        .map((ty) => t(`${ty}_subscription.summary`))
        .join(" " + tCommon("and") + " ");
    return (
        <>
            <div class="uk-modal-header">
                <h2>{tMember("subscriptions.cancel.title")}</h2>
            </div>
            <div class="uk-modal-body">
                <p>
                    {tMember("subscriptions.cancel.no_longer_renewed", {
                        type: typeStr,
                    })}
                </p>
                {types.includes("membership") &&
                    membership.membership_active && (
                        <p>
                            {tMember(
                                "subscriptions.cancel.membership.valid_until",
                                { date: formatDate(membership.membership_end) },
                            )}
                        </p>
                    )}
                {types.includes("labaccess") && membership.labaccess_active && (
                    <p>
                        {tMember("subscriptions.cancel.labaccess.valid_until", {
                            date: formatDate(membership.labaccess_end),
                        })}
                    </p>
                )}
            </div>
            <div class="uk-modal-footer uk-text-right">
                <button class="uk-button" onClick={onCancelDialog}>
                    {tMember(
                        "subscriptions.cancel.cancel_cancelling_subscription",
                    )}
                </button>{" "}
                <button
                    class="uk-button uk-button-primary"
                    onClick={async () => {
                        try {
                            await ajax(
                                "DELETE",
                                `${window.apiBasePath}/webshop/member/current/subscriptions`,
                                { subscriptions: types },
                            );
                        } catch (e) {
                            show_error("Failed to cancel subscription", e);
                            onCancelDialog();
                            return;
                        }
                        onCancelSubscriptions();
                    }}
                >
                    Cancel subscription
                </button>
            </div>
        </>
    );
};

export async function getCurrentSubscriptions(): Promise<SubscriptionInfo[]> {
    return (
        await ajax(
            "GET",
            `${window.apiBasePath}/webshop/member/current/subscriptions`,
        )
    ).data as SubscriptionInfo[];
}

export async function cancelSubscription(
    type: SubscriptionType,
    membership: membership_t,
    subscriptions: SubscriptionInfo[],
) {
    const types = [type];
    if (
        type === "membership" &&
        subscriptions.some((s) => s.type === "labaccess")
    ) {
        // If we cancel membership, we must also cancel labaccess
        types.push("labaccess");
    }

    const p = UIkit.modal.dialog("", { bgClose: false });
    const promise = new Promise((resolve, reject) => {
        render(
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
            />,
            p.panel,
        );
        p.panel.parentElement!.addEventListener("hide", reject);
    });

    await promise;
}

export async function activateSubscription(
    type: SubscriptionType,
    member: member_t,
    membership: membership_t,
    subscriptions: SubscriptionInfo[],
    t: Translator<"member_page">,
) {
    if (subscriptions.some((s) => s.type === type)) {
        throw new Error("Member already has this subscription");
    }

    const productData = await LoadProductData();
    let subscription_product = FindWellKnownProduct(
        productData.products,
        `${type}_subscription`,
    )!;
    if (subscription_product == null) {
        UIkit.modal.alert(
            `<h2>Could not find product for subscription ${type}</h2> Please contact the admin.`,
        );
        return;
    }
    let products = [subscription_product];
    if (
        type === "labaccess" &&
        !subscriptions.some((s) => s.type === "membership")
    ) {
        try {
            await UIkit.modal.alert(
                `<p>${t(
                    "subscriptions.makerspace_access_also_activates_base_subscription",
                )}</p>`,
            );
        } catch {
            return;
        }
        subscription_product = FindWellKnownProduct(
            productData.products,
            "membership_subscription",
        )!;
        if (subscription_product == null) {
            UIkit.modal.alert(
                `<h2>Could not find product for subscription ${type}</h2> Please contact the admin.`,
            );
            return;
        }
        products.push(subscription_product);
    }

    // Note: This is not the same as the subscriptions array. A member may have access even if they do not have an active subscription.
    const currentMemberships: SubscriptionType[] = [];
    if (membership.membership_active) currentMemberships.push("membership");
    if (membership.labaccess_active) currentMemberships.push("labaccess");

    const stripe = createStripeCardInput();

    const p = UIkit.modal.dialog("", { bgClose: false });
    const panel: HTMLDivElement = p.panel;
    const promise = new Promise((resolve, reject) => {
        render(
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
            />,
            p.panel,
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
    }
}
