import * as common from "./common";
import * as login from "./login";
import { UNAUTHORIZED, get_error } from "./common";
import { JSX } from "preact/jsx-runtime";
import { LoadCurrentMemberGroups, LoadCurrentMemberInfo, LoadCurrentMembershipInfo, date_t, member_t, membership_t } from "./member_common";
import { render } from "preact";
import { useEffect, useMemo, useState } from "preact/hooks";
import { show_phone_number_dialog } from "./change_phone";
import { SubscriptionInfo, SubscriptionInfos, SubscriptionType, activateSubscription, cancelSubscription, getCurrentSubscriptions } from "./subscriptions";
import { TranslationKey, useTranslation } from "./translations";
import { Sidebar } from "./sidebar";
import { FindWellKnownProduct, LoadProductData, Product, ProductData, RelevantProducts, extractRelevantProducts, initializeStripe } from "./payment_common";
import Cart, { useCart } from "./cart";
import { URL_MEMBERBOOTH } from "./urls";
declare var UIkit: any;



type fn_past_enddate = (enddate: date_t, remaining_days: number) => JSX.Element;
type fn_expired_yesterday = () => JSX.Element;
type fn_less_than_one_day_left = (remaining_hours: number) => JSX.Element;
type fn_less_than_two_weeks_left = (enddate: date_t, remaining_days: number) => JSX.Element;
type fn_lots_of_time_left = (enddate: date_t, remaining_days: number) => JSX.Element;
type fn_inactive = () => JSX.Element;

type template_strings_t = [fn_past_enddate, fn_expired_yesterday,
    fn_less_than_one_day_left, fn_less_than_two_weeks_left,
    fn_lots_of_time_left, fn_inactive];



type membership_info_t = {
    enddate: date_t,
    active: boolean
};

const calendarURL = "https://www.makerspace.se/kalendarium";
const webshop_url = `${window.location.origin}/shop`;


function get_random_pin_code(numbers: number): string {
    return Math.random().toString(10).substr(2, numbers);
}


function Info({ info, template_strings }: { info: membership_info_t, template_strings: template_strings_t }) {
    let text: JSX.Element;
    let icon: string;
    let color: string;

    const millisecondsPerHour = 1000 * 3600;
    const millisecondsPerDay = millisecondsPerHour * 24;

    const end = Date.parse(info.enddate) + millisecondsPerDay;

    if (info.active) {
        const remainingDays = Math.floor((end - Date.now()) / millisecondsPerDay);

        if (remainingDays < -1) {
            text = template_strings[0](info.enddate, -remainingDays);
            icon = "close";
            color = "member-key-color-inactive";
        } else if (remainingDays < 0) {
            text = template_strings[1]();
            icon = "close";
            color = "member-key-color-inactive";
        } else if (remainingDays < 1) {
            const remainingHours = Math.ceil((end - Date.now()) / millisecondsPerHour);
            text = template_strings[2](remainingHours);
            icon = "check";
            color = "member-key-color-warning";
        } else if (remainingDays < 14) {
            text = template_strings[3](info.enddate, remainingDays);
            icon = "check";
            color = "member-key-color-warning";
        } else {
            text = template_strings[4](info.enddate, remainingDays);
            icon = "check";
            color = "member-key-color-active";
        }
    } else {
        text = template_strings[5]();
        icon = "close";
        color = "member-key-color-inactive";
    }

    return (
        <div class="member-key-box">
            <div class={`uk-icon-small member-key-icon ${color}`} uk-icon={icon}>
            </div>
            <div class="member-key-status">
                {text}
            </div>
        </div>
    );
}

