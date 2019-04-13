import Cart from "./cart"

declare var UIkit: any;

declare global {
	interface Window {
		stripeKey: string;
		apiBasePath: string;
		productId: number;
		transactionId: number;
	}
}


export const UNAUTHORIZED = "unauthorized";


export function formatDateTime(str: any) {
    const options = {
        year: 'numeric', month: 'numeric', day: 'numeric',
        hour: 'numeric', minute: 'numeric', second: 'numeric',
        hour12: false
    };
        
    const parsed_date = Date.parse(str);
        
    // If the date was parsed successfully we should update the string
    if (!isNaN(parsed_date)) {
        return new Intl.DateTimeFormat("sv-SE", options).format(parsed_date);
    }
    return "";
}

export function get_error(json: any) {
	if (typeof json.message === 'string') return json.message;
	return json.status;
}

export function ajax(type: string, url: string, data: object): Promise<any> {
	return new Promise((resolve, reject) => {
		var xhr = new XMLHttpRequest();
		xhr.open(type, url);
		xhr.setRequestHeader('Content-Type', 'application/json; charset=utf-8');
		let token = localStorage.getItem("token");
		if (token) {
            xhr.setRequestHeader('Authorization', "Bearer " + token);
        }
		xhr.onload = () => {
			if (xhr.status >= 200 && xhr.status <= 300) {
				resolve(JSON.parse(xhr.responseText));
			}
			else if (xhr.status === 401 || xhr.status === 403) {
			    removeToken();
			    reject({status: UNAUTHORIZED, message: JSON.parse(xhr.responseText).message})
            }
			else reject(JSON.parse(xhr.responseText));
		};
		xhr.onerror = () => {
			reject(JSON.parse(xhr.responseText));
		};

		if (data == null) {
			xhr.send();
		} else {
			xhr.send(JSON.stringify(data));
		}
	});
}

export function documentLoaded() {
    return new Promise((resolve, reject) => {
        document.addEventListener('DOMContentLoaded', () => resolve());
    });
}

export function refreshLoggedIn(callback: (loggedIn: boolean, permissions: string[]) => void) {
	const apiBasePath = window.apiBasePath;
	ajax("GET", apiBasePath + "/member/current/permissions", null)
		.then(json => {
			callback(true, json.data.permissions);
		})
		.catch(json => {
			if (json.status === UNAUTHORIZED) {
				callback(false, null);
			} else {
				UIkit.modal.alert("<h2>Error</h2>" + json.status + "\n" + json.message);
			}
		}
		);
}

export function updateCartSum(cart: Cart, id2item: any) {
	const cartEmpty = cart.items.length == 0;
	const sidebarBuyBtn = document.querySelector(".sidebar-buy-btn");

	if (sidebarBuyBtn !== null) {
		sidebarBuyBtn.classList.toggle("cart-empty", cartEmpty);
	}

	if (cartEmpty) {
		document.querySelectorAll("#cart-sum").forEach(e => e.textContent = "");
    } else {
    	document.querySelectorAll("#cart-sum").forEach(e => e.textContent = " (" + Cart.formatCurrency(cart.sum(id2item)) + ")");
    }
}

export function getValue(selector: string): string {
	return (<HTMLInputElement>document.querySelector(selector)).value;
}

export function onGetAndDocumentLoaded(url: string, callback: any) {
    Promise
        .all([
            ajax("GET", window.apiBasePath + url, {}),
            documentLoaded()
        ])
        .catch(json => {
            UIkit.modal.alert("<h2>Error</h2>" + get_error(json));
        })
        .then((res: any) => {
            const data :any = res[0].data;
            callback(data);
        })
}

export function addSidebarListeners() {
	const logoutButton = document.querySelector("#logout");
	if (logoutButton != null) {
		logoutButton.addEventListener("click", (e) => {
	        e.preventDefault();
	        logout();
	    });
	}
}

export function removeToken() {
    delete localStorage.token;
}


export function logout() {
    removeToken();
    window.location.href = "/";
}


export function login(token: string) {
    localStorage.setItem("token", token);
}


