import * as common from "./common"
import * as login from "./login"
declare var UIkit: any;

document.addEventListener('DOMContentLoaded', () => {
    const apiBasePath = window.apiBasePath;

    function renderInfo(info: any, templateStrings: any) {
        let text = "";
        let icon = "";
        let color = "";

        const millisecondsPerHour = 1000 * 3600;
        const millisecondsPerDay = millisecondsPerHour * 24;

        const end = Date.parse(info.enddate) + millisecondsPerDay;
        
        if (info.active) {
            const remainingDays = Math.floor((end - Date.now()) / millisecondsPerDay);

            if (remainingDays < -1) {
                text = templateStrings[0](info.enddate, -remainingDays);
                icon = "close";
                color = "member-key-color-inactive";
            } else if (remainingDays < 0) {
                text = templateStrings[1]();
                icon = "close";
                color = "member-key-color-inactive";
            } else if (remainingDays < 1) {
                const remainingHours = Math.ceil((end - Date.now()) / millisecondsPerHour);
                text = templateStrings[2](remainingHours);
                icon = "check";
                color = "member-key-color-warning";
            } else if (remainingDays < 14) {
                text = templateStrings[3](info.enddate, remainingDays);
                icon = "check";
                color = "member-key-color-warning";
            } else {
                text = templateStrings[4](info.enddate, remainingDays);
                icon = "check";
                color = "member-key-color-active";
            }
        } else {
            text = templateStrings[5]();
            icon = "close";
            color = "member-key-color-inactive";
        }

        return `<div class="member-key-box">
                    <div class="uk-icon-small member-key-icon ${color}" uk-icon="${icon}">
                    </div>
                    <div class="member-key-status">
                        ${text}
                    </div>
                </div>`;
    }

    function render_key_view(membership: any, pending_actions_json: any) {
        const info_labaccess = {
            active:  membership.has_labaccess,
            enddate: membership.labaccess_end,
        };
        const info_membership = {
            active:  membership.has_membership,
            enddate: membership.membership_end,
        };

        let pendingLabaccessDays = 0;
        for (let pending of pending_actions_json.data) {
            if (pending.action.name === "add_labaccess_days") {
                pendingLabaccessDays += pending.pending_action.value;
            }
        }

        const labaccessStrings = [
            (enddate: string, days: number) => `Din labaccess är ogiltig sedan ${days} dagar (${enddate}).`,
            () => `Din labaccess gick ut igår.`,
            (hours: number) => `Din labaccess är giltig i mindre än ${hours} timmar till.`,
            (enddate: string, days: number) => `Din labaccess är giltig t.o.m. ${enddate} (endast ${days} dagar till). Kom ihåg att förnya den innan nästa nyckelutlämning.`,
            (enddate: string, days: number) => `Din labaccess är giltig t.o.m. ${enddate} (${days} dagar till).`,
            () => `Din labaccess är inaktiv.`,
        ];

        const membershipStrings = [
            (enddate: string, days: number) => `Ditt föreningsmedlemsskap är ogiltigt sedan ${days} dagar (${enddate}).`,
            () => `Ditt föreningsmedlemsskap gick ut igår.`,
            (hours: number) => `Ditt föreningsmedlemsskap går ut idag.`,
            (enddate: string, days: number) => `Ditt föreningsmedlemsskap är giltigt t.o.m. ${enddate} (endast ${days} dagar till).`,
            (enddate: string, days: number) => `Ditt föreningsmedlemsskap är giltigt t.o.m. ${enddate} (${days} dagar till).`,
            () => `Ditt föreningsmedlemsskap är inaktivt.`,
        ];

        let calendarURL = "https://www.makerspace.se/kalendarium";
        let pendingAccess = "";
        if (pendingLabaccessDays > 0) {
            pendingAccess = `<p>Du har ${pendingLabaccessDays} dagar som kommer att läggas till på din labaccess vid nästa <a href=${calendarURL}>nyckelutlämning</a>.</p>`;
        } else {
            pendingAccess = `<p>Om du köper ny labaccess i webshoppen så kommer den aktiveras vid nästa <a href=${calendarURL}>nyckelutlämning</a>.</p>`;
        }

        return `
            <fieldset class="data-uk-margin">
                <legend><i uk-icon="lock"></i> Medlemsskap</legend>
                ${renderInfo(info_membership, membershipStrings)}
                ${renderInfo(info_labaccess, labaccessStrings)}
                ${pendingAccess}
            </fieldset>`;
    }

    const root = <HTMLElement>document.querySelector("#single-page-content");

    const future1 = common.ajax("GET", apiBasePath + "/member/current", null);
    const future2 = common.ajax("GET", apiBasePath + "/member/current/membership", null);
    const future3 = common.ajax("GET", apiBasePath + "/webshop/member/current/pending_actions", null);

    Promise.all([future1, future2, future3]).then(([member_json, membership_json, pending_actions_json]) => {
        const member = member_json.data;
        const membership = membership_json.data;
        root.innerHTML = `
            <form class="product-edit-form uk-form uk-form-stacked uk-margin-bottom">
                <h2>Medlem ${member.member_number}: ${member.firstname} ${member.lastname}</h2>
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
                        <input name='phone'           class="uk-input readonly-input" value="${member.phone || ''}" disabled />
                    </div>
                </fieldset>
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

                ${render_key_view(membership, pending_actions_json)}

                <fieldset>
                    <legend><i uk-icon="cart"></i> Webshop</legend>
                    <a class="uk-button uk-button-default uk-margin-top" href="/shop/member/history">Visa köphistorik</a>
                    <a class="uk-button uk-button-default uk-margin-top uk-margin-left" href="/shop/">Gå till webshoppen</a>
                </fieldset>

                <div class="uk-form-row">
                    <button type="button" id="logout" class="uk-button uk-button-secondary uk-margin-left"><span uk-icon="sign-out"></span> Logga ut</button>
                </div>
            </form>`;

        root.querySelector("#logout").addEventListener("click", (e) => {
            e.preventDefault();
            login.logout();
        });
    }).catch(e => {
        // Probably Unauthorized, redirect to login page.
        if (e.message == "Unauthorized") {
            // Render login
            login.render_login(root, null, null);
        } else {
            UIkit.modal.alert("<h2>Failed to load member info</h2>");
        }
    });
});