function Info2({ translation_key, info }: { translation_key: "labaccess" | "membership" | "special_labaccess", info: membership_info_t }) {
    const t = useTranslation();
    let text: JSX.Element | string;
    let icon: string;
    let color: string;

    const millisecondsPerHour = 1000 * 3600;
    const millisecondsPerDay = millisecondsPerHour * 24;

    const end = Date.parse(info.enddate) + millisecondsPerDay;

    if (info.active) {
        const remainingDays = Math.floor((end - Date.now()) / millisecondsPerDay);

        if (remainingDays < -1) {
            text = t(`member_page.old_membership_status.${translation_key}.inactive_recent`)(-remainingDays);
            icon = "close";
            color = "member-key-color-inactive";
        } else if (remainingDays < 0) {
            text = t(`member_page.old_membership_status.${translation_key}.inactive_yesterday`);
            icon = "close";
            color = "member-key-color-inactive";
        } else if (remainingDays < 1) {
            const remainingHours = Math.ceil((end - Date.now()) / millisecondsPerHour);
            text = t(`member_page.old_membership_status.${translation_key}.active_hours_remaining`)(remainingHours);
            icon = "check";
            color = "member-key-color-warning";
        } else if (remainingDays < 14) {
            text = t(`member_page.old_membership_status.${translation_key}.active_few_days_remaining`)(info.enddate, remainingDays);
            icon = "check";
            color = "member-key-color-warning";
        } else {
            text = t(`member_page.old_membership_status.${translation_key}.active_days_remaining`)(info.enddate, remainingDays);
            icon = "check";
            color = "member-key-color-active";
        }
    } else {
        text = t(`member_page.old_membership_status.${translation_key}.inactive`);
        icon = "close";
        color = "member-key-color-inactive";
    }

    return (
        <div class="member-key-box">
            <div class={`uk-icon-small member-key-icon ${color}`} uk-icon={icon}>
            </div>
            <div class="member-key-status">
                {text}
            </div>
        </div>
    );
}

function WarningItem({ children }: { children: preact.ComponentChildren }) {
    return <p><i class="member-text-warning" uk-icon="warning"></i> &nbsp; {children}</p>;
}

function SignedContractWarning({ member }: { member: member_t }) {
    return member.labaccess_agreement_at ? null : <WarningItem>Du måste delta på en <strong>medlemintroduktion</strong>. Du hittar dem i <a href={calendarURL}>kalendern</a>.</WarningItem>;
}


function NoMembershipWarning({ membership }: { membership: membership_t }) {
    return membership.membership_active ? null : <WarningItem>Du måste köpa <strong>föreningsmedlemskap</strong> i <a href={webshop_url}>webshoppen</a>.</WarningItem>;
}


function MissingPhoneNumber({ member }: { member: member_t }) {
    return member.phone ? null : <WarningItem>Du måste lägga in ditt <strong>telefonnummer</strong> i personuppgifterna nedan.</WarningItem>;
}


function PendingLabaccessInstructions({ can_sync_labaccess, pending_labaccess_days }: { can_sync_labaccess: boolean, pending_labaccess_days: number }) {
    if (!can_sync_labaccess && pending_labaccess_days) {
        return <>Du behöver åtgärda ovanstående fel innan din labbaccess kan synkas. När de är åtgärdade kommer den digitala nyckeln att förlängas med <strong>{pending_labaccess_days} dagar</strong> vid nästa nyckelsynkronisering.</>;
    } else if (can_sync_labaccess && pending_labaccess_days) {
        return <><strong>{pending_labaccess_days} dagar</strong> kommer läggas till vid nästa nyckelsynkronisering. Då kommer din access att förlängas.</>;
    }

    return <>Du behöver köpa labbmedlemskap i <a href={webshop_url}>webshoppen</a> för att förlänga ditt labbmedlemskap.</>;
}


