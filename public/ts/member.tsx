import * as common from "./common";
import * as login from "./login";
import { UNAUTHORIZED, get_error } from "./common";
import { JSX } from "preact/jsx-runtime";
import { LoadCurrentMemberInfo, date_t, member_t } from "./member_common";
import { render } from "preact";
import { useState } from "preact/hooks";
import { showPhoneNumberDialog } from "./change_phone";
import { Sidebar } from "./sidebar";
import { LoadProductData, ProductData } from "./payment_common";
import { useCart } from "./cart";
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


type membership_t = {
    membership_active: boolean,
    membership_end: date_t,
    labaccess_active: boolean,
    labaccess_end: date_t,
    special_labaccess_active: boolean,
    special_labaccess_end: date_t
};


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
        <SignedContractWarning member={member} />,
        <NoMembershipWarning membership={membership} />,
        <MissingPhoneNumber member={member} />,
    ];

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
    const pin_warning = member.pin_code == null ? <label class="uk-form-label" style="color: red;">Du har inte satt någon PIN-kod ännu. Använd BYT-knappen för att sätta den.</label> : null;
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

function MemberPage({ member, membership, pending_labaccess_days, productData }: { member: member_t, membership: membership_t, pending_labaccess_days: number, productData: ProductData }) {
    const apiBasePath = window.apiBasePath;
    const { cart } = useCart();

    return (
        <>
            <Sidebar cart={cart.items.length > 0 ? { cart, productData } : null} />
            <div id="content">
                <form class="uk-form uk-form-stacked uk-margin-bottom">
                    <h2>Medlem {member.member_number}: {member.firstname} {member.lastname}</h2>
                    <MembershipView member={member} membership={membership} pendingLabaccessDays={pending_labaccess_days} />
                    <Help member={member} membership={membership} pending_labaccess_days={pending_labaccess_days} onSendAccessyInvite={async () => {
                        try {
                            await common.ajax("POST", `${window.apiBasePath}/webshop/member/current/accessy_invite`);
                            UIkit.modal.alert(`<h2>Inbjudan skickad</h2>`);
                        } catch (e) {
                            UIkit.modal.alert(`<h2>Inbjudan misslyckades</h2><b class="uk-text-danger"">${get_error(e)}</b>`);
                        }
                    }} />
                    <PersonalData member={member} onChangePinCode={async () => {
                        const pin_code = await UIkit.modal.prompt("Välj en pinkod", member.pin_code === null ? get_random_pin_code(4) : member.pin_code);
                        if (pin_code === null)
                            return;

                        try {
                            await common.ajax("POST", `${apiBasePath}/member/current/set_pin_code`, { pin_code: pin_code })
                            await UIkit.modal.alert(`<h2>Pinkoden är nu bytt</h2>`);
                            location.reload();
                        } catch (e) {
                            UIkit.modal.alert(`<h2>Kunde inte byta pinkod</h2><b class="uk-text-danger"">${get_error(e)}</b>`);
                        }
                    }}
                        onChangePhoneNumber={async () => {
                            switch (await showPhoneNumberDialog(member.phone)) {
                                case "ok":
                                    await UIkit.modal.alert(`<h2>Telefonnummret är nu bytt</h2>`)
                                    location.reload();
                                    break;
                                case "cancel":
                                    break;
                                case UNAUTHORIZED:
                                    login.redirect_to_member_page();
                                    break;
                            }
                        }} />
                    <Address member={member} />
                </form>
            </div>
        </>
    )
}

common.documentLoaded().then(() => {
    common.addSidebarListeners();

    const apiBasePath = window.apiBasePath;
    const root = document.querySelector("#root") as HTMLElement;

    const future1 = LoadCurrentMemberInfo();
    const future2 = common.ajax("GET", apiBasePath + "/member/current/membership", null);
    const future3 = common.ajax("GET", apiBasePath + "/webshop/member/current/pending_actions", null);
    const productData = LoadProductData();

    Promise.all([future1, future2, future3, productData]).then(([member, membership_json, pending_actions_json, productData]) => {
        const membership: membership_t = membership_json.data;
        const pending_labaccess_days = get_pending_labaccess_days(pending_actions_json);
        if (root != null) {
            render(
                <MemberPage member={member} membership={membership} pending_labaccess_days={pending_labaccess_days} productData={productData} />,
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
