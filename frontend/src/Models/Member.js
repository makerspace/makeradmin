import Base from './Base';


export default class Member extends Base {
}

Member.model = {
    id: "member_id",
    root: "/membership/member",
    attributes: {
        created_at: "",
        updated_at: "",
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