function Help({ member, membership, pending_labaccess_days, onSendAccessyInvite }: { member: member_t, membership: membership_t, pending_labaccess_days: number, onSendAccessyInvite: () => void }) {
    const todo_bullets = [
        SignedContractWarning({ member }),
        NoMembershipWarning({ membership }),
        MissingPhoneNumber({ member }),
        // TODO: Accessy invite. Check if user is in accessy group.
    ].filter(x => x !== null);

    if (todo_bullets.length === 0) {
        return null;
    }

    const pending_labaccess_instruction = <PendingLabaccessInstructions can_sync_labaccess={!todo_bullets} pending_labaccess_days={pending_labaccess_days} />;

    const disabled = !member.phone || (!membership.labaccess_active && !membership.special_labaccess_active);
    const accessyInvite = <p><button disabled={disabled} class="uk-button uk-button-danger" onClick={e => {
        e.preventDefault();
        onSendAccessyInvite();
    }}>Skicka Accessy-inbjudan</button></p>;

    return <fieldset>
        <legend><i uk-icon="info"></i> Instruktioner för att bli labbmedlem</legend>
        {todo_bullets}
        {pending_labaccess_instruction}
        {accessyInvite}
    </fieldset>;
}


function get_pending_labaccess_days(pending_actions_json: any): number {
    let pendingLabaccessDays = 0;
    for (let pending of pending_actions_json.data) {
        if (pending.action.action === "add_labaccess_days") {
            pendingLabaccessDays += pending.action.value;
        }
    }
    return pendingLabaccessDays;
}

async function change_pin_code(member: member_t) {
    const pin_code = await UIkit.modal.prompt("Välj en pinkod", member.pin_code === null ? get_random_pin_code(4) : member.pin_code);
    if (pin_code === null)
        return;

    try {
        await common.ajax("POST", `${window.apiBasePath}/member/current/set_pin_code`, { pin_code: pin_code })
        await UIkit.modal.alert(`<h2>Pinkoden är nu bytt</h2>`);
        location.reload();
    } catch (e) {
        UIkit.modal.alert(`<h2>Kunde inte byta pinkod</h2><b class="uk-text-danger"">${get_error(e)}</b>`);
    }
}

async function change_phone_number(member: member_t, membership: membership_t) {
    switch (await show_phone_number_dialog(member.phone)) {
        case "ok":
            await UIkit.modal.alert(`<h2>Telefonnummret är nu bytt</h2>`);

            if (membership.labaccess_active || membership.special_labaccess_active) {
                // Send accessy invite to the new phone number
                await common.ajax("POST", `${window.apiBasePath}/webshop/member/current/accessy_invite`);
            }

            location.reload();
            break;
        case "cancel":
        case "no-change":
            break;
        case UNAUTHORIZED:
            login.redirect_to_member_page();
            break;
    }
}

async function send_accessy_invite() {
    try {
        await common.ajax("POST", `${window.apiBasePath}/webshop/member/current/accessy_invite`);
        UIkit.modal.alert(`<h2>Inbjudan skickad</h2>`);
    } catch (e) {
        UIkit.modal.alert(`<h2>Inbjudan misslyckades</h2><b class="uk-text-danger"">${get_error(e)}</b>`);
    }
}

