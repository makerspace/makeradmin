

declare var UIkit: any;

declare global {
	interface Window {
		stripeKey: string;
		apiBasePath: string;
		productId: number;
		transactionId: number;
	}
}

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
	if (typeof json.message_sv === 'string') return json.message_sv;
	if (typeof json.message === 'string') return json.message;
	if (typeof json.message_en === 'string') return json.message_en;
	return json.status;
}

export function ajax(type: string, url: string, data: object): Promise<any> {
	return new Promise((resolve, reject) => {
		var xhr = new XMLHttpRequest();
		xhr.open(type, url);
		xhr.setRequestHeader('Content-Type', 'application/json; charset=utf-8');
		xhr.setRequestHeader('Authorization', "Bearer " + localStorage.getItem("token"));
		xhr.onload = () => {
			if (xhr.status >= 200 && xhr.status <= 300) {
				resolve(JSON.parse(xhr.responseText));
			}
			else if (xhr.status === 401) {
			    reject({status: "unauthorized", message: JSON.parse(xhr.responseText).message})
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
			if (json.message == "Unauthorized") {
				callback(false, null);
			} else {
				UIkit.modal.alert("<h2>Error</h2>" + json.status + "\n" + json.message);
			}
		}
		);
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


export function logout() {
    localStorage.setItem("token", null);
    window.location.href = "/";
}


export function login(token: string) {
    localStorage.setItem("token", token);
}


