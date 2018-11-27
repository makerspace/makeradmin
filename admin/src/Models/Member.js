import Base from './Base';


export default class Member extends Base {
    
    deleteConfirmMessage() {
        return `Are you sure you want to delete member ${this.firstname} ${this.lastname}?`;
    }
    
    canSave() {
        return this.isDirty() && this.email.length > 0 && this.firstname.length > 0;
    }
}

Member.model = {
    id: "member_id",
    root: "/membership/member",
    attributes: {
        member_id: 0,
        created_at: null,
        updated_at: null,
        member_number: "",
        civicregno: "",
        firstname: "",
        lastname: "",
        email: "",
        phone: "",
        address_street: "",
        address_extra: "",
        address_zipcode: "",
        address_city: "",
        address_country: "se",
    },
};