function MembershipView({ member, membership, pendingLabaccessDays }: { member: member_t, membership: membership_t, pendingLabaccessDays: number }) {
    const labaccessStrings: template_strings_t = [
        (enddate: string, days: number) => <>Din <strong>labaccess</strong> är ogiltig sedan {days} dagar ({enddate}). <br />Your <strong>lab membership</strong> expired {days} day(s) ago ({enddate}).</>,
        () => <>Din <strong>labaccess</strong> gick ut igår. <br />Your <strong>lab membership</strong> expired yesterday.</>,
        (hours: number) => <>Din <strong>labaccess</strong> är giltig i mindre än {hours} timmar till. <br />Your <strong>lab membership</strong> is valid for {hours} more hours.</>,
        (enddate: string, days: number) => <>Din <strong>labaccess</strong> är giltig t.o.m. {enddate} (endast {days} dagar till). Kom ihåg att förnya den innan nästa fredag morgon. <br />Your <strong>lab membership</strong> is valid through {enddate} (only {days} day(s) left). Remember to extend your lab membership before next Friday morning.</>,
        (enddate: string, days: number) => <>Din <strong>labaccess</strong> är giltig t.o.m. {enddate} ({days} dagar till). <br />Your <strong>lab membership</strong> is valid through {enddate} (only {days} day(s) left).</>,
        () => <>Din <strong>labaccess</strong> är inaktiv. <br />Your <strong>lab membership</strong> is inactive.</>,
    ];

    const membershipStrings: template_strings_t = [
        (enddate: string, days: number) => <>Ditt <strong>föreningsmedlemsskap</strong> är ogiltigt sedan {days} dagar ({enddate}). <br />Your <strong>membership</strong> expired {days} day(s) ago ({enddate})</>,
        () => <>Ditt <strong>föreningsmedlemsskap</strong> gick ut igår. <br />Your <strong>membership</strong> expired yesterday.</>,
        (hours: number) => <>Ditt <strong>föreningsmedlemsskap</strong> går ut idag. <br />Your <strong>membership</strong> expires today.</>,
        (enddate: string, days: number) => <>Ditt <strong>föreningsmedlemsskap</strong> är giltigt t.o.m. {enddate} (endast {days} dagar till). <br />Your <strong>membership</strong> is valid through {enddate} (only {days} day(s) left).</>,
        (enddate: string, days: number) => <>Ditt <strong>föreningsmedlemsskap</strong> är giltigt t.o.m. {enddate} ({days} dagar till). <br />Your <strong>membership</strong> is valid through {enddate} (only {days} day(s) left).</>,
        () => <>Ditt <strong>föreningsmedlemsskap</strong> är inaktivt. <br />Your <strong>membership</strong> is inactive.</>,
    ];

    const specialLabaccessStrings: template_strings_t = [
        (enddate: string, days: number) => <></>,
        () => <></>,
        (hours: number) => <></>,
        (enddate: string, days: number) => <>Du har fått <strong>specialtillträde</strong> till föreningslokalerna t.o.m. {enddate} ({days} dagar till). <br />You have been given <strong>special access</strong> to the premises through {enddate} ({days} day(s) left).</>,
        (enddate: string, days: number) => <>Du har fått <strong>specialtillträde</strong> till föreningslokalerna t.o.m. {enddate} ({days} dagar till). <br />You have been given <strong>special access</strong> to the premises through {enddate} ({days} day(s) left).</>,
        () => <></>,
    ];

    return <fieldset class="data-uk-margin">
        <legend><i uk-icon="lock"></i> Medlemsskap</legend>
        <Info info={{ active: membership.membership_active, enddate: membership.membership_end }} template_strings={membershipStrings} />
        <Info info={{ active: membership.labaccess_active, enddate: membership.labaccess_end }} template_strings={labaccessStrings} />
        {membership.special_labaccess_active ? <Info info={{ active: membership.special_labaccess_active, enddate: membership.special_labaccess_end }} template_strings={specialLabaccessStrings} /> : null}
    </fieldset>;
}


function PersonalData({ member, onChangePinCode, onChangePhoneNumber }: { member: member_t, onChangePinCode: () => void, onChangePhoneNumber: () => void }) {
    const pin_warning = member.pin_code == null ? <label class="uk-form-label" style="color: red;">Du har inte satt någon PIN-kod ännu. Använd BYT-knappen för att sätta den. PIN-koden används för <a href={URL_MEMBERBOOTH}>memberbooth</a>.</label> : null;
    const [showPinCode, setShowPinCode] = useState(false);
    return (
        <fieldset>
            <legend><i uk-icon="user"></i> Personuppgifter</legend>
            <div>
                <label for='firstname' class="uk-form-label">Förnamn</label>
                <input name='firstname' class="uk-input readonly-input" value={member.firstname || ''} disabled />
            </div>
            <div>
                <label for='lastname' class="uk-form-label">Efternamn</label>
                <input name='lastname' class="uk-input readonly-input" value={member.lastname || ''} disabled />
            </div>
            <div>
                <label for='email' class="uk-form-label">E-post</label>
                <input name='email' class="uk-input readonly-input" value={member.email || ''} disabled />
            </div>
            <div>
                <label for='phone' class="uk-form-label">Telefonnummer</label>
                <span style="width: 100%; display: flex;">
                    <input name='phone' class="uk-input readonly-input" value={member.phone || ''} disabled />
                    <button class="uk-button uk-button-danger" onClick={e => {
                        e.preventDefault();
                        onChangePhoneNumber();
                    }} >Byt</button>
                </span>
            </div>
            <div>
                <label for='pin_code' class="uk-form-label">Pin code</label>
                <span style="width: 100%; display: flex;">
                    <input name='pin_code' type={showPinCode ? "text" : "password"} class="uk-input readonly-input" style="white-space: nowrap; font-family: monospace;" value={member.pin_code || ''} disabled />
                    <button class="uk-icon-button uk-margin-small-left uk-margin-small-right" uk-icon={showPinCode ? "eye" : "eye-slash"} onClick={e => {
                        setShowPinCode(!showPinCode);
                        e.preventDefault();
                    }}></button>
                    <button class="uk-button uk-button-danger" onClick={e => {
                        e.preventDefault();
                        onChangePinCode();
                    }}>Byt</button>
                </span>
                {pin_warning}
            </div>
        </fieldset>
    );
}


