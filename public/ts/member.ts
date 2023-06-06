import * as common from "./common";
import * as login from "./login";
import { UNAUTHORIZED } from "./common";
declare var UIkit: any;


type date_t = string;


type fn_past_enddate = (enddate: date_t, remaining_days: number) => string;
type fn_expired_yesterday = () => string;
type fn_less_than_one_day_left = (remaining_hours: number) => string;
type fn_less_than_two_weeks_left = (enddate: date_t, remaining_days: number) => string;
type fn_lots_of_time_left = (enddate: date_t, remaining_days: number) => string;
type fn_inactive = () => string;

type template_strings_t = [fn_past_enddate, fn_expired_yesterday,
    fn_less_than_one_day_left, fn_less_than_two_weeks_left,
    fn_lots_of_time_left, fn_inactive];


type member_t = {
    address_street: string,
    address_extra: string,
    address_zipcode: string,
    address_city: string,
    email: string,
    member_number: number,
    firstname: string,
    lastname: string,
    phone: string,
    pin_code: string,
    labaccess_agreement_at: date_t
};


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


const id_pin_code_input = "pin-code-input";
const id_toggle_show_pin_code = "toggle-show-pin-code";
const id_change_pin_code = "change-pin-code";
const id_accessy_invite_button = "accessy-invite-button";

const calendarURL = "https://www.makerspace.se/kalendarium";
const webshop_url = `${window.location.origin}/shop`;


function get_random_pin_code(numbers: number): string {
    return Math.random().toString(10).substr(2, numbers);
}


function render_info(info: membership_info_t, template_strings: template_strings_t) {
    let text = "";
    let icon = "";
    let color = "";

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

    return `
        <div class="member-key-box">
            <div class="uk-icon-small member-key-icon ${color}" uk-icon="${icon}">
            </div>
            <div class="member-key-status">
                ${text}
            </div>
        </div>
    `;
}


function render_signed_contract_warning(member: member_t): string {
    if (member.labaccess_agreement_at)
        return "";

    return `Du måste delta på en <strong>medlemintroduktion</strong> för att kunna bli labbmedlem. Du hittar dem i <a href="${calendarURL}">kalendern</a>.`;
}


function render_no_labaccess_warning(membership: membership_t): string {
    if (membership.labaccess_active)
        return "";

    return `Du måste köpa <strong>labbaccess</strong> i <a href="${webshop_url}">webshoppen</a> för att bli labbmedlem.`;
}


function render_no_membership_warning(membership: membership_t): string {
    if (membership.membership_active)
        return "";

    return `Du måste köpa <strong>föreningsmedlemskap</strong> i <a href="${webshop_url}">webshoppen</a> för att bli labbmedlem.`;
}


function render_missing_phone_number(member: member_t): string {
    if (member.phone)
        return "";

    return "Du måste lägga in ditt <strong>telefonnummer</strong> nedan för att bli labbmedlem.";
}


function render_pending_labaccess_instructions(can_sync_labaccess: boolean, pending_labaccess_days: number): string {
    if (!can_sync_labaccess && pending_labaccess_days) {
        return `Du behöver åtgärda ovanstående fel innan din labbaccess kan synkas. När de är åtgärdade kommer den digitala nyckeln att förlängas med <strong>${pending_labaccess_days} dagar</strong> vid nästa nyckelsynkronisering.`;
    } else if (can_sync_labaccess && pending_labaccess_days) {
        return `<strong>${pending_labaccess_days} dagar</strong> kommer läggas till vid nästa nyckelsynk. Då kommer din access att förlängas.`;
    }

    return `För att bli labbmedlem så behöver du köpa labbmedlemskap i <a href="${webshop_url}">webshoppen</a>.`;
}


