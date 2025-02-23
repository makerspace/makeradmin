import { post } from "../gateway";
import Base from "./Base";

export default class Member extends Base<Member> {
    member_id!: number;
    created_at!: Date | null;
    updated_at!: Date | null;
    member_number!: number;
    civicregno!: string;
    firstname!: string;
    lastname!: string;
    email!: string;
    phone!: string;
    address_street!: string;
    address_extra!: string;
    address_zipcode!: number | null;
    address_city!: string;
    address_country!: string;
    labaccess_agreement_at!: Date | null;
    pending_activation!: boolean;
    price_level!: string;

    static model = {
        id: "member_id",
        root: "/membership/member",
        attributes: {
            member_id: 0,
            created_at: null,
            updated_at: null,
            member_number: null,
            civicregno: "",
            firstname: "",
            lastname: "",
            email: "",
            phone: "",
            address_street: "",
            address_extra: "",
            address_zipcode: null,
            address_city: "",
            address_country: "se",
            labaccess_agreement_at: null,
            pending_activation: false,
            price_level: "normal",
        },
    };

    override deleteConfirmMessage() {
        return `Are you sure you want to delete member ${this.firstname} ${this.lastname}?`;
    }

    maybe_inform_member_before_changed_info() {
        const has_email = !!this.saved["email"];
        const email_is_changed = Object.prototype.hasOwnProperty.call(
            this.unsaved,
            "email",
        );
        if (has_email && email_is_changed) {
            post({
                url: "/member/send_updated_member_info",
                data: {
                    member_id: this.member_id,
                    msg_swe: `Din epost ändrades från ${this.saved["email"]} till ${this.unsaved["email"]}`,
                    msg_en: `Your email was updated from ${this.saved["email"]} to ${this.unsaved["email"]}`,
                },
                errorMessage:
                    "Error when sending email about updated information.",
                expectedDataStatus: "ok",
            });
        }
    }

    override async save() {
        this.maybe_inform_member_before_changed_info();
        await super.save();
    }

    override canSave() {
        return (
            this.isDirty() &&
            this.firstname.length > 0 &&
            this.email.length > 0 &&
            this.email.includes("@") &&
            this.email.includes(".")
        );
    }
}
