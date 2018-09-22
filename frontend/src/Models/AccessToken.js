import Base from './Base';


export default class AccessToken extends Base {
}

AccessToken.model = {
    root: "/oauth/token",
    attributes: {
        access_token: "",
        browser: "",
        ip: "",
        expires: null,
    },
};
