import Base from './Base';


export default class ServiceAccessToken extends Base {
}

ServiceAccessToken.model = {
    root: "/oauth/service_token",
    attributes: {
        service_name: "",
        access_token: "",
        permissions: "",
    },
};
