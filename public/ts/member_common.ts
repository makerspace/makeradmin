import * as common from "./common";

export type date_t = string;

export type member_t = {
    address_street: string,
    address_extra: string,
    address_zipcode: number,
    address_city: string,
    email: string,
    member_id: number,
    member_number: number,
    firstname: string,
    lastname: string,
    phone: string,
    pin_code: string,
    labaccess_agreement_at: date_t
};

export type membership_t = {
    membership_active: boolean,
    membership_end: date_t,
    labaccess_active: boolean,
    labaccess_end: date_t,
    special_labaccess_active: boolean,
    special_labaccess_end: date_t
};

export type group_t = {
    created_at: date_t,
    deleted_at: date_t | null,
    description: string,
    group_id: number,
    name: string,
    num_members: number,
    title: string,
    updated_at: string,
}

export type access_t = {
    in_org: boolean,
    pending_invite_count: number,
    access_permission_group_names: string[],
}

export async function LoadCurrentMemberInfo(): Promise<member_t> {
    return (await common.ajax("GET", window.apiBasePath + "/member/current", null)).data;
}

export async function LoadCurrentMembershipInfo(): Promise<membership_t> {
    return (await common.ajax("GET", window.apiBasePath + "/member/current/membership", null)).data;
}

export async function LoadCurrentMemberGroups(): Promise<group_t[]> {
    return (await common.ajax("GET", `${window.apiBasePath}/member/current/groups`)).data;
}

export async function LoadCurrentAccessInfo(): Promise<access_t> {
    return (await common.ajax("GET", window.apiBasePath + "/member/current/access", null)).data;
}