function render_help(member: member_t, membership: membership_t, pending_labaccess_days: number) {
    const todo_bullets = [
        render_signed_contract_warning(member),
        render_no_labaccess_warning(membership),
        render_no_membership_warning(membership),
        render_missing_phone_number(member)
    ].map((todo_string: string) => {
        if (!todo_string)
            return "";

        return `<p><i class="member-text-warning" uk-icon="warning"></i> &nbsp; ${todo_string}</p>`
    }).join("\n");

    const pending_labaccess_instruction = render_pending_labaccess_instructions(
        !todo_bullets, pending_labaccess_days
    );

    return `
        <fieldset>
            <legend><i uk-icon="info"></i> Instruktioner för att bli labbmedlem</legend>
            ${todo_bullets}
            ${pending_labaccess_instruction}
        </fieldset>
    `;
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


function render_membership_view(member: member_t, membership: membership_t, pendingLabaccessDays: number) {
    const labaccessStrings: template_strings_t = [
        (enddate: string, days: number) => `Din <strong>labaccess</strong> är ogiltig sedan ${days} dagar (${enddate}). <br>Your <strong>lab membership</strong> expired ${days} day(s) ago (${enddate}).`,
        () => `Din <strong>labaccess</strong> gick ut igår. <br>Your <strong>lab membership</strong> expired yesterday.`,
        (hours: number) => `Din <strong>labaccess</strong> är giltig i mindre än ${hours} timmar till. <br>Your <strong>lab membership</strong> is valid for ${hours} more hours.`,
        (enddate: string, days: number) => `Din <strong>labaccess</strong> är giltig t.o.m. ${enddate} (endast ${days} dagar till). Kom ihåg att förnya den innan nästa nyckelutlämning. <br>Your <strong>lab membership</strong> is valid through ${enddate} (only ${days} day(s) left). Remember to extend your lab membership before the next nyckelutlämning.`,
        (enddate: string, days: number) => `Din <strong>labaccess</strong> är giltig t.o.m. ${enddate} (${days} dagar till). <br>Your <strong>lab membership</strong> is valid through ${enddate} (only ${days} day(s) left).`,
        () => `Din <strong>labaccess</strong> är inaktiv. <br>Your <strong>lab membership</strong> is inactive.`,
    ];

    const membershipStrings: template_strings_t = [
        (enddate: string, days: number) => `Ditt <strong>föreningsmedlemsskap</strong> är ogiltigt sedan ${days} dagar (${enddate}). <br>Your <strong>membership</strong> expired ${days} day(s) ago (${enddate})`,
        () => `Ditt <strong>föreningsmedlemsskap</strong> gick ut igår. <br>Your <strong>membership</strong> expired yesterday.`,
        (hours: number) => `Ditt <strong>föreningsmedlemsskap</strong> går ut idag. <br>Your <strong>membership</strong> expires today.`,
        (enddate: string, days: number) => `Ditt <strong>föreningsmedlemsskap</strong> är giltigt t.o.m. ${enddate} (endast ${days} dagar till). <br>Your <strong>membership</strong> is valid through ${enddate} (only ${days} day(s) left).`,
        (enddate: string, days: number) => `Ditt <strong>föreningsmedlemsskap</strong> är giltigt t.o.m. ${enddate} (${days} dagar till). <br>Your <strong>membership</strong> is valid through ${enddate} (only ${days} day(s) left).`,
        () => `Ditt <strong>föreningsmedlemsskap</strong> är inaktivt. <br>Your <strong>membership</strong> is inactive.`,
    ];

    const specialLabaccessStrings: template_strings_t = [
        (enddate: string, days: number) => ``,
        () => ``,
        (hours: number) => ``,
        (enddate: string, days: number) => `Du har fått <strong>specialtillträde</strong> till föreningslokalerna t.o.m. ${enddate} (${days} dagar till). <br>You have been given <strong>special access</strong> to the premises through ${enddate} (${days} day(s) left).`,
        (enddate: string, days: number) => `Du har fått <strong>specialtillträde</strong> till föreningslokalerna t.o.m. ${enddate} (${days} dagar till). <br>You have been given <strong>special access</strong> to the premises through ${enddate} (${days} day(s) left).`,
        () => ``,
    ];

    const disabled = (!member.phone || (!membership.labaccess_active && !membership.special_labaccess_active)) ? "disabled" : ""
    let explanation = "";
    if (!member.phone) {
        explanation = "Telefonnummer saknas, fyll i med knappen ovan."
    } else if (!membership.labaccess_active && !membership.special_labaccess_active) {
        if (pendingLabaccessDays === 0) {
            explanation = "Ingen labaccess aktiv, köp mer och vänta på synk (notifieras via mejl)." // TODO :( :( seriously? vänta i en vecka?
        } else {
            explanation = "Ingen labaccess aktiv, den blir aktiv vid nästa synk (notifieras via mejl)." // TODO :( :( seriously? vänta i en vecka?
        }
    }

    const accessyInvite = `<p><button id="${id_accessy_invite_button}" ${disabled} class="uk-button uk-button-danger" onclick="">Skicka Accessy-inbjudan</button></button> ${explanation}</p>`

    return `
        <fieldset class="data-uk-margin">
            <legend><i uk-icon="lock"></i> Medlemsskap</legend>
            ${render_info({ active: membership.membership_active, enddate: membership.membership_end }, membershipStrings)}
            ${render_info({ active: membership.labaccess_active, enddate: membership.labaccess_end }, labaccessStrings)}
            ${membership.special_labaccess_active ? render_info({ active: membership.special_labaccess_active, enddate: membership.special_labaccess_end }, specialLabaccessStrings) : ``}
            ${accessyInvite}
        </fieldset>`;
}


function render_personal_data(member: member_t) {
    const pin_warning = member.pin_code == null ? `<label class="uk-form-label" style="color: red;">Du har inte satt någon PIN-kod ännu. Använd BYT-knappen för att sätta den.</label>` : "";
    return `
        <fieldset>
            <legend><i uk-icon="user"></i> Personuppgifter</legend>
            <div>
                <label  for='firstname'       class="uk-form-label">Förnamn</label>
                <input name='firstname'       class="uk-input readonly-input" value="${member.firstname || ''}" disabled />
            </div>
            <div>
                <label  for='lastname'        class="uk-form-label">Efternamn</label>
                <input name='lastname'        class="uk-input readonly-input" value="${member.lastname || ''}" disabled />
            </div>
            <div>
                <label  for='email'           class="uk-form-label">E-post</label>
                <input name='email'           class="uk-input readonly-input" value="${member.email || ''}" disabled />
            </div>
            <div>
                <label  for='phone'           class="uk-form-label">Telefonnummer</label>
                <span style="width: 100%; display: flex;">
                    <input name='phone'           class="uk-input readonly-input" value="${member.phone || ''}" disabled />
                    <a href="/member/change_phone" class="uk-button uk-button-danger" >Byt</a>
                </span>
            </div>
            <div>
                <label  for='pin_code'        class="uk-form-label">Pin code</label>
                <span style="width: 100%; display: flex;">
                    <input name='pin_code' type="password" class="uk-input readonly-input" style="white-space: nowrap; font-family: monospace;" value="${member.pin_code || ''}" disabled id="${id_pin_code_input}"/>
                    <button class="uk-icon-button uk-margin-small-left uk-margin-small-right" uk-icon="more" id="${id_toggle_show_pin_code}"></button>
                    <button class="uk-button uk-button-danger" id="${id_change_pin_code}">Byt</button>
                </span>
                ${pin_warning}
            </div>
        </fieldset>
    `;
}


function render_address(member: member_t) {
    return `
        <fieldset data-uk-margin>
            <legend><i uk-icon="home"></i> Adress</legend>
            <div>
                <label  for='address_street'  class="uk-form-label">Address</label>
                <input name='address_street'  class="uk-input readonly-input" value="${member.address_street || ''}" disabled />
            </div>
            <div>
                <label  for='address_extra'   class="uk-form-label">Extra adressrad, t ex C/O</label>
                <input name='address_extra'   class="uk-input readonly-input" value="${member.address_extra || ''}" disabled />
            </div>
            <div>
                <label  for='address_zipcode' class="uk-form-label">Postnummer</label>
                <input name='address_zipcode' class="uk-input readonly-input" value="${member.address_zipcode || ''}" disabled />
            </div>
            <div>
                <label  for='address_city'    class="uk-form-label">Postort</label>
                <input name='address_city'    class="uk-input readonly-input" value="${member.address_city || ''}" disabled />
            </div>
        </fieldset>
    `;
}


function attach_callbacks(member: member_t) {
    const apiBasePath = window.apiBasePath;
    document.getElementById(id_accessy_invite_button)!.onclick = (e) => {
        e.preventDefault();
        common.ajax("POST", `${window.apiBasePath}/webshop/member/current/accessy_invite`)
            .then(() => UIkit.modal.alert(`<h2>Inbjudan skickad</h2>`))
            .catch((e) => {
                UIkit.modal.alert(`<h2>Inbjudan misslyckades</h2><b class="uk-text-danger"">${e.message}</b>`);
            });
        return false;
    };

    let pin_code_hidden = true;
    document.getElementById(id_toggle_show_pin_code)!.onclick = (e) => {
        e.preventDefault();
        pin_code_hidden = ! pin_code_hidden;
        const attr_value = pin_code_hidden ? "password" : "text";
        document.getElementById(id_pin_code_input)?.setAttribute("type", attr_value);
    };

    document.getElementById(id_change_pin_code)!.onclick = (e) => {
        e.preventDefault();
        UIkit.modal.prompt("Välj en pinkod", member.pin_code === null ? get_random_pin_code(4) : member.pin_code).then((pin_code: string) => {
            if (pin_code === null)
                return;

            common.ajax("POST", `${apiBasePath}/member/current/set_pin_code`, {pin_code: pin_code})
                .then(() => UIkit.modal.alert(`<h2>Pinkod är nu bytt</h2>`).then(() => location.reload()))
                .catch((e) => {
                    UIkit.modal.alert(`<h2>Kunde inte byta pinkod</h2><b class="uk-text-danger"">${e.message}</b>`);
                });
        }, () => {});
    };
}


common.documentLoaded().then(() => {
    common.addSidebarListeners();

    const apiBasePath = window.apiBasePath;
    const root = <HTMLElement>document.querySelector("#content");

    const future1 = common.ajax("GET", apiBasePath + "/member/current", null);
    const future2 = common.ajax("GET", apiBasePath + "/member/current/membership", null);
    const future3 = common.ajax("GET", apiBasePath + "/webshop/member/current/pending_actions", null);

    Promise.all([future1, future2, future3]).then(([member_json, membership_json, pending_actions_json]) => {
        const member: member_t = member_json.data;
        const membership: membership_t = membership_json.data;
        const pending_labaccess_days = get_pending_labaccess_days(pending_actions_json);
        root.innerHTML = `
            <form class="uk-form uk-form-stacked uk-margin-bottom" xmlns="http://www.w3.org/1999/html">
                <h2>Medlem ${member.member_number}: ${member.firstname} ${member.lastname}</h2>
                ${render_membership_view(member, membership, pending_labaccess_days)}
                ${render_help(member, membership, pending_labaccess_days)}
                ${render_personal_data(member)}
                ${render_address(member)}
            </form>`;

        attach_callbacks(member);
    }).catch(e => {
        // Probably Unauthorized, redirect to login page.
        if (e.status === UNAUTHORIZED) {
            // Render login
            login.render_login(root, null, null);
        } else {
            UIkit.modal.alert("<h2>Failed to load member info</h2>");
        }
    });
});
