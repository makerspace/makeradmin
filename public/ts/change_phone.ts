import * as common from "./common"
import { UNAUTHORIZED } from "./common";
import { Translator } from "./translations";

declare var UIkit: any;

export async function show_phone_number_dialog(member_id: number | null, prompt: () => Promise<string | null>, validate_prompt: () => Promise<string | null>, t: Translator): Promise<"ok" | "cancel" | typeof UNAUTHORIZED> {
    let new_number: string | null = await prompt();
    if (new_number === null) {
        return "cancel";
    }

    let change_id: number;
    try {
        change_id = (await common.ajax("POST", `${window.apiBasePath}/member/send_phone_number_validation_code`, { member_id, phone: new_number.trim() })).data;
        console.assert(typeof change_id === "number");
    } catch (error: any) {
        if (error.status === UNAUTHORIZED) {
            return UNAUTHORIZED;
        } else {
            await common.show_error(t("change_phone.errors.generic"), error)
            return "cancel";
        }
    }

    return await validate_phone_number_prompt(change_id, validate_prompt, t);
}

async function validate_phone_number_prompt(id: number, prompt: () => Promise<string | null>, t: Translator): Promise<"ok" | "cancel" | typeof UNAUTHORIZED> {
    while (true) {
        let validation_code: string | null = await prompt();
        if (validation_code === null) {
            return "cancel";
        }

        if (isNaN(parseInt(validation_code))) {
            await UIkit.modal.alert(`<h2>${t("change_phone.errors.incorrect_code")}</h2>`);
        } else {
            try {
                await common.ajax("POST", `${window.apiBasePath}/member/validate_phone_number`, { id, validation_code });
                break;
            } catch (error: any) {
                if (error.status === UNAUTHORIZED) {
                    return UNAUTHORIZED;
                } else {
                    await common.show_error(t("change_phone.errors.incorrect_code"), error);
                }
            }
        }
    }

    return "ok";
}