function Address({ member }: { member: member_t }) {
    return (
        <fieldset data-uk-margin>
            <legend><i uk-icon="home"></i> Adress</legend>
            <div>
                <label for='address_street' class="uk-form-label">Address</label>
                <input name='address_street' class="uk-input readonly-input" value={member.address_street || ''} disabled />
            </div>
            <div>
                <label for='address_extra' class="uk-form-label">Extra adressrad, t ex C/O</label>
                <input name='address_extra' class="uk-input readonly-input" value={member.address_extra || ''} disabled />
            </div>
            <div>
                <label for='address_zipcode' class="uk-form-label">Postnummer</label>
                <input name='address_zipcode' class="uk-input readonly-input" value={member.address_zipcode || ''} disabled />
            </div>
            <div>
                <label for='address_city' class="uk-form-label">Postort</label>
                <input name='address_city' class="uk-input readonly-input" value={member.address_city || ''} disabled />
            </div>
        </fieldset>
    );
}

function SubscriptionPayment({ sub, membership, subscriptions, member, type, productData }: { sub: SubscriptionInfo | null, membership: membership_t, subscriptions: SubscriptionInfo[], member: member_t, type: SubscriptionType, productData: ProductData }) {
    const product = FindWellKnownProduct(productData.products, `${type}_subscription`)!;
    const t = useTranslation();
    if (product.unit !== "mån" && product.unit !== "år" && product.unit !== "st") throw new Error(`Unexpected unit '${product.unit}' for ${product.name}. Expected one of år/mån/st`);

    return sub ?
        <div class="uk-button-group">
            <button class="uk-button" disabled>Auto renew: Active</button>
            <button class="uk-button uk-button-danger" onClick={e => {
                e.preventDefault();
                cancelSubscription(type, membership, subscriptions);
            }}>Cancel</button>
        </div>
        :
        <>
            <button class="uk-button uk-button-primary" onClick={e => {
                e.preventDefault();
                if (member.labaccess_agreement_at === null) {
                    UIkit.modal.alert(`<h2>Cannot start subscription</h2><p>You must attend a member introduction before you can start an auto-renewal subscription.</p><p>You can find them in the <a href="${calendarURL}">calendar</a>.</p>`);
                    return;
                }

                activateSubscription(type, member, membership, subscriptions);
            }}>Activate auto renewal: {product.price}/{t(`unit.${product.unit}.one`)}</button>
        </>;
}

function SubscriptionProduct({ product, cart, onChangeCart }: { product: Product, cart: Cart, onChangeCart: (cart: Cart) => void }) {
    const t = useTranslation();
    if (product.unit !== "mån" && product.unit !== "år" && product.unit !== "st") throw new Error(`Unexpected unit '${product.unit}' for ${product.name}. Expected one of år/mån/st`);

    return <button
        class="uk-button uk-button-primary"
        onClick={e => {
            e.preventDefault();
            cart.setItem(product.id, cart.getItemCount(product.id) + 1);
            onChangeCart(cart);
        }}
    >
        {t("member_page.subscriptions.add_to_cart")(product.smallest_multiple, t(`unit.${product.unit}.${product.smallest_multiple > 1 ? 'many' : 'one'}`), Number(product.price) * product.smallest_multiple)}
    </button>
}

