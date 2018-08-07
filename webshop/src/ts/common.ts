declare var UIkit: any;

declare global {
	interface Window {
		stripeKey: string;
		apiBasePath: string;
	}
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
		xhr.setRequestHeader('Authorization', "Bearer " + localStorage.token);
		xhr.onload = () => {
			if (xhr.status >= 200 && xhr.status <= 300) {
				resolve(JSON.parse(xhr.responseText));
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
