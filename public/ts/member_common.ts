import * as common from "./common";

export type date_t = string;

export type member_t = {
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

export async function LoadCurrentMemberInfo(): Promise<member_t> {
    return (await common.ajax("GET", window.apiBasePath + "/member/current", null)).data;
}