function BaseMembership({ member, membership, subscriptions, relevantProducts, cart, onChangeCart, productData }: { member: member_t, membership: membership_t, subscriptions: SubscriptionInfo[], relevantProducts: RelevantProducts, cart: Cart, onChangeCart: (cart: Cart) => void, productData: ProductData }) {
    const t = useTranslation();
    const sub = subscriptions.find(sub => sub.type === "membership") || null;
    return <fieldset>
        <legend><i uk-icon="home"></i> Base Membership</legend>
        <Info2 info={{ active: membership.membership_active, enddate: membership.membership_end }} translation_key="membership" />
        <p>{t("member_page.subscriptions.descriptions.membership")}</p>
        <hr />
        <SubscriptionPayment type="membership" sub={sub} membership={membership} subscriptions={subscriptions} member={member} productData={productData} />
        <div class="uk-margin-small-top" />
        {sub && sub.upcoming_invoice && <p>{t("member_page.subscriptions.next_charge")(sub.upcoming_invoice.amount_due, sub.upcoming_invoice.payment_date)}</p>}
        {!sub && <SubscriptionProduct product={relevantProducts.baseMembershipProduct} cart={cart} onChangeCart={onChangeCart} />}
    </fieldset>
}

function MakerspaceAccess({ member, membership, subscriptions, relevantProducts, pending_labaccess_days, cart, onChangeCart, productData }: { member: member_t, membership: membership_t, pending_labaccess_days: number, subscriptions: SubscriptionInfo[], relevantProducts: RelevantProducts, cart: Cart, onChangeCart: (cart: Cart) => void, productData: ProductData }) {
    const t = useTranslation();
    const sub = subscriptions.find(sub => sub.type === "labaccess") || null;
    return <fieldset>
        <legend><i uk-icon="home"></i> Makerspace Access</legend>
        <Info2 info={{ active: membership.labaccess_active, enddate: membership.labaccess_end }} translation_key="labaccess" />
        {
            membership.special_labaccess_active && <Info2 info={{ active: membership.special_labaccess_active, enddate: membership.special_labaccess_end }} translation_key="special_labaccess" />
        }
        {pending_labaccess_days > 0 && <p>Your <strong>{pending_labaccess_days}</strong> days of makerspace access will start when you attend a member introduction.</p>}
        <p>{t("member_page.subscriptions.descriptions.labaccess")}</p>
        <hr />
        <SubscriptionPayment type="labaccess" sub={sub} membership={membership} subscriptions={subscriptions} member={member} productData={productData} />
        <div class="uk-margin-small-top" />
        {sub && sub.upcoming_invoice && <p>{t("member_page.subscriptions.next_charge")(sub.upcoming_invoice.amount_due, sub.upcoming_invoice.payment_date)}</p>}
        {!sub && <SubscriptionProduct product={relevantProducts.labaccessProduct} cart={cart} onChangeCart={onChangeCart} />}
    </fieldset>
}

function Billing() {
    const t = useTranslation();
    return <fieldset>
        <legend><i uk-icon="credit-card"></i> {t("member_page.billing.title")}</legend>
        <button className="uk-button" onClick={async e => {
            e.preventDefault();
            const url = (await common.ajax("GET", `${window.apiBasePath}/webshop/member/current/stripe_customer_portal`)).data;
            location.href = url;
        }}>{t("member_page.billing.manage")}</button>
    </fieldset>;
}

