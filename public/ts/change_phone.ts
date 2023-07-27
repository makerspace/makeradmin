import * as common from "./common"
import { UNAUTHORIZED } from "./common";

declare var UIkit: any;

export async function showPhoneNumberDialog(current_number: string): Promise<"ok" | "cancel" | typeof UNAUTHORIZED> {
    let new_number: string | null = await UIkit.modal.prompt("Nytt telefonnummer", current_number);
    if (new_number === null) {
        return "cancel";
    }

    try {
        const {data} = await common.ajax("POST", `${window.apiBasePath}/member/current/change_phone_request`, {phone: new_number.trim()});
    } catch (error: any) {
        if (error.status === UNAUTHORIZED) {
            return UNAUTHORIZED;
        } else {
            await common.show_error("Kunde inte byta telefonnummer", error)
            return "cancel";
        }
    }

    while(true) {
        let validation_code: string | null = await UIkit.modal.prompt("Valideringskod: ", "");
        if (validation_code === null) {
            return "cancel";
        }

        if (isNaN(parseInt(validation_code))) {
            await UIkit.modal.alert("<h2>Ogiltig kod. Försök igen.</h2>");
        } else {
            try {
                await common.ajax("POST", `${window.apiBasePath}/member/current/change_phone_validate`, {validation_code});
                break;
            } catch (error: any) {
                if (error.status === UNAUTHORIZED) {
                    return UNAUTHORIZED;
                } else {
                    await common.show_error("Felaktig kod. Försök igen.", error);
                }
            }
        }
    }

    return "ok";
}
