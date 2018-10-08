import {showError, showSuccess} from "./message";


class Auth {

    getAccessToken() {
        return localStorage.token;
    }
    
    setToken(token) {
        localStorage.token = token;
        this.onChange(true);
    }

    getUsername() {
        return localStorage.username;
    }
    
    setUsername(username) {
        localStorage.username = username;
        this.onChange(true);
    }
    
    isLoggedIn() {
        return typeof(this.getAccessToken()) !== "undefined";
    }

    // Ask server to send a request on time login email to the user.
    requestPassword(username) {
        fetch(config.apiBasePath + "/oauth/resetpassword",
            {
                body: JSON.stringify({username}),
                method: "POST",
                headers: {'Content-Type': 'application/json; charset=UTF-8'},
            })
            .then(() => null, () => null);
    }
    
    login(username, password) {
        fetch(config.apiBasePath + "/oauth/token",
            {
                body:    JSON.stringify({grant_type: "password", username, password}),
                method:  "POST",
                headers: {'Content-Type': 'application/json; charset=UTF-8'},
            })
            .then(response => {
                if (response.status === 401) {
                    return Promise.reject("Felaktigt användarnamn eller lösenord.");
                }
                if (response.status === 429) {
                    return Promise.reject("För många misslyckades inloggningar. Kontot spärrat i 60 minuter.");
                }
                if (response.status === 200) {
                    return response.json();
                }
            
                return Promise.reject("Oväntad statuskod (" + response.status + ") från servern.");
            })
            .catch(msg => {
                showError("<h2>Inloggningen misslyckades</h2>" + msg);
                return Promise.reject(null);
            })
            .then(data => {
                this.setToken(data.access_token);
                this.setUsername(username);
                this.onChange(true);
            })
            .catch(() => null);
    }

    logout() {
        // Tell the server to delete the access token
        const token = this.getAccessToken();
        if (token) {
            fetch(config.apiBasePath + "/oauth/token/" + token,
                {
                    method:  "DELETE",
                    headers: {'Content-Type': 'application/json; charset=UTF-8', "Authorization": "Bearer " + token},
                })
                .then(() => null, () => null);
        }
        
        // Delete from localStorage and send user to login form.
        delete localStorage.token;
        this.onChange(false);
    }

    login_via_single_use_link(tag) {
        fetch(config.apiBasePath + "/member/send_access_token",
            {
                body:    JSON.stringify({user_tag: tag}),
                method:  "POST",
                headers: {'Content-Type': 'application/json; charset=UTF-8'},
            })
            .then(response => response.json().then(responseData => ({response, responseData})))
            .then(({response, responseData}) => {
                if (response.status === 200) {
                    showSuccess("Ett mail har skickats till dig med en inloggningslänk, använd den för att logga in.");
                }
                else if (responseData.status === "ambiguous") {
                    showError("<h2>Inloggningen misslyckades</h2>Det finns flera medlemmar som matchar '" + tag + "'. Välj något som är mer unikt, t.ex email eller medlemsnummer.");
                }
                else if (responseData.status === "not found") {
                    showError(
                        "<h2>Inloggningen misslyckades</h2>Ingen medlem med det namnet, email eller medlemsnummer existerar.");
                }
                else {
                    showError("<h2>Inloggningen misslyckades</h2>Tog emot ett oväntat svar från servern:<br><br>" + response.status + " " + response.statusText);
                }
            })
            .catch(() => {
                showError("<h2>Inloggningen misslyckades</h2>Kunde inte kommunicera med servern.");
            });
    }
    
    onChange() {
    }
}


const auth = new Auth();

export default auth;