function useFetchRepeatedly<T>(fetcher: () => Promise<T>, callback: (t: T) => void) {
    useEffect(() => {
        let i = 0;
        let id: NodeJS.Timeout;
        const f = async () => {
            callback(await fetcher());
            i++;
            id = setTimeout(f, Math.min(60 * 60 * 1000, Math.pow(1.5, i) * 1000));
        };
        id = setTimeout(f, 1000);
        return () => clearInterval(id);
    }, []);
}

function MemberPage({ member, membership: initial_membership, pending_labaccess_days, productData, subscriptions, show_beta }: { member: member_t, membership: membership_t, pending_labaccess_days: number, subscriptions: SubscriptionInfo[], show_beta: boolean, productData: ProductData }) {
    const apiBasePath = window.apiBasePath;
    const [membership, setMembership] = useState(initial_membership);
    const relevantProducts = useMemo(() => extractRelevantProducts([...productData.id2item.values()]), [productData.id2item]);

    // Automatically refresh membership info.
    // This is particularly useful when the user has just bought a subscription,
    // but the invoice has not yet been paid.
    // In most cases it will get paid in a few seconds, and we want to show this to the user when it happens.
    useFetchRepeatedly(LoadCurrentMembershipInfo, setMembership);
    const t = useTranslation();
    const { cart, setCart } = useCart();

    return (
        <>
            <Sidebar cart={cart.items.length > 0 ? { cart, productData } : null} />
            <div id="content">
                <form class="uk-form uk-form-stacked uk-margin-bottom">
                    <h2>{t("member_page.member")} {member.member_number}: {member.firstname} {member.lastname}</h2>
                    {show_beta ? <>
                        <Help member={member} membership={membership} pending_labaccess_days={pending_labaccess_days} onSendAccessyInvite={send_accessy_invite} />
                        <BaseMembership member={member} membership={membership} subscriptions={subscriptions} relevantProducts={relevantProducts} cart={cart} onChangeCart={setCart} productData={productData} />
                        <MakerspaceAccess member={member} membership={membership} subscriptions={subscriptions} relevantProducts={relevantProducts} cart={cart} onChangeCart={setCart} productData={productData} pending_labaccess_days={pending_labaccess_days} />
                        <Billing />
                    </>
                        : <>
                            <MembershipView member={member} membership={membership} pendingLabaccessDays={pending_labaccess_days} />
                            <Help member={member} membership={membership} pending_labaccess_days={pending_labaccess_days} onSendAccessyInvite={send_accessy_invite} />
                        </>
                    }
                    <PersonalData
                        member={member}
                        onChangePinCode={() => void change_pin_code(member)}
                        onChangePhoneNumber={() => void change_phone_number(member, membership)}
                    />
                    <Address member={member} />
                </form>
            </div>
        </>
    )
}

common.documentLoaded().then(() => {
    common.addSidebarListeners();
    initializeStripe();

    const apiBasePath = window.apiBasePath;
    const root = document.querySelector("#root") as HTMLElement;

    const future1 = LoadCurrentMemberInfo();
    const membership = LoadCurrentMembershipInfo();
    const future3 = common.ajax("GET", apiBasePath + "/webshop/member/current/pending_actions", null);
    const subscriptions = getCurrentSubscriptions().then(s => s.filter(sub => sub.active));
    const groups = LoadCurrentMemberGroups();
    const productData = LoadProductData();


    Promise.all([future1, membership, future3, subscriptions, groups, productData]).then(([member, membership, pending_actions_json, subscriptions, groups, productData]) => {
        const pending_labaccess_days = get_pending_labaccess_days(pending_actions_json);
        const in_beta_group = groups.some(g => g.name === "betatesters");
        if (root != null) {
            render(
                <MemberPage member={member} membership={membership} pending_labaccess_days={pending_labaccess_days} subscriptions={subscriptions} show_beta={in_beta_group} productData={productData} />,
                root
            );
        }
    }).catch(e => {
        // Probably Unauthorized, redirect to login page.
        if (e.status === UNAUTHORIZED) {
            // Render login
            login.render_login(root, null, null);
        } else {
            console.log(e);
            UIkit.modal.alert("<h2>Failed to load member info</h2>");
        }
    });
